# examples/demo_line_plot.py

import sys, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import matplotlib.pyplot as plt
import bangla_render as br

def main():
    x = [1, 2, 3, 4, 5]
    y = [3, 1, 4, 2, 5]

    fig, ax = plt.subplots(figsize=(5, 4))
    br.apply_bangla_layout(fig)

    ax.plot(x, y, marker="o")
    ax.grid(True, alpha=0.3)

    br.set_bangla_title(ax, "বাংলা লাইন প্লট", font_size=32)
    br.set_bangla_xlabel(ax, "এক্স অক্ষ", font_size=24)
    br.set_bangla_ylabel(ax, "ওয়াই অক্ষ", font_size=24)

    br.text(ax, 0.5, 0.8, "উদাহরণ", coord="axes", font_size=24)

    plt.savefig("assets/line_plot_after.png", dpi=150, bbox_inches="tight")
    plt.close(fig)

if __name__ == "__main__":
    main()
