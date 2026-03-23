# bangla_render/__init__.py

"""
bangla_render: Bengali text rendering for Matplotlib.

Typical usage:

    import bangla_render as br
    import matplotlib.pyplot as plt

    br.init_renderer()

    fig, ax = plt.subplots()
    ax.plot([1, 2, 3], [3, 1, 4])

    br.set_bangla_title(ax, "বাংলা শিরোনাম")
    br.set_bangla_xlabel(ax, "এক্স অক্ষ")
    br.set_bangla_ylabel(ax, "ওয়াই অক্ষ")
    br.set_bangla_suptitle(fig, "চিত্রের শিরোনাম")

    br.set_bangla_xticks(ax, [1, 2, 3], ["এক", "দুই", "তিন"])
    br.text(ax, 0.5, 0.5, "মাঝখানে লেখা", coord="axes")

    br.apply_bangla_layout(fig, auto=True)
"""

__version__ = "0.2.0"

# ---------------------------------------------------------------------
# Backend / environment
# ---------------------------------------------------------------------

from .backend import (
    init_renderer,
    ensure_qt_application,
    get_renderer_status,
    check_environment,
    is_headless_environment,
    is_notebook_environment,
    is_colab_environment,
    is_kaggle_environment,
    reset_renderer_state,
)

# ---------------------------------------------------------------------
# Font management
# ---------------------------------------------------------------------

from .fonts import (
    register_font,
    register_fonts,
    list_available_fonts,
    list_registered_fonts,
    list_bangla_candidate_fonts,
    set_default_font,
    get_default_font,
    resolve_font,
    validate_font,
    find_best_bangla_font,
    ensure_default_font,
    font_info,
)

# ---------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------

from .renderer import (
    render_text,
    render_paragraph,
    render_text_qimage,
    render_paragraph_qimage,
    measure_text,
    clear_render_cache,
    get_render_cache_info,
    set_render_cache_maxsize,
    set_render_defaults,
    get_render_defaults,
)

# ---------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------

from .layout import (
    get_layout_manager,
    clear_layout_manager,
)

# ---------------------------------------------------------------------
# Matplotlib-facing APIs
# ---------------------------------------------------------------------

from .mpl_support import (
    to_bangla_numerals,
    set_bangla_legend,
    set_bangla_numeric_ticks,
    set_bangla_title,
    set_bangla_xlabel,
    set_bangla_ylabel,
    set_bangla_suptitle,
    set_bangla_xticks,
    set_bangla_yticks,
    add_bangla_in_cell,
    bangla_text,
    annotate_bangla,
    bangla_paragraph,
    apply_bangla_layout,
)


def text(ax, *args, **kwargs):
    """
    Short alias for bangla_text(), so you can write:

        import bangla_render as br
        br.text(ax, 0.5, 0.5, "বাংলা", coord="axes")
    """
    return bangla_text(ax, *args, **kwargs)


__all__ = [
    "__version__",
    # backend
    "init_renderer",
    "ensure_qt_application",
    "get_renderer_status",
    "check_environment",
    "is_headless_environment",
    "is_notebook_environment",
    "is_colab_environment",
    "is_kaggle_environment",
    "reset_renderer_state",
    # fonts
    "register_font",
    "register_fonts",
    "list_available_fonts",
    "list_registered_fonts",
    "list_bangla_candidate_fonts",
    "set_default_font",
    "get_default_font",
    "resolve_font",
    "validate_font",
    "find_best_bangla_font",
    "ensure_default_font",
    "font_info",
    # renderer
    "render_text",
    "render_paragraph",
    "render_text_qimage",
    "render_paragraph_qimage",
    "measure_text",
    "clear_render_cache",
    "get_render_cache_info",
    "set_render_cache_maxsize",
    "set_render_defaults",
    "get_render_defaults",
    # layout
    "get_layout_manager",
    "clear_layout_manager",
    # mpl support
    "to_bangla_numerals",
    "set_bangla_numeric_ticks",
    "set_bangla_legend",
    "set_bangla_title",
    "set_bangla_xlabel",
    "set_bangla_ylabel",
    "set_bangla_suptitle",
    "set_bangla_xticks",
    "set_bangla_yticks",
    "add_bangla_in_cell",
    "bangla_text",
    "annotate_bangla",
    "bangla_paragraph",
    "apply_bangla_layout",
    "text",
]