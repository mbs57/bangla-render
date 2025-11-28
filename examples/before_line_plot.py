import matplotlib.pyplot as plt

def main():
    x = [1, 2, 3, 4, 5]
    y = [3, 1, 4, 2, 5]

    fig, ax = plt.subplots(figsize=(5, 4))

    ax.plot(x, y, marker="o")
    ax.grid(True, alpha=0.3)

    # ❌ Matplotlib will NOT shape this correctly
    ax.set_title("বাংলা লাইন প্লট")
    ax.set_xlabel("এক্স অক্ষ")
    ax.set_ylabel("ওয়াই অক্ষ")

    plt.savefig("assets/line_plot_before.png", dpi=150, bbox_inches="tight")
    plt.close(fig)

if __name__ == "__main__":
    main()
