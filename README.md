# bangla-render

Render **proper Bengali (বাংলা)** text in Matplotlib using Qt (PySide6) for shaping.

Matplotlib’s built-in text engine does *not* use HarfBuzz, so Bangla text often looks
broken: juktakkhor, reph, vowel signs, and ligatures don’t render correctly.

`bangla-render` fixes this by rendering text with Qt and then overlaying it in Matplotlib
as images.

---

## ✨ Features

- Correct shaping for Bengali text (matra, juktakkhor, reph, ligatures)
- Drop-in style helpers:
  - `set_bangla_title(ax, ...)`
  - `set_bangla_xlabel(ax, ...)`
  - `set_bangla_ylabel(ax, ...)`
  - `bangla_text(ax, ...)` / `br.text(...)`
- Works with:
  - regular Matplotlib plots
  - seaborn heatmaps
  - confusion matrices
- Simple layout helper: `apply_bangla_layout(fig)`


## 🔍 Before / After

### 1. Line plot

| Default Matplotlib (broken) | With `bangla-render` (fixed) |
|-----------------------------|------------------------------|
| ![before line](assets/line_plot_before.png) | ![after line](assets/line_plot_after.png) |

### 2. Heatmap

| Default Matplotlib (broken labels) | With `bangla-render` |
|-----------------------------------|-----------------------|
| ![before heatmap](assets/heatmap_before.png) | ![after heatmap](assets/heatmap_after.png) |

### 3. Confusion matrix

| Default Matplotlib | With `bangla-render` |
|--------------------|----------------------|
| ![before confusion](assets/confusion_matrix_before.png) | ![after confusion](assets/confusion_matrix_after.png) |

---

## 🚀 Quick start

```python
import matplotlib.pyplot as plt
import bangla_render as br

fig, ax = plt.subplots()
br.apply_bangla_layout(fig)

ax.plot([1, 2, 3], [3, 1, 4])

br.set_bangla_title(ax, "বাংলা লাইন প্লট")
br.set_bangla_xlabel(ax, "এক্স অক্ষ")
br.set_bangla_ylabel(ax, "ওয়াই অক্ষ")

br.text(ax, 0.5, 0.8, "উদাহরণ", coord="axes")

plt.show()
