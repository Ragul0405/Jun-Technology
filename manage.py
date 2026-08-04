#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def _make_console_unicode_safe():
    """
    Stop a Windows console's legacy code page from killing a command.

    A default cp1252 console cannot encode characters that appear all over this
    project's content and help text — “ ” — and Python raises
    UnicodeEncodeError mid-write, aborting the command with a traceback.
    Switching the streams to UTF-8 fixes it outright; `errors="replace"` keeps
    even an exotic character from ever being fatal.
    """
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):  # already wrapped, or not a TTY
            pass


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    _make_console_unicode_safe()
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:  # pragma: no cover
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and available "
            "on your PYTHONPATH environment variable? Did you forget to "
            "activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
