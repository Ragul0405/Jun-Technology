/*
 * Splash cursor — a WebGL fluid simulation that follows the pointer.
 *
 * Vanilla port of the "Splash Cursor" effect (React Bits), which itself wraps
 * Pavel Dobryakov's WebGL Fluid Simulation (MIT). Kept dependency-free and
 * framework-free so it drops straight into this project's plain-JS front end.
 *
 * Usage:  var handle = window.SplashCursor.start(canvasElement, options);
 *         handle.destroy();
 *
 * Returns null when WebGL is unavailable, so callers can fall back quietly.
 */
(function () {
  "use strict";

  var DEFAULTS = {
    SIM_RESOLUTION: 128,
    DYE_RESOLUTION: 1440,
    DENSITY_DISSIPATION: 3.5,
    VELOCITY_DISSIPATION: 2,
    PRESSURE: 0.1,
    PRESSURE_ITERATIONS: 20,
    CURL: 3,
    SPLAT_RADIUS: 0.2,
    SPLAT_FORCE: 6000,
    SHADING: true,
    COLOR_UPDATE_SPEED: 10
  };

  // ------------------------------------------------------------------ //
  // Shaders
  // ------------------------------------------------------------------ //
  var BASE_VERTEX = [
    "precision highp float;",
    "attribute vec2 aPosition;",
    "varying vec2 vUv;",
    "varying vec2 vL;",
    "varying vec2 vR;",
    "varying vec2 vT;",
    "varying vec2 vB;",
    "uniform vec2 texelSize;",
    "void main () {",
    "  vUv = aPosition * 0.5 + 0.5;",
    "  vL = vUv - vec2(texelSize.x, 0.0);",
    "  vR = vUv + vec2(texelSize.x, 0.0);",
    "  vT = vUv + vec2(0.0, texelSize.y);",
    "  vB = vUv - vec2(0.0, texelSize.y);",
    "  gl_Position = vec4(aPosition, 0.0, 1.0);",
    "}"
  ].join("\n");

  var COPY_SHADER = [
    "precision mediump float;",
    "precision mediump sampler2D;",
    "varying highp vec2 vUv;",
    "uniform sampler2D uTexture;",
    "void main () { gl_FragColor = texture2D(uTexture, vUv); }"
  ].join("\n");

  var CLEAR_SHADER = [
    "precision mediump float;",
    "precision mediump sampler2D;",
    "varying highp vec2 vUv;",
    "uniform sampler2D uTexture;",
    "uniform float value;",
    "void main () { gl_FragColor = value * texture2D(uTexture, vUv); }"
  ].join("\n");

  var DISPLAY_SHADER = [
    "precision highp float;",
    "precision highp sampler2D;",
    "varying vec2 vUv;",
    "varying vec2 vL;",
    "varying vec2 vR;",
    "varying vec2 vT;",
    "varying vec2 vB;",
    "uniform sampler2D uTexture;",
    "uniform vec2 texelSize;",
    "void main () {",
    "  vec3 c = texture2D(uTexture, vUv).rgb;",
    "#ifdef SHADING",
    "  vec3 lc = texture2D(uTexture, vL).rgb;",
    "  vec3 rc = texture2D(uTexture, vR).rgb;",
    "  vec3 tc = texture2D(uTexture, vT).rgb;",
    "  vec3 bc = texture2D(uTexture, vB).rgb;",
    "  float dx = length(rc) - length(lc);",
    "  float dy = length(tc) - length(bc);",
    "  vec3 n = normalize(vec3(dx, dy, length(texelSize)));",
    "  vec3 l = vec3(0.0, 0.0, 1.0);",
    "  float diffuse = clamp(dot(n, l) + 0.7, 0.7, 1.0);",
    "  c *= diffuse;",
    "#endif",
    "  float a = max(c.r, max(c.g, c.b));",
    "  gl_FragColor = vec4(c, a);",
    "}"
  ].join("\n");

  var SPLAT_SHADER = [
    "precision highp float;",
    "precision highp sampler2D;",
    "varying vec2 vUv;",
    "uniform sampler2D uTarget;",
    "uniform float aspectRatio;",
    "uniform vec3 color;",
    "uniform vec2 point;",
    "uniform float radius;",
    "void main () {",
    "  vec2 p = vUv - point.xy;",
    "  p.x *= aspectRatio;",
    "  vec3 splat = exp(-dot(p, p) / radius) * color;",
    "  vec3 base = texture2D(uTarget, vUv).xyz;",
    "  gl_FragColor = vec4(base + splat, 1.0);",
    "}"
  ].join("\n");

  var ADVECTION_SHADER = [
    "precision highp float;",
    "precision highp sampler2D;",
    "varying vec2 vUv;",
    "uniform sampler2D uVelocity;",
    "uniform sampler2D uSource;",
    "uniform vec2 texelSize;",
    "uniform vec2 dyeTexelSize;",
    "uniform float dt;",
    "uniform float dissipation;",
    "vec4 bilerp (sampler2D sam, vec2 uv, vec2 tsize) {",
    "  vec2 st = uv / tsize - 0.5;",
    "  vec2 iuv = floor(st);",
    "  vec2 fuv = fract(st);",
    "  vec4 a = texture2D(sam, (iuv + vec2(0.5, 0.5)) * tsize);",
    "  vec4 b = texture2D(sam, (iuv + vec2(1.5, 0.5)) * tsize);",
    "  vec4 c = texture2D(sam, (iuv + vec2(0.5, 1.5)) * tsize);",
    "  vec4 d = texture2D(sam, (iuv + vec2(1.5, 1.5)) * tsize);",
    "  return mix(mix(a, b, fuv.x), mix(c, d, fuv.x), fuv.y);",
    "}",
    "void main () {",
    "#ifdef MANUAL_FILTERING",
    "  vec2 coord = vUv - dt * bilerp(uVelocity, vUv, texelSize).xy * texelSize;",
    "  vec4 result = bilerp(uSource, coord, dyeTexelSize);",
    "#else",
    "  vec2 coord = vUv - dt * texture2D(uVelocity, vUv).xy * texelSize;",
    "  vec4 result = texture2D(uSource, coord);",
    "#endif",
    "  float decay = 1.0 + dissipation * dt;",
    "  gl_FragColor = result / decay;",
    "}"
  ].join("\n");

  var DIVERGENCE_SHADER = [
    "precision mediump float;",
    "precision mediump sampler2D;",
    "varying highp vec2 vUv;",
    "varying highp vec2 vL;",
    "varying highp vec2 vR;",
    "varying highp vec2 vT;",
    "varying highp vec2 vB;",
    "uniform sampler2D uVelocity;",
    "void main () {",
    "  float L = texture2D(uVelocity, vL).x;",
    "  float R = texture2D(uVelocity, vR).x;",
    "  float T = texture2D(uVelocity, vT).y;",
    "  float B = texture2D(uVelocity, vB).y;",
    "  vec2 C = texture2D(uVelocity, vUv).xy;",
    "  if (vL.x < 0.0) { L = -C.x; }",
    "  if (vR.x > 1.0) { R = -C.x; }",
    "  if (vT.y > 1.0) { T = -C.y; }",
    "  if (vB.y < 0.0) { B = -C.y; }",
    "  float div = 0.5 * (R - L + T - B);",
    "  gl_FragColor = vec4(div, 0.0, 0.0, 1.0);",
    "}"
  ].join("\n");

  var CURL_SHADER = [
    "precision mediump float;",
    "precision mediump sampler2D;",
    "varying highp vec2 vUv;",
    "varying highp vec2 vL;",
    "varying highp vec2 vR;",
    "varying highp vec2 vT;",
    "varying highp vec2 vB;",
    "uniform sampler2D uVelocity;",
    "void main () {",
    "  float L = texture2D(uVelocity, vL).y;",
    "  float R = texture2D(uVelocity, vR).y;",
    "  float T = texture2D(uVelocity, vT).x;",
    "  float B = texture2D(uVelocity, vB).x;",
    "  float vorticity = R - L - T + B;",
    "  gl_FragColor = vec4(0.5 * vorticity, 0.0, 0.0, 1.0);",
    "}"
  ].join("\n");

  var VORTICITY_SHADER = [
    "precision highp float;",
    "precision highp sampler2D;",
    "varying vec2 vUv;",
    "varying vec2 vL;",
    "varying vec2 vR;",
    "varying vec2 vT;",
    "varying vec2 vB;",
    "uniform sampler2D uVelocity;",
    "uniform sampler2D uCurl;",
    "uniform float curl;",
    "uniform float dt;",
    "void main () {",
    "  float L = texture2D(uCurl, vL).x;",
    "  float R = texture2D(uCurl, vR).x;",
    "  float T = texture2D(uCurl, vT).x;",
    "  float B = texture2D(uCurl, vB).x;",
    "  float C = texture2D(uCurl, vUv).x;",
    "  vec2 force = 0.5 * vec2(abs(T) - abs(B), abs(R) - abs(L));",
    "  force /= length(force) + 0.0001;",
    "  force *= curl * C;",
    "  force.y *= -1.0;",
    "  vec2 velocity = texture2D(uVelocity, vUv).xy;",
    "  velocity += force * dt;",
    "  velocity = min(max(velocity, -1000.0), 1000.0);",
    "  gl_FragColor = vec4(velocity, 0.0, 1.0);",
    "}"
  ].join("\n");

  var PRESSURE_SHADER = [
    "precision mediump float;",
    "precision mediump sampler2D;",
    "varying highp vec2 vUv;",
    "varying highp vec2 vL;",
    "varying highp vec2 vR;",
    "varying highp vec2 vT;",
    "varying highp vec2 vB;",
    "uniform sampler2D uPressure;",
    "uniform sampler2D uDivergence;",
    "void main () {",
    "  float L = texture2D(uPressure, vL).x;",
    "  float R = texture2D(uPressure, vR).x;",
    "  float T = texture2D(uPressure, vT).x;",
    "  float B = texture2D(uPressure, vB).x;",
    "  float divergence = texture2D(uDivergence, vUv).x;",
    "  float pressure = (L + R + B + T - divergence) * 0.25;",
    "  gl_FragColor = vec4(pressure, 0.0, 0.0, 1.0);",
    "}"
  ].join("\n");

  var GRADIENT_SUBTRACT_SHADER = [
    "precision mediump float;",
    "precision mediump sampler2D;",
    "varying highp vec2 vUv;",
    "varying highp vec2 vL;",
    "varying highp vec2 vR;",
    "varying highp vec2 vT;",
    "varying highp vec2 vB;",
    "uniform sampler2D uPressure;",
    "uniform sampler2D uVelocity;",
    "void main () {",
    "  float L = texture2D(uPressure, vL).x;",
    "  float R = texture2D(uPressure, vR).x;",
    "  float T = texture2D(uPressure, vT).x;",
    "  float B = texture2D(uPressure, vB).x;",
    "  vec2 velocity = texture2D(uVelocity, vUv).xy;",
    "  velocity.xy -= vec2(R - L, T - B);",
    "  gl_FragColor = vec4(velocity, 0.0, 1.0);",
    "}"
  ].join("\n");

  // ------------------------------------------------------------------ //
  // Small helpers
  // ------------------------------------------------------------------ //
  function hexToRgb(hex, fallback) {
    var m = /^#?([\da-f]{2})([\da-f]{2})([\da-f]{2})$/i.exec(hex || "");
    if (!m) return fallback;
    return {
      r: parseInt(m[1], 16) / 255,
      g: parseInt(m[2], 16) / 255,
      b: parseInt(m[3], 16) / 255
    };
  }

  function HSVtoRGB(h, s, v) {
    var i = Math.floor(h * 6);
    var f = h * 6 - i;
    var p = v * (1 - s);
    var q = v * (1 - f * s);
    var t = v * (1 - (1 - f) * s);
    switch (i % 6) {
      case 0: return { r: v, g: t, b: p };
      case 1: return { r: q, g: v, b: p };
      case 2: return { r: p, g: v, b: t };
      case 3: return { r: p, g: q, b: v };
      case 4: return { r: t, g: p, b: v };
      default: return { r: v, g: p, b: q };
    }
  }

  function scaleByPixelRatio(input) {
    var ratio = window.devicePixelRatio || 1;
    return Math.floor(input * ratio);
  }

  // ------------------------------------------------------------------ //
  // Entry point
  // ------------------------------------------------------------------ //
  function start(canvas, options) {
    if (!canvas || !canvas.getContext) return null;

    var config = {};
    var key;
    for (key in DEFAULTS) config[key] = DEFAULTS[key];
    for (key in options || {}) config[key] = options[key];

    var ctx = getWebGLContext(canvas);
    if (!ctx) return null;
    var gl = ctx.gl;
    var ext = ctx.ext;

    if (!ext.supportLinearFiltering) {
      config.DYE_RESOLUTION = 256;
      config.SHADING = false;
    }

    // -------------------------------------------------------------- //
    // GL plumbing
    // -------------------------------------------------------------- //
    function getWebGLContext(cv) {
      var params = {
        alpha: true,
        depth: false,
        stencil: false,
        antialias: false,
        preserveDrawingBuffer: false
      };
      var context = cv.getContext("webgl2", params);
      var isWebGL2 = !!context;
      if (!isWebGL2) {
        context =
          cv.getContext("webgl", params) ||
          cv.getContext("experimental-webgl", params);
      }
      if (!context) return null;

      var halfFloat = null;
      var supportLinearFiltering = false;
      if (isWebGL2) {
        context.getExtension("EXT_color_buffer_float");
        supportLinearFiltering = !!context.getExtension("OES_texture_float_linear");
      } else {
        halfFloat = context.getExtension("OES_texture_half_float");
        supportLinearFiltering = !!context.getExtension(
          "OES_texture_half_float_linear"
        );
      }
      context.clearColor(0.0, 0.0, 0.0, 0.0);

      var halfFloatTexType = isWebGL2
        ? context.HALF_FLOAT
        : halfFloat && halfFloat.HALF_FLOAT_OES;
      if (!halfFloatTexType) return null;

      var formatRGBA;
      var formatRG;
      var formatR;
      if (isWebGL2) {
        formatRGBA = getSupportedFormat(context, context.RGBA16F, context.RGBA, halfFloatTexType);
        formatRG = getSupportedFormat(context, context.RG16F, context.RG, halfFloatTexType);
        formatR = getSupportedFormat(context, context.R16F, context.RED, halfFloatTexType);
      } else {
        formatRGBA = getSupportedFormat(context, context.RGBA, context.RGBA, halfFloatTexType);
        formatRG = formatRGBA;
        formatR = formatRGBA;
      }
      if (!formatRGBA) return null;

      return {
        gl: context,
        ext: {
          formatRGBA: formatRGBA,
          formatRG: formatRG,
          formatR: formatR,
          halfFloatTexType: halfFloatTexType,
          supportLinearFiltering: supportLinearFiltering
        }
      };
    }

    function getSupportedFormat(context, internalFormat, format, type) {
      if (!supportRenderTextureFormat(context, internalFormat, format, type)) {
        if (typeof WebGL2RenderingContext === "undefined") return null;
        switch (internalFormat) {
          case context.R16F:
            return getSupportedFormat(context, context.RG16F, context.RG, type);
          case context.RG16F:
            return getSupportedFormat(context, context.RGBA16F, context.RGBA, type);
          default:
            return null;
        }
      }
      return { internalFormat: internalFormat, format: format };
    }

    function supportRenderTextureFormat(context, internalFormat, format, type) {
      var texture = context.createTexture();
      context.bindTexture(context.TEXTURE_2D, texture);
      context.texParameteri(context.TEXTURE_2D, context.TEXTURE_MIN_FILTER, context.NEAREST);
      context.texParameteri(context.TEXTURE_2D, context.TEXTURE_MAG_FILTER, context.NEAREST);
      context.texParameteri(context.TEXTURE_2D, context.TEXTURE_WRAP_S, context.CLAMP_TO_EDGE);
      context.texParameteri(context.TEXTURE_2D, context.TEXTURE_WRAP_T, context.CLAMP_TO_EDGE);
      context.texImage2D(context.TEXTURE_2D, 0, internalFormat, 4, 4, 0, format, type, null);

      var fbo = context.createFramebuffer();
      context.bindFramebuffer(context.FRAMEBUFFER, fbo);
      context.framebufferTexture2D(
        context.FRAMEBUFFER, context.COLOR_ATTACHMENT0, context.TEXTURE_2D, texture, 0
      );
      var status = context.checkFramebufferStatus(context.FRAMEBUFFER);
      context.bindFramebuffer(context.FRAMEBUFFER, null);
      context.deleteFramebuffer(fbo);
      context.deleteTexture(texture);
      return status === context.FRAMEBUFFER_COMPLETE;
    }

    function compileShader(type, source, keywords) {
      var body = source;
      if (keywords) {
        var prefix = "";
        keywords.forEach(function (word) {
          prefix += "#define " + word + "\n";
        });
        body = prefix + source;
      }
      var shader = gl.createShader(type);
      gl.shaderSource(shader, body);
      gl.compileShader(shader);
      if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) {
        throw new Error(gl.getShaderInfoLog(shader) || "shader compile failed");
      }
      return shader;
    }

    function createProgram(vertex, fragment) {
      var program = gl.createProgram();
      gl.attachShader(program, vertex);
      gl.attachShader(program, fragment);
      gl.linkProgram(program);
      if (!gl.getProgramParameter(program, gl.LINK_STATUS)) {
        throw new Error(gl.getProgramInfoLog(program) || "program link failed");
      }
      return program;
    }

    function getUniforms(program) {
      var uniforms = {};
      var count = gl.getProgramParameter(program, gl.ACTIVE_UNIFORMS);
      for (var i = 0; i < count; i++) {
        var name = gl.getActiveUniform(program, i).name;
        uniforms[name] = gl.getUniformLocation(program, name);
      }
      return uniforms;
    }

    function Program(vertex, fragment) {
      this.program = createProgram(vertex, fragment);
      this.uniforms = getUniforms(this.program);
    }
    Program.prototype.bind = function () {
      gl.useProgram(this.program);
    };

    /** The display program is rebuilt when its #defines change. */
    function Material(vertex, fragmentSource) {
      this.vertexShader = vertex;
      this.fragmentShaderSource = fragmentSource;
      this.programs = {};
      this.activeProgram = null;
      this.uniforms = {};
    }
    Material.prototype.setKeywords = function (keywords) {
      var hash = 0;
      for (var i = 0; i < keywords.length; i++) {
        var word = keywords[i];
        for (var j = 0; j < word.length; j++) {
          hash = ((hash << 5) - hash + word.charCodeAt(j)) | 0;
        }
      }
      var program = this.programs[hash];
      if (program == null) {
        var fragment = compileShader(gl.FRAGMENT_SHADER, this.fragmentShaderSource, keywords);
        program = createProgram(this.vertexShader, fragment);
        this.programs[hash] = program;
      }
      if (program === this.activeProgram) return;
      this.uniforms = getUniforms(program);
      this.activeProgram = program;
    };
    Material.prototype.bind = function () {
      gl.useProgram(this.activeProgram);
    };

    // -------------------------------------------------------------- //
    // Fullscreen quad
    // -------------------------------------------------------------- //
    var quadBuffer = gl.createBuffer();
    var quadElements = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, quadBuffer);
    gl.bufferData(
      gl.ARRAY_BUFFER, new Float32Array([-1, -1, -1, 1, 1, 1, 1, -1]), gl.STATIC_DRAW
    );
    gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, quadElements);
    gl.bufferData(
      gl.ELEMENT_ARRAY_BUFFER, new Uint16Array([0, 1, 2, 0, 2, 3]), gl.STATIC_DRAW
    );
    gl.vertexAttribPointer(0, 2, gl.FLOAT, false, 0, 0);
    gl.enableVertexAttribArray(0);

    function blit(target, clear) {
      if (target == null) {
        gl.viewport(0, 0, gl.drawingBufferWidth, gl.drawingBufferHeight);
        gl.bindFramebuffer(gl.FRAMEBUFFER, null);
      } else {
        gl.viewport(0, 0, target.width, target.height);
        gl.bindFramebuffer(gl.FRAMEBUFFER, target.fbo);
      }
      if (clear) {
        gl.clearColor(0.0, 0.0, 0.0, 1.0);
        gl.clear(gl.COLOR_BUFFER_BIT);
      }
      gl.drawElements(gl.TRIANGLES, 6, gl.UNSIGNED_SHORT, 0);
    }

    // -------------------------------------------------------------- //
    // Framebuffers
    // -------------------------------------------------------------- //
    function createFBO(w, h, internalFormat, format, type, param) {
      gl.activeTexture(gl.TEXTURE0);
      var texture = gl.createTexture();
      gl.bindTexture(gl.TEXTURE_2D, texture);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, param);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, param);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
      gl.texImage2D(gl.TEXTURE_2D, 0, internalFormat, w, h, 0, format, type, null);

      var fbo = gl.createFramebuffer();
      gl.bindFramebuffer(gl.FRAMEBUFFER, fbo);
      gl.framebufferTexture2D(
        gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.TEXTURE_2D, texture, 0
      );
      gl.viewport(0, 0, w, h);
      gl.clear(gl.COLOR_BUFFER_BIT);

      return {
        texture: texture,
        fbo: fbo,
        width: w,
        height: h,
        texelSizeX: 1.0 / w,
        texelSizeY: 1.0 / h,
        attach: function (id) {
          gl.activeTexture(gl.TEXTURE0 + id);
          gl.bindTexture(gl.TEXTURE_2D, texture);
          return id;
        }
      };
    }

    function createDoubleFBO(w, h, internalFormat, format, type, param) {
      var fbo1 = createFBO(w, h, internalFormat, format, type, param);
      var fbo2 = createFBO(w, h, internalFormat, format, type, param);
      return {
        width: w,
        height: h,
        texelSizeX: fbo1.texelSizeX,
        texelSizeY: fbo1.texelSizeY,
        read: fbo1,
        write: fbo2,
        swap: function () {
          var temp = this.read;
          this.read = this.write;
          this.write = temp;
        }
      };
    }

    function resizeFBO(target, w, h, internalFormat, format, type, param) {
      var newFBO = createFBO(w, h, internalFormat, format, type, param);
      copyProgram.bind();
      gl.uniform1i(copyProgram.uniforms.uTexture, target.attach(0));
      blit(newFBO);
      return newFBO;
    }

    function resizeDoubleFBO(target, w, h, internalFormat, format, type, param) {
      if (target.width === w && target.height === h) return target;
      target.read = resizeFBO(target.read, w, h, internalFormat, format, type, param);
      target.write = createFBO(w, h, internalFormat, format, type, param);
      target.width = w;
      target.height = h;
      target.texelSizeX = 1.0 / w;
      target.texelSizeY = 1.0 / h;
      return target;
    }

    function getResolution(resolution) {
      var aspectRatio = gl.drawingBufferWidth / gl.drawingBufferHeight;
      if (aspectRatio < 1) aspectRatio = 1.0 / aspectRatio;
      var min = Math.round(resolution);
      var max = Math.round(resolution * aspectRatio);
      if (gl.drawingBufferWidth > gl.drawingBufferHeight) {
        return { width: max, height: min };
      }
      return { width: min, height: max };
    }

    // -------------------------------------------------------------- //
    // Programs
    // -------------------------------------------------------------- //
    var baseVertexShader;
    var copyProgram;
    var clearProgram;
    var splatProgram;
    var advectionProgram;
    var divergenceProgram;
    var curlProgram;
    var vorticityProgram;
    var pressureProgram;
    var gradienSubtractProgram;
    var displayMaterial;

    try {
      baseVertexShader = compileShader(gl.VERTEX_SHADER, BASE_VERTEX);
      copyProgram = new Program(baseVertexShader, compileShader(gl.FRAGMENT_SHADER, COPY_SHADER));
      clearProgram = new Program(baseVertexShader, compileShader(gl.FRAGMENT_SHADER, CLEAR_SHADER));
      splatProgram = new Program(baseVertexShader, compileShader(gl.FRAGMENT_SHADER, SPLAT_SHADER));
      advectionProgram = new Program(
        baseVertexShader,
        compileShader(
          gl.FRAGMENT_SHADER,
          ADVECTION_SHADER,
          ext.supportLinearFiltering ? null : ["MANUAL_FILTERING"]
        )
      );
      divergenceProgram = new Program(
        baseVertexShader, compileShader(gl.FRAGMENT_SHADER, DIVERGENCE_SHADER)
      );
      curlProgram = new Program(baseVertexShader, compileShader(gl.FRAGMENT_SHADER, CURL_SHADER));
      vorticityProgram = new Program(
        baseVertexShader, compileShader(gl.FRAGMENT_SHADER, VORTICITY_SHADER)
      );
      pressureProgram = new Program(
        baseVertexShader, compileShader(gl.FRAGMENT_SHADER, PRESSURE_SHADER)
      );
      gradienSubtractProgram = new Program(
        baseVertexShader, compileShader(gl.FRAGMENT_SHADER, GRADIENT_SUBTRACT_SHADER)
      );
      displayMaterial = new Material(baseVertexShader, DISPLAY_SHADER);
      displayMaterial.setKeywords(config.SHADING ? ["SHADING"] : []);
    } catch (err) {
      return null; // a driver we cannot satisfy — the caller falls back
    }

    // -------------------------------------------------------------- //
    // Simulation state
    // -------------------------------------------------------------- //
    var dye;
    var velocity;
    var divergence;
    var curl;
    var pressure;

    function initFramebuffers() {
      var simRes = getResolution(config.SIM_RESOLUTION);
      var dyeRes = getResolution(config.DYE_RESOLUTION);
      var texType = ext.halfFloatTexType;
      var rgba = ext.formatRGBA;
      var rg = ext.formatRG;
      var r = ext.formatR;
      var filtering = ext.supportLinearFiltering ? gl.LINEAR : gl.NEAREST;
      gl.disable(gl.BLEND);

      dye = dye
        ? resizeDoubleFBO(dye, dyeRes.width, dyeRes.height, rgba.internalFormat, rgba.format, texType, filtering)
        : createDoubleFBO(dyeRes.width, dyeRes.height, rgba.internalFormat, rgba.format, texType, filtering);

      velocity = velocity
        ? resizeDoubleFBO(velocity, simRes.width, simRes.height, rg.internalFormat, rg.format, texType, filtering)
        : createDoubleFBO(simRes.width, simRes.height, rg.internalFormat, rg.format, texType, filtering);

      divergence = createFBO(simRes.width, simRes.height, r.internalFormat, r.format, texType, gl.NEAREST);
      curl = createFBO(simRes.width, simRes.height, r.internalFormat, r.format, texType, gl.NEAREST);
      pressure = createDoubleFBO(simRes.width, simRes.height, r.internalFormat, r.format, texType, gl.NEAREST);
    }

    function resizeCanvas() {
      var width = scaleByPixelRatio(canvas.clientWidth);
      var height = scaleByPixelRatio(canvas.clientHeight);
      if (canvas.width !== width || canvas.height !== height) {
        canvas.width = width;
        canvas.height = height;
        return true;
      }
      return false;
    }

    // -------------------------------------------------------------- //
    // Pointers
    // -------------------------------------------------------------- //
    function Pointer() {
      this.id = -1;
      this.texcoordX = 0;
      this.texcoordY = 0;
      this.prevTexcoordX = 0;
      this.prevTexcoordY = 0;
      this.deltaX = 0;
      this.deltaY = 0;
      this.down = false;
      this.moved = false;
      this.color = { r: 0, g: 0, b: 0 };
    }

    var pointers = [new Pointer()];
    var palette = (options && options.palette) || null;
    var colorSeed = 0;

    function nextColor() {
      var c;
      if (palette && palette.length) {
        // Cycle the brand accents, jittering each so splashes stay lively.
        var base = palette[colorSeed++ % palette.length];
        var jitter = 0.85 + Math.random() * 0.4;
        c = { r: base.r * jitter, g: base.g * jitter, b: base.b * jitter };
      } else {
        c = HSVtoRGB(Math.random(), 1.0, 1.0);
      }
      return { r: c.r * 0.15, g: c.g * 0.15, b: c.b * 0.15 };
    }

    function correctDeltaX(delta) {
      var aspectRatio = canvas.width / canvas.height;
      return aspectRatio < 1 ? delta * aspectRatio : delta;
    }

    function correctDeltaY(delta) {
      var aspectRatio = canvas.width / canvas.height;
      return aspectRatio > 1 ? delta / aspectRatio : delta;
    }

    function updatePointerMoveData(pointer, posX, posY, color) {
      pointer.prevTexcoordX = pointer.texcoordX;
      pointer.prevTexcoordY = pointer.texcoordY;
      pointer.texcoordX = posX / canvas.width;
      pointer.texcoordY = 1.0 - posY / canvas.height;
      pointer.deltaX = correctDeltaX(pointer.texcoordX - pointer.prevTexcoordX);
      pointer.deltaY = correctDeltaY(pointer.texcoordY - pointer.prevTexcoordY);
      pointer.moved = Math.abs(pointer.deltaX) > 0 || Math.abs(pointer.deltaY) > 0;
      pointer.color = color;
    }

    function updatePointerDownData(pointer, id, posX, posY) {
      pointer.id = id;
      pointer.down = true;
      pointer.moved = false;
      pointer.texcoordX = posX / canvas.width;
      pointer.texcoordY = 1.0 - posY / canvas.height;
      pointer.prevTexcoordX = pointer.texcoordX;
      pointer.prevTexcoordY = pointer.texcoordY;
      pointer.deltaX = 0;
      pointer.deltaY = 0;
      pointer.color = nextColor();
    }

    // -------------------------------------------------------------- //
    // Splats
    // -------------------------------------------------------------- //
    function correctRadius(radius) {
      var aspectRatio = canvas.width / canvas.height;
      return aspectRatio > 1 ? radius * aspectRatio : radius;
    }

    function splat(x, y, dx, dy, color) {
      splatProgram.bind();
      gl.uniform1i(splatProgram.uniforms.uTarget, velocity.read.attach(0));
      gl.uniform1f(splatProgram.uniforms.aspectRatio, canvas.width / canvas.height);
      gl.uniform2f(splatProgram.uniforms.point, x, y);
      gl.uniform3f(splatProgram.uniforms.color, dx, dy, 0.0);
      gl.uniform1f(
        splatProgram.uniforms.radius, correctRadius(config.SPLAT_RADIUS / 100.0)
      );
      blit(velocity.write);
      velocity.swap();

      gl.uniform1i(splatProgram.uniforms.uTarget, dye.read.attach(0));
      gl.uniform3f(splatProgram.uniforms.color, color.r, color.g, color.b);
      blit(dye.write);
      dye.swap();
    }

    function splatPointer(pointer) {
      var dx = pointer.deltaX * config.SPLAT_FORCE;
      var dy = pointer.deltaY * config.SPLAT_FORCE;
      splat(pointer.texcoordX, pointer.texcoordY, dx, dy, pointer.color);
    }

    function clickSplat(pointer) {
      var color = nextColor();
      color.r *= 10.0;
      color.g *= 10.0;
      color.b *= 10.0;
      var dx = 10 * (Math.random() - 0.5);
      var dy = 30 * (Math.random() - 0.5);
      splat(pointer.texcoordX, pointer.texcoordY, dx, dy, color);
    }

    function applyInputs() {
      for (var i = 0; i < pointers.length; i++) {
        var pointer = pointers[i];
        if (pointer.moved) {
          pointer.moved = false;
          splatPointer(pointer);
        }
      }
    }

    // -------------------------------------------------------------- //
    // Step
    // -------------------------------------------------------------- //
    function step(dt) {
      gl.disable(gl.BLEND);

      curlProgram.bind();
      gl.uniform2f(curlProgram.uniforms.texelSize, velocity.texelSizeX, velocity.texelSizeY);
      gl.uniform1i(curlProgram.uniforms.uVelocity, velocity.read.attach(0));
      blit(curl);

      vorticityProgram.bind();
      gl.uniform2f(vorticityProgram.uniforms.texelSize, velocity.texelSizeX, velocity.texelSizeY);
      gl.uniform1i(vorticityProgram.uniforms.uVelocity, velocity.read.attach(0));
      gl.uniform1i(vorticityProgram.uniforms.uCurl, curl.attach(1));
      gl.uniform1f(vorticityProgram.uniforms.curl, config.CURL);
      gl.uniform1f(vorticityProgram.uniforms.dt, dt);
      blit(velocity.write);
      velocity.swap();

      divergenceProgram.bind();
      gl.uniform2f(divergenceProgram.uniforms.texelSize, velocity.texelSizeX, velocity.texelSizeY);
      gl.uniform1i(divergenceProgram.uniforms.uVelocity, velocity.read.attach(0));
      blit(divergence);

      clearProgram.bind();
      gl.uniform1i(clearProgram.uniforms.uTexture, pressure.read.attach(0));
      gl.uniform1f(clearProgram.uniforms.value, config.PRESSURE);
      blit(pressure.write);
      pressure.swap();

      pressureProgram.bind();
      gl.uniform2f(pressureProgram.uniforms.texelSize, velocity.texelSizeX, velocity.texelSizeY);
      gl.uniform1i(pressureProgram.uniforms.uDivergence, divergence.attach(0));
      for (var i = 0; i < config.PRESSURE_ITERATIONS; i++) {
        gl.uniform1i(pressureProgram.uniforms.uPressure, pressure.read.attach(1));
        blit(pressure.write);
        pressure.swap();
      }

      gradienSubtractProgram.bind();
      gl.uniform2f(
        gradienSubtractProgram.uniforms.texelSize, velocity.texelSizeX, velocity.texelSizeY
      );
      gl.uniform1i(gradienSubtractProgram.uniforms.uPressure, pressure.read.attach(0));
      gl.uniform1i(gradienSubtractProgram.uniforms.uVelocity, velocity.read.attach(1));
      blit(velocity.write);
      velocity.swap();

      advectionProgram.bind();
      gl.uniform2f(
        advectionProgram.uniforms.texelSize, velocity.texelSizeX, velocity.texelSizeY
      );
      if (!ext.supportLinearFiltering) {
        gl.uniform2f(
          advectionProgram.uniforms.dyeTexelSize, velocity.texelSizeX, velocity.texelSizeY
        );
      }
      var velocityId = velocity.read.attach(0);
      gl.uniform1i(advectionProgram.uniforms.uVelocity, velocityId);
      gl.uniform1i(advectionProgram.uniforms.uSource, velocityId);
      gl.uniform1f(advectionProgram.uniforms.dt, dt);
      gl.uniform1f(advectionProgram.uniforms.dissipation, config.VELOCITY_DISSIPATION);
      blit(velocity.write);
      velocity.swap();

      if (!ext.supportLinearFiltering) {
        gl.uniform2f(advectionProgram.uniforms.dyeTexelSize, dye.texelSizeX, dye.texelSizeY);
      }
      gl.uniform1i(advectionProgram.uniforms.uVelocity, velocity.read.attach(0));
      gl.uniform1i(advectionProgram.uniforms.uSource, dye.read.attach(1));
      gl.uniform1f(advectionProgram.uniforms.dissipation, config.DENSITY_DISSIPATION);
      blit(dye.write);
      dye.swap();
    }

    function render() {
      // Premultiplied-style blending so the fluid sits over the page without
      // painting a black rectangle behind itself.
      gl.blendFunc(gl.ONE, gl.ONE_MINUS_SRC_ALPHA);
      gl.enable(gl.BLEND);

      displayMaterial.bind();
      if (config.SHADING) {
        gl.uniform2f(
          displayMaterial.uniforms.texelSize,
          1.0 / gl.drawingBufferWidth,
          1.0 / gl.drawingBufferHeight
        );
      }
      gl.uniform1i(displayMaterial.uniforms.uTexture, dye.read.attach(0));
      blit(null);
    }

    // -------------------------------------------------------------- //
    // Loop
    // -------------------------------------------------------------- //
    var lastUpdate = Date.now();
    var colorTimer = 0;
    var raf = null;
    var running = true;

    function calcDeltaTime() {
      var now = Date.now();
      var dt = (now - lastUpdate) / 1000;
      lastUpdate = now;
      return Math.min(dt, 0.016666);
    }

    function updateColors(dt) {
      colorTimer += dt * config.COLOR_UPDATE_SPEED;
      if (colorTimer >= 1) {
        colorTimer = colorTimer % 1;
        pointers.forEach(function (pointer) {
          pointer.color = nextColor();
        });
      }
    }

    function updateFrame() {
      var dt = calcDeltaTime();
      if (resizeCanvas()) initFramebuffers();
      updateColors(dt);
      applyInputs();
      step(dt);
      render();
      if (running) raf = requestAnimationFrame(updateFrame);
    }

    // -------------------------------------------------------------- //
    // Wiring
    // -------------------------------------------------------------- //
    var listeners = [];

    function listen(target, type, handler) {
      target.addEventListener(type, handler);
      listeners.push(function () {
        target.removeEventListener(type, handler);
      });
    }

    listen(window, "mousemove", function (e) {
      var pointer = pointers[0];
      var posX = scaleByPixelRatio(e.clientX);
      var posY = scaleByPixelRatio(e.clientY);
      var color = pointer.color;
      if (!pointer.down) {
        updatePointerDownData(pointer, -1, posX, posY);
        color = pointer.color;
      }
      updatePointerMoveData(pointer, posX, posY, color);
    });

    listen(window, "mousedown", function (e) {
      var pointer = pointers[0];
      var posX = scaleByPixelRatio(e.clientX);
      var posY = scaleByPixelRatio(e.clientY);
      updatePointerDownData(pointer, -1, posX, posY);
      clickSplat(pointer);
    });

    listen(document, "visibilitychange", function () {
      // Coming back from a hidden tab must not replay a huge time step.
      lastUpdate = Date.now();
    });

    resizeCanvas();
    initFramebuffers();
    updateFrame();

    return {
      destroy: function () {
        running = false;
        if (raf) cancelAnimationFrame(raf);
        listeners.forEach(function (off) {
          off();
        });
        listeners = [];
      }
    };
  }

  window.SplashCursor = { start: start, hexToRgb: hexToRgb };
})();
