# bangla_render/renderer.py
from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass, asdict
from typing import Any, Dict, Optional, Tuple

import numpy as np

from .backend import ensure_qt_application
from .fonts import resolve_font

try:
    from PySide6.QtCore import Qt, QRect, QRectF
    from PySide6.QtGui import (
        QColor,
        QFont,
        QFontMetrics,
        QImage,
        QPainter,
        QPen,
        QTextOption,
    )
    QT_RENDER_AVAILABLE = True
    QT_RENDER_IMPORT_ERROR = None
except Exception as e:  # pragma: no cover
    Qt = None
    QRect = None
    QRectF = None
    QColor = None
    QFont = None
    QFontMetrics = None
    QImage = None
    QPainter = None
    QPen = None
    QTextOption = None
    QT_RENDER_AVAILABLE = False
    QT_RENDER_IMPORT_ERROR = e


# ---------------------------------------------------------------------
# Defaults / cache
# ---------------------------------------------------------------------

_RENDER_CACHE_MAXSIZE = 256
_RENDER_CACHE: "OrderedDict[Tuple[Any, ...], QImage]" = OrderedDict()

_RENDER_DEFAULTS: Dict[str, Any] = {
    "color": "black",
    "bg": "transparent",
    "padding": 10,
    "scale": 1.0,
    "trim": True,
    "trim_margin_px": 1,
}


@dataclass
class RenderParams:
    text: str
    font_family: str
    font_path: Optional[str]
    font_size: int
    color: str
    bg: str
    padding: int
    scale: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------
# Core helpers
# ---------------------------------------------------------------------

def _ensure_runtime() -> None:
    ensure_qt_application()
    if not QT_RENDER_AVAILABLE:
        raise RuntimeError(
            "Qt rendering classes are not available. "
            f"Original import error: {QT_RENDER_IMPORT_ERROR}"
        )


def _normalize_color(color: str) -> QColor:
    qc = QColor(color)
    if not qc.isValid():
        qc = QColor("black")
    return qc


def _normalize_bg(bg: str) -> Optional[QColor]:
    if bg is None:
        return None
    s = str(bg).strip().lower()
    if s in ("", "none", "transparent", "rgba(0,0,0,0)"):
        return None
    qc = QColor(bg)
    if not qc.isValid():
        return None
    return qc


def _font_for_render(font_family: str, font_size: int, scale: float = 1.0) -> QFont:
    scaled_size = max(1, int(round(font_size * scale)))
    font = QFont(font_family)
    font.setPixelSize(scaled_size)
    return font


def _trim_rgba_alpha_bounds(alpha: np.ndarray, threshold: int = 0) -> Optional[Tuple[int, int, int, int]]:
    """
    Return (top, bottom, left, right) bounds inclusive-exclusive
    for non-empty alpha content.
    """
    if alpha.size == 0:
        return None

    ys, xs = np.where(alpha > threshold)
    if len(xs) == 0 or len(ys) == 0:
        return None

    top = int(ys.min())
    bottom = int(ys.max()) + 1
    left = int(xs.min())
    right = int(xs.max()) + 1
    return top, bottom, left, right


def _qimage_to_rgba_uint8(qimg: QImage) -> np.ndarray:
    qimg = qimg.convertToFormat(QImage.Format.Format_RGBA8888)
    w, h = qimg.width(), qimg.height()
    ptr = qimg.bits()
    buf = ptr.tobytes()
    return np.frombuffer(buf, np.uint8).reshape((h, w, 4)).copy()

def _rgba_uint8_to_qimage(arr: np.ndarray) -> QImage:
    arr = np.ascontiguousarray(arr)
    h, w, _ = arr.shape
    qimg = QImage(arr.data, w, h, 4 * w, QImage.Format.Format_RGBA8888)
    return qimg.copy()

def _trim_transparent_borders(
    qimg: QImage,
    *,
    margin_px: int = 1,
    alpha_threshold: int = 0,
) -> QImage:
    """
    Trim fully transparent borders and keep a small safety margin.
    """
    arr = _qimage_to_rgba_uint8(qimg)
    bounds = _trim_rgba_alpha_bounds(arr[:, :, 3], threshold=alpha_threshold)

    if bounds is None:
        return qimg

    top, bottom, left, right = bounds

    top = max(0, top - margin_px)
    bottom = min(arr.shape[0], bottom + margin_px)
    left = max(0, left - margin_px)
    right = min(arr.shape[1], right + margin_px)

    cropped = np.ascontiguousarray(arr[top:bottom, left:right, :])
    if cropped.size == 0:
        return qimg
    return _rgba_uint8_to_qimage(cropped)


def _make_cache_key(params: RenderParams) -> Tuple[Any, ...]:
    return (
        params.text,
        params.font_family,
        params.font_path,
        params.font_size,
        params.color,
        params.bg,
        params.padding,
        round(float(params.scale), 4),
    )


def _get_cached_qimage(key: Tuple[Any, ...]) -> Optional[QImage]:
    cached = _RENDER_CACHE.get(key)
    if cached is None:
        return None
    _RENDER_CACHE.move_to_end(key)
    return cached.copy()


def _set_cached_qimage(key: Tuple[Any, ...], qimg: QImage) -> None:
    _RENDER_CACHE[key] = qimg.copy()
    _RENDER_CACHE.move_to_end(key)
    while len(_RENDER_CACHE) > _RENDER_CACHE_MAXSIZE:
        _RENDER_CACHE.popitem(last=False)


def get_render_cache_info() -> Dict[str, int]:
    return {
        "size": len(_RENDER_CACHE),
        "maxsize": _RENDER_CACHE_MAXSIZE,
    }


def clear_render_cache() -> None:
    _RENDER_CACHE.clear()


def set_render_cache_maxsize(maxsize: int) -> int:
    """
    Set the maximum number of cached rendered text images.
    """
    global _RENDER_CACHE_MAXSIZE

    maxsize = int(maxsize)
    if maxsize < 1:
        raise ValueError("maxsize must be at least 1")

    _RENDER_CACHE_MAXSIZE = maxsize

    while len(_RENDER_CACHE) > _RENDER_CACHE_MAXSIZE:
        _RENDER_CACHE.popitem(last=False)

    return _RENDER_CACHE_MAXSIZE


def set_render_defaults(
    *,
    color: Optional[str] = None,
    bg: Optional[str] = None,
    padding: Optional[int] = None,
    scale: Optional[float] = None,
    trim: Optional[bool] = None,
    trim_margin_px: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Set package-level render defaults.
    """
    if color is not None:
        _RENDER_DEFAULTS["color"] = str(color)
    if bg is not None:
        _RENDER_DEFAULTS["bg"] = str(bg)
    if padding is not None:
        _RENDER_DEFAULTS["padding"] = int(padding)
    if scale is not None:
        _RENDER_DEFAULTS["scale"] = float(scale)
    if trim is not None:
        _RENDER_DEFAULTS["trim"] = bool(trim)
    if trim_margin_px is not None:
        _RENDER_DEFAULTS["trim_margin_px"] = int(trim_margin_px)

    return dict(_RENDER_DEFAULTS)


def get_render_defaults() -> Dict[str, Any]:
    """
    Return current render defaults.
    """
    return dict(_RENDER_DEFAULTS)


# ---------------------------------------------------------------------
# Measurement
# ---------------------------------------------------------------------

def _resolve_render_params(
    text: str,
    font_family: Optional[str] = None,
    font_path: Optional[str] = None,
    font_size: int = 24,
    color: Optional[str] = None,
    bg: Optional[str] = None,
    padding: Optional[int] = None,
    scale: Optional[float] = None,
) -> RenderParams:
    _ensure_runtime()

    resolved_family = resolve_font(font_family=font_family, font_path=font_path)

    if color is None:
        color = _RENDER_DEFAULTS["color"]
    if bg is None:
        bg = _RENDER_DEFAULTS["bg"]
    if padding is None:
        padding = _RENDER_DEFAULTS["padding"]
    if scale is None:
        scale = _RENDER_DEFAULTS["scale"]

    return RenderParams(
        text=str(text),
        font_family=resolved_family,
        font_path=font_path,
        font_size=int(font_size),
        color=str(color),
        bg=str(bg),
        padding=int(padding),
        scale=float(scale),
    )


def measure_text(
    text: str,
    font_family: Optional[str] = None,
    font_path: Optional[str] = None,
    font_size: int = 24,
    padding: Optional[int] = None,
    scale: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Measure single-line text before rendering.
    """
    params = _resolve_render_params(
        text=text,
        font_family=font_family,
        font_path=font_path,
        font_size=font_size,
        padding=padding,
        scale=scale,
    )

    font = _font_for_render(params.font_family, params.font_size, params.scale)
    fm = QFontMetrics(font)

    try:
        rect = fm.boundingRect(params.text)
    except Exception:
        rect = QRect(0, 0, 1, 1)

    text_w = max(1, rect.width())
    text_h = max(1, rect.height())
    ascent = fm.ascent()
    descent = fm.descent()

    full_w = text_w + (2 * params.padding)
    full_h = text_h + (2 * params.padding)

    return {
        "font_family": params.font_family,
        "font_size": params.font_size,
        "scale": params.scale,
        "text_width_px": text_w,
        "text_height_px": text_h,
        "image_width_px": full_w,
        "image_height_px": full_h,
        "ascent_px": ascent,
        "descent_px": descent,
        "bounding_rect": {
            "x": rect.x(),
            "y": rect.y(),
            "width": rect.width(),
            "height": rect.height(),
        },
    }


# ---------------------------------------------------------------------
# Single-line render
# ---------------------------------------------------------------------

def render_text_qimage(
    text: str,
    font_family: Optional[str] = None,
    font_path: Optional[str] = None,
    font_size: int = 24,
    color: Optional[str] = None,
    bg: Optional[str] = None,
    padding: Optional[int] = None,
    scale: Optional[float] = None,
    trim: Optional[bool] = None,
    trim_margin_px: Optional[int] = None,
) -> QImage:
    """
    Render a single-line Bengali text string to a QImage.

    Important improvement:
    - trims transparent borders after render, so layout boxes track visible text
      more closely and title/suptitle spacing becomes more natural.
    """
    if trim is None:
        trim = _RENDER_DEFAULTS["trim"]
    if trim_margin_px is None:
        trim_margin_px = _RENDER_DEFAULTS["trim_margin_px"]

    params = _resolve_render_params(
        text=text,
        font_family=font_family,
        font_path=font_path,
        font_size=font_size,
        color=color,
        bg=bg,
        padding=padding,
        scale=scale,
    )

    key = _make_cache_key(params) + (bool(trim), int(trim_margin_px))
    cached = _get_cached_qimage(key)
    if cached is not None:
        return cached

    font = _font_for_render(params.font_family, params.font_size, params.scale)
    fm = QFontMetrics(font)

    rect = fm.boundingRect(params.text)
    text_w = max(1, rect.width())
    text_h = max(1, rect.height())

    img_w = max(1, text_w + (2 * params.padding))
    img_h = max(1, text_h + (2 * params.padding))

    qimg = QImage(img_w, img_h, QImage.Format.Format_ARGB32)
    qimg.fill(Qt.GlobalColor.transparent)

    painter = QPainter(qimg)
    try:
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        painter.setFont(font)

        bg_qc = _normalize_bg(params.bg)
        if bg_qc is not None:
            painter.fillRect(0, 0, img_w, img_h, bg_qc)

        pen = QPen(_normalize_color(params.color))
        painter.setPen(pen)

        x = params.padding - rect.left()
        y = params.padding - rect.top()
        painter.drawText(x, y, params.text)
    finally:
        painter.end()

    if trim:
        qimg = _trim_transparent_borders(qimg, margin_px=int(trim_margin_px))

    _set_cached_qimage(key, qimg)
    return qimg.copy()


def render_text_array(
    text: str,
    font_family: Optional[str] = None,
    font_path: Optional[str] = None,
    font_size: int = 24,
    color: Optional[str] = None,
    bg: Optional[str] = None,
    padding: Optional[int] = None,
    scale: Optional[float] = None,
    trim: Optional[bool] = None,
    trim_margin_px: Optional[int] = None,
) -> np.ndarray:
    qimg = render_text_qimage(
        text=text,
        font_family=font_family,
        font_path=font_path,
        font_size=font_size,
        color=color,
        bg=bg,
        padding=padding,
        scale=scale,
        trim=trim,
        trim_margin_px=trim_margin_px,
    )
    return _qimage_to_rgba_uint8(qimg)


def render_text(
    text: str,
    output_path: Optional[str] = None,
    font_family: Optional[str] = None,
    font_path: Optional[str] = None,
    font_size: int = 24,
    width: Optional[int] = None,
    height: Optional[int] = None,
    color: Optional[str] = None,
    bg: Optional[str] = None,
    padding: Optional[int] = None,
    scale: Optional[float] = None,
    trim: Optional[bool] = None,
    trim_margin_px: Optional[int] = None,
):
    """
    Backward-compatible public single-line render helper.
    """
    qimg = render_text_qimage(
        text=text,
        font_family=font_family,
        font_path=font_path,
        font_size=font_size,
        color=color,
        bg=bg,
        padding=padding,
        scale=scale,
        trim=trim,
        trim_margin_px=trim_margin_px,
    )

    if width is not None or height is not None:
        target_w = max(qimg.width(), int(width) if width is not None else qimg.width())
        target_h = max(qimg.height(), int(height) if height is not None else qimg.height())
        if target_w != qimg.width() or target_h != qimg.height():
            canvas = QImage(target_w, target_h, QImage.Format.Format_ARGB32)
            bg_qc = _normalize_bg(bg if bg is not None else _RENDER_DEFAULTS["bg"])
            if bg_qc is None:
                canvas.fill(Qt.GlobalColor.transparent)
            else:
                canvas.fill(bg_qc)

            painter = QPainter(canvas)
            try:
                painter.drawImage(0, 0, qimg)
            finally:
                painter.end()
            qimg = canvas

    if output_path:
        ok = qimg.save(output_path)
        if not ok:
            raise RuntimeError(f"Failed to save rendered image to: {output_path}")

    return qimg


# ---------------------------------------------------------------------
# Paragraph render
# ---------------------------------------------------------------------

def _estimate_paragraph_height(width: int, font: QFont, text: str, margin: int) -> int:
    fm = QFontMetrics(font)
    inner_w = max(1, width - (2 * margin))
    rect = fm.boundingRect(QRect(0, 0, inner_w, 100000), int(Qt.TextFlag.TextWordWrap), text)
    return max(1, rect.height() + (2 * margin))


def render_paragraph_qimage(
    text: str,
    width: int = 600,
    height: Optional[int] = None,
    font_family: Optional[str] = None,
    font_path: Optional[str] = None,
    font_size: int = 24,
    color: Optional[str] = None,
    bg: Optional[str] = None,
    margin: int = 12,
    scale: Optional[float] = None,
    trim: Optional[bool] = None,
    trim_margin_px: Optional[int] = None,
) -> QImage:
    """
    Render wrapped paragraph text to a QImage.
    """
    _ensure_runtime()

    if color is None:
        color = _RENDER_DEFAULTS["color"]
    if bg is None:
        bg = _RENDER_DEFAULTS["bg"]
    if scale is None:
        scale = _RENDER_DEFAULTS["scale"]
    if trim is None:
        trim = _RENDER_DEFAULTS["trim"]
    if trim_margin_px is None:
        trim_margin_px = _RENDER_DEFAULTS["trim_margin_px"]

    resolved_family = resolve_font(font_family=font_family, font_path=font_path)
    font = _font_for_render(resolved_family, font_size, scale)

    width = max(1, int(width))
    margin = max(0, int(margin))

    if height is None:
        height = _estimate_paragraph_height(width, font, str(text), margin)
    else:
        height = max(1, int(height))

    qimg = QImage(width, height, QImage.Format.Format_ARGB32)
    bg_qc = _normalize_bg(bg)
    if bg_qc is None:
        qimg.fill(Qt.GlobalColor.transparent)
    else:
        qimg.fill(bg_qc)

    painter = QPainter(qimg)
    try:
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        painter.setFont(font)
        painter.setPen(QPen(_normalize_color(color)))

        text_rect = QRectF(
            float(margin),
            float(margin),
            float(max(1, width - (2 * margin))),
            float(max(1, height - (2 * margin))),
        )

        option = QTextOption()
        option.setWrapMode(QTextOption.WrapMode.WordWrap)
        painter.drawText(text_rect, str(text), option)
    finally:
        painter.end()

    if trim and _normalize_bg(bg) is None:
        qimg = _trim_transparent_borders(qimg, margin_px=int(trim_margin_px))

    return qimg


def render_paragraph(
    text: str,
    output_path: Optional[str] = None,
    width: int = 600,
    height: Optional[int] = None,
    font_family: Optional[str] = None,
    font_path: Optional[str] = None,
    font_size: int = 24,
    color: Optional[str] = None,
    bg: Optional[str] = None,
    margin: int = 12,
    scale: Optional[float] = None,
    trim: Optional[bool] = None,
    trim_margin_px: Optional[int] = None,
):
    qimg = render_paragraph_qimage(
        text=text,
        width=width,
        height=height,
        font_family=font_family,
        font_path=font_path,
        font_size=font_size,
        color=color,
        bg=bg,
        margin=margin,
        scale=scale,
        trim=trim,
        trim_margin_px=trim_margin_px,
    )

    if output_path:
        ok = qimg.save(output_path)
        if not ok:
            raise RuntimeError(f"Failed to save rendered paragraph image to: {output_path}")

    return qimg