# examples/before_heatmap.py
import numpy as np
import matplotlib.pyplot as plt

def main():
    data = np.array([
        [0.1, 0.5, 0.9],
        [0.3, 0.7, 0.2],
        [0.8, 0.4, 0.6],
    ])

    fig, ax = plt.subplots(figsize=(6, 6))

    im = ax.imshow(data, cmap="viridis", origin="upper", aspect="equal")

    ax.set_xticks(range(3))
    ax.set_yticks(range(3))

    # ❌ Matplotlib will break Bangla here
    ax.set_xticklabels(["খুশি", "দুঃখ", "রাগ"])
    ax.set_yticklabels(["শান্তি", "ঘৃণা", "আনন্দ"])

    ax.set_title("বাংলা ইমোশন হিটম্যাপ")
    ax.set_xlabel("এক্স অক্ষ")
    ax.set_ylabel("ওয়াই অক্ষ")

    plt.colorbar(im, ax=ax)
    plt.savefig("assets/heatmap_before.png", dpi=200, bbox_inches="tight")
    plt.close(fig)

if __name__ == "__main__":
    main()
