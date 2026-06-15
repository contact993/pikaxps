"""Tiny inline i18n: t("English", "한국어") returns the active language's string.

Language is chosen once at startup (saved setting, else the OS locale) and
changed from the Help ▸ Language menu (applied on restart). Keeping the
translations inline at each call site avoids a separate key catalogue.
"""
from __future__ import annotations

from PySide6.QtCore import QLocale, QSettings

_LANG: str | None = None
LANGUAGES = {"en": "English", "ko": "한국어"}


def _settings() -> QSettings:
    return QSettings("xpsfit", "PikaXPS")


def current_language() -> str:
    global _LANG
    if _LANG is None:
        saved = _settings().value("language", "")
        if saved in LANGUAGES:
            _LANG = saved
        else:
            _LANG = "ko" if QLocale.system().name().startswith("ko") else "en"
    return _LANG


def set_language(lang: str) -> None:
    """Persist the language choice (takes effect on next launch)."""
    global _LANG
    if lang in LANGUAGES:
        _LANG = lang
        _settings().setValue("language", lang)


def t(en: str, ko: str) -> str:
    return ko if current_language() == "ko" else en


def restart_app() -> None:
    """Relaunch the process so the new language applies cleanly."""
    import os
    import sys

    if getattr(sys, "frozen", False):
        os.execv(sys.executable, [sys.executable])
    else:
        os.execv(sys.executable, [sys.executable, *sys.argv])
