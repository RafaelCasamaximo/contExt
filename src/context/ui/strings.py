import json
from pathlib import Path


DEFAULT_LOCALE = "pt-BR"
FALLBACK_LOCALE = "en"

_TRANSLATIONS_PATH = Path(__file__).with_name("translations.json")
_TRANSLATIONS = json.loads(_TRANSLATIONS_PATH.read_text(encoding="utf-8"))
_current_locale = DEFAULT_LOCALE

OPTION_GROUPS = {
    "approximation_mode": ["none", "simple", "tc89_l1", "tc89_kcos"],
    "sobel_axis": ["x_axis", "y_axis", "xy_axis"],
    "interpolation_mode": ["nearest", "bilinear", "bicubic", "quadratic", "spline3"],
    "zoom_node_size": ["div2", "div4", "div8", "div16"],
    "theme": ["light", "dark"],
}


def available_locales():
    return tuple(_TRANSLATIONS.keys())


def set_locale(locale: str) -> str:
    global _current_locale
    if locale not in _TRANSLATIONS:
        locale = FALLBACK_LOCALE
    _current_locale = locale
    return _current_locale


def get_locale() -> str:
    return _current_locale


def _locale_data(locale: str):
    return _TRANSLATIONS.get(locale) or _TRANSLATIONS[FALLBACK_LOCALE]


def _lookup(locale: str, key: str):
    current = _locale_data(locale)
    for part in key.split("."):
        current = current[part]
    return current


def t(key: str, locale: str | None = None, **params) -> str:
    locale = locale or _current_locale
    try:
        value = _lookup(locale, key)
    except KeyError:
        value = _lookup(FALLBACK_LOCALE, key)
    if params:
        return value.format(**params)
    return value


def fmt(key: str, **params) -> str:
    return t(f"formats.{key}", **params)


def option_labels(group: str, locale: str | None = None) -> list[str]:
    locale = locale or _current_locale
    return [t(f"options.{group}.{key}", locale=locale) for key in OPTION_GROUPS[group]]


def option_label(group: str, key: str, locale: str | None = None) -> str:
    locale = locale or _current_locale
    return t(f"options.{group}.{key}", locale=locale)


def option_key(group: str, label: str, locale: str | None = None) -> str:
    locale = locale or _current_locale
    for key in OPTION_GROUPS[group]:
        if option_label(group, key, locale=locale) == label:
            return key
    for key in OPTION_GROUPS[group]:
        if option_label(group, key, locale=FALLBACK_LOCALE) == label:
            return key
    return OPTION_GROUPS[group][0]


def translate_option_value(group: str, label: str, from_locale: str, to_locale: str | None = None) -> str:
    key = option_key(group, label, locale=from_locale)
    return option_label(group, key, locale=to_locale or _current_locale)
