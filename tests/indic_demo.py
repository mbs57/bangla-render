# tests/test_indic_demo.py
"""
Indic script demo — renders Bengali pipeline for Hindi (Devanagari)
and Tamil scripts, producing two separate figures.
"""
import os
import sys
import numpy as np
import matplotlib.pyplot as plt

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

import bangla_render as br

OUT_DIR = os.path.join(ROOT_DIR, "test_outputs")


def ensure_outdir():
    os.makedirs(OUT_DIR, exist_ok=True)


def choose_best_font(candidates):
    available = set(br.list_available_fonts())
    for name in candidates:
        if name in available:
            return name
    return None


def init_environment():
    br.init_renderer()
    print("Renderer status:", br.get_renderer_status())

    hindi_candidates = [
        "Noto Sans Devanagari", "Mangal",
        "Nirmala UI", "Kohinoor Devanagari", "Arial Unicode MS",
    ]
    tamil_candidates = [
        "Noto Sans Tamil", "Latha", "Vijaya",
        "Nirmala UI", "Arial Unicode MS",
    ]

    hindi_font = choose_best_font(hindi_candidates)
    tamil_font = choose_best_font(tamil_candidates)
    print("Resolved Hindi font:", hindi_font)
    print("Resolved Tamil font:", tamil_font)

    if hindi_font is None:
        raise RuntimeError(
            "No Hindi/Devanagari font found. Install Noto Sans Devanagari or Mangal."
        )
    if tamil_font is None:
        raise RuntimeError(
            "No Tamil font found. Install Noto Sans Tamil, Latha, or Vijaya."
        )
    return hindi_font, tamil_font


def render_single_words(hindi_font, tamil_font):
    for text, font, fname in [
        ("नमस्ते",    hindi_font, "word_hindi.png"),
        ("வணக்கம்", tamil_font, "word_tamil.png"),
    ]:
        p = os.path.join(OUT_DIR, fname)
        br.render_text(text=text, output_path=p,
                       font_family=font, font_size=56, width=700, height=220)
        print(f"Rendered {fname} ->", p)


def _confusion_matrix_panel(ax, data, labels, title, xlabel, ylabel, font):
    """Add one confusion matrix panel to ax."""
    im = ax.imshow(data, cmap="Blues", origin="upper", aspect="equal")
    rows, cols = data.shape
    ax.set_xlim(-0.5, cols - 0.5)
    ax.set_ylim(rows - 0.5, -0.5)
    for i in range(rows):
        for j in range(cols):
            ax.text(j, i, str(data[i, j]),
                    ha="center", va="center", color="black", fontsize=12)

    br.set_bangla_title(ax,  title,  font_family=font, font_size=24, zoom=0.42)
    br.set_bangla_xlabel(ax, xlabel, font_family=font, font_size=18, zoom=0.38)
    br.set_bangla_ylabel(ax, ylabel, font_family=font, font_size=18, zoom=0.40)
    br.set_bangla_xticks(ax, list(range(cols)), labels,
                         font_family=font, font_size=16, zoom=0.38,
                         collision_avoidance=False)
    br.set_bangla_yticks(ax, list(range(rows)), labels,
                         font_family=font, font_size=16, zoom=0.38,
                         collision_avoidance=False)
    return im


def render_hindi_figure(hindi_font):
    """
    Single-subplot Hindi confusion matrix.
    No colorbar between subplots — ylabel renders correctly.
    """
    cm = np.array([
        [84, 12,  4],
        [10, 79, 11],
        [ 3,  8, 89],
    ])
    labels = ["खुशी", "दुख", "क्रोध"]

    fig, ax = plt.subplots(figsize=(7, 6.5))
    im = _confusion_matrix_panel(
        ax, cm, labels,
        title="हिंदी भ्रम मैट्रिक्स",
        xlabel="पूर्वानुमान वर्ग",
        ylabel="वास्तविक वर्ग",
        font=hindi_font,
    )
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04).ax.set_ylabel(
        "Value", rotation=-90, va="bottom")
    br.apply_bangla_layout(fig, auto=True)

    p = os.path.join(OUT_DIR, "indic_hindi_confusion_matrix.png")
    plt.savefig(p, dpi=220); plt.close(fig)
    print("Rendered Hindi confusion matrix ->", p)


def render_tamil_figure(tamil_font):
    """
    Single-subplot Tamil confusion matrix.
    """
    cm = np.array([
        [90,  7, 3],
        [ 9, 82, 9],
        [ 4, 11, 85],
    ])
    labels = ["மகிழ்ச்சி", "துக்கம்", "கோபம்"]

    fig, ax = plt.subplots(figsize=(7, 6.5))
    im = _confusion_matrix_panel(
        ax, cm, labels,
        title="தமிழ் குழப்ப அணி",
        xlabel="கணிக்கப்பட்ட வகை",
        ylabel="உண்மை வகை",
        font=tamil_font,
    )
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04).ax.set_ylabel(
        "Value", rotation=-90, va="bottom")
    br.apply_bangla_layout(fig, auto=True)

    p = os.path.join(OUT_DIR, "indic_tamil_confusion_matrix.png")
    plt.savefig(p, dpi=220); plt.close(fig)
    print("Rendered Tamil confusion matrix ->", p)

def run_demo():
    ensure_outdir()
    print("Output directory:", OUT_DIR)
    hindi_font, tamil_font = init_environment()

    render_single_words(hindi_font, tamil_font)
    render_hindi_figure(hindi_font)        # single subplot — ylabel always works
    render_tamil_figure(tamil_font)        # single subplot — ylabel always works
    print("\nIndic demo completed.")
    print("Outputs:")
    for f in ["word_hindi.png", "word_tamil.png",
              "indic_hindi_confusion_matrix.png",
              "indic_tamil_confusion_matrix.png"]:
        print(" ", os.path.join(OUT_DIR, f))


if __name__ == "__main__":
    run_demo()