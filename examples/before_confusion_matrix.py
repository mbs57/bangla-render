import os
import numpy as np
import matplotlib.pyplot as plt

# Make sure assets/ exists
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "assets")
os.makedirs(ASSETS, exist_ok=True)


def main():
    # Simple 3x3 confusion matrix
    cm = np.array([
        [863, 1343, 193],
        [585, 3710, 541],
        [26,  245, 7003],
    ])

    classes = ["ঘৃণা", "অপমানজনক", "ঠিক আছে"]

    fig, ax = plt.subplots(figsize=(6, 6))

    im = ax.imshow(
        cm,
        cmap="autumn",
        origin="upper",
        aspect="equal",
    )

    ax.set_xticks(range(len(classes)))
    ax.set_yticks(range(len(classes)))

    # ❌ Matplotlib will break these Bangla labels (no proper shaping)
    ax.set_xticklabels(classes)
    ax.set_yticklabels(classes)

    ax.set_title("কনফিউশন ম্যাট্রিক্স")
    ax.set_xlabel("প্রেডিক্টেড লেবেল")
    ax.set_ylabel("সত্যিকারের লেবেল")

    # Numeric cell values
    rows, cols = cm.shape
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

    cbar = fig.colorbar(im, ax=ax)
    cbar.ax.set_ylabel("Normalized value", rotation=-90, va="bottom")

    out_path = os.path.join(ASSETS, "confusion_matrix_before.png")
    plt.savefig(out_path, dpi=250, bbox_inches="tight")
    plt.close(fig)
    print("Saved BEFORE confusion matrix ->", out_path)


if __name__ == "__main__":
    main()
