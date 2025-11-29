# bangla_render/mpl_support.py
import numpy as np
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from PySide6.QtGui import QImage

from .renderer import render_text_qimage


# -------------------------------
# QImage → RGBA numpy array
# -------------------------------
def _qimage_to_rgba_array(qimg: QImage) -> np.ndarray:
    """
    Convert a QImage to an RGBA numpy array in [0, 1].
    Works with PySide6 where QImage.bits() returns a memoryview.
    """
    qimg = qimg.convertToFormat(QImage.Format.Format_RGBA8888)
    w, h = qimg.width(), qimg.height()

    ptr = qimg.bits()          # memoryview
    buf = ptr.tobytes()        # raw bytes
    arr = np.frombuffer(buf, np.uint8).reshape((h, w, 4))
    return arr / 255.0


def _resolve_font_size(fontsize, font_size, default):
    """
    Allow both Matplotlib-style `fontsize` and our internal `font_size`.
    Priority: explicit font_size > fontsize > default.
    """
    if font_size is not None:
        return font_size
    if fontsize is not None:
        return fontsize
    return default


# ============================================================
#  BENGALI TITLE / XLABEL / YLABEL  (dynamic placement)
# ============================================================

def set_bangla_title(
    ax,
    text,
    fontsize=None,
    font_size=None,
    zoom=0.40,
    extra_pad=0.01,  # fraction of figure height
):
    """
    Bangla title above the axes, with automatic vertical spacing
    based on the rendered text height.
    """
    fig = ax.figure
    fs = _resolve_font_size(fontsize, font_size, default=32)

    # Render via Qt
    qimg = render_text_qimage(text, font_size=fs)
    img = _qimage_to_rgba_array(qimg)
    oi = OffsetImage(img, zoom=zoom)

    # Figure size in pixels
    fig_w_in, fig_h_in = fig.get_size_inches()
    dpi = fig.dpi
    fig_h_px = fig_h_in * dpi

    # Height of title (in figure fraction)
    title_h_px = qimg.height() * zoom
    delta_fig = (title_h_px / fig_h_px) + extra_pad

    # Place centered above the axes
    bbox = ax.get_position()
    x_fig = bbox.x0 + bbox.width / 2.0
    y_fig = bbox.y1 + delta_fig
    y_fig = min(0.99, y_fig)

    ab = AnnotationBbox(
        oi,
        (x_fig, y_fig),
        xycoords=fig.transFigure,
        frameon=False,
        box_alignment=(0.5, 0.5),
        zorder=5,
    )
    fig.artists.append(ab)
    ax.set_title("")


def set_bangla_xlabel(
    ax,
    text,
    fontsize=None,
    font_size=None,
    zoom=0.40,
    extra_pad=0.01,  # fraction of figure height
):
    """
    Bangla X-axis label below the axes, with automatic vertical spacing
    based on the rendered text height.
    """
    fig = ax.figure
    fs = _resolve_font_size(fontsize, font_size, default=26)

    # Render via Qt
    qimg = render_text_qimage(text, font_size=fs)
    img = _qimage_to_rgba_array(qimg)
    oi = OffsetImage(img, zoom=zoom)

    # Figure size in pixels
    fig_w_in, fig_h_in = fig.get_size_inches()
    dpi = fig.dpi
    fig_h_px = fig_h_in * dpi

    # Height of label in figure fraction
    label_h_px = qimg.height() * zoom
    delta_fig = (label_h_px / fig_h_px) + extra_pad

    # Place centered under the axes
    bbox = ax.get_position()
    x_fig = bbox.x0 + bbox.width / 2.0
    y_fig = bbox.y0 - delta_fig
    y_fig = max(0.0, y_fig)

    ab = AnnotationBbox(
        oi,
        (x_fig, y_fig),
        xycoords=fig.transFigure,
        frameon=False,
        box_alignment=(0.5, 1.0),
        zorder=5,
    )
    fig.artists.append(ab)
    ax.set_xlabel("")


def set_bangla_ylabel(
    ax,
    text,
    fontsize=None,
    font_size=None,
    zoom=0.40,
    extra_pad=0.05,  # fraction of figure width
):
    """
    Bangla Y-axis label with automatic horizontal spacing based on
    the rendered text width, so the plot remains visually centered.
    """
    fig = ax.figure
    fs = _resolve_font_size(fontsize, font_size, default=26)

    # 1) Render via Qt
    qimg = render_text_qimage(text, font_size=fs)
    img = _qimage_to_rgba_array(qimg)

    # 2) Rotate vertically (90°)
    img = np.rot90(img, k=1)
    oi = OffsetImage(img, zoom=zoom)

    # 3) Figure width in pixels
    fig_w_in, fig_h_in = fig.get_size_inches()
    dpi = fig.dpi
    fig_w_px = fig_w_in * dpi

    # 4) Label width in figure fraction
    label_w_px = qimg.height() * zoom  # because after rotation
    label_frac = (label_w_px / fig_w_px) + extra_pad

    # 5) Position label just left of the axes
    bbox = ax.get_position()
    x_fig = bbox.x0 - label_frac
    y_fig = bbox.y0 + bbox.height / 2.0

    ab = AnnotationBbox(
        oi,
        (x_fig, y_fig),
        xycoords=fig.transFigure,
        frameon=False,
        box_alignment=(0.5, 0.5),
        zorder=5,
    )
    fig.artists.append(ab)
    ax.set_ylabel("")


# ============================================================
#  GENERAL BANGLA TEXT + HEATMAP CELLS
# ============================================================

def bangla_text(
    ax,
    x,
    y,
    text,
    fontsize=None,
    font_size=None,
    coord="data",   # "data", "axes", or "figure"
    ha="center",
    va="center",
    zoom=None,
    zorder=5,
):
    """
    General Bangla text helper, similar to ax.text() but using the Qt renderer.
    """
    fs = _resolve_font_size(fontsize, font_size, default=18)

    # Render via Qt
    qimg = render_text_qimage(text, font_size=fs)
    img = _qimage_to_rgba_array(qimg)

    # Simple zoom heuristic if not provided
    if zoom is None:
        zoom = 0.35 * (fs / 24.0)

    oi = OffsetImage(img, zoom=zoom)

    # Alignment mapping → box_alignment
    ha_map = {"center": 0.5, "left": 0.0, "right": 1.0}
    va_map = {
        "center": 0.5,
        "middle": 0.5,
        "bottom": 0.0,
        "baseline": 0.0,
        "top": 1.0,
    }
    box_alignment = (
        ha_map.get(ha, 0.5),
        va_map.get(va, 0.5),
    )

    # Coordinate system
    if coord == "axes":
        xycoords = ax.transAxes
    elif coord == "figure":
        xycoords = ax.figure.transFigure
    else:
        xycoords = ax.transData

    ab = AnnotationBbox(
        oi,
        (x, y),
        xycoords=xycoords,
        frameon=False,
        box_alignment=box_alignment,
        zorder=zorder,
    )
    ax.add_artist(ab)
    return ab


def add_bangla_in_cell(
    ax,
    row,
    col,
    text,
    rows,
    cols,
    fontsize=None,
    font_size=None,
    origin="upper",
    zoom=None,
    zorder=6,
):
    """
    Draw Bangla text at the center of a heatmap cell using axes coordinates.
    """
    fs = _resolve_font_size(fontsize, font_size, default=22)

    # Axes coordinates for cell center
    x_axes = (col + 0.5) / cols
    if origin == "upper":
        y_axes = 1.0 - (row + 0.5) / rows
    else:
        y_axes = (row + 0.5) / rows

    return bangla_text(
        ax,
        x_axes,
        y_axes,
        text,
        coord="axes",
        ha="center",
        va="center",
        font_size=fs,
        zoom=zoom,
        zorder=zorder,
    )


# ============================================================
#  LAYOUT HELPER
# ============================================================

def apply_bangla_layout(
    fig,
    left=0.18,
    right=0.88,
    bottom=0.22,
    top=0.84,
):
    """
    Adjust figure margins to leave enough space for Bangla titles
    and axis labels, while keeping the axes roughly centered.

    Call this once per figure after creating subplots and before
    adding Bangla labels.
    """
    fig.subplots_adjust(
        left=left,
        right=right,
        bottom=bottom,
        top=top,
    )
