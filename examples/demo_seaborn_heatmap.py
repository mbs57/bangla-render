import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import sys, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import bangla_render as br


def main():
    data = np.array([
        [0.1, 0.5, 0.9],
        [0.3, 0.7, 0.2],
        [0.8, 0.4, 0.6],
    ])

    words = np.array([
        ["খুশি",   "দুঃখ",   "রাগ"],
        ["ভয়",    "আশা",    "বিস্ময়"],
        ["শান্তি", "ঘৃণা",   "আনন্দ"],
    ])

    fig, ax = plt.subplots(figsize=(6, 6))
    br.apply_bangla_layout(fig)

    sns.heatmap(
        data,
        ax=ax,
        cmap="viridis",
        annot=False,
        cbar=True,
        square=True,
        xticklabels=False,
        yticklabels=False,
    )

    rows, cols = data.shape

    for i in range(rows):
        for j in range(cols):
            br.add_bangla_in_cell(
                ax,
                i, j,
                words[i, j],
                rows, cols,
                font_size=22,
            )

    br.set_bangla_title(ax, "বাংলা সিবর্ন হিটম্যাপ", font_size=36)
    br.set_bangla_xlabel(ax, "প্রেডিক্টেড ক্লাস", font_size=24)
    br.set_bangla_ylabel(ax, "সত্যিকারের ক্লাস", font_size=24)

    plt.savefig("assets/heatmap_after.png", dpi=200, bbox_inches="tight")
    plt.show()


if __name__ == "__main__":
    main()
