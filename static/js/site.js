/*
 * Jun Technology — front-end behaviour.
 *
 * A direct port of the original prototype's component logic to plain browser
 * JavaScript. Every animation, easing value and interaction is preserved; the
 * only additions are real form submission and data-driven project pop-ups.
 */
(function () {
  "use strict";

  var root = document.querySelector("[data-root]");
  if (!root) return;

  var cfg = readJSON("jt-config") || {};
  var PROJECTS = readJSON("jt-projects") || [];
  var cleanups = [];
  var theme = "dark";
  var rafCursor = null;
  var rafParticles = null;
  var rafMap = null;

  function readJSON(id) {
    var el = document.getElementById(id);
    if (!el) return null;
    try {
      return JSON.parse(el.textContent);
    } catch (e) {
      return null;
    }
  }

  function q(sel) {
    return Array.prototype.slice.call(root.querySelectorAll(sel));
  }

  function one(sel) {
    return root.querySelector(sel);
  }

  function on(el, ev, fn, opts) {
    if (!el) return;
    el.addEventListener(ev, fn, opts);
    cleanups.push(function () {
      el.removeEventListener(ev, fn, opts);
    });
  }

  // ------------------------------------------------------------------ //
  // Hover styles (replaces the prototype runtime's `style-hover` support)
  // ------------------------------------------------------------------ //
  function setupHoverStyles() {
    q("[style-hover]").forEach(function (el) {
      var decls = (el.getAttribute("style-hover") || "")
        .split(";")
        .map(function (part) {
          var idx = part.indexOf(":");
          if (idx < 0) return null;
          return [part.slice(0, idx).trim(), part.slice(idx + 1).trim()];
        })
        .filter(Boolean);
      if (!decls.length) return;
      var original = decls.map(function (d) {
        return el.style.getPropertyValue(d[0]);
      });
      on(el, "mouseenter", function () {
        decls.forEach(function (d) {
          el.style.setProperty(d[0], d[1]);
        });
      });
      on(el, "mouseleave", function () {
        decls.forEach(function (d, i) {
          if (original[i]) el.style.setProperty(d[0], original[i]);
          else el.style.removeProperty(d[0]);
        });
      });
    });
  }

  // ------------------------------------------------------------------ //
  // Theme
  // ------------------------------------------------------------------ //
  function applyTheme(mode) {
    theme = mode === "light" ? "light" : "dark";
    root.setAttribute("data-theme", theme);
    var fx = one("[data-fx]");
    if (fx) fx.style.opacity = theme === "light" ? ".42" : "1";
    var d = one('[data-theme-ico="dark"]');
    var l = one('[data-theme-ico="light"]');
    if (d && l) {
      var isLight = theme === "light";
      d.style.opacity = isLight ? "0" : "1";
      d.style.transform = isLight ? "rotate(90deg) scale(.5)" : "none";
      l.style.opacity = isLight ? "1" : "0";
      l.style.transform = isLight ? "none" : "rotate(-90deg) scale(.5)";
    }
    document.body.style.background = theme === "light" ? "#f2f5fb" : "#04060f";
  }

  function setupTheme() {
    var saved = null;
    try {
      saved = localStorage.getItem("jt-theme");
    } catch (e) {}
    applyTheme(saved || cfg.theme || "dark");
    var toggle = one("[data-theme-toggle]");
    on(toggle, "click", function () {
      applyTheme(theme === "dark" ? "light" : "dark");
      try {
        localStorage.setItem("jt-theme", theme);
      } catch (e) {}
    });
  }

  // ------------------------------------------------------------------ //
  // Loader
  // ------------------------------------------------------------------ //
  function setupLoader() {
    var loader = one("[data-loader]");
    if (!loader) return;
    var progress = 0;
    var timer = setInterval(function () {
      progress = Math.min(100, progress + 9 + Math.random() * 17);
      var bar = one("[data-loader-bar]");
      if (bar) bar.style.width = progress + "%";
      if (progress >= 100) {
        clearInterval(timer);
        setTimeout(exitLoader, 360);
      }
    }, 125);
    cleanups.push(function () {
      clearInterval(timer);
    });

    function exitLoader() {
      loader.style.opacity = "0";
      loader.style.transform = "scale(1.06)";
      setTimeout(function () {
        if (loader.parentNode) loader.parentNode.removeChild(loader);
      }, 680);
    }
  }

  // ------------------------------------------------------------------ //
  // Custom cursor
  // ------------------------------------------------------------------ //
  function setupCursor() {
    var dot = one("[data-cursor-dot]");
    var ring = one("[data-cursor-ring]");
    var txt = one("[data-cursor-text]");
    var spot = one("[data-spotlight]");
    if (!dot || !ring) return;

    var fine = window.matchMedia("(pointer:fine)").matches;
    var st = {
      x: innerWidth / 2,
      y: innerHeight / 2,
      rx: innerWidth / 2,
      ry: innerHeight / 2,
      sx: innerWidth / 2,
      sy: innerHeight / 2
    };

    // Splash cursor — a WebGL fluid simulation that the pointer stirs.
    // Skipped on touch pointers, when the dashboard turns the custom cursor
    // off, and on any driver the simulation cannot run on.
    var splashCanvas = one("[data-splash]");
    if (splashCanvas) {
      var wanted = fine && cfg.customCursor !== false && window.SplashCursor;
      var splash = wanted
        ? window.SplashCursor.start(splashCanvas, {
            palette: [
              window.SplashCursor.hexToRgb(cfg.accentPrimary, { r: 0.23, g: 0.51, b: 0.96 }),
              window.SplashCursor.hexToRgb(cfg.accentSecondary, { r: 0.49, g: 0.36, b: 1 })
            ]
          })
        : null;
      if (splash) cleanups.push(splash.destroy);
      else splashCanvas.style.display = "none";
    }

    if (fine && cfg.customCursor !== false) {
      document.documentElement.style.cursor = "none";
      on(
        document,
        "mousemove",
        function () {
          dot.style.opacity = "1";
          ring.style.opacity = "1";
        },
        { once: true }
      );
    }

    on(window, "mousemove", function (e) {
      st.x = e.clientX;
      st.y = e.clientY;
      if (spot) spot.style.opacity = "1";
    });

    on(window, "mousedown", function (e) {
      var rp = document.createElement("div");
      rp.style.cssText =
        "position:fixed;left:" + e.clientX + "px;top:" + e.clientY +
        "px;width:14px;height:14px;margin:-7px 0 0 -7px;border-radius:50%;" +
        "border:1px solid rgba(150,180,255,.7);z-index:201;pointer-events:none;" +
        "transition:transform .6s cubic-bezier(.16,1,.3,1),opacity .6s ease";
      document.body.appendChild(rp);
      requestAnimationFrame(function () {
        rp.style.transform = "scale(4.5)";
        rp.style.opacity = "0";
      });
      setTimeout(function () {
        if (rp.parentNode) rp.parentNode.removeChild(rp);
      }, 700);
    });

    (function tick() {
      st.rx += (st.x - st.rx) * 0.16;
      st.ry += (st.y - st.ry) * 0.16;
      st.sx += (st.x - st.sx) * 0.045;
      st.sy += (st.y - st.sy) * 0.045;
      dot.style.transform = "translate3d(" + st.x + "px," + st.y + "px,0)";
      ring.style.transform = "translate3d(" + st.rx + "px," + st.ry + "px,0)";
      if (spot) spot.style.transform = "translate3d(" + st.sx + "px," + st.sy + "px,0)";
      rafCursor = requestAnimationFrame(tick);
    })();
    cleanups.push(function () {
      cancelAnimationFrame(rafCursor);
    });

    function grow(size, label) {
      ring.style.width = size + "px";
      ring.style.height = size + "px";
      ring.style.margin = -size / 2 + "px 0 0 " + -size / 2 + "px";
      ring.style.background = label ? "rgba(59,130,246,.9)" : "rgba(150,180,255,.1)";
      ring.style.borderColor = label ? "rgba(59,130,246,.9)" : "rgba(150,180,255,.55)";
      if (txt) {
        txt.textContent = label || "";
        txt.style.opacity = label ? "1" : "0";
      }
      dot.style.opacity = label ? "0" : "1";
    }
    function reset() {
      grow(36, "");
    }

    q('[data-cursor="expand"], button, a, input, textarea').forEach(function (el) {
      on(el, "mouseenter", function () {
        grow(60, "");
      });
      on(el, "mouseleave", reset);
    });
    q("[data-cursor-label]").forEach(function (el) {
      on(el, "mouseenter", function () {
        grow(96, el.getAttribute("data-cursor-label"));
      });
      on(el, "mouseleave", reset);
    });
    q("h1, h2, h3, p").forEach(function (el) {
      on(el, "mouseenter", function () {
        ring.style.width = "3px";
        ring.style.height = "30px";
        ring.style.margin = "-15px 0 0 -1.5px";
        ring.style.borderRadius = "2px";
        ring.style.background = "rgba(150,180,255,.7)";
      });
      on(el, "mouseleave", function () {
        ring.style.borderRadius = "50%";
        reset();
      });
    });
  }

  // ------------------------------------------------------------------ //
  // Particle field
  // ------------------------------------------------------------------ //
  function setupParticles() {
    var cv = one("[data-particles]");
    if (!cv) return;
    if (cfg.showParticles === false) {
      cv.style.display = "none";
      return;
    }
    var ctx = cv.getContext("2d");
    var w = 0;
    var h = 0;
    var dpr = Math.min(2, window.devicePixelRatio || 1);
    var parts = [];
    var mx = -999;
    var my = -999;

    function size() {
      w = cv.clientWidth;
      h = cv.clientHeight;
      cv.width = w * dpr;
      cv.height = h * dpr;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      var n = Math.min(90, Math.round((w * h) / 20000));
      parts = [];
      for (var i = 0; i < n; i++) {
        parts.push({
          x: Math.random() * w,
          y: Math.random() * h,
          r: Math.random() * 1.7 + 0.5,
          vx: (Math.random() - 0.5) * 0.16,
          vy: -(Math.random() * 0.22 + 0.05),
          a: Math.random() * 0.5 + 0.2,
          c: Math.random() > 0.55 ? "124,92,255" : "96,165,250"
        });
      }
    }
    size();
    on(window, "resize", size);
    on(window, "mousemove", function (e) {
      mx = e.clientX;
      my = e.clientY;
    });

    (function draw() {
      ctx.clearRect(0, 0, w, h);
      parts.forEach(function (p) {
        p.x += p.vx;
        p.y += p.vy;
        var dx = p.x - mx;
        var dy = p.y - my;
        var d2 = dx * dx + dy * dy;
        if (d2 < 16000) {
          var f = (1 - d2 / 16000) * 0.9;
          p.x += (dx / Math.sqrt(d2 || 1)) * f;
          p.y += (dy / Math.sqrt(d2 || 1)) * f;
        }
        if (p.y < -10) {
          p.y = h + 10;
          p.x = Math.random() * w;
        }
        if (p.x < -10) p.x = w + 10;
        if (p.x > w + 10) p.x = -10;
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r, 0, 6.2832);
        ctx.fillStyle = "rgba(" + p.c + "," + p.a + ")";
        ctx.fill();
      });
      rafParticles = requestAnimationFrame(draw);
    })();
    cleanups.push(function () {
      cancelAnimationFrame(rafParticles);
    });
  }

  // ------------------------------------------------------------------ //
  // Scroll behaviour
  // ------------------------------------------------------------------ //
  function setupScroll() {
    var bar = one("[data-progress]");
    var nav = one("[data-nav]");
    var links = q("[data-navlink]");
    var pill = one("[data-nav-pill]");
    var secs = links
      .map(function (l) {
        return one("#" + l.getAttribute("data-navlink"));
      })
      .filter(Boolean);

    function movePill(a) {
      if (!pill || !a) return;
      pill.style.width = a.offsetWidth + "px";
      pill.style.transform = "translateX(" + a.offsetLeft + "px)";
      pill.style.opacity = "1";
    }

    function onScroll() {
      var y = window.scrollY;
      var max = document.documentElement.scrollHeight - innerHeight;
      if (bar) bar.style.width = (max > 0 ? (y / max) * 100 : 0) + "%";
      if (nav) nav.style.padding = y > 30 ? "10px 24px" : "20px 24px";
      var active = secs[0];
      secs.forEach(function (s) {
        if (s.getBoundingClientRect().top <= innerHeight * 0.4) active = s;
      });
      links.forEach(function (l) {
        var isOn = l.getAttribute("data-navlink") === (active && active.id);
        l.style.color = isOn ? "var(--tx,#fff)" : "var(--tx66,rgba(232,236,248,.66))";
        if (isOn) movePill(l);
      });
      q("[data-parallax]").forEach(function (el) {
        var rect = el.getBoundingClientRect();
        var prog = (rect.top + rect.height / 2 - innerHeight / 2) / innerHeight;
        el.style.transform =
          "translate3d(0," + prog * parseFloat(el.getAttribute("data-parallax")) + "px,0)";
      });
    }
    on(window, "scroll", onScroll, { passive: true });
    onScroll();

    q("[data-hero-parallax]").forEach(function (el) {
      var amt = parseFloat(el.getAttribute("data-hero-parallax"));
      on(window, "mousemove", function (e) {
        var nx = e.clientX / innerWidth - 0.5;
        var ny = e.clientY / innerHeight - 0.5;
        el.style.transform =
          "translate3d(" + nx * amt * 8 + "px," + ny * amt * 8 + "px,0)";
      });
    });

    var stack = one("[data-orbit-stack]");
    if (stack) {
      on(window, "mousemove", function (e) {
        var nx = e.clientX / innerWidth - 0.5;
        var ny = e.clientY / innerHeight - 0.5;
        stack.style.transform =
          "rotateY(" + nx * 16 + "deg) rotateX(" + -ny * 12 + "deg)";
      });
    }

    q('a[href^="#"]').forEach(function (a) {
      on(a, "click", function (e) {
        var href = a.getAttribute("href");
        if (!href || href === "#") return;
        var target = one(href) || document.querySelector(href);
        if (!target) return;
        e.preventDefault();
        var start = window.scrollY;
        var end =
          target.getBoundingClientRect().top + window.scrollY - (href === "#home" ? 0 : 90);
        var t0 = performance.now();
        (function step(now) {
          var p = Math.min(1, (now - t0) / 1100);
          var eased = 1 - Math.pow(1 - p, 4);
          window.scrollTo(0, start + (end - start) * eased);
          if (p < 1) requestAnimationFrame(step);
        })(performance.now());
        var menu = one("[data-mobile-menu]");
        if (menu) {
          menu.style.opacity = "0";
          menu.style.pointerEvents = "none";
        }
      });
    });
  }

  // ------------------------------------------------------------------ //
  // Reveal + counters
  // ------------------------------------------------------------------ //
  function setupReveal() {
    var io = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (en) {
          if (!en.isIntersecting) return;
          var el = en.target;
          var delay = parseInt(el.getAttribute("data-delay") || "0", 10);
          setTimeout(function () {
            el.style.opacity = "1";
            el.style.transform = "none";
            el.style.filter = "none";
          }, delay);
          io.unobserve(el);
        });
      },
      { threshold: 0.12, rootMargin: "0px 0px -8% 0px" }
    );
    q("[data-reveal]").forEach(function (el) {
      io.observe(el);
    });

    var cio = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (en) {
          if (!en.isIntersecting) return;
          var el = en.target;
          var target = parseFloat(el.getAttribute("data-count"));
          var suffix = el.getAttribute("data-suffix") || "";
          var t0 = performance.now();
          var dur = 1900;
          (function step(now) {
            var p = Math.min(1, (now - t0) / dur);
            var eased = 1 - Math.pow(1 - p, 3);
            el.textContent = Math.round(target * eased) + suffix;
            if (p < 1) requestAnimationFrame(step);
          })(performance.now());
          var icon = el.parentElement && el.parentElement.querySelector("[data-stat-icon]");
          if (icon) {
            icon.style.transform = "rotate(360deg)";
            setTimeout(function () {
              icon.style.transition = "none";
              icon.style.transform = "none";
            }, 800);
          }
          cio.unobserve(el);
        });
      },
      { threshold: 0.5 }
    );
    q("[data-count]").forEach(function (el) {
      cio.observe(el);
    });
  }

  // ------------------------------------------------------------------ //
  // Micro-interactions
  // ------------------------------------------------------------------ //
  function setupInteractions() {
    q("[data-magnetic]").forEach(function (el) {
      var amt = parseFloat(el.getAttribute("data-magnetic")) || 8;
      on(el, "mousemove", function (e) {
        var r = el.getBoundingClientRect();
        el.style.transform =
          "translate(" +
          ((e.clientX - r.left - r.width / 2) / r.width) * amt * 2 +
          "px," +
          ((e.clientY - r.top - r.height / 2) / r.height) * amt * 2 +
          "px) scale(1.03)";
      });
      on(el, "mouseleave", function () {
        el.style.transform = "none";
      });
      on(el, "mousedown", function () {
        el.style.transform += " scale(.96)";
      });
    });

    q("[data-ripple]").forEach(function (el) {
      on(el, "click", function (e) {
        var r = el.getBoundingClientRect();
        var s = document.createElement("span");
        s.style.cssText =
          "position:absolute;left:" + (e.clientX - r.left) + "px;top:" + (e.clientY - r.top) +
          "px;width:12px;height:12px;margin:-6px 0 0 -6px;border-radius:50%;" +
          "background:var(--w5,rgba(255,255,255,.5));pointer-events:none;" +
          "transition:transform .7s cubic-bezier(.16,1,.3,1),opacity .7s ease";
        el.appendChild(s);
        requestAnimationFrame(function () {
          s.style.transform = "scale(16)";
          s.style.opacity = "0";
        });
        setTimeout(function () {
          if (s.parentNode) s.parentNode.removeChild(s);
        }, 760);
      });
    });

    q("[data-tilt]").forEach(function (el) {
      var amt = parseFloat(el.getAttribute("data-tilt")) || 6;
      on(el, "mousemove", function (e) {
        var r = el.getBoundingClientRect();
        var nx = (e.clientX - r.left) / r.width - 0.5;
        var ny = (e.clientY - r.top) / r.height - 0.5;
        el.style.transform =
          "perspective(900px) rotateY(" + nx * amt + "deg) rotateX(" + -ny * amt +
          "deg) translateY(-6px)";
      });
      on(el, "mouseleave", function () {
        el.style.transform = "none";
      });
    });

    q("[data-service]").forEach(function (card) {
      var shine = card.querySelector("[data-shine]");
      var icon = card.querySelector("[data-svc-icon]");
      var arrow = card.querySelector("[data-arrow]");
      on(card, "mouseenter", function () {
        card.style.borderColor = "rgba(96,165,250,.42)";
        card.style.boxShadow = "0 40px 80px -40px rgba(59,130,246,.75)";
        if (shine) shine.style.left = "130%";
        if (icon) icon.style.transform = "rotate(-9deg) scale(1.1)";
        if (arrow) arrow.style.gap = "13px";
      });
      on(card, "mouseleave", function () {
        card.style.borderColor = "var(--w07,rgba(255,255,255,.07))";
        card.style.boxShadow = "none";
        if (shine) {
          shine.style.transition = "none";
          shine.style.left = "-60%";
          requestAnimationFrame(function () {
            shine.style.transition = "left .85s cubic-bezier(.16,1,.3,1)";
          });
        }
        if (icon) icon.style.transform = "none";
        if (arrow) arrow.style.gap = "7px";
      });
      var url = card.getAttribute("data-service-url");
      if (url) {
        card.style.cursor = "pointer";
        on(card, "click", function () {
          if (url.charAt(0) === "#") {
            var target = document.querySelector(url);
            if (target) target.scrollIntoView({ behavior: "smooth" });
          } else {
            window.open(url, "_blank", "noopener");
          }
        });
      }
    });

    q("[data-project]").forEach(function (card) {
      var zoom = card.querySelector("[data-zoom]");
      var scrim = card.querySelector("[data-scrim]");
      var up = card.querySelector("[data-slideup]");
      on(card, "mouseenter", function () {
        card.style.borderColor = "rgba(96,165,250,.45)";
        card.style.boxShadow = "0 50px 90px -44px rgba(59,130,246,.8)";
        if (zoom) zoom.style.transform = "scale(1.08)";
        if (scrim) scrim.style.opacity = ".9";
        // The description already occupies its space — only fade it in,
        // so the card cannot change size.
        if (up) up.style.opacity = "1";
      });
      on(card, "mouseleave", function () {
        card.style.borderColor = "var(--w07,rgba(255,255,255,.07))";
        card.style.boxShadow = "none";
        if (zoom) zoom.style.transform = "none";
        if (scrim) scrim.style.opacity = ".5";
        if (up) up.style.opacity = "0";
      });
      on(card, "click", function () {
        openModal(parseInt(card.getAttribute("data-project"), 10));
      });
    });

    q("[data-tcard]").forEach(function (c) {
      on(c, "mouseenter", function () {
        c.style.boxShadow = "0 40px 80px -40px rgba(59,130,246,.7)";
      });
      on(c, "mouseleave", function () {
        c.style.boxShadow = "none";
      });
    });

    var mq = one("[data-marquee]");
    var wrap = one("[data-marquee-wrap]");
    if (mq && wrap && mq.children.length) {
      mq.innerHTML += mq.innerHTML;
      on(wrap, "mouseenter", function () {
        mq.style.animationPlayState = "paused";
      });
      on(wrap, "mouseleave", function () {
        mq.style.animationPlayState = "running";
      });
    }

    q("[data-lift]").forEach(function (el) {
      on(el, "mouseenter", function () {
        el.style.transform = "translateY(-5px)";
      });
      on(el, "mouseleave", function () {
        el.style.transform = "none";
      });
    });

    q("[data-social]").forEach(function (el) {
      on(el, "mouseenter", function () {
        el.style.transform = "translateY(-4px) rotate(-8deg)";
      });
      on(el, "mouseleave", function () {
        el.style.transform = "none";
      });
    });

    q("[data-flink]").forEach(function (el) {
      on(el, "mouseenter", function () {
        el.style.transform = "translateX(5px)";
      });
      on(el, "mouseleave", function () {
        el.style.transform = "none";
      });
    });

    var logo = one("[data-logo-mark]");
    if (logo) {
      on(logo, "mouseenter", function () {
        logo.style.transform = "rotate(-12deg) scale(1.1)";
        logo.style.boxShadow = "0 12px 30px -10px rgba(59,130,246,1)";
      });
      on(logo, "mouseleave", function () {
        logo.style.transform = "none";
        logo.style.boxShadow = "none";
      });
    }

    var map = one("[data-map]");
    if (map) {
      var p1 = map.querySelector("[data-map-pulse]");
      var p2 = map.querySelector("[data-map-pulse2]");
      if (p1 || p2) {
        var t = 0;
        (function beat() {
          t += 0.02;
          var s = 1 + Math.sin(t) * 0.25;
          if (p1) {
            p1.setAttribute("r", String(10 * s));
            p1.setAttribute("opacity", String(0.4 - Math.sin(t) * 0.12));
          }
          if (p2) {
            p2.setAttribute("r", String(22 * s));
            p2.setAttribute("opacity", String(0.16 - Math.sin(t) * 0.07));
          }
          rafMap = requestAnimationFrame(beat);
        })();
        cleanups.push(function () {
          cancelAnimationFrame(rafMap);
        });
      }
    }
  }

  // ------------------------------------------------------------------ //
  // Portfolio filters
  // ------------------------------------------------------------------ //
  function setupFilters() {
    // Filtering is done by the server now — each pill is a link to the project
    // listing page. All this does is light up the one matching this page, and
    // hold the ticker still while the pointer is over it.
    var pills = q("[data-filter]");
    var active = cfg.activeCategory || "all";

    pills.forEach(function (pill) {
      var isOn = pill.getAttribute("data-filter") === active;
      pill.style.background = isOn
        ? "linear-gradient(120deg,#3b82f6,#6d5cff)"
        : "var(--w04,rgba(255,255,255,.04))";
      pill.style.color = isOn ? "#fff" : "var(--tx62,rgba(232,236,248,.62))";
      pill.style.borderColor = isOn ? "transparent" : "var(--w09,rgba(255,255,255,.09))";
      pill.style.transform = isOn ? "translateY(-2px)" : "none";
    });

    var track = one("[data-cat-track]");
    var zone = one("[data-cat-marquee]");
    if (!track || !zone) return;
    on(zone, "mouseenter", function () {
      track.style.animationPlayState = "paused";
    });
    on(zone, "mouseleave", function () {
      track.style.animationPlayState = "running";
    });
  }

  // ------------------------------------------------------------------ //
  // Project pop-up
  // ------------------------------------------------------------------ //
  function openModal(index) {
    var data = PROJECTS[index];
    var modalRoot = one("[data-modal-root]");
    if (!data || !modalRoot) return;

    var modal = one("[data-modal]");
    var card = one("[data-modal-card]");
    var hero = one("[data-modal-hero]");

    one("[data-modal-cat]").textContent = data.category || "";
    one("[data-modal-stack]").textContent = data.stack || "";
    one("[data-modal-title]").textContent = data.title || "";
    one("[data-modal-desc]").textContent = data.description || "";

    hero.innerHTML = "";
    if (data.image) {
      var img = document.createElement("img");
      img.src = data.image;
      img.alt = data.title || "";
      img.style.cssText = "display:block;width:100%;height:100%;object-fit:cover";
      hero.appendChild(img);
    }

    var metrics = one("[data-modal-metrics]");
    metrics.innerHTML = "";
    (data.metrics || []).forEach(function (m) {
      var box = document.createElement("div");
      box.style.cssText =
        "padding:16px 18px;border-radius:18px;border:1px solid var(--w07,rgba(255,255,255,.07));" +
        "background:var(--w035,rgba(255,255,255,.035))";
      var value = document.createElement("div");
      value.style.cssText = "font-family:'Sora',sans-serif;font-size:22px;font-weight:600";
      value.textContent = m.value;
      var label = document.createElement("div");
      label.style.cssText =
        "margin-top:4px;font-size:12px;color:var(--tx45,rgba(232,236,248,.45))";
      label.textContent = m.label;
      box.appendChild(value);
      box.appendChild(label);
      metrics.appendChild(box);
    });
    metrics.style.display = (data.metrics || []).length ? "grid" : "none";

    var gallery = one("[data-modal-gallery]");
    gallery.innerHTML = "";
    (data.gallery || []).forEach(function (g, i) {
      var delay = (0.1 + i * 0.12).toFixed(2) + "s";
      var cell = document.createElement("div");
      cell.setAttribute("data-gal", "");
      cell.style.cssText =
        "position:relative;aspect-ratio:4/3;border-radius:18px;overflow:hidden;" +
        "border:1px solid var(--w07,rgba(255,255,255,.07));opacity:0;transform:translateY(18px);" +
        "transition:opacity .7s ease " + delay + ",transform .7s cubic-bezier(.16,1,.3,1) " + delay;
      var gimg = document.createElement("img");
      gimg.src = g.image;
      gimg.alt = g.caption || "";
      gimg.loading = "lazy";
      gimg.style.cssText = "display:block;width:100%;height:100%;object-fit:cover";
      cell.appendChild(gimg);
      gallery.appendChild(cell);
    });
    gallery.style.display = (data.gallery || []).length ? "grid" : "none";

    modalRoot.style.display = "block";
    document.body.style.overflow = "hidden";
    requestAnimationFrame(function () {
      modal.style.opacity = "1";
      card.style.transform = "translateY(0) scale(1)";
      q("[data-gal]").forEach(function (g) {
        g.style.opacity = "1";
        g.style.transform = "translateY(0)";
      });
    });
  }

  function closeModal() {
    var modalRoot = one("[data-modal-root]");
    if (!modalRoot || modalRoot.style.display === "none") return;
    var modal = one("[data-modal]");
    var card = one("[data-modal-card]");
    modal.style.opacity = "0";
    card.style.transform = "translateY(26px) scale(.97)";
    setTimeout(function () {
      modalRoot.style.display = "none";
      document.body.style.overflow = "";
    }, 380);
  }

  function setupModal() {
    var modal = one("[data-modal]");
    if (!modal) return;
    on(one("[data-modal-close]"), "click", closeModal);
    on(modal, "click", function (e) {
      if (e.target === modal) closeModal();
    });
    on(document, "keydown", function (e) {
      if (e.key === "Escape") closeModal();
    });
  }

  // ------------------------------------------------------------------ //
  // Contact form
  // ------------------------------------------------------------------ //
  function setupForm() {
    var form = one("[data-form]");
    if (!form) return;
    form.noValidate = true;
    var fields = q("[data-field]");

    /**
     * Arriving from a service link — `/?service=<slug>#contact` — fills the
     * subject in so the visitor only has to say what they need. The slug is
     * looked up against the services on the page, so nothing from the URL is
     * ever written into the form verbatim.
     */
    function prefillFromService() {
      var match = /[?&]service=([\w-]+)/.exec(window.location.search);
      if (!match) return;
      var name = (cfg.services || {})[match[1]];
      if (!name) return;
      var subject = form.querySelector('[name="subject"]');
      if (!subject || subject.value) return;
      subject.value = name + " enquiry";
      var field = subject.closest("[data-field]");
      var label = field && field.querySelector("[data-label]");
      if (label) {
        label.style.transform = "translateY(-9px) scale(.74)";
        label.style.color = "rgba(143,180,255,.9)";
      }
      var message = form.querySelector('[name="message"]');
      if (message && !message.value) message.focus();
    }

    function float(label, isOn) {
      label.style.transform = isOn ? "translateY(-9px) scale(.74)" : "none";
      label.style.color = isOn
        ? "rgba(143,180,255,.9)"
        : "var(--tx42,rgba(232,236,248,.42))";
    }

    prefillFromService();

    function setError(field, msg) {
      var input = field.querySelector("[data-input]");
      var err = field.querySelector("[data-err]");
      err.textContent = msg;
      err.style.height = msg ? "18px" : "0";
      err.style.padding = msg ? "6px 0 0 2px" : "0";
      input.style.borderColor = msg
        ? "rgba(251,113,133,.7)"
        : input.value.trim()
        ? "rgba(74,222,128,.55)"
        : "var(--w1,rgba(255,255,255,.1))";
    }

    function validate(field, show) {
      var input = field.querySelector("[data-input]");
      var value = input.value.trim();
      var msg = "";
      if (input.required && !value) msg = "This field is required";
      else if (
        input.type === "email" &&
        value &&
        !/^[^@\s]+@[^@\s]+\.[a-z]{2,}$/i.test(value)
      )
        msg = "Enter a valid email address";
      if (show) setError(field, msg);
      return !msg;
    }

    fields.forEach(function (field) {
      var input = field.querySelector("[data-input]");
      var label = field.querySelector("[data-label]");
      on(input, "focus", function () {
        float(label, true);
        input.style.borderColor = "rgba(96,165,250,.75)";
        input.style.background = "rgba(59,130,246,.07)";
        input.style.boxShadow = "0 0 0 4px rgba(59,130,246,.12)";
      });
      on(input, "blur", function () {
        float(label, !!input.value);
        input.style.background = "var(--w03,rgba(255,255,255,.03))";
        input.style.boxShadow = "none";
        validate(field, true);
      });
      on(input, "input", function () {
        if (input.value) validate(field, true);
      });
    });

    on(form, "submit", function (e) {
      e.preventDefault();
      var ok = fields
        .map(function (f) {
          return validate(f, true);
        })
        .every(Boolean);
      if (!ok) {
        form.style.transform = "translateX(-6px)";
        setTimeout(function () {
          form.style.transition = "transform .4s cubic-bezier(.16,1,.3,1)";
          form.style.transform = "none";
        }, 90);
        return;
      }

      var btn = one("[data-submit]");
      var label = one("[data-submit-label]");
      var spinner = one("[data-spinner]");
      var check = one("[data-check]");
      label.style.opacity = "0";
      spinner.style.display = "flex";
      btn.disabled = true;

      var started = Date.now();
      fetch(form.getAttribute("action") || cfg.contactUrl, {
        method: "POST",
        body: new FormData(form),
        headers: { "X-Requested-With": "XMLHttpRequest" },
        credentials: "same-origin"
      })
        .then(function (res) {
          return res.json().then(function (body) {
            return { ok: res.ok, body: body };
          });
        })
        .then(function (result) {
          var wait = Math.max(0, 900 - (Date.now() - started));
          setTimeout(function () {
            spinner.style.display = "none";
            btn.disabled = false;
            if (result.ok && result.body.ok) {
              check.style.display = "flex";
              btn.style.background = "linear-gradient(120deg,#22c55e,#16a34a)";
              setTimeout(function () {
                fields.forEach(function (f) {
                  var input = f.querySelector("[data-input]");
                  var lab = f.querySelector("[data-label]");
                  input.value = "";
                  input.style.borderColor = "var(--w1,rgba(255,255,255,.1))";
                  float(lab, false);
                });
                check.style.display = "none";
                label.style.opacity = "1";
                btn.style.background = "linear-gradient(120deg,#3b82f6,#6d5cff)";
              }, 2400);
            } else {
              label.style.opacity = "1";
              showServerErrors(result.body && result.body.errors);
            }
          }, wait);
        })
        .catch(function () {
          spinner.style.display = "none";
          label.style.opacity = "1";
          btn.disabled = false;
          showServerErrors({ message: ["Something went wrong. Please try again."] });
        });
    });

    function showServerErrors(errors) {
      if (!errors) return;
      Object.keys(errors).forEach(function (name) {
        var input = form.querySelector('[name="' + name + '"]');
        var field = input && input.closest("[data-field]");
        if (field) setError(field, String(errors[name][0]));
      });
      form.style.transform = "translateX(-6px)";
      setTimeout(function () {
        form.style.transition = "transform .4s cubic-bezier(.16,1,.3,1)";
        form.style.transform = "none";
      }, 90);
    }
  }

  // ------------------------------------------------------------------ //
  // Mobile navigation
  // ------------------------------------------------------------------ //
  function setupNavExtras() {
    var burger = one("[data-burger]");
    var menu = one("[data-mobile-menu]");
    if (!burger || !menu) return;
    var lines = Array.prototype.slice.call(burger.querySelectorAll("[data-burger-line]"));
    var open = false;

    function sync() {
      burger.style.display = innerWidth <= 900 ? "flex" : "none";
    }
    sync();
    on(window, "resize", sync);

    on(burger, "click", function () {
      open = !open;
      menu.style.opacity = open ? "1" : "0";
      menu.style.pointerEvents = open ? "auto" : "none";
      lines[0].style.transform = open ? "translateY(3.5px) rotate(45deg)" : "none";
      lines[1].style.transform = open ? "translateY(-3px) rotate(-45deg)" : "none";
    });
  }

  // ------------------------------------------------------------------ //
  // Flip decks — the hero's featured projects and the about photo frame
  // ------------------------------------------------------------------ //
  function setupFlipDecks() {
    q("[data-flip]").forEach(function (deck) {
      var faces = Array.prototype.slice.call(
        deck.querySelectorAll("[data-flip-face]")
      );
      if (faces.length < 2) return;

      // The zone owns the dots and the hover pause — it is the frame around
      // the card, not the rotating deck itself.
      var zone =
        (deck.closest && deck.closest("[data-flip-zone]")) || deck.parentNode;
      var dotWrap = zone.querySelector("[data-flip-dots]");
      var dots = dotWrap
        ? Array.prototype.slice.call(dotWrap.querySelectorAll("[data-flip-dot]"))
        : [];
      var rest = dots.map(function (dot) {
        return dot.style.background;
      });

      var wait = parseInt(deck.getAttribute("data-flip-interval"), 10) || 4500;
      // Half the CSS transition — the moment the card is edge-on and the
      // outgoing face can be swapped for the incoming one unseen.
      var half =
        (parseFloat(getComputedStyle(deck).transitionDuration) * 1000 || 850) / 2;
      var index = 0;
      var rot = 0;
      var timer = null;
      var swap = null;
      var paused = false;

      faces.forEach(function (face, i) {
        face.style.transform = "rotateY(0deg)";
        face.style.visibility = i === 0 ? "visible" : "hidden";
      });

      function paint() {
        dots.forEach(function (dot, i) {
          var live = i === index;
          dot.style.width = live ? "20px" : "7px";
          dot.style.borderRadius = live ? "4px" : "50%";
          dot.style.background = live
            ? "linear-gradient(90deg,var(--a,#3b82f6),var(--b,#7c5cff))"
            : rest[i];
        });
      }

      function flipTo(next) {
        if (next === index || swap) return;
        rot += 180;
        deck.style.transform = "rotateY(" + rot + "deg)";
        var previous = index;
        index = next;
        paint();
        swap = setTimeout(function () {
          swap = null;
          faces[previous].style.visibility = "hidden";
          faces[next].style.transform = "rotateY(" + -rot + "deg)";
          faces[next].style.visibility = "visible";
        }, half);
      }

      function schedule() {
        clearTimeout(timer);
        timer = setTimeout(function () {
          if (!paused && !document.hidden) flipTo((index + 1) % faces.length);
          schedule();
        }, wait);
      }

      if (deck.getAttribute("data-flip-pause-hover") !== "0") {
        on(zone, "mouseenter", function () {
          paused = true;
        });
        on(zone, "mouseleave", function () {
          paused = false;
        });
      }

      dots.forEach(function (dot, i) {
        on(dot, "click", function () {
          flipTo(i);
          schedule();
        });
      });

      paint();
      schedule();
      cleanups.push(function () {
        clearTimeout(timer);
        clearTimeout(swap);
      });
    });
  }

  // ------------------------------------------------------------------ //
  // Boot
  // ------------------------------------------------------------------ //
  function init() {
    root.style.setProperty("--a", cfg.accentPrimary || "#3b82f6");
    root.style.setProperty("--b", cfg.accentSecondary || "#7c5cff");
    setupHoverStyles();
    setupTheme();
    setupLoader();
    setupCursor();
    setupParticles();
    setupScroll();
    setupReveal();
    setupInteractions();
    setupFlipDecks();
    setupFilters();
    setupModal();
    setupForm();
    setupNavExtras();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
