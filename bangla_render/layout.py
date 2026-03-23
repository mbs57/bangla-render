# bangla_render/layout.py
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np
from matplotlib.offsetbox import AnnotationBbox, OffsetImage
from matplotlib.transforms import Bbox

from .renderer import render_text_qimage

try:
    from PySide6.QtGui import QImage
except Exception:  # pragma: no cover
    QImage = None


_MANAGER_REGISTRY: Dict[int, "BanglaLayoutManager"] = {}


# ─────────────────────────────────────────────────────────────────────
# Utilities
# ─────────────────────────────────────────────────────────────────────

def _qimage_to_rgba_array(qimg: QImage) -> np.ndarray:
    qimg = qimg.convertToFormat(QImage.Format.Format_RGBA8888)
    w, h = qimg.width(), qimg.height()
    buf  = qimg.bits().tobytes()
    return np.frombuffer(buf, np.uint8).reshape((h, w, 4)) / 255.0


def _pixels_to_fig_dx(fig, px: float) -> float:
    fw = fig.get_size_inches()[0] * fig.dpi
    return px / fw if fw > 0 else 0.0


def _pixels_to_fig_dy(fig, px: float) -> float:
    fh = fig.get_size_inches()[1] * fig.dpi
    return px / fh if fh > 0 else 0.0


def _pixels_to_axes_dx(ax, px: float) -> float:
    bp = ax.get_position()
    fw = ax.figure.get_size_inches()[0] * ax.figure.dpi
    return px / max(1.0, bp.width * fw)


def _pixels_to_axes_dy(ax, px: float) -> float:
    bp = ax.get_position()
    fh = ax.figure.get_size_inches()[1] * ax.figure.dpi
    return px / max(1.0, bp.height * fh)


def _remove_artist_safe(artist) -> None:
    if artist is None:
        return
    try:
        artist.remove()
    except Exception:
        pass


def _resolve_font_size(fontsize, font_size, default):
    if font_size is not None:  return font_size
    if fontsize   is not None: return fontsize
    return default


def _ensure_list(value) -> List[Any]:
    if value is None:           return []
    if isinstance(value, list): return value
    return list(value)


def _union_bboxes(bboxes: List[Optional[Bbox]]) -> Optional[Bbox]:
    valid = [b for b in bboxes
             if b is not None and np.isfinite([b.x0, b.y0, b.x1, b.y1]).all()]
    if not valid:
        return None
    return Bbox.from_extents(
        min(b.x0 for b in valid), min(b.y0 for b in valid),
        max(b.x1 for b in valid), max(b.y1 for b in valid),
    )


# ─────────────────────────────────────────────────────────────────────
# Data classes
# ─────────────────────────────────────────────────────────────────────

@dataclass
class ManagedBanglaItem:
    kind: str
    text: str
    ax:   Any = None
    fig:  Any = None

    fontsize:    Optional[float] = None
    font_size:   Optional[float] = None
    font_family: Optional[str]   = None
    font_path:   Optional[str]   = None
    color:        str   = "black"
    padding:      int   = 10
    scale:        float = 1.0
    zoom:         float = 0.40
    extra_pad_px: float = 8.0
    zorder:       int   = 5

    artist: Any = None
    last_image_size_px:  Tuple[int, int]     = field(default_factory=lambda: (0, 0))
    last_render_size_px: Tuple[float, float] = field(default_factory=lambda: (0.0, 0.0))


@dataclass
class ManagedTickGroup:
    kind: str
    ax:   Any
    positions: Sequence[float]
    labels:    Sequence[str]

    fontsize:    Optional[float] = None
    font_size:   Optional[float] = None
    font_family: Optional[str]   = None
    font_path:   Optional[str]   = None
    color:  str   = "black"
    bg:     str   = "transparent"
    padding: int  = 8
    scale:  float = 1.0
    zoom:   Optional[float] = None
    extra_pad_axes: float = 0.02
    zorder: int   = 5
    ha: str = "center"
    va: str = "top"
    hide_native:         bool = True
    collision_avoidance: bool = True

    artists:       List[Any]                 = field(default_factory=list)
    last_sizes_px: List[Tuple[float, float]] = field(default_factory=list)


# ─────────────────────────────────────────────────────────────────────
# Layout manager
# ─────────────────────────────────────────────────────────────────────

class BanglaLayoutManager:
    """
    ylabel placement — colorbar-aware, correct for any subplot position
    ─────────────────────────────────────────────────────────────────────
    Position formula:
        cx_px = strip_right - GAP - screen_width / 2

    where strip_right = ytick labels left edge (renderer-measured,
    post-colorbar accurate).

    The x position is clamped to stay left of the axes left edge
    (NOT to a fixed figure fraction like 0.48 — that was wrong for
    right-side subplots where the correct x fraction can be > 0.48).

    Colorbar detection: if any other axes has its right edge within
    COLORBAR_OVERLAP_TOL px of the ytick left edge, AND the remaining
    space is < MIN_YLABEL_STRIP_PX, the ylabel is skipped.

    User zoom is used exactly — no auto-zoom manipulation.
    """

    X_TICK_GAP_PX           = 4.0
    Y_TICK_GAP_PX           = 4.0
    X_LABEL_BASE_GAP_PX     = 10.0
    Y_LABEL_BASE_GAP_PX     = 10.0
    TITLE_TO_AXES_GAP_PX    = 10.0
    LEFT_MARGIN_SAFETY_PX   = 10.0
    BOTTOM_MARGIN_SAFETY_PX = 10.0
    TOP_MARGIN_SAFETY_PX    = 12.0

    # Any other axes whose right edge is within this px of ytick_left
    # is treated as potentially blocking the ylabel strip.
    COLORBAR_OVERLAP_TOL = 60.0

    # Skip ylabel if clear space left of ytick labels is < this.
    MIN_YLABEL_STRIP_PX  = 20.0

    def __init__(self, fig):
        self.fig = fig
        self.items:       List[ManagedBanglaItem] = []
        self.tick_groups: List[ManagedTickGroup]  = []
        self._draw_cid   = None
        self._resize_cid = None
        self._is_updating = False
        self._connect_events()

    # ── events ──────────────────────────────────────────────────────

    def _connect_events(self):
        c = self.fig.canvas
        if c is None: return
        self._draw_cid   = c.mpl_connect("draw_event",   self._on_draw_event)
        self._resize_cid = c.mpl_connect("resize_event", self._on_resize_event)

    def disconnect(self):
        c = self.fig.canvas
        if c is None: return
        for attr in ("_draw_cid", "_resize_cid"):
            cid = getattr(self, attr, None)
            if cid is not None:
                try: c.mpl_disconnect(cid)
                except Exception: pass
                setattr(self, attr, None)

    def _on_draw_event(self, _):
        if not self._is_updating: self.update_layout()

    def _on_resize_event(self, _):
        if not self._is_updating: self.update_layout()

    # ── registration ────────────────────────────────────────────────

    def _make_item(self, kind, text, ax=None, fig=None, **kw):
        return ManagedBanglaItem(
            kind=kind, text=text, ax=ax, fig=fig,
            fontsize=kw.get("fontsize"),
            font_size=kw.get("font_size"),
            font_family=kw.get("font_family"),
            font_path=kw.get("font_path"),
            color=kw.get("color", "black"),
            padding=kw.get("padding", 10),
            scale=kw.get("scale", 1.0),
            zoom=kw.get("zoom", 0.40),
            extra_pad_px=kw.get("extra_pad_px", 8.0),
            zorder=kw.get("zorder", 5),
        )

    def add_title(self, ax, text, **kw):
        self._rm_item("title", ax=ax)
        it = self._make_item("title", text, ax=ax, fig=ax.figure, **kw)
        self.items.append(it); ax.set_title("")
        self.update_layout(); return it

    def add_xlabel(self, ax, text, **kw):
        self._rm_item("xlabel", ax=ax)
        it = self._make_item("xlabel", text, ax=ax, fig=ax.figure, **kw)
        self.items.append(it); ax.set_xlabel("")
        self.update_layout(); return it

    def add_ylabel(self, ax, text, **kw):
        self._rm_item("ylabel", ax=ax)
        it = self._make_item("ylabel", text, ax=ax, fig=ax.figure, **kw)
        self.items.append(it); ax.set_ylabel("")
        self.update_layout(); return it

    def add_suptitle(self, fig, text, **kw):
        return None  # silent stub

    def add_xticks(self, ax, positions, labels, **kw):
        self._rm_tick("xticks", ax)
        g = ManagedTickGroup(
            kind="xticks", ax=ax,
            positions=list(positions), labels=list(labels),
            fontsize=kw.get("fontsize"),       font_size=kw.get("font_size"),
            font_family=kw.get("font_family"), font_path=kw.get("font_path"),
            color=kw.get("color", "black"),    bg=kw.get("bg", "transparent"),
            padding=kw.get("padding", 8),      scale=kw.get("scale", 1.0),
            zoom=kw.get("zoom"),
            extra_pad_axes=kw.get("extra_pad_axes", 0.02),
            zorder=kw.get("zorder", 5),
            ha=kw.get("ha", "center"),         va=kw.get("va", "top"),
            hide_native=kw.get("hide_native", True),
            collision_avoidance=kw.get("collision_avoidance", True),
        )
        self.tick_groups.append(g)
        ax.set_xticks(list(positions))
        if g.hide_native: ax.set_xticklabels([])
        self.update_layout(); return g

    def add_yticks(self, ax, positions, labels, **kw):
        self._rm_tick("yticks", ax)
        g = ManagedTickGroup(
            kind="yticks", ax=ax,
            positions=list(positions), labels=list(labels),
            fontsize=kw.get("fontsize"),       font_size=kw.get("font_size"),
            font_family=kw.get("font_family"), font_path=kw.get("font_path"),
            color=kw.get("color", "black"),    bg=kw.get("bg", "transparent"),
            padding=kw.get("padding", 8),      scale=kw.get("scale", 1.0),
            zoom=kw.get("zoom"),
            extra_pad_axes=kw.get("extra_pad_axes", 0.02),
            zorder=kw.get("zorder", 5),
            ha=kw.get("ha", "right"),          va=kw.get("va", "center"),
            hide_native=kw.get("hide_native", True),
            collision_avoidance=kw.get("collision_avoidance", True),
        )
        self.tick_groups.append(g)
        ax.set_yticks(list(positions))
        if g.hide_native: ax.set_yticklabels([])
        self.update_layout(); return g

    # ── removal ─────────────────────────────────────────────────────

    def _rm_item(self, kind, ax=None, fig=None):
        for it in [x for x in self.items if x.kind == kind and (
                (ax  is not None and x.ax  is ax) or
                (fig is not None and x.fig is fig))]:
            self.remove_item(it)

    def _rm_tick(self, kind, ax):
        for g in [x for x in self.tick_groups if x.kind == kind and x.ax is ax]:
            self.remove_tick_group(g)

    def remove_item(self, it):
        _remove_artist_safe(it.artist); it.artist = None
        try: self.items.remove(it)
        except ValueError: pass

    def remove_tick_group(self, g):
        for a in _ensure_list(g.artists): _remove_artist_safe(a)
        g.artists = []; g.last_sizes_px = []
        try: self.tick_groups.remove(g)
        except ValueError: pass

    def clear(self):
        for it in self.items:
            _remove_artist_safe(it.artist); it.artist = None
        self.items.clear()
        for g in self.tick_groups:
            for a in _ensure_list(g.artists): _remove_artist_safe(a)
            g.artists = []; g.last_sizes_px = []
        self.tick_groups.clear()

    # ── rendering ────────────────────────────────────────────────────

    def _default_fs(self, kind):
        return {"title": 32, "xlabel": 26, "ylabel": 26,
                "suptitle": 34, "xticks": 16, "yticks": 16}.get(kind, 24)

    def _render_item_image(self, item):
        fs = _resolve_font_size(item.fontsize, item.font_size,
                                self._default_fs(item.kind))
        q  = render_text_qimage(
            item.text, font_family=item.font_family, font_path=item.font_path,
            font_size=fs, color=item.color, bg="transparent",
            padding=item.padding, scale=item.scale,
        )
        img = _qimage_to_rgba_array(q)
        rw  = q.width()  * item.zoom
        rh  = q.height() * item.zoom
        item.last_image_size_px  = (q.width(), q.height())
        item.last_render_size_px = (rw, rh)
        return fs, q, img, rw, rh

    def _render_tick_image(self, g, label):
        fs = _resolve_font_size(g.fontsize, g.font_size, self._default_fs(g.kind))
        q  = render_text_qimage(
            label, font_family=g.font_family, font_path=g.font_path,
            font_size=fs, color=g.color, bg=g.bg,
            padding=g.padding, scale=g.scale,
        )
        img = _qimage_to_rgba_array(q)
        z   = g.zoom if g.zoom is not None else 0.35 * (fs / 24.0)
        return fs, q, img, q.width() * z, q.height() * z

    # ── lookup ───────────────────────────────────────────────────────

    def _get_item(self, kind, ax=None, fig=None):
        for it in self.items:
            if it.kind != kind: continue
            if ax  is not None and it.ax  is ax:  return it
            if fig is not None and it.fig is fig:  return it
        return None

    def _get_tick_group(self, kind, ax):
        for g in self.tick_groups:
            if g.kind == kind and g.ax is ax: return g
        return None

    def _get_managed_axes(self):
        axes = []
        for it in self.items:
            if it.ax is not None and it.ax not in axes: axes.append(it.ax)
        for g in self.tick_groups:
            if g.ax is not None and g.ax not in axes: axes.append(g.ax)
        return axes

    # ── renderer ────────────────────────────────────────────────────

    def _get_renderer(self):
        """
        Draw first so renderer reflects post-colorbar positions.
        Without canvas.draw(), colorbar axes positions are stale.
        """
        c = self.fig.canvas
        if c is None: return None
        try: c.draw()
        except Exception: pass
        try: return c.get_renderer()
        except Exception: return None

    # ── bbox helpers ─────────────────────────────────────────────────

    def _artist_bbox(self, artist, r):
        if artist is None or r is None: return None
        try:
            b = artist.get_window_extent(r)
            return b if (b and b.width > 0 and b.height > 0) else None
        except Exception: return None

    def _group_bbox(self, g, r):
        if g is None: return None
        return _union_bboxes([self._artist_bbox(a, r) for a in _ensure_list(g.artists)])

    def _native_tick_bbox(self, ax, axis, r):
        if r is None: return None
        lbls = ax.get_xticklabels() if axis == "x" else ax.get_yticklabels()
        bbs  = []
        for lbl in lbls:
            try:
                if not lbl.get_visible() or not lbl.get_text(): continue
                b = lbl.get_window_extent(r)
                if b and b.width > 0 and b.height > 0: bbs.append(b)
            except Exception: pass
        return _union_bboxes(bbs)

    def _total_x_tick_bbox(self, ax, r):
        return _union_bboxes([
            self._group_bbox(self._get_tick_group("xticks", ax), r),
            self._native_tick_bbox(ax, "x", r),
        ])

    def _total_y_tick_bbox(self, ax, r):
        return _union_bboxes([
            self._group_bbox(self._get_tick_group("yticks", ax), r),
            self._native_tick_bbox(ax, "y", r),
        ])

    def _x_tick_outward_px(self, ax, r):
        b = self._total_x_tick_bbox(ax, r)
        if b is None: return 0.0
        try: return max(0.0, ax.get_window_extent(r).y0 - b.y0)
        except Exception: return 0.0

    # ── colorbar detection ───────────────────────────────────────────

    def _ylabel_blocked(self, ax, r, cx_px: float, screen_w: float) -> bool:
        """
        Return True if placing the ylabel at cx_px would overlap any
        other axes (including colorbar axes with their tick labels).

        Uses two tests:
        1. Direct image bbox collision with any other axes bbox.
        2. Whether cx_px falls inside the gap between any other axes
           and the ytick labels — i.e. cx_px is to the RIGHT of any
           other axes left edge and LEFT of the ytick left edge.
           This catches colorbars whose axes bbox (including tick labels)
           extends past cx_px even if the colorbar bar itself does not.
        """
        label_left  = cx_px - screen_w / 2.0 - 2.0
        label_right = cx_px + screen_w / 2.0 + 2.0

        for other in self.fig.axes:
            if other is ax: continue
            try:
                ob = other.get_window_extent(r)
            except Exception: continue
            if ob.width <= 0 or ob.height <= 0: continue

            # Test 1: direct bbox overlap
            if label_right > ob.x0 and label_left < ob.x1:
                return True

            # Test 2: cx_px is inside the gap between this axes and ours.
            # If another axes has its LEFT edge to the LEFT of cx_px,
            # it means cx_px is in the territory of or to the right of
            # that other axes — which means we are in the gap region
            # between that axes and the ytick labels.
            # This catches colorbars that end before cx_px but whose
            # visual presence occupies the gap.
            if ob.x0 < cx_px and ob.x1 > label_left:
                return True

        return False

    # ── tick placement ───────────────────────────────────────────────

    def _tick_ba(self, ha, va):
        hm = {"left": 0.0, "center": 0.5, "right": 1.0}
        vm = {"bottom": 0.0, "baseline": 0.0,
              "center": 0.5, "middle": 0.5, "top": 1.0}
        return (hm.get((ha or "center").lower(), 0.5),
                vm.get((va or "center").lower(), 0.5))

    def _xpx(self, ax, pos):
        pts = ax.transData.transform(
            np.column_stack([pos, np.zeros(len(pos))]))
        return [float(p[0]) for p in pts]

    def _ypx(self, ax, pos):
        pts = ax.transData.transform(
            np.column_stack([np.zeros(len(pos)), pos]))
        return [float(p[1]) for p in pts]

    @staticmethod
    def _filt_x(cx, wx, gap=6.0):
        vis, last = [True] * len(cx), None
        for i, (c, w) in enumerate(zip(cx, wx)):
            l, r = c - w / 2, c + w / 2
            if last is None: last = r
            elif l < last + gap: vis[i] = False
            else: last = r
        return vis

    @staticmethod
    def _filt_y(cy, hy, gap=6.0):
        vis, last = [True] * len(cy), None
        for i, (c, h) in enumerate(zip(cy, hy)):
            b, t = c - h / 2, c + h / 2
            if last is None: last = t
            elif b < last + gap: vis[i] = False
            else: last = t
        return vis

    def _place_xticks(self, g):
        ax = g.ax
        for a in _ensure_list(g.artists): _remove_artist_safe(a)
        g.artists = []; g.last_sizes_px = []
        if g.hide_native: ax.set_xticklabels([])
        ax.set_xticks(list(g.positions))
        trans = ax.get_xaxis_transform()
        ba    = self._tick_ba(g.ha, g.va)
        gap   = _pixels_to_axes_dy(ax, self.X_TICK_GAP_PX)
        pays  = [self._render_tick_image(g, lbl) for lbl in g.labels]
        vis   = ([True] * len(g.positions) if not g.collision_avoidance
                 else self._filt_x(self._xpx(ax, g.positions), [p[3] for p in pays]))
        for i, pos in enumerate(g.positions):
            if not vis[i]: continue
            fs, _, img, dw, dh = pays[i]
            z  = g.zoom if g.zoom is not None else 0.35 * (fs / 24.0)
            ab = AnnotationBbox(OffsetImage(img, zoom=z), (pos, -gap),
                                xycoords=trans, frameon=False,
                                box_alignment=ba, zorder=g.zorder,
                                annotation_clip=False)
            ax.add_artist(ab)
            g.artists.append(ab); g.last_sizes_px.append((dw, dh))

    def _place_yticks(self, g):
        ax = g.ax
        for a in _ensure_list(g.artists): _remove_artist_safe(a)
        g.artists = []; g.last_sizes_px = []
        if g.hide_native: ax.set_yticklabels([])
        ax.set_yticks(list(g.positions))
        trans = ax.get_yaxis_transform()
        ba    = self._tick_ba(g.ha, g.va)
        gap   = _pixels_to_axes_dx(ax, self.Y_TICK_GAP_PX)
        pays  = [self._render_tick_image(g, lbl) for lbl in g.labels]
        vis   = ([True] * len(g.positions) if not g.collision_avoidance
                 else self._filt_y(self._ypx(ax, g.positions), [p[4] for p in pays]))
        for i, pos in enumerate(g.positions):
            if not vis[i]: continue
            fs, _, img, dw, dh = pays[i]
            z  = g.zoom if g.zoom is not None else 0.35 * (fs / 24.0)
            ab = AnnotationBbox(OffsetImage(img, zoom=z), (-gap, pos),
                                xycoords=trans, frameon=False,
                                box_alignment=ba, zorder=g.zorder,
                                annotation_clip=False)
            ax.add_artist(ab)
            g.artists.append(ab); g.last_sizes_px.append((dw, dh))

    # ── label / title placement ──────────────────────────────────────

    def _place_title(self, item):
        ax, fig = item.ax, item.ax.figure
        bp = ax.get_position()
        _, _, img, _, rh = self._render_item_image(item)
        gap_px = max(item.extra_pad_px, self.TITLE_TO_AXES_GAP_PX)
        y = min(0.97, bp.y1 + _pixels_to_fig_dy(fig, gap_px + rh / 2.0))
        ab = AnnotationBbox(
            OffsetImage(img, zoom=item.zoom),
            (bp.x0 + bp.width / 2.0, y),
            xycoords=fig.transFigure, frameon=False,
            box_alignment=(0.5, 0.5), zorder=item.zorder,
        )
        fig.add_artist(ab); return ab

    def _place_xlabel(self, item, r):
        ax, fig = item.ax, item.ax.figure
        bp = ax.get_position()
        _, _, img, _, rh = self._render_item_image(item)
        tick_px = self._x_tick_outward_px(ax, r)
        total   = tick_px + self.X_LABEL_BASE_GAP_PX + item.extra_pad_px + rh / 2.0
        y = max(0.0, bp.y0 - _pixels_to_fig_dy(fig, total))
        ab = AnnotationBbox(
            OffsetImage(img, zoom=item.zoom),
            (bp.x0 + bp.width / 2.0, y),
            xycoords=fig.transFigure, frameon=False,
            box_alignment=(0.5, 0.5), zorder=item.zorder,
        )
        fig.add_artist(ab); return ab

    def _place_ylabel(self, item, r):
        """
        Place the ylabel just left of the ytick labels.

        Formula:
            screen_width = img_height * zoom  (image is rotated 90°)
            cx_px = strip_right - GAP - screen_width / 2

        where strip_right = ytick labels left edge (renderer-measured).

        THE KEY FIX:
            x_fig is clamped to [0.01, axes_left - small_margin]
            NOT to a fixed 0.48 maximum.
            Fixed 0.48 was wrong for right-side subplots where the
            correct x fraction can be > 0.48.

        Skips ylabel silently if a colorbar blocks the strip.
        User zoom is used exactly — no manipulation.
        """
        ax, fig = item.ax, item.ax.figure
        fw = fig.get_size_inches()[0] * fig.dpi

        # ytick labels left edge (post-colorbar, renderer-measured)
        ytick_bb = self._total_y_tick_bbox(ax, r)
        if ytick_bb is not None:
            strip_right = ytick_bb.x0
        else:
            try:    strip_right = ax.get_window_extent(r).x0
            except: strip_right = ax.get_position().x0 * fw

        # Render (user zoom unchanged)
        _, _, img, _, _ = self._render_item_image(item)
        rotated  = np.rot90(img, k=1)

        # After 90° rotation: screen_width = original_img_height * zoom
        img_h    = item.last_image_size_px[1]
        screen_w = img_h * item.zoom

        # Place centre just left of ytick labels
        GAP_PX = self.Y_LABEL_BASE_GAP_PX + item.extra_pad_px
        cx_px  = strip_right - GAP_PX - screen_w / 2.0

        # Clamp to axes left edge (not a fixed fraction)
        try:
            axes_left_px = ax.get_window_extent(r).x0
        except Exception:
            axes_left_px = ax.get_position().x0 * fw

        cx_px = max(screen_w / 2.0 + 2.0, cx_px)
        cx_px = min(axes_left_px - screen_w / 2.0 - 2.0, cx_px)

        # Skip if the ACTUAL computed ylabel position overlaps any other axes.
        # Must be done AFTER computing cx_px so the test uses real coordinates.
        # This catches colorbars where the gap to ytick is >20px but the
        # label image still lands on the colorbar.
        if self._ylabel_blocked(ax, r, cx_px, screen_w):
            return None

        x_fig = cx_px / max(1.0, fw)
        x_fig = max(0.01, x_fig)          # absolute minimum: inside figure

        bp    = ax.get_position()
        y_fig = bp.y0 + bp.height / 2.0

        ab = AnnotationBbox(
            OffsetImage(rotated, zoom=item.zoom),
            (x_fig, y_fig),
            xycoords=fig.transFigure, frameon=False,
            box_alignment=(0.5, 0.5), zorder=item.zorder,
        )
        fig.add_artist(ab)
        item.last_render_size_px = (screen_w, item.last_image_size_px[0] * item.zoom)
        return ab

    # ── full placement pass ──────────────────────────────────────────

    def _place_all_artists(self):
        for g in self.tick_groups:
            if   g.kind == "xticks": self._place_xticks(g)
            elif g.kind == "yticks": self._place_yticks(g)

        r = self._get_renderer()

        for it in self.items:
            if it.kind in ("title", "suptitle"): continue
            _remove_artist_safe(it.artist); it.artist = None
            if   it.kind == "xlabel": it.artist = self._place_xlabel(it, r)
            elif it.kind == "ylabel": it.artist = self._place_ylabel(it, r)

        for it in self.items:
            if it.kind != "title": continue
            _remove_artist_safe(it.artist)
            it.artist = self._place_title(it)

    def update_layout(self):
        if self._is_updating: return
        self._is_updating = True
        try: self._place_all_artists()
        finally: self._is_updating = False

    # ── auto_adjust_margins ──────────────────────────────────────────

    def auto_adjust_margins(
        self,
        min_left=0.12, min_right=0.90,
        min_bottom=0.12, min_top=0.88,
        extra_left_px=10.0, extra_bottom_px=10.0,
        extra_top_px=18.0, extra_right_px=6.0,
    ):
        fig = self.fig
        self._place_all_artists()
        try: fig.canvas.draw()
        except Exception: pass
        r = self._get_renderer()
        if r is None: return

        fw = fig.get_size_inches()[0] * fig.dpi
        fh = fig.get_size_inches()[1] * fig.dpi
        axes_seen = self._get_managed_axes()

        left_px = 0.0; bot_px = 0.0
        title_bbs = []

        for ax in axes_seen:
            axb = ax.get_window_extent(r)
            xi  = self._get_item("xlabel", ax=ax)
            yi  = self._get_item("ylabel", ax=ax)
            ti  = self._get_item("title",  ax=ax)
            xb  = self._total_x_tick_bbox(ax, r)
            yb  = self._total_y_tick_bbox(ax, r)
            xbb = self._artist_bbox(xi.artist, r) if xi else None
            ybb = self._artist_bbox(yi.artist, r) if yi else None
            title_bbs.append(self._artist_bbox(ti.artist, r) if ti else None)

            lu = _union_bboxes([yb, ybb])
            if lu:
                left_px = max(left_px,
                    max(0.0, axb.x0 - lu.x0)
                    + self.LEFT_MARGIN_SAFETY_PX + extra_left_px)

            bu = _union_bboxes([xb, xbb])
            if bu:
                bot_px = max(bot_px,
                    max(0.0, axb.y0 - bu.y0)
                    + self.BOTTOM_MARGIN_SAFETY_PX + extra_bottom_px)

        left   = max(min_left,   left_px / max(1.0, fw) + 0.01)
        bottom = max(min_bottom, bot_px  / max(1.0, fh) + 0.01)
        right  = min_right
        top    = min_top

        tu = _union_bboxes(title_bbs)
        if tu:
            prot = max(0.0, tu.y1 - fh)
            if prot > 0:
                top = min(top,
                    1.0 - (prot + self.TOP_MARGIN_SAFETY_PX + extra_top_px)
                    / max(1.0, fh))

        left   = min(max(left,   0.0), 0.95)   # wide upper bound for multi-subplot
        right  = min(max(right,  0.05), 1.0)
        bottom = min(max(bottom, 0.0), 0.45)
        top    = min(max(top,    0.45), 1.0)

        fig.subplots_adjust(left=left, right=right, bottom=bottom, top=top)
        self._place_all_artists()
        try: fig.canvas.draw_idle()
        except Exception: pass

    def summary(self):
        return {
            "figure_id": id(self.fig),
            "managed_items":      [it.kind for it in self.items],
            "managed_tick_groups":[g.kind  for g  in self.tick_groups],
            "num_items":       len(self.items),
            "num_tick_groups": len(self.tick_groups),
        }


# ─────────────────────────────────────────────────────────────────────
# Public helpers
# ─────────────────────────────────────────────────────────────────────

def get_layout_manager(fig) -> BanglaLayoutManager:
    key = id(fig)
    if key not in _MANAGER_REGISTRY:
        _MANAGER_REGISTRY[key] = BanglaLayoutManager(fig)
    return _MANAGER_REGISTRY[key]


def clear_layout_manager(fig) -> None:
    key = id(fig)
    m   = _MANAGER_REGISTRY.pop(key, None)
    if m is not None:
        m.clear(); m.disconnect()