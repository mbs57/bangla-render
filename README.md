

# 🇧🇩 bangla-render

### Bengali Text Rendering for Matplotlib & Seaborn (with full OpenType shaping)

**bangla-render** is the first open-source Python library that enables fully correct **Bengali text rendering** inside Matplotlib and Seaborn.

Matplotlib cannot shape Bengali text — it does not use HarfBuzz and cannot handle:

* Matra (ি, ী, ু, ূ, ৃ)
* Reph (র্)
* Juktakkhor (জ্ঞ, ক্ষ, ত্ম, ন্দ …)
* OpenType GSUB/GPOS shaping

So Bengali titles, axis labels, and heatmap text appear **broken**.

💡 **bangla-render fixes this entirely** by using **Qt’s HarfBuzz-based text engine**, converting shaped text into RGBA images, and inserting them into Matplotlib.

---

## ✨ Features

### ✔ Full and correct Bengali shaping

* Complex conjuncts: ক্ষ, দ্ধ, ন্দ, জ্ঞ, ত্ম …
* Correct matra placement
* Reph, rafar, vowel signs
* Multi-line paragraphs
* UTF-8 / Unicode native (no ANSI/Bijoy hacks)

### ✔ Easy API for Matplotlib

```
br.set_bangla_title(ax, "বাংলা শিরোনাম")
br.set_bangla_xlabel(ax, "এক্স অক্ষ")
br.set_bangla_ylabel(ax, "ওয়াই অক্ষ")
br.text(ax, 0.5, 0.5, "মাঝখানে", coord="axes")
```

### ✔ Heatmap & confusion matrix support

```
br.add_bangla_in_cell(ax, row, col, "খুশি", rows, cols)
```

### ✔ Automatic layout handling

`apply_bangla_layout()` adjusts margins so nothing overlaps.

### ✔ Works everywhere

* Matplotlib
* Seaborn
* Windows / Linux / Mac
* Jupyter Notebook / VS Code
* Any backend (Agg, Tk, Qt, etc.)

---

## 🔥 Why This Library Exists

Matplotlib cannot shape Indic scripts.
Even with proper fonts, Bengali text becomes:

* Disjoint
* Out of order
* Matra misplaced
* Conjuncts broken
* Unreadable

Existing online solutions only support *very simple* words (e.g. ভয়, রাগ).
They **fail** for real Bengali:

* খুশি
* শ্রদ্ধা
* দৃষ্টিভঙ্গি
* ব্যবস্থাপনা
* হাস্যোজ্জ্বল
* পর্যালোচনায়
* Any paragraph

Before **bangla-render**:

* ❌ No PyPI library
* ❌ No working shape engine
* ❌ No support for heatmaps / confusion matrices
* ❌ No API for Bengali title/xlabel/ylabel
* ❌ No Unicode-complete solution

People used hacks like:

* PNG text pasted manually
* Bijoy/ANSI legacy encoding
* Broken rendering
* Inconsistent positioning

**bangla-render fills this gap completely.**

---

## 🎯 Our Contribution

### 1️⃣ Full Bengali shaping in Matplotlib for the first time

Built using:

* Qt → HarfBuzz shaping
* QPainter → QImage
* NumPy RGBA conversion
* AnnotationBbox → Matplotlib overlay

### 2️⃣ High-level Bengali plotting API

A drop-in replacement for Matplotlib text functions:

* Bangla title
* Bangla xlabel
* Bangla ylabel
* Bangla annotation (`br.text`)
* Heatmap cell text
* Confusion matrix axis text

### 3️⃣ Automatic layout engine

`apply_bangla_layout()` prevents overlap and centers everything.

### 4️⃣ Works with Seaborn

Position-perfect Bengali text inside heatmap cells.

### 5️⃣ Full test suite

Tests:

* Basic Bengali words
* Complex juktakkhor
* Paragraphs
* Line plot
* Heatmap
* Confusion matrix
* Before/after comparisons

### 6️⃣ Unicode-compliant & beginner friendly

Just install and use.

---

## 🔍 Before / After Comparison

### Line Plot

| Before (Broken)                        | After (Correct)                      |
| -------------------------------------- | ------------------------------------ |
| ![before](assets/line_plot_before.png) | ![after](assets/line_plot_after.png) |

### Heatmap

| Before                               | After                              |
| ------------------------------------ | ---------------------------------- |
| ![before](assets/heatmap_before.png) | ![after](assets/heatmap_after.png) |

### Confusion Matrix

| Before                                        | After                                       |
| --------------------------------------------- | ------------------------------------------- |
| ![before](assets/confusion_matrix_before.png) | ![after](assets/confusion_matrix_after.png) |

---

## 📦 Installation

(Currently local — will publish to PyPI soon)

```
pip install PySide6
git clone https://github.com/mbs57/bangla-render.git
cd bangla-render
pip install -e .
```

---

## 🧪 Usage Example — Line Plot

```
import matplotlib.pyplot as plt
import bangla_render as br

fig, ax = plt.subplots(figsize=(5,4))
br.apply_bangla_layout(fig)

ax.plot([1,2,3], [3,1,4])

br.set_bangla_title(ax, "বাংলা লাইন প্লট")
br.set_bangla_xlabel(ax, "এক্স অক্ষ")
br.set_bangla_ylabel(ax, "ওয়াই অক্ষ")

plt.show()
```

---

## 🎨 Usage Example — Heatmap

```
import seaborn as sns
import numpy as np
import matplotlib.pyplot as plt
import bangla_render as br

data = np.random.rand(3,3)
words = [
    ["খুশি","রাগ","আশা"],
    ["ভয়","বিস্ময়","শান্তি"],
    ["ঘৃণা","আনন্দ","সুখ"]
]

fig, ax = plt.subplots(figsize=(6,6))
br.apply_bangla_layout(fig)

sns.heatmap(data, ax=ax, cbar=True, xticklabels=False, yticklabels=False)

rows, cols = data.shape
for i in range(rows):
    for j in range(cols):
        br.add_bangla_in_cell(ax, i, j, words[i][j], rows, cols)

br.set_bangla_title(ax, "বাংলা হিটম্যাপ")
br.set_bangla_xlabel(ax, "প্রেডিক্টেড ক্লাস")
br.set_bangla_ylabel(ax, "সত্যিকারের ক্লাস")

plt.show()
```

---

## 🧩 API Overview

### Titles & Labels

* `set_bangla_title(ax, text, font_size=...)`
* `set_bangla_xlabel(ax, text, font_size=...)`
* `set_bangla_ylabel(ax, text, font_size=...)`

### Text

* `bangla_text(ax, x, y, text, coord="axes", ...)`
  Drop-in replacement for `ax.text()` but properly shaped.

### Heatmap Cells

* `add_bangla_in_cell(ax, row, col, text, rows, cols)`

### Layout

* `apply_bangla_layout(fig, left=..., right=..., top=..., bottom=...)`

---

## 🏗 How It Works

* Qt text engine (PySide6) → uses **HarfBuzz**
* Shapes Bengali fully
* Render to QImage
* Convert to NumPy
* Insert into Matplotlib with AnnotationBbox
* Layout handled by figure metrics

A complete bypass of Matplotlib’s broken text pipeline.

---

## 🧪 Test Suite

The `tests/` folder includes:

* Simple words
* Complex words
* Paragraph rendering
* Line plot
* Heatmap
* Confusion matrix
* Before/after images

---

## 📚 Roadmap

* Publish to PyPI
* Expand to Hindi/Tamil/Telugu/etc
* Mixed Bengali + MathText
* Deeper Matplotlib backend integration (Level B)
* Submit to JOSS (Journal of Open Source Software)

---

## 📄 License

MIT License.

---

## ⭐ Acknowledgement

This project enables clear, professional scientific visualization for **millions of Bengali speakers** — students, teachers, researchers, and engineers.


