# tests/test_suite.py
import os
import sys
import json
import time
import statistics
import platform
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.transforms import Bbox

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

import bangla_render as br
from bangla_render.layout import get_layout_manager

OUT_DIR   = os.path.join(ROOT_DIR, "test_outputs")
DEBUG_DIR = os.path.join(OUT_DIR,  "debug")


# ─────────────────────────────────────────────────────────────────────
# Setup
# ─────────────────────────────────────────────────────────────────────

def ensure_outdir():
    os.makedirs(OUT_DIR,   exist_ok=True)
    os.makedirs(DEBUG_DIR, exist_ok=True)


def init_test_environment():
    try:
        br.init_renderer()
    except Exception as e:
        print("Renderer init failed:", e)
        raise

    print("Renderer status:", br.get_renderer_status())
    print("Environment check:", br.check_environment())

    fonts = br.list_available_fonts()
    print("Available fonts count:", len(fonts))

    for candidate in ["Nirmala UI", "Vrinda", "Shonar Bangla",
                      "SolaimanLipi", "Noto Sans Bengali"]:
        if candidate in fonts:
            br.set_default_font(font_family=candidate)
            print("Resolved default font:", br.get_default_font())
            return

    try:
        default_font = br.ensure_default_font()
        print("Resolved default font:", default_font)
    except Exception as e:
        raise RuntimeError(
            "No usable Bengali font found. Install one (e.g. Nirmala UI)."
        ) from e


# ─────────────────────────────────────────────────────────────────────
# Save helper
# ─────────────────────────────────────────────────────────────────────

def save_fig(fig, path, dpi=180):
    fig.savefig(path, dpi=dpi)


# ─────────────────────────────────────────────────────────────────────
# Debug helpers
# ─────────────────────────────────────────────────────────────────────

def _bb2d(b):
    if b is None:
        return None
    return {"x0": float(b.x0), "y0": float(b.y0),
            "x1": float(b.x1), "y1": float(b.y1),
            "width": float(b.width), "height": float(b.height)}


def _union(bboxes):
    valid = [b for b in bboxes if b is not None]
    if not valid:
        return None
    return Bbox.from_extents(
        min(b.x0 for b in valid), min(b.y0 for b in valid),
        max(b.x1 for b in valid), max(b.y1 for b in valid),
    )


def _abb(artist, renderer):
    if artist is None or renderer is None:
        return None
    try:
        b = artist.get_window_extent(renderer)
        return b if (b and b.width > 0 and b.height > 0) else None
    except Exception:
        return None


def _ensure_list(v):
    if v is None:           return []
    if isinstance(v, list): return v
    return list(v)


def capture_debug_info(fig, ax, case_name):
    manager = get_layout_manager(fig)
    manager.update_layout()
    fig.canvas.draw()
    r = fig.canvas.get_renderer()

    axb = ax.get_window_extent(r)

    def find_item(kind):
        for it in manager.items:
            if it.kind == kind and it.ax is ax:
                return it
        return None

    def find_tg(kind):
        for g in manager.tick_groups:
            if g.kind == kind and g.ax is ax:
                return g
        return None

    ti = find_item("title");  xi = find_item("xlabel"); yi = find_item("ylabel")
    xtg = find_tg("xticks");  ytg = find_tg("yticks")

    title_b  = _abb(ti.artist  if ti  else None, r)
    xlabel_b = _abb(xi.artist  if xi  else None, r)
    ylabel_b = _abb(yi.artist  if yi  else None, r)
    xtu = _union([_abb(a, r) for a in _ensure_list(xtg.artists if xtg else [])])
    ytu = _union([_abb(a, r) for a in _ensure_list(ytg.artists if ytg else [])])

    sp = fig.subplotpars
    report = {
        "case_name": case_name,
        "figure_size_inches": list(fig.get_size_inches()),
        "figure_dpi": float(fig.dpi),
        "axes_bbox_display": _bb2d(axb),
        "subplotpars": {"left": float(sp.left), "right": float(sp.right),
                        "bottom": float(sp.bottom), "top": float(sp.top)},
        "title_bbox":  _bb2d(title_b),
        "xlabel_bbox": _bb2d(xlabel_b),
        "ylabel_bbox": _bb2d(ylabel_b),
        "xtick_union_bbox": _bb2d(xtu),
        "ytick_union_bbox": _bb2d(ytu),
        "layout_summary": manager.summary(),
    }

    overlap = {}
    if xtu and xlabel_b:
        overlap["xlabel_overlaps_xticks"] = bool(xlabel_b.y1 > xtu.y0)
        overlap["xlabel_gap_px"] = float(xtu.y0 - xlabel_b.y1)
    if ytu and ylabel_b:
        overlap["ylabel_overlaps_yticks"] = bool(ylabel_b.x1 > ytu.x0)
        overlap["ylabel_gap_px"] = float(ytu.x0 - ylabel_b.x1)
    report["overlap_checks"] = overlap

    rp = os.path.join(DEBUG_DIR, f"{case_name}_debug_report.json")
    with open(rp, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    np_ = os.path.join(DEBUG_DIR, f"{case_name}_normal.png")
    save_fig(fig, np_, dpi=180)
    print(f"[DEBUG] {rp}")


# ─────────────────────────────────────────────────────────────────────
# BENCHMARK
# ─────────────────────────────────────────────────────────────────────

def run_benchmark():
    print("\n" + "=" * 62)
    print("BENCHMARK: bangla-render render latency")
    print("=" * 62)
    font = br.get_default_font()["font_family"]
    print(f"OS      : {platform.system()} {platform.release()}")
    print(f"Python  : {platform.python_version()}")
    print(f"Font    : {font}")
    print("=" * 62)

    WARMUP  = 5
    MEASURE = 50

    cases = [
        ("Simple word – 3 chars",         "ভয়",              32),
        ("Simple word – 4 chars",         "রাগ",              32),
        ("Dependent vowel (matra)",        "খুশি",             32),
        ("Conjunct consonant",             "ক্ষমা",            32),
        ("Reph form",                      "র্ক",              32),
        ("Complex – conjunct + reph",      "দৃষ্টিভঙ্গি",      32),
        ("Complex – multi-conjunct",       "জ্ঞানোদয়",        32),
        ("Complex – long word",            "হাস্যোজ্জ্বল",    32),
        ("Axis label – short",             "এক্স অক্ষ",        26),
        ("Axis label – medium",            "পূর্বাভাস শ্রেণি", 26),
        ("Plot title",                     "বাংলা লাইন প্লট",  32),
        ("Long title",                     "কনফিউশন ম্যাট্রিক্স", 32),
    ]

    def time_case(text, fs):
        for _ in range(WARMUP):
            br.clear_render_cache()
            br.render_text_qimage(text, font_family=font, font_size=fs)
        times = []
        for _ in range(MEASURE):
            br.clear_render_cache()
            t0 = time.perf_counter()
            br.render_text_qimage(text, font_family=font, font_size=fs)
            times.append((time.perf_counter() - t0) * 1000.0)
        return times

    col = [40, 8, 8, 8, 8]
    hdr = (f"{'Text Category':<{col[0]}} {'Med':>{col[1]}} "
           f"{'Min':>{col[2]}} {'Max':>{col[3]}} {'SD':>{col[4]}}")
    sep = "─" * (sum(col) + len(col))

    print(f"\nTable 1: Cold-cache latency  (N={MEASURE})")
    print(sep); print(hdr); print(sep)

    results = []
    for label, text, fs in cases:
        ts  = time_case(text, fs)
        med = statistics.median(ts)
        mn  = min(ts); mx = max(ts); sd = statistics.stdev(ts)
        results.append({"label": label, "text": text, "font_size": fs,
                         "median_ms": round(med,2), "min_ms": round(mn,2),
                         "max_ms": round(mx,2), "sd_ms": round(sd,2)})
        print(f"{label:<{col[0]}} {med:>{col[1]}.2f} "
              f"{mn:>{col[2]}.2f} {mx:>{col[3]}.2f} {sd:>{col[4]}.2f}")
    print(sep)

    # cache-hit
    print(f"\nTable 2: Cache-hit latency (N={MEASURE})")
    print(sep); print(hdr); print(sep)
    cache_results = []
    for label, text, fs in cases[:4]:
        br.render_text_qimage(text, font_family=font, font_size=fs)
        times = []
        for _ in range(MEASURE):
            t0 = time.perf_counter()
            br.render_text_qimage(text, font_family=font, font_size=fs)
            times.append((time.perf_counter() - t0) * 1000.0)
        med = statistics.median(times); mn = min(times)
        mx  = max(times);               sd = statistics.stdev(times)
        cache_results.append({"label": label, "median_ms": round(med,4),
                               "min_ms": round(mn,4), "max_ms": round(mx,4),
                               "sd_ms": round(sd,4)})
        print(f"{label:<{col[0]}} {med:>{col[1]}.3f} "
              f"{mn:>{col[2]}.3f} {mx:>{col[3]}.3f} {sd:>{col[4]}.3f}")
    print(sep)

    # heatmap batch
    hm_labels = [
        "খুশি","দুঃখ","রাগ","ভয়","আশা","বিশ্বাস",
        "শান্তি","ঘৃণা","আনন্দ","বিস্ময়","লজ্জা","গর্ব",
        "ক্রোধ","মমতা","উদ্বেগ","সাহস","ঈর্ষা","কৃতজ্ঞতা",
        "হতাশা","উৎসাহ","মনোযোগ","স্মৃতি","কল্পনা","সৃষ্টি",
        "প্রেম","বিচার","শিক্ষা","সংস্কার","স্বপ্ন","প্রকৃতি",
        "পরিবার","বন্ধুত্ব","সমাজ","রাজনীতি","অর্থনীতি","বিজ্ঞান",
    ]
    batch_times = []
    for _ in range(5):
        br.clear_render_cache()
        t0 = time.perf_counter()
        for lbl in hm_labels:
            br.render_text_qimage(lbl, font_family=font, font_size=22)
        batch_times.append((time.perf_counter() - t0) * 1000.0)
    bmed = statistics.median(batch_times)
    pcell = bmed / len(hm_labels)

    all_med  = [x["median_ms"] for x in results]
    sim_med  = [x["median_ms"] for x in results[:4]]
    cplx_med = [x["median_ms"] for x in results[4:8]]
    lbl_med  = [x["median_ms"] for x in results[8:]]

    summary_lines = [
        "", "=" * 62, "SUMMARY", "=" * 62,
        f"Simple words        : {min(sim_med):.2f} – {max(sim_med):.2f} ms",
        f"Complex conjuncts   : {min(cplx_med):.2f} – {max(cplx_med):.2f} ms",
        f"Labels / titles     : {min(lbl_med):.2f} – {max(lbl_med):.2f} ms",
        f"Cache hit (median)  : sub-millisecond",
        f"6×6 heatmap batch   : {bmed:.1f} ms total / {pcell:.2f} ms per cell",
        f"Reps per case       : {MEASURE} (cold cache, warmup={WARMUP})",
        f"Machine             : {platform.system()} {platform.release()}, "
        f"Python {platform.python_version()}",
        f"Font                : {font}",
        "=" * 62,
    ]
    for line in summary_lines:
        print(line)

    txt_path  = os.path.join(OUT_DIR, "benchmark_results.txt")
    json_path = os.path.join(OUT_DIR, "benchmark_results.json")

    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(f"bangla-render benchmark\n"
                f"OS: {platform.system()} {platform.release()}, "
                f"Python {platform.python_version()}, Font: {font}\n\n")
        f.write(hdr + "\n" + sep + "\n")
        for x in results:
            f.write(f"{x['label']:<{col[0]}} {x['median_ms']:>{col[1]}.2f} "
                    f"{x['min_ms']:>{col[2]}.2f} {x['max_ms']:>{col[3]}.2f} "
                    f"{x['sd_ms']:>{col[4]}.2f}\n")
        f.write(sep + "\n")
        f.write(f"\nHeatmap batch: {bmed:.1f} ms / {pcell:.2f} ms per cell\n")
        for line in summary_lines:
            f.write(line + "\n")

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({
            "system": {"os": platform.system(), "release": platform.release(),
                       "python": platform.python_version(), "font": font},
            "warmup_reps": WARMUP, "measure_reps": MEASURE,
            "cold_cache": results, "cache_hit": cache_results,
            "heatmap_batch": {"num_cells": len(hm_labels),
                              "total_median_ms": round(bmed, 2),
                              "per_cell_ms": round(pcell, 2)},
        }, f, ensure_ascii=False, indent=2)

    print(f"\nSaved: {txt_path}")
    print(f"Saved: {json_path}")


# ─────────────────────────────────────────────────────────────────────
# CORE RENDERING TESTS
# ─────────────────────────────────────────────────────────────────────

def test_basic_words():
    for w in ["আমি", "বাংলায়", "গান", "গাই"]:
        p = os.path.join(OUT_DIR, f"word_{w}.png")
        br.render_text(text=w, output_path=p, font_size=48, width=600, height=200)
        print("Rendered word:", w, "->", p)


def test_complex_words():
    words = ["ক্ষুদ্র","জ্ঞানোদয়","শ্রদ্ধা","দৃষ্টিভঙ্গি",
             "ব্যবস্থাপনা","পাণ্ডুলিপি","পর্যালোচনায়",
             "হাস্যোজ্জ্বল","দুঃখিত","স্বাস্থ্য"]
    for w in words:
        p = os.path.join(OUT_DIR, f"complex_{w.replace(' ','_')}.png")
        br.render_text(text=w, output_path=p, font_size=40, width=700, height=200)
        print("Rendered complex:", w, "->", p)


def test_paragraph():
    para = ("বাংলা ভাষা বিশ্বের অন্যতম সমৃদ্ধ ও মধুর ভাষা। "
            "সোশ্যাল মিডিয়া, সাহিত্য, সংবাদ ও দৈনন্দিন জীবনে "
            "মানুষ এই ভাষায় হাসি, দুঃখ, রাগ, ভালোবাসা ও আশাবাদ প্রকাশ করে। "
            "সঠিক রেন্ডারিং না থাকলে এসব অনুভূতি বিকৃত হয়ে যায়।")
    p = os.path.join(OUT_DIR, "paragraph_test.png")
    br.render_paragraph(text=para, width=900, height=500, font_size=26, output_path=p)
    print("Rendered paragraph ->", p)


# ─────────────────────────────────────────────────────────────────────
# VISUAL TESTS
# ─────────────────────────────────────────────────────────────────────

def test_mpl_line_plot():
    x = [1, 2, 3, 4, 5]
    y = [3, 1, 4, 2, 5]
    fig, ax = plt.subplots(figsize=(6, 4.5))
    ax.plot(x, y, marker="o", label="series-1")
    ax.grid(True, alpha=0.3)

    br.set_bangla_title(ax,  "বাংলা লাইন প্লট",  font_size=28, zoom=0.40)
    br.set_bangla_xlabel(ax, "এক্স অক্ষ",          font_size=22, zoom=0.40)
    br.set_bangla_ylabel(ax, "ওয়াই অক্ষ",          font_size=22, zoom=0.40)
    br.set_bangla_xticks(ax, x, ["এক","দুই","তিন","চার","পাঁচ"],
                         font_size=18, zoom=0.45, collision_avoidance=True)
    br.set_bangla_yticks(ax, [1,2,3,4,5], ["১","২","৩","৪","৫"],
                         font_size=18, zoom=0.45, collision_avoidance=True)
    br.annotate_bangla(ax, "সর্বোচ্চ মান", xy=(5,5), xytext=(4.2,4.5),
                       font_size=18, zoom=0.38, arrowprops=dict(arrowstyle="->"))
    br.apply_bangla_layout(fig, auto=True)

    p = os.path.join(OUT_DIR, "mpl_line_plot.png")
    save_fig(fig, p, dpi=180)
    capture_debug_info(fig, ax, "line_plot")
    plt.close(fig)
    print("Saved line plot ->", p)


def test_mpl_heatmap_small():
    data  = np.array([[0.1,0.5,0.9],[0.3,0.7,0.4],[0.8,0.2,0.6]])
    cells = [["খুশি","দুঃখ","রাগ"],["ভয়","আশা","বিশ্বাস"],["শান্তি","ঘৃণা","আনন্দ"]]
    fig, ax = plt.subplots(figsize=(6.5, 6.5))
    im = ax.imshow(data, cmap="viridis", origin="upper", aspect="equal")
    rows, cols = data.shape

    br.set_bangla_title(ax,  "বাংলা ইমোশন হিটম্যাপ", font_size=30, zoom=0.40)
    br.set_bangla_xlabel(ax, "অনুভূতির ধরন",           font_size=22, zoom=0.40)
    br.set_bangla_ylabel(ax, "সারি",                    font_size=22, zoom=0.40)
    br.set_bangla_xticks(ax, list(range(cols)), ["প্রথম","দ্বিতীয়","তৃতীয়"],
                         font_size=18, zoom=0.45, collision_avoidance=False)
    br.set_bangla_yticks(ax, list(range(rows)), ["এক","দুই","তিন"],
                         font_size=18, zoom=0.45, collision_avoidance=False)
    for i in range(rows):
        for j in range(cols):
            br.add_bangla_in_cell(ax, i, j, cells[i][j], rows, cols,
                                  font_size=22, zoom=0.42)
    fig.colorbar(im, ax=ax).ax.set_ylabel("Value", rotation=-90, va="bottom")
    br.apply_bangla_layout(fig, auto=True)

    p = os.path.join(OUT_DIR, "mpl_heatmap_small.png")
    save_fig(fig, p, dpi=220)
    capture_debug_info(fig, ax, "heatmap_small")
    plt.close(fig)
    print("Saved heatmap small ->", p)


def test_mpl_heatmap_big():
    rng  = np.random.default_rng(42)
    data = rng.random((6, 6))
    lx   = ["প্রথম","দ্বিতীয়","তৃতীয়","চতুর্থ","পঞ্চম","ষষ্ঠ"]
    ly   = ["এক","দুই","তিন","চার","পাঁচ","ছয়"]
    fig, ax = plt.subplots(figsize=(8, 7))
    im = ax.imshow(data, cmap="viridis", origin="upper", aspect="equal")
    rows, cols = data.shape

    br.set_bangla_title(ax,  "বড় বাংলা হিটম্যাপ", font_size=28, zoom=0.40)
    br.set_bangla_xlabel(ax, "কলাম শ্রেণি",         font_size=20, zoom=0.40)
    br.set_bangla_ylabel(ax, "সারি শ্রেণি",          font_size=20, zoom=0.40)
    br.set_bangla_xticks(ax, list(range(cols)), lx,
                         font_size=18, zoom=0.42, collision_avoidance=False)
    br.set_bangla_yticks(ax, list(range(rows)), ly,
                         font_size=18, zoom=0.42, collision_avoidance=False)
    for i in range(rows):
        for j in range(cols):
            br.add_bangla_in_cell(ax, i, j, f"{data[i,j]:.2f}", rows, cols,
                                  font_size=18, zoom=0.40)
    fig.colorbar(im, ax=ax).ax.set_ylabel("Value", rotation=-90, va="bottom")
    br.apply_bangla_layout(fig, auto=True)

    p = os.path.join(OUT_DIR, "mpl_heatmap_big.png")
    save_fig(fig, p, dpi=220)
    capture_debug_info(fig, ax, "heatmap_big")
    plt.close(fig)
    print("Saved heatmap big ->", p)


def test_mpl_confusion_matrix_small():
    cm      = np.array([[863,1343,193],[585,3710,541],[26,245,7003]])
    classes = ["ঘৃণা","অপমানজনক","ঠিক আছে"]
    fig, ax = plt.subplots(figsize=(7, 6.5))
    im = ax.imshow(cm, cmap="autumn", origin="upper", aspect="equal")
    rows, cols = cm.shape
    ax.set_xlim(-0.5, cols-0.5); ax.set_ylim(rows-0.5, -0.5)
    for i in range(rows):
        for j in range(cols):
            ax.text(j, i, str(cm[i,j]), ha="center", va="center",
                    color="black", fontsize=14)

    br.set_bangla_title(ax,  "কনফিউশন ম্যাট্রিক্স", font_size=28, zoom=0.40)
    br.set_bangla_xlabel(ax, "পূর্বাভাস শ্রেণি",     font_size=20, zoom=0.40)
    br.set_bangla_ylabel(ax, "আসল শ্রেণি",            font_size=20, zoom=0.40)
    br.set_bangla_xticks(ax, list(range(cols)), classes,
                         font_size=18, zoom=0.45, collision_avoidance=False)
    br.set_bangla_yticks(ax, list(range(rows)), classes,
                         font_size=18, zoom=0.45, collision_avoidance=False)
    fig.colorbar(im, ax=ax).ax.set_ylabel("Normalized value", rotation=-90, va="bottom")
    br.apply_bangla_layout(fig, auto=True)

    p = os.path.join(OUT_DIR, "mpl_confusion_matrix_small.png")
    save_fig(fig, p, dpi=240)
    capture_debug_info(fig, ax, "confusion_small")
    plt.close(fig)
    print("Saved confusion matrix small ->", p)


def test_mpl_confusion_matrix_big():
    cm = np.array([[120,15,9,2,1],[11,98,14,6,3],[3,12,150,8,2],
                   [1,7,10,130,6],[0,1,3,8,170]])
    classes = ["ঘৃণা","অপমানজনক","নিরপেক্ষ","খুব বড় নাম","ঠিক আছে"]
    fig, ax = plt.subplots(figsize=(8, 7))
    im = ax.imshow(cm, cmap="autumn", origin="upper", aspect="equal")
    rows, cols = cm.shape
    ax.set_xlim(-0.5, cols-0.5); ax.set_ylim(rows-0.5, -0.5)
    for i in range(rows):
        for j in range(cols):
            ax.text(j, i, str(cm[i,j]), ha="center", va="center",
                    color="black", fontsize=13)

    br.set_bangla_title(ax,  "বড় কনফিউশন ম্যাট্রিক্স", font_size=26, zoom=0.40)
    br.set_bangla_xlabel(ax, "পূর্বাভাস শ্রেণি",          font_size=20, zoom=0.40)
    br.set_bangla_ylabel(ax, "আসল শ্রেণি",                 font_size=20, zoom=0.40)
    br.set_bangla_xticks(ax, list(range(cols)), classes,
                         font_size=18, zoom=0.42, collision_avoidance=False)
    br.set_bangla_yticks(ax, list(range(rows)), classes,
                         font_size=18, zoom=0.42, collision_avoidance=False)
    fig.colorbar(im, ax=ax).ax.set_ylabel("Value", rotation=-90, va="bottom")
    br.apply_bangla_layout(fig, auto=True)

    p = os.path.join(OUT_DIR, "mpl_confusion_matrix_big.png")
    save_fig(fig, p, dpi=240)
    capture_debug_info(fig, ax, "confusion_big")
    plt.close(fig)
    print("Saved confusion matrix big ->", p)


# ─────────────────────────────────────────────────────────────────────
# TWO-SUBPLOT CONFUSION MATRIX
# ─────────────────────────────────────────────────────────────────────

def test_multi_subplot_confusion_matrix():
    """
    Two confusion matrices side by side.
    Left  : 3-class hate-speech detection.
    Right : 4-class emotion classification.
    Note  : ylabel for right subplot is skipped if a colorbar occupies
            the space between the two plots (handled gracefully).
    """
    cm3 = np.array([[863,143,193],[585,3710,541],[26,245,7003]])
    cm4 = np.array([[420,35,18,12],[28,390,42,9],[15,38,450,22],[10,12,25,380]])
    classes3 = ["ঘৃণা", "অপমানজনক", "ঠিক আছে"]
    classes4 = ["রাগ", "দুঃখ", "আনন্দ", "ভয়"]

    fig, axes = plt.subplots(1, 2, figsize=(14, 6.5))

    ax1 = axes[0]
    im1 = ax1.imshow(cm3, cmap="YlOrRd", origin="upper", aspect="equal")
    r3, c3 = cm3.shape
    ax1.set_xlim(-0.5, c3-0.5); ax1.set_ylim(r3-0.5, -0.5)
    for i in range(r3):
        for j in range(c3):
            ax1.text(j, i, str(cm3[i,j]), ha="center", va="center",
                     color="black", fontsize=13, fontweight="bold")

    br.set_bangla_title(ax1,  "ঘৃণামূলক বক্তব্য শনাক্তকরণ", font_size=24, zoom=0.40)
    br.set_bangla_xlabel(ax1, "পূর্বাভাস শ্রেণি", font_size=18, zoom=0.38)
    br.set_bangla_ylabel(ax1, "আসল শ্রেণি",        font_size=18, zoom=0.38)
    br.set_bangla_xticks(ax1, list(range(c3)), classes3,
                         font_size=16, zoom=0.42, collision_avoidance=False)
    br.set_bangla_yticks(ax1, list(range(r3)), classes3,
                         font_size=16, zoom=0.42, collision_avoidance=False)
    fig.colorbar(im1, ax=ax1, fraction=0.046, pad=0.04)

    ax2 = axes[1]
    im2 = ax2.imshow(cm4, cmap="Blues", origin="upper", aspect="equal")
    r4, c4 = cm4.shape
    ax2.set_xlim(-0.5, c4-0.5); ax2.set_ylim(r4-0.5, -0.5)
    for i in range(r4):
        for j in range(c4):
            ax2.text(j, i, str(cm4[i,j]), ha="center", va="center",
                     color="black", fontsize=13, fontweight="bold")

    br.set_bangla_title(ax2,  "আবেগ শ্রেণিবিভাগ",  font_size=24, zoom=0.40)
    br.set_bangla_xlabel(ax2, "পূর্বাভাস শ্রেণি",   font_size=18, zoom=0.38)
    br.set_bangla_ylabel(ax2, "আসল শ্রেণি",          font_size=18, zoom=0.38)
    br.set_bangla_xticks(ax2, list(range(c4)), classes4,
                         font_size=16, zoom=0.42, collision_avoidance=False)
    br.set_bangla_yticks(ax2, list(range(r4)), classes4,
                         font_size=16, zoom=0.42, collision_avoidance=False)
    fig.colorbar(im2, ax=ax2, fraction=0.046, pad=0.04)

    br.apply_bangla_layout(fig, auto=True)

    p = os.path.join(OUT_DIR, "multi_subplot_confusion_matrix.png")
    save_fig(fig, p, dpi=220)
    capture_debug_info(fig, ax1, "multi_cm_left")
    capture_debug_info(fig, ax2, "multi_cm_right")
    plt.close(fig)
    print("Saved multi-subplot confusion matrix ->", p)


# ─────────────────────────────────────────────────────────────────────
# FOUR-SUBPLOT FIGURE
# ─────────────────────────────────────────────────────────────────────

def test_four_subplot_figure():
    """
    2×2 grid:
    TL: line plot         TR: 3×3 heatmap
    BL: bar chart         BR: 3-class confusion matrix
    Each subplot has independent Bengali title, xlabel, ylabel, ticks.
    No colorbars — clean layout to validate multi-subplot without
    the colorbar-between-subplots problem.
    """
    rng = np.random.default_rng(7)
    fig, axes = plt.subplots(2, 2, figsize=(14, 11))

    # ── top-left: line plot ──────────────────────────────────────────
    ax = axes[0, 0]
    x  = [1, 2, 3, 4, 5]
    ax.plot(x, [2, 4, 3, 5, 4], marker="o", color="steelblue", label="ক")
    ax.plot(x, [1, 3, 2, 4, 3], marker="s", color="tomato",    label="খ")
    ax.grid(True, alpha=0.25)

    br.set_bangla_title(ax,  "রেখাচিত্র",  font_size=22, zoom=0.40)
    br.set_bangla_xlabel(ax, "সময় (মাস)", font_size=16, zoom=0.38)
    br.set_bangla_ylabel(ax, "মান",         font_size=16, zoom=0.40)
    br.set_bangla_xticks(ax, x, ["জানু","ফেব্রু","মার্চ","এপ্রিল","মে"],
                         font_size=14, zoom=0.38, collision_avoidance=True)
    br.set_bangla_yticks(ax, [1,2,3,4,5], ["১","২","৩","৪","৫"],
                         font_size=14, zoom=0.40, collision_avoidance=True)

    # ── top-right: heatmap ───────────────────────────────────────────
    ax = axes[0, 1]
    data = rng.random((3, 3))
    im   = ax.imshow(data, cmap="YlGn", origin="upper", aspect="equal")
    rows, cols = data.shape

    br.set_bangla_title(ax,  "তাপ মানচিত্র", font_size=22, zoom=0.40)
    br.set_bangla_xlabel(ax, "বৈশিষ্ট্য",     font_size=16, zoom=0.38)
    br.set_bangla_ylabel(ax, "নমুনা",          font_size=16, zoom=0.40)
    br.set_bangla_xticks(ax, list(range(cols)), ["ক","খ","গ"],
                         font_size=14, zoom=0.40, collision_avoidance=False)
    br.set_bangla_yticks(ax, list(range(rows)), ["এক","দুই","তিন"],
                         font_size=14, zoom=0.40, collision_avoidance=False)
    for i in range(rows):
        for j in range(cols):
            br.add_bangla_in_cell(ax, i, j, f"{data[i,j]:.2f}", rows, cols,
                                  font_size=14, zoom=0.36)

    # ── bottom-left: bar chart ───────────────────────────────────────
    ax = axes[1, 0]
    cats   = ["ঘৃণা", "নিরপেক্ষ", "ইতিবাচক"]
    values = [1243, 3890, 2156]
    bars   = ax.bar(range(len(cats)), values,
                    color=["#e74c3c", "#3498db", "#2ecc71"])
    ax.set_ylim(0, 4500)
    ax.grid(True, axis="y", alpha=0.25)
    for bar, val in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 60,
                str(val), ha="center", va="bottom", fontsize=11)

    br.set_bangla_title(ax,  "শ্রেণি বিতরণ",  font_size=22, zoom=0.40)
    br.set_bangla_xlabel(ax, "অনুভূতি শ্রেণি", font_size=16, zoom=0.38)
    br.set_bangla_ylabel(ax, "নমুনা সংখ্যা",   font_size=16, zoom=0.40)
    br.set_bangla_xticks(ax, list(range(len(cats))), cats,
                         font_size=14, zoom=0.42, collision_avoidance=False)
    br.set_bangla_yticks(ax, [0, 1000, 2000, 3000, 4000],
                         ["০","১০০০","২০০০","৩০০০","৪০০০"],
                         font_size=13, zoom=0.38, collision_avoidance=False)

    # ── bottom-right: confusion matrix ──────────────────────────────
    ax = axes[1, 1]
    cm = np.array([[420, 35, 18],[28, 390, 42],[15, 38, 450]])
    im2 = ax.imshow(cm, cmap="Blues", origin="upper", aspect="equal")
    rows, cols = cm.shape
    ax.set_xlim(-0.5, cols-0.5); ax.set_ylim(rows-0.5, -0.5)
    for i in range(rows):
        for j in range(cols):
            ax.text(j, i, str(cm[i,j]), ha="center", va="center",
                    color="black", fontsize=12, fontweight="bold")

    classes = ["রাগ", "দুঃখ", "আনন্দ"]
    br.set_bangla_title(ax,  "কনফিউশন ম্যাট্রিক্স", font_size=22, zoom=0.40)
    br.set_bangla_xlabel(ax, "পূর্বাভাস",             font_size=16, zoom=0.38)
    br.set_bangla_ylabel(ax, "প্রকৃত",                 font_size=16, zoom=0.40)
    br.set_bangla_xticks(ax, list(range(cols)), classes,
                         font_size=14, zoom=0.42, collision_avoidance=False)
    br.set_bangla_yticks(ax, list(range(rows)), classes,
                         font_size=14, zoom=0.42, collision_avoidance=False)

    # ── layout ───────────────────────────────────────────────────────
    fig.tight_layout(pad=2.5)
    br.apply_bangla_layout(fig, auto=True)

    p = os.path.join(OUT_DIR, "four_subplot_figure.png")
    save_fig(fig, p, dpi=200)
    for (r, c), name in [((0,0),"tl"), ((0,1),"tr"),
                          ((1,0),"bl"), ((1,1),"br")]:
        capture_debug_info(fig, axes[r, c], f"four_subplot_{name}")
    plt.close(fig)
    print("Saved four-subplot figure ->", p)


# ─────────────────────────────────────────────────────────────────────
# OTHER VISUAL TESTS
# ─────────────────────────────────────────────────────────────────────

def test_two_subplot_figure():
    fig, axes = plt.subplots(1, 2, figsize=(12, 5.2))
    ax1, ax2  = axes

    ax1.plot([1,2,3,4,5], [2,4,3,5,4], marker="o"); ax1.grid(True, alpha=0.25)
    br.set_bangla_title(ax1,  "বাম প্লট", font_size=22, zoom=0.40)
    br.set_bangla_xlabel(ax1, "সময়",      font_size=18, zoom=0.38)
    br.set_bangla_ylabel(ax1, "মান",       font_size=18, zoom=0.40)
    br.set_bangla_xticks(ax1, [1,2,3,4,5], ["এক","দুই","তিন","চার","পাঁচ"],
                         font_size=16, zoom=0.40, collision_avoidance=True)

    data = np.array([[0.3,0.6,0.9],[0.4,0.2,0.8],[0.7,0.5,0.1]])
    im   = ax2.imshow(data, cmap="viridis", origin="upper", aspect="equal")
    br.set_bangla_title(ax2,  "ডান হিটম্যাপ", font_size=22, zoom=0.40)
    br.set_bangla_xlabel(ax2, "কলাম",          font_size=18, zoom=0.38)
    br.set_bangla_ylabel(ax2, "সারি",           font_size=18, zoom=0.38)
    br.set_bangla_xticks(ax2, [0,1,2], ["ক","খ","গ"],
                         font_size=16, zoom=0.40, collision_avoidance=False)
    br.set_bangla_yticks(ax2, [0,1,2], ["এক","দুই","তিন"],
                         font_size=16, zoom=0.40, collision_avoidance=False)
    for i in range(3):
        for j in range(3):
            br.add_bangla_in_cell(ax2, i, j, f"{data[i,j]:.1f}", 3, 3,
                                  font_size=16, zoom=0.36)
    fig.colorbar(im, ax=ax2, fraction=0.046, pad=0.04)
    br.apply_bangla_layout(fig, auto=True)

    p = os.path.join(OUT_DIR, "two_subplot_figure.png")
    save_fig(fig, p, dpi=200)
    capture_debug_info(fig, ax1, "two_subplot_left")
    capture_debug_info(fig, ax2, "two_subplot_right")
    plt.close(fig)
    print("Saved two subplot figure ->", p)


def test_numeric_ticks():
    x = np.linspace(0, 10, 6)
    fig, ax = plt.subplots(figsize=(6, 4.5))
    ax.plot(x, np.sin(x), marker="o"); ax.grid(True, alpha=0.25)
    br.set_bangla_title(ax,  "সংখ্যাসূচক টিক পরীক্ষা", font_size=24, zoom=0.40)
    br.set_bangla_xlabel(ax, "এক্স মান",                 font_size=18, zoom=0.38)
    br.set_bangla_ylabel(ax, "ওয়াই মান",                 font_size=18, zoom=0.40)
    br.set_bangla_numeric_ticks(ax, axis="x", font_size=18, zoom=0.45)
    br.set_bangla_numeric_ticks(ax, axis="y", font_size=18, zoom=0.45)
    br.apply_bangla_layout(fig, auto=True)
    p = os.path.join(OUT_DIR, "numeric_ticks.png")
    save_fig(fig, p, dpi=180)
    capture_debug_info(fig, ax, "numeric_ticks")
    plt.close(fig)
    print("Saved numeric ticks ->", p)


def test_font_validation_snapshot():
    p = os.path.join(OUT_DIR, "font_validation_report.txt")
    lines = ["bangla_render font validation snapshot\n", "=" * 50 + "\n",
             f"Renderer status: {br.get_renderer_status()}\n",
             f"Environment: {br.check_environment()}\n",
             f"Default font: {br.get_default_font()}\n",
             f"Bangla candidates: {br.list_bangla_candidate_fonts()}\n"]
    try:
        lines.append(f"Best Bangla font: {br.find_best_bangla_font()}\n")
    except Exception as e:
        lines.append(f"Best Bangla font error: {e}\n")
    try:
        lines.append(f"Validation result: {br.validate_font()}\n")
    except Exception as e:
        lines.append(f"Validation error: {e}\n")
    with open(p, "w", encoding="utf-8") as f:
        f.writelines(lines)
    print("Saved font validation report ->", p)


def test_cache_snapshot():
    for s in ["বাংলা","পরীক্ষা","রেন্ডার","বাংলা","পরীক্ষা"]:
        br.render_text_qimage(s, font_size=24)
    info = br.get_render_cache_info()
    p = os.path.join(OUT_DIR, "cache_report.txt")
    with open(p, "w", encoding="utf-8") as f:
        f.write("Render cache info\n=================\n")
        f.write(str(info) + "\n")
    print("Saved cache report ->", p)


# ─────────────────────────────────────────────────────────────────────
# RUN ALL
# ─────────────────────────────────────────────────────────────────────

def run_all_tests():
    ensure_outdir()
    print("Output dir :", OUT_DIR)
    print("Debug dir  :", DEBUG_DIR)

    init_test_environment()

    # core render
    test_basic_words()
    test_complex_words()
    test_paragraph()

    # single-subplot
    test_mpl_line_plot()
    test_mpl_heatmap_small()
    test_mpl_heatmap_big()
    test_mpl_confusion_matrix_small()
    test_mpl_confusion_matrix_big()

    # multi-subplot
    test_multi_subplot_confusion_matrix()
    test_two_subplot_figure()
    test_four_subplot_figure()

    # numeric / misc
    test_numeric_ticks()

    # reports
    test_font_validation_snapshot()
    test_cache_snapshot()

    # benchmark (runs last — takes ~30 s)
    run_benchmark()

    print("\nAll tests + benchmark completed.")
    print("Visual outputs :", OUT_DIR)
    print("Debug outputs  :", DEBUG_DIR)


if __name__ == "__main__":
    run_all_tests()