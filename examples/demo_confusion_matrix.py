import numpy as np
import matplotlib.pyplot as plt

import sys, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import bangla_render as br

def main():
    cm = np.array([
        [863, 1343, 193],
        [585, 3710, 541],
        [26,  245, 7003],
    ])

    classes_true = ["ঘৃণা", "অপমানজনক", "ঠিক আছে"]
    classes_pred = ["ঘৃণা", "অপমানজনক", "ঠিক আছে"]

    fig, ax = plt.subplots(figsize=(6, 6))
    br.apply_bangla_layout(fig)  # balanced margins

    im = ax.imshow(
        cm,
        cmap="autumn",
        origin="upper",
        aspect="equal",
    )

    rows, cols = cm.shape

    # Fix visible grid boundaries
    ax.set_xlim(-0.5, cols - 0.5)
    ax.set_ylim(rows - 0.5, -0.5)

    # Numeric ticks only (no Bangla)
    ax.set_xticks(range(cols))
    ax.set_yticks(range(rows))
    ax.set_xticklabels([])
    ax.set_yticklabels([])

    # Numeric values inside cells
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

    # Bangla class names along X-axis (predicted labels)
    for j, label in enumerate(classes_pred):
        x_axes = (j + 0.5) / cols
        br.text(
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

    # Bangla class names along Y-axis (true labels)
    for i, label in enumerate(classes_true):
        y_axes = 1.0 - (i + 0.5) / rows
        br.text(
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

    br.set_bangla_title(ax, "কনফিউশন ম্যাট্রিক্স", font_size=32, zoom=0.44)

    cbar = fig.colorbar(im, ax=ax)
    cbar.ax.set_ylabel("Normalized value", rotation=-90, va="bottom")

    plt.savefig("assets/confusion_matrix_after.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    main()
