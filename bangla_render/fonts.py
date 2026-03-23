# bangla_render/fonts.py
from __future__ import annotations

import os
from dataclasses import dataclass, asdict, field
from typing import Any, Dict, List, Optional, Sequence, Tuple

from .backend import ensure_qt_application

try:
    from PySide6.QtGui import (
        QFont,
        QFontDatabase,
        QFontMetrics,
        QImage,
        QPainter,
        QColor,
    )
    from PySide6.QtCore import Qt
    QT_FONT_AVAILABLE = True
    QT_FONT_IMPORT_ERROR = None
except Exception as e:  # pragma: no cover
    QFont = None
    QFontDatabase = None
    QFontMetrics = None
    QImage = None
    QPainter = None
    QColor = None
    Qt = None
    QT_FONT_AVAILABLE = False
    QT_FONT_IMPORT_ERROR = e


# ---------------------------------------------------------------------
# Module state
# ---------------------------------------------------------------------

_DEFAULT_FONT_FAMILY = "Noto Sans Bengali"
_DEFAULT_FONT_PATH: Optional[str] = None

_REGISTERED_FONT_FILES: List[str] = []
_REGISTERED_FONT_FAMILIES: Dict[str, List[str]] = {}  # font_path -> families


BANGLA_FONT_CANDIDATES = [
    "Nirmala UI",
    "Noto Sans Bengali",
    "Noto Serif Bengali",
    "SolaimanLipi",
    "Kalpurush",
    "Nikosh",
    "Vrinda",
    "Siyam Rupali",
    "AdorshoLipi",
    "Hind Siliguri",
    "Mukti",
    "Akaash",
    "Lohit Bengali",
]


@dataclass
class FontValidationResult:
    ok: bool
    requested_family: Optional[str] = None
    requested_path: Optional[str] = None
    resolved_family: Optional[str] = None
    path_registered: bool = False
    family_exists: bool = False
    glyph_metrics_nonempty: bool = False
    rendered_nonempty: bool = False
    exact_family_match: bool = False
    warnings: List[str] = field(default_factory=list)
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------

def _ensure_font_runtime() -> None:
    ensure_qt_application()
    if not QT_FONT_AVAILABLE:
        raise RuntimeError(
            "Qt font classes are not available. "
            f"Original import error: {QT_FONT_IMPORT_ERROR}"
        )


def _font_db() -> QFontDatabase:
    _ensure_font_runtime()
    return QFontDatabase()


def _normalize_path(path: str) -> str:
    return os.path.abspath(os.path.expanduser(path))


def _all_font_families() -> List[str]:
    db = _font_db()
    try:
        fams = list(db.families())
    except Exception:
        fams = []
    return sorted(set(str(f) for f in fams))


def _family_exists(family: str) -> bool:
    family = str(family).strip()
    if not family:
        return False
    return family in _all_font_families()


def _case_insensitive_family_lookup(family: str) -> Optional[str]:
    family = str(family).strip()
    if not family:
        return None

    families = _all_font_families()
    if family in families:
        return family

    lower_map = {f.lower(): f for f in families}
    return lower_map.get(family.lower())


def _register_font_file(font_path: str) -> Tuple[bool, List[str], Optional[str]]:
    """
    Register a font file with Qt.

    Returns
    -------
    (ok, families, error_message)
    """
    _ensure_font_runtime()

    path = _normalize_path(font_path)

    if not os.path.exists(path):
        return False, [], f"Font file does not exist: {path}"

    if not os.path.isfile(path):
        return False, [], f"Font path is not a file: {path}"

    try:
        font_id = QFontDatabase.addApplicationFont(path)
    except Exception as e:
        return False, [], f"Failed to register font '{path}': {e}"

    if font_id < 0:
        return False, [], f"Qt could not register font file: {path}"

    try:
        families = list(QFontDatabase.applicationFontFamilies(font_id))
    except Exception:
        families = []

    families = [str(f) for f in families]

    if path not in _REGISTERED_FONT_FILES:
        _REGISTERED_FONT_FILES.append(path)
    _REGISTERED_FONT_FAMILIES[path] = families

    return True, families, None


def _try_render_sample(
    family: str,
    sample_text: str,
    font_size: int = 24,
    color: str = "black",
) -> Tuple[bool, bool, Optional[str]]:
    """
    Best-effort validation: measure and render sample Bengali text.

    Returns
    -------
    (glyph_metrics_nonempty, rendered_nonempty, error_message)
    """
    _ensure_font_runtime()

    try:
        font = QFont(family, font_size)
        fm = QFontMetrics(font)

        rect = fm.boundingRect(sample_text)
        glyph_metrics_nonempty = rect.width() > 0 and rect.height() > 0

        w = max(1, rect.width() + 20)
        h = max(1, rect.height() + 20)

        img = QImage(w, h, QImage.Format.Format_ARGB32)
        img.fill(Qt.GlobalColor.transparent)

        painter = QPainter(img)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.TextAntialiasing)
        painter.setFont(font)
        painter.setPen(QColor(color))

        x = 10 - rect.left()
        y = 10 - rect.top()
        painter.drawText(x, y, sample_text)
        painter.end()

        rendered_nonempty = img.width() > 0 and img.height() > 0
        return glyph_metrics_nonempty, rendered_nonempty, None

    except Exception as e:
        return False, False, str(e)


def _resolve_from_candidates() -> Optional[str]:
    for name in BANGLA_FONT_CANDIDATES:
        match = _case_insensitive_family_lookup(name)
        if match:
            return match
    return None


# ---------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------

def register_font(font_path: str) -> List[str]:
    """
    Register a single .ttf / .otf font file with Qt.
    """
    ok, families, error = _register_font_file(font_path)
    if not ok:
        raise RuntimeError(error)
    return families


def register_fonts(font_paths: Sequence[str]) -> Dict[str, List[str]]:
    """
    Register multiple font files.
    """
    results: Dict[str, List[str]] = {}
    errors: List[str] = []

    for path in font_paths:
        ok, families, error = _register_font_file(path)
        norm = _normalize_path(path)
        if ok:
            results[norm] = families
        else:
            errors.append(error or f"Failed to register {norm}")

    if errors and not results:
        raise RuntimeError("\n".join(errors))

    return results


def list_available_fonts() -> List[str]:
    """
    Return all font families currently visible to Qt.
    """
    return _all_font_families()


def list_registered_fonts() -> Dict[str, List[str]]:
    """
    Return application-registered font files and their family names.
    """
    return dict(_REGISTERED_FONT_FAMILIES)


def list_bangla_candidate_fonts(installed_only: bool = True) -> List[str]:
    """
    Return candidate Bengali font families.
    """
    if not installed_only:
        return list(BANGLA_FONT_CANDIDATES)

    found: List[str] = []
    for name in BANGLA_FONT_CANDIDATES:
        match = _case_insensitive_family_lookup(name)
        if match:
            found.append(match)

    seen = set()
    out = []
    for f in found:
        if f not in seen:
            seen.add(f)
            out.append(f)
    return out


def set_default_font(
    font_family: Optional[str] = None,
    font_path: Optional[str] = None,
) -> str:
    """
    Set package-wide default font.
    """
    global _DEFAULT_FONT_FAMILY, _DEFAULT_FONT_PATH

    if font_path:
        families = register_font(font_path)
        if not families:
            raise RuntimeError(
                f"Font file was registered but no family names were returned: {font_path}"
            )

        if font_family:
            match = _case_insensitive_family_lookup(font_family)
            if not match:
                raise RuntimeError(
                    f"Requested font family '{font_family}' was not found after "
                    f"registering '{font_path}'. Available families from this file: {families}"
                )
            resolved = match
        else:
            resolved = families[0]

        _DEFAULT_FONT_FAMILY = resolved
        _DEFAULT_FONT_PATH = _normalize_path(font_path)
        return resolved

    if font_family:
        match = _case_insensitive_family_lookup(font_family)
        if not match:
            raise RuntimeError(
                f"Font family '{font_family}' was not found. "
                "Use list_available_fonts() or register_font()."
            )
        _DEFAULT_FONT_FAMILY = match
        _DEFAULT_FONT_PATH = None
        return match

    match = _case_insensitive_family_lookup(_DEFAULT_FONT_FAMILY)
    if match:
        _DEFAULT_FONT_FAMILY = match
        return match

    resolved = _resolve_from_candidates()
    if resolved:
        _DEFAULT_FONT_FAMILY = resolved
        _DEFAULT_FONT_PATH = None
        return resolved

    raise RuntimeError(
        "Could not determine a default Bengali font. "
        "Please install or register a Bengali-capable font."
    )


def get_default_font() -> Dict[str, Optional[str]]:
    """
    Return current package-wide font defaults.
    """
    return {
        "font_family": _DEFAULT_FONT_FAMILY,
        "font_path": _DEFAULT_FONT_PATH,
    }


def resolve_font(
    font_family: Optional[str] = None,
    font_path: Optional[str] = None,
) -> str:
    """
    Resolve a usable font family for rendering.
    """
    global _DEFAULT_FONT_FAMILY, _DEFAULT_FONT_PATH

    if font_path:
        families = register_font(font_path)
        if not families:
            raise RuntimeError(
                f"Registered font file but found no family names: {font_path}"
            )

        if font_family:
            match = _case_insensitive_family_lookup(font_family)
            if not match:
                raise RuntimeError(
                    f"Requested family '{font_family}' not found after registering '{font_path}'. "
                    f"Families from file: {families}"
                )
            return match

        return families[0]

    if font_family:
        match = _case_insensitive_family_lookup(font_family)
        if match:
            return match
        raise RuntimeError(
            f"Font family '{font_family}' not found. "
            "Use list_available_fonts() or register_font()."
        )

    match = _case_insensitive_family_lookup(_DEFAULT_FONT_FAMILY)
    if match:
        return match

    resolved = _resolve_from_candidates()
    if resolved:
        _DEFAULT_FONT_FAMILY = resolved
        _DEFAULT_FONT_PATH = None
        return resolved

    raise RuntimeError(
        "No usable Bengali font family could be resolved. "
        "Install or register a Bengali-capable font, then try again."
    )


def validate_font(
    font_family: Optional[str] = None,
    font_path: Optional[str] = None,
    sample_text: str = "বাংলা লেখা পরীক্ষা",
    font_size: int = 24,
) -> Dict[str, Any]:
    """
    Validate a font family or font file with a practical render test.
    """
    result = FontValidationResult(
        ok=False,
        requested_family=font_family,
        requested_path=_normalize_path(font_path) if font_path else None,
    )

    try:
        _ensure_font_runtime()
    except Exception as e:
        result.error = str(e)
        return result.to_dict()

    registered_families: List[str] = []
    path_registered = False

    if font_path:
        ok, families, error = _register_font_file(font_path)
        path_registered = ok
        registered_families = families

        if not ok:
            result.error = error
            result.path_registered = False
            return result.to_dict()

        result.path_registered = True

    try:
        resolved = resolve_font(font_family=font_family, font_path=font_path)
    except Exception as e:
        result.error = str(e)
        if registered_families:
            result.warnings.append(
                f"Families detected from font file: {registered_families}"
            )
        result.path_registered = path_registered
        return result.to_dict()

    result.resolved_family = resolved
    result.path_registered = path_registered
    result.family_exists = _family_exists(resolved)

    if font_family:
        exact = resolved == font_family
        result.exact_family_match = exact
        if not exact:
            result.warnings.append(
                f"Requested family '{font_family}' resolved to '{resolved}'."
            )

    glyph_ok, render_ok, render_error = _try_render_sample(
        family=resolved,
        sample_text=sample_text,
        font_size=font_size,
    )
    result.glyph_metrics_nonempty = glyph_ok
    result.rendered_nonempty = render_ok

    if render_error:
        result.error = render_error
    if not glyph_ok:
        result.warnings.append(
            "Font metrics for the sample text were empty or zero-sized."
        )
    if not render_ok:
        result.warnings.append(
            "Sample text render did not produce a usable non-empty image."
        )

    result.ok = (
        result.family_exists
        and result.glyph_metrics_nonempty
        and result.rendered_nonempty
    )

    return result.to_dict()


def find_best_bangla_font() -> Optional[str]:
    """
    Return the first installed Bengali candidate font, or None if not found.
    """
    return _resolve_from_candidates()


def ensure_default_font() -> str:
    """
    Ensure that a usable default font is available and return it.
    """
    return set_default_font()


def font_info(
    font_family: Optional[str] = None,
    font_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Resolve a font and return a concise info dictionary.
    """
    resolved = resolve_font(font_family=font_family, font_path=font_path)
    return {
        "requested_family": font_family,
        "requested_path": _normalize_path(font_path) if font_path else None,
        "resolved_family": resolved,
        "default_font_family": _DEFAULT_FONT_FAMILY,
        "default_font_path": _DEFAULT_FONT_PATH,
        "is_default": resolved == _DEFAULT_FONT_FAMILY,
    }


__all__ = [
    "register_font",
    "register_fonts",
    "list_available_fonts",
    "list_registered_fonts",
    "list_bangla_candidate_fonts",
    "set_default_font",
    "get_default_font",
    "resolve_font",
    "validate_font",
    "find_best_bangla_font",
    "ensure_default_font",
    "font_info",
]