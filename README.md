# 🇧🇩 bangla-render
<p align="center">
  <img src="https://raw.githubusercontent.com/mbs57/bangla-render/main/assets/banner.png" alt="bangla-render: Bengali text rendering for Matplotlib & Seaborn" width="80%">
</p>

<p align="center">

  <!-- PyPI version -->
  <a href="https://pypi.org/project/bangla-render/">
    <img src="https://img.shields.io/pypi/v/bangla-render?color=3fb950&label=PyPI&logo=pypi&logoColor=white" alt="PyPI version">
  </a>

  <!-- Python versions (explicit >=3.8 badge) -->
  <a href="https://pypi.org/project/bangla-render/">
    <img src="https://img.shields.io/badge/Python-%E2%89%A53.8-blue?logo=python&logoColor=white" alt="Python ≥3.8">
  </a>

  <!-- License -->
  <a href="https://github.com/mbs57/bangla-render/blob/main/LICENSE">
    <img src="https://img.shields.io/github/license/mbs57/bangla-render.svg?color=orange" alt="License">
  </a>

  <!-- Author -->
  <a href="https://github.com/mbs57">
    <img src="https://img.shields.io/badge/Author-Mrinal%20Basak%20Shuvo-6f42c1.svg?logo=github" alt="Author">
  </a>

</p>




### Bengali Text Rendering for Matplotlib & Seaborn (with full OpenType shaping)

**bangla-render** is the first open-source Python library that enables fully correct **Bengali text rendering** inside Matplotlib and Seaborn.

Matplotlib cannot shape Bengali text — it does not use HarfBuzz and therefore fails with:

* Matra (ি, ী, ু, ূ, ৃ)
* Reph (র্)
* Juktakkhor (জ্ঞ, ক্ষ, ন্দ, ত্ম, ন্ত …)
* GSUB/GPOS OpenType shaping

So Bengali titles, axis labels, annotations, and heatmap text become **broken, disjoint, or scrambled**.

💡 **bangla-render solves this completely.**
It uses **Qt's HarfBuzz engine** to shape Bengali correctly, renders it into an RGBA image, and overlays it into Matplotlib using `OffsetImage`, bypassing Matplotlib's broken text renderer entirely.

---

## ✨ What's New in v0.2

| Area | Change |
|---|---|
| **Architecture** | Single file split into 5 dedicated modules |
| **Font handling** | Auto-discovery, validation & fallback chain |
| **Performance** | LRU render cache (256 entries, ~4× speedup on repeated labels) |
| **Layout engine** | Full `BanglaLayoutManager` — event-driven, multi-subplot aware |
| **Tick labels** | New `set_bangla_xticks()` / `set_bangla_yticks()` |
| **Indic scripts** | Hindi (Devanagari) and Tamil verified out-of-the-box |
| **Environment** | Headless / Colab / Kaggle detection in `backend.py` |
| **Test suite** | Benchmark, debug JSON reports, 4-subplot and multi-subplot tests |

---

## ✨ Features

### ✔ Full Bengali OpenType shaping

* Correct matra placement
* Proper conjunct formation
* Reph, rafar, vowel signs
* Multi-line paragraph shaping
* True Unicode (no ANSI/Bijoy hacks)

### ✔ High-level Matplotlib API

```python
br.set_bangla_title(ax, "বাংলা শিরোনাম")
br.set_bangla_xlabel(ax, "এক্স অক্ষ")
br.set_bangla_ylabel(ax, "ওয়াই অক্ষ")
br.set_bangla_xticks(ax, positions, ["একটি", "দুটি", "তিনটি"])
br.set_bangla_yticks(ax, positions, ["রাগ", "আনন্দ", "ভয়"])
br.text(ax, 0.5, 0.5, "মাঝখানে", coord="axes")
```

### ✔ Heatmap and confusion-matrix support

```python
br.add_bangla_in_cell(ax, row, col, "খুশি", rows, cols)
```

### ✔ Automatic layout engine

`apply_bangla_layout(fig, auto=True)` measures every placed label using the
Matplotlib renderer and adjusts margins so titles, tick labels, and axis labels
never overlap — correctly for any number of subplots.

### ✔ Works everywhere

* Matplotlib and Seaborn
* Jupyter / JupyterLab / VS Code
* Windows 10/11, macOS, Linux
* Any Matplotlib backend (Agg, TkAgg, QtAgg, …)

---

## 🔍 Before & After Comparison

### Line Plot

| Default Matplotlib | With bangla-render |
|---|---|
| ![before](https://raw.githubusercontent.com/mbs57/bangla-render/main/assets/line_plot_before.png) | ![after](https://raw.githubusercontent.com/mbs57/bangla-render/main/assets/line_plot_after.png) |

### Heatmap

| Before | After |
|---|---|
| ![before](https://raw.githubusercontent.com/mbs57/bangla-render/main/assets/heatmap_before.png) | ![after](https://raw.githubusercontent.com/mbs57/bangla-render/main/assets/heatmap_after.png) |

### Confusion Matrix

| Before | After |
|---|---|
| ![before](https://raw.githubusercontent.com/mbs57/bangla-render/main/assets/confusion_matrix_before.png) | ![after](https://raw.githubusercontent.com/mbs57/bangla-render/main/assets/confusion_matrix_after.png) |

---

## 🔥 Why This Library Exists

Matplotlib cannot shape Indic scripts.
Even with Bangla fonts installed, it produces:

* Disjoint characters
* Wrong glyph order
* Broken juktakkhor
* Incorrect matra positioning

Existing "solutions" only work for **very simple words** like ভয়, রাগ —
but fail completely for:

* খুশি
* দৃষ্টিভঙ্গি
* শ্রদ্ধা
* ব্যবস্থাপনা
* হাস্যোজ্জ্বল
* পর্যালোচনায়
* And any real paragraph

Before **bangla-render**, there was:

* No PyPI library
* No correct Bengali shaping
* No Seaborn heatmap support
* No way to set Bengali xlabel/ylabel/title
* No Unicode-safe method

**bangla-render fills this gap for the first time.**

---

## 🚀 Try It Instantly

Run the demo notebook directly in your browser — no setup needed:

| Platform | Launch |
|---|---|
| Kaggle | [![Open in Kaggle](https://kaggle.com/static/images/open-in-kaggle.svg)](https://kaggle.com/kernels/welcome?src=https://raw.githubusercontent.com/mbs57/bangla-render/main/examples/bangla_render_kaggle_colab_demo.ipynb) |
| Google Colab | [![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/mbs57/bangla-render/blob/main/examples/bangla_render_kaggle_colab_demo.ipynb) |

---

## 📦 Installation

```bash
pip install bangla-render
```

**Dependencies** (installed automatically):

| Package | Purpose |
|---|---|
| `PySide6` | Qt / HarfBuzz shaping engine |
| `NumPy` | RGBA array conversion |
| `Matplotlib` | Plot integration |

> **Font note:** On Windows, *Nirmala UI* (built-in) is used automatically.  
> On Linux / macOS, install *Noto Sans Bengali*:  
> `sudo apt install fonts-noto` or `brew install font-noto-sans`

---

## 🚀 Quick Start

### Line plot

```python
import matplotlib.pyplot as plt
import bangla_render as br

br.init_renderer()                          # initialise Qt once

fig, ax = plt.subplots(figsize=(6, 4))

ax.plot([1, 2, 3, 4, 5], [2, 4, 3, 5, 4])

br.set_bangla_title(ax,  "রেখাচিত্র")
br.set_bangla_xlabel(ax, "সময় (মাস)")
br.set_bangla_ylabel(ax, "মান")
br.set_bangla_xticks(ax, [1, 2, 3, 4, 5],
                    ["জানু", "ফেব্রু", "মার্চ", "এপ্রিল", "মে"])

br.apply_bangla_layout(fig, auto=True)
plt.savefig("line_plot.png", dpi=150)
plt.show()
```

### Heatmap

```python
import seaborn as sns
import numpy as np
import matplotlib.pyplot as plt
import bangla_render as br

br.init_renderer()

data  = np.random.rand(3, 3)
words = [["খুশি", "রাগ", "আশা"],
         ["ভয়",  "বিস্ময়", "শান্তি"],
         ["ঘৃণা", "আনন্দ", "সুখ"]]

fig, ax = plt.subplots(figsize=(6, 6))
sns.heatmap(data, ax=ax, cbar=True,
            xticklabels=False, yticklabels=False)

rows, cols = data.shape
for i in range(rows):
    for j in range(cols):
        br.add_bangla_in_cell(ax, i, j, words[i][j], rows, cols)

br.set_bangla_title(ax,  "বাংলা হিটম্যাপ")
br.set_bangla_xlabel(ax, "পূর্বাভাস শ্রেণি")
br.set_bangla_ylabel(ax, "আসল শ্রেণি")

br.apply_bangla_layout(fig, auto=True)
plt.savefig("heatmap.png", dpi=150)
plt.show()
```

### Multi-subplot figure

```python
import matplotlib.pyplot as plt
import bangla_render as br

br.init_renderer()

fig, axes = plt.subplots(1, 2, figsize=(12, 5))

# Left subplot
axes[0].plot([1, 2, 3], [3, 1, 4])
br.set_bangla_title(axes[0],  "বাম প্লট")
br.set_bangla_xlabel(axes[0], "সময়")
br.set_bangla_ylabel(axes[0], "মান")

# Right subplot — with colorbar (ylabel auto-skipped when blocked)
import numpy as np
im = axes[1].imshow(np.random.rand(3, 3), cmap="viridis")
fig.colorbar(im, ax=axes[1])
br.set_bangla_title(axes[1],  "ডান হিটম্যাপ")
br.set_bangla_xlabel(axes[1], "কলাম")

br.apply_bangla_layout(fig, auto=True)
plt.savefig("multisubplot.png", dpi=150)
plt.show()
```

---

## 🌐 Other Indic Scripts

The rendering pipeline is **language-agnostic** — pass any Brahmic script Unicode
string and a matching OpenType font:

```python
# Hindi (Devanagari) — uses Nirmala UI on Windows
br.set_bangla_ylabel(ax, "वास्तविक वर्ग",
                    font_family="Nirmala UI")

# Tamil — same font on Windows
br.set_bangla_ylabel(ax, "உண்மை வகை",
                    font_family="Nirmala UI")
```

Verified scripts: **Bengali, Hindi (Devanagari), Tamil.**  
Expected to work (font availability required):
Assamese, Odia, Gujarati, Gurmukhi, Sinhala.

---

## 🧩 API Reference

### Initialisation

| Function | Description |
|---|---|
| `init_renderer()` | Initialise Qt application (call once at startup) |
| `check_environment()` | Report Qt status, headless mode, Colab/Kaggle detection |
| `get_renderer_status()` | Detailed Qt initialisation info |

### Font utilities

| Function | Description |
|---|---|
| `find_best_bangla_font()` | Return the best available Bengali font name |
| `list_available_fonts()` | List all system fonts |
| `list_bangla_candidate_fonts()` | List Bengali candidate fonts found on system |

### Plot labels

| Function | Description |
|---|---|
| `set_bangla_title(ax, text, **kw)` | Set per-axes title |
| `set_bangla_xlabel(ax, text, **kw)` | Set x-axis label |
| `set_bangla_ylabel(ax, text, **kw)` | Set y-axis label |
| `set_bangla_xticks(ax, positions, labels, **kw)` | Set x-axis tick labels |
| `set_bangla_yticks(ax, positions, labels, **kw)` | Set y-axis tick labels |

### Annotations

| Function | Description |
|---|---|
| `bangla_text(ax, x, y, text, coord="axes", **kw)` | Place text at arbitrary coordinates |
| `add_bangla_in_cell(ax, row, col, text, rows, cols, **kw)` | Annotate heatmap / matrix cell |

### Layout

| Function | Description |
|---|---|
| `apply_bangla_layout(fig, auto=False, **kw)` | Adjust margins; `auto=True` measures placed artists |

### Cache

| Function | Description |
|---|---|
| `get_render_cache_info()` | Return cache hit/miss counts and occupancy |
| `clear_render_cache()` | Clear the LRU cache (useful before benchmarking) |

### Low-level rendering

| Function | Description |
|---|---|
| `render_text(text, output_path, **kw)` | Render text to a PNG file |
| `render_text_qimage(text, **kw)` | Render text to a QImage (internal use) |
| `render_paragraph(text, output_path, **kw)` | Render multi-line paragraph to PNG |

---

## 🏗 Architecture

```
bangla-render v0.2 — five-module architecture
─────────────────────────────────────────────
backend.py      Qt application lifecycle, headless / Colab / Kaggle detection
fonts.py        Font discovery, validation (conjunct/matra test), fallback chain
renderer.py     HarfBuzz shaping via Qt, QImage rasterisation, LRU cache
layout.py       BanglaLayoutManager — event-driven, multi-subplot, colorbar-aware
mpl_support.py  Public Matplotlib API — all set_bangla_* functions
```

---

## ⚡ Performance

Measured on Windows 10, Python 3.11.9, font: *Nirmala UI*, N = 50 calls, cold cache.

| Text category | Median (ms) | Cache hit (ms) |
|---|---|---|
| Simple word (3–4 chars) | 0.27 | 0.06 |
| Conjunct consonant | 0.32 | 0.07 |
| Complex multi-conjunct | 0.40 | 0.08 |
| Axis label (medium) | 0.57 | 0.10 |
| 6×6 heatmap (36 cells, batch) | 10.5 ms total | — |

The LRU cache delivers roughly a **4× speedup** for repeated labels.

---

## 🧪 Running the Test Suite

```bash
git clone https://github.com/mbs57/bangla-render.git
cd bangla-render
pip install -e .
python tests/test_suite.py
```

Outputs saved to `test_outputs/`. Debug JSON reports saved to `test_outputs/debug/`.  
Benchmark results saved to `test_outputs/benchmark_results.txt` and `.json`.

---

## 🗺 Roadmap

- [x] v0.1 — Bengali rendering for title, xlabel, ylabel, heatmap cells
- [x] v0.2 — Five-module architecture, font validation, LRU cache, tick labels, Indic scripts, layout engine
- [ ] v0.3 — Mixed Bengali + MathText (`$\alpha$`) support
- [ ] v0.4 — Vector output via SVG path extraction
- [ ] v0.5 — Extend verified Indic support: Odia, Gujarati, Malayalam, Telugu
- [ ] v1.0 — Production-ready stable release and full documentation site

---

## 📄 License

MIT License — free for personal, academic, and commercial use.

---

## 📖 Citation

If you use bangla-render in research, please cite:

```bibtex
@article{shuvo2025banglarender,
  title   = {bangla-render: Correct Bengali Text Rendering for
             Matplotlib \& Seaborn Using Qt/HarfBuzz},
  author  = {Shuvo, Mrinal Basak},
  journal = {SoftwareX},
  year    = {2025},
  note    = {Under review, Manuscript SOFTX-D-25-00884}
}
```

---

## ⭐ Acknowledgements

This project aims to make scientific and data visualisation accessible to
**millions of Bengali speakers** — helping students, educators, analysts,
and researchers present data in their native language.

Built on the shoulders of Qt, HarfBuzz, Matplotlib, NumPy, and PySide6.