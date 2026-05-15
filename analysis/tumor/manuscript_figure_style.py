"""
Shared matplotlib defaults for manuscript figures:
Times New Roman, slightly larger type, bold titles/labels/ticks.

Call apply_manuscript_figure_style() once before creating a figure.
Does not change data, layout logic, or output filenames.
"""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg", force=True)

# Display-only shorthand for long stage string on figure axes/legends (data keys stay full name).
STAGE_BORDERLINE_LONG = "Borderline Resectable/Locally Advanced"
STAGE_BORDERLINE_SHORT = "Bor.Res./Loc.Adv."


def short_stage_label(stage: str) -> str:
    s = str(stage).strip()
    if s == STAGE_BORDERLINE_LONG:
        return STAGE_BORDERLINE_SHORT
    return s


def shorten_stage_labels_on_axes(ax) -> None:
    """Shorten Borderline… stage name on tick labels and legend entries for one matplotlib Axes."""
    try:
        for t in ax.get_xticklabels():
            t.set_text(short_stage_label(t.get_text()))
        for t in ax.get_yticklabels():
            t.set_text(short_stage_label(t.get_text()))
        leg = ax.get_legend()
        if leg is not None:
            for t in leg.get_texts():
                t.set_text(short_stage_label(t.get_text()))
    except Exception:
        pass


def apply_manuscript_figure_style() -> None:
    import matplotlib.pyplot as plt

    plt.style.use("default")
    plt.rcParams.update(
        {
            "font.family": "Times New Roman",
            "font.serif": ["Times New Roman", "Times", "DejaVu Serif"],
            "mathtext.fontset": "dejavuserif",
            "font.size": 15,
            "font.weight": "bold",
            "axes.titleweight": "bold",
            "axes.labelweight": "bold",
            "axes.titlesize": 21,
            "axes.labelsize": 17,
            "xtick.labelsize": 14,
            "ytick.labelsize": 14,
            "legend.fontsize": 13,
            "figure.titlesize": 21,
        }
    )
