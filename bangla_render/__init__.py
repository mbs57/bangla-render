# bangla_render/__init__.py

"""
bangla_render: Bengali text rendering for Matplotlib.

Typical usage:

    import bangla_render as br

    fig, ax = plt.subplots()
    br.apply_bangla_layout(fig)
    ax.plot(...)

    br.set_bangla_title(ax, "বাংলা শিরোনাম")
    br.set_bangla_xlabel(ax, "এক্স অক্ষ")
    br.set_bangla_ylabel(ax, "ওয়াই অক্ষ")

    br.text(ax, 0.5, 0.5, "মাঝখানে লেখা", coord="axes")
"""

from .renderer import render_text, render_paragraph
from .mpl_support import (
    set_bangla_title,
    set_bangla_xlabel,
    set_bangla_ylabel,
    add_bangla_in_cell,
    bangla_text,
    apply_bangla_layout,
)


def text(ax, *args, **kwargs):
    """
    Short alias for bangla_text(), so you can write:

        import bangla_render as br
        br.text(ax, 0.5, 0.5, "বাংলা", coord="axes")
    """
    return bangla_text(ax, *args, **kwargs)
