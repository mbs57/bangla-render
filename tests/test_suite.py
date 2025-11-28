import os
import sys
import numpy as np
import matplotlib.pyplot as plt

# Make sure we can import the local package when running from repo root
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from bangla_render.renderer import render_text, render_paragraph
from bangla_render.mpl_support import (
    set_bangla_title,
    set_bangla_xlabel,
    set_bangla_ylabel,
    add_bangla_in_cell,
    bangla_text,
    apply_bangla_layout,
)

OUT_DIR = os.path.join(ROOT_DIR, "test_outputs")


def ensure_outdir():
    os.makedirs(OUT_DIR, exist_ok=True)


def test_basic_words():
    """Render a few basic words."""
    words = ["আমি", "বাংলায়", "গান", "গাই"]
    for w in words:
        fname = os.path.join(OUT_DIR, f"word_{w}.png")
        render_text(text=w, output_path=fname, font_size=48, width=600, height=200)
        print("Rendered word:", w, "->", fname)


def test_complex_words():
    """Render complex conjuncts / juktakkhor."""
    words = [
        "ক্ষুদ্র", "জ্ঞানোদয়", "শ্রদ্ধা", "দৃষ্টিভঙ্গি",
        "ব্যবস্থাপনা", "পাণ্ডুলিপি", "পর্যালোচনায়",
        "হাস্যোজ্জ্বল", "দুঃখিত", "স্বাস্থ্য",
    ]
    for w in words:
        safe = w.replace(" ", "_")
        fname = os.path.join(OUT_DIR, f"complex_{safe}.png")
        render_text(text=w, output_path=fname, font_size=40, width=700, height=200)
        print("Rendered complex:", w, "->", fname)


def test_paragraph():
    """Render a multi-line paragraph with wrapping."""
    paragraph = (
        "বাংলা ভাষা বিশ্বের অন্যতম সমৃদ্ধ ও মধুর ভাষা। "
        "সোশ্যাল মিডিয়া, সাহিত্য, সংবাদ ও দৈনন্দিন জীবনে "
        "মানুষ এই ভাষায় হাসি, দুঃখ, রাগ, ভালোবাসা ও আশাবাদ প্রকাশ করে। "
        "সঠিক রেন্ডারিং না থাকলে এসব অনুভূতি বিকৃত হয়ে যায়।"
    )
    fname = os.path.join(OUT_DIR, "paragraph_test.png")
    render_paragraph(
        text=paragraph,
        width=900,
        height=500,
        font_size=26,
        output_path=fname,
    )
    print("Rendered paragraph ->", fname)


def test_mpl_line_plot():
    """Test Bangla title/xlabel/ylabel on a simple line plot."""
    x = [1, 2, 3, 4, 5]
    y = [3, 1, 4, 2, 5]

    fig, ax = plt.subplots(figsize=(5, 4))
    apply_bangla_layout(fig)  # use balanced defaults

    ax.plot(x, y, marker="o")
    ax.grid(True, alpha=0.3)

    set_bangla_title(ax, "বাংলা লাইন প্লট", font_size=32, zoom=0.42)
    set_bangla_xlabel(ax, "এক্স অক্ষ", font_size=24, zoom=0.40)
    set_bangla_ylabel(ax, "ওয়াই অক্ষ", font_size=24, zoom=0.40)

    out_path = os.path.join(OUT_DIR, "mpl_line_plot.png")
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("Saved Matplotlib line plot ->", out_path)


def test_mpl_heatmap():
    """Test Bangla title and axis labels on a heatmap, plus Bangla text inside cells."""
    data = np.array([
        [0.1, 0.5, 0.9],
        [0.3, 0.7, 0.4],
        [0.8, 0.2, 0.6],
    ])

    cell_texts = [
        ["খুশি", "দুঃখ", "রাগ"],
        ["ভয়", "আশা", "বিশ্বাস"],
        ["শান্তি", "ঘৃণা", "আনন্দ"],
    ]

    fig, ax = plt.subplots(figsize=(6, 6))
    apply_bangla_layout(fig)  # defaults also work well here

    im = ax.imshow(
        data,
        cmap="viridis",
        origin="upper",
        aspect="equal",
    )

    rows, cols = data.shape

    ax.set_xticks(range(cols))
    ax.set_yticks(range(rows))
    ax.set_xticklabels([])
    ax.set_yticklabels([])

    for i in range(rows):
        for j in range(cols):
            add_bangla_in_cell(
                ax,
                i, j,
                cell_texts[i][j],
                rows, cols,
                font_size=22,
            )

    cbar = fig.colorbar(im, ax=ax)
    cbar.ax.set_ylabel("Value", rotation=-90, va="bottom")

    set_bangla_title(ax, "বাংলা ইমোশন হিটম্যাপ", font_size=36, zoom=0.42)
    set_bangla_xlabel(ax, "এক্স অক্ষ", font_size=28, zoom=0.40)
    set_bangla_ylabel(ax, "ওয়াই অক্ষ", font_size=28, zoom=0.40)

    out_path = os.path.join(OUT_DIR, "mpl_heatmap.png")
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print("Saved Matplotlib heatmap ->", out_path)


def test_mpl_confusion_matrix_bangla_classes():
    """Confusion-matrix style heatmap with Bangla class names along axes."""
    cm = np.array([
        [863, 1343, 193],
        [585, 3710, 541],
        [26,  245, 7003],
    ])

    classes_true = ["ঘৃণা", "অপমানজনক", "ঠিক আছে"]
    classes_pred = ["ঘৃণা", "অপমানজনক", "ঠিক আছে"]

    fig, ax = plt.subplots(figsize=(6, 6))
    apply_bangla_layout(fig)

    im = ax.imshow(
        cm,
        cmap="autumn",
        origin="upper",
        aspect="equal",
    )

    rows, cols = cm.shape

    ax.set_xlim(-0.5, cols - 0.5)
    ax.set_ylim(rows - 0.5, -0.5)

    ax.set_xticks(range(cols))
    ax.set_yticks(range(rows))
    ax.set_xticklabels([])
    ax.set_yticklabels([])

    for i in range(rows):
        for j in range(cols):
            ax.text(
                j, i,
                str(cm[i, j]),
                ha="center",
                va="center",
                color="black",
                fontsize=12,
            )

    for j, label in enumerate(classes_pred):
        x_axes = (j + 0.5) / cols
        bangla_text(
            ax,
            x_axes,
            -0.10,
            label,
            coord="axes",
            ha="center",
            va="top",
            font_size=20,
            zoom=0.42,
        )

    for i, label in enumerate(classes_true):
        y_axes = 1.0 - (i + 0.5) / rows
        bangla_text(
            ax,
            -0.12,
            y_axes,
            label,
            coord="axes",
            ha="right",
            va="center",
            font_size=20,
            zoom=0.42,
        )

    set_bangla_title(ax, "কনফিউশন ম্যাট্রিক্স", font_size=32, zoom=0.44)

    cbar = fig.colorbar(im, ax=ax)
    cbar.ax.set_ylabel("Normalized value", rotation=-90, va="bottom")

    out_path = os.path.join(OUT_DIR, "mpl_confusion_matrix_bangla_classes.png")
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print("Saved Bangla confusion matrix ->", out_path)


def run_all_tests():
    ensure_outdir()
    print("Output directory:", OUT_DIR)
    test_basic_words()
    test_complex_words()
    test_paragraph()
    test_mpl_line_plot()
    test_mpl_heatmap()
    test_mpl_confusion_matrix_bangla_classes()
    print("\nAll tests completed. Inspect images in:", OUT_DIR)


if __name__ == "__main__":
    run_all_tests()
