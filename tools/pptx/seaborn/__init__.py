"""Shared chart helpers, executive chart renderer, and the EDA chart dispatcher.

The EDA chart functions live in sub-modules:
  statistical  — hist, kde, ecdf, ridge, boxen, scatter, bubble, line, lmplot*, logistic, resid, joint*
  categorical  — bar, pie, count, point, box, violin, strip, swarm
  multivariate — heatmap, clustermap, pair, pair_kde, timeseries, timeseries_facet
"""

import inspect
import warnings
from typing import IO, List, Optional, Union

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from cycler import cycler

warnings.filterwarnings("ignore")

DEFAULT_PALETTE = "tab10"
DEFAULT_FIGSIZE = (10, 6)
DEFAULT_STYLE = "ticks"
DEFAULT_CONTEXT = "notebook"

_SEQUENTIAL_RAMPS = {
    "Blues", "Oranges", "Greys", "Greens", "Purples", "Reds", "YlOrBr",
    "Blues_r", "Oranges_r", "Greys_r", "Greens_r", "Purples_r", "Reds_r", "YlOrBr_r",
}

_VL_COLOR = "#222222"
_WATERFALL_DOWN = "#C0504D"


def _themed_colors(palette: str, n: int, lo: float = 0.34, hi: float = 0.86):
    """Return n colors for n categories. Samples the inner sub-range for single-hue ramps."""
    if n is None or n <= 0:
        return sns.color_palette(palette)
    if palette not in _SEQUENTIAL_RAMPS:
        return sns.color_palette(palette, n)
    import numpy as _np
    ramp = sns.color_palette(palette, n_colors=256)
    m = len(ramp) - 1
    if n == 1:
        return [ramp[int(round(((lo + hi) / 2) * m))]]
    return [ramp[int(round(p * m))] for p in _np.linspace(lo, hi, n)]


def _setup(style: str = DEFAULT_STYLE, context: str = DEFAULT_CONTEXT) -> None:
    sns.set_theme(
        style=style,
        context=context,
        font_scale=1.05,
        rc={
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "savefig.facecolor": "white",
            "savefig.edgecolor": "white",
            "axes.edgecolor": "#444444",
            "axes.linewidth": 1.0,
            "axes.grid": True,
            "grid.color": "#E9ECEF",
            "grid.linestyle": "-",
            "grid.linewidth": 0.8,
            "grid.alpha": 0.9,
            "xtick.color": "#333333",
            "ytick.color": "#333333",
            "xtick.direction": "out",
            "ytick.direction": "out",
            "legend.frameon": False,
            "font.family": "sans-serif",
            "font.sans-serif": ["Arial", "Calibri", "DejaVu Sans", "Liberation Sans", "sans-serif"],
            "lines.linewidth": 2.0,
            "axes.titlepad": 10,
            "axes.titleweight": "bold",
            "axes.labelsize": 12,
            "axes.titlesize": 14,
            "xtick.labelsize": 11,
            "ytick.labelsize": 11,
            "legend.fontsize": 11,
            "axes.labelcolor": "#222222",
            "text.color": "#222222",
            "axes.prop_cycle": cycler("color", sns.color_palette("tab10")),
        },
    )
    mpl.rcParams["figure.dpi"] = 120


def _finalize(fig, ax, title: str, xlabel: str, ylabel: str,
              save_path: Optional[Union[str, IO[bytes]]]) -> None:
    if ax is not None:
        if title:
            ax.set_title(title)
        if xlabel:
            ax.set_xlabel(xlabel)
        if ylabel:
            ax.set_ylabel(ylabel)
        ax.set_axisbelow(True)
        ax.set_facecolor("white")
        ax.grid(True, axis="y", color="#E9ECEF", linewidth=0.8)
        ax.grid(False, axis="x")
        ax.tick_params(axis="both", which="major", length=4, color="#444444")
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["bottom"].set_color("#CCCCCC")
        ax.spines["left"].set_color("#CCCCCC")
    fig.tight_layout()
    if save_path:
        fig.savefig(save_path, bbox_inches="tight", pad_inches=0.2)
        if isinstance(save_path, str):
            print(f"✓ Guardado: {save_path}")
    else:
        plt.show()


def _compact_number(x: float) -> str:
    """1,250,000 -> '1.25M', 12,500 -> '12.5K' (board-friendly compact form)."""
    ax = abs(x)
    for div, suf in ((1e9, "B"), (1e6, "M"), (1e3, "K")):
        if ax >= div:
            s = f"{x / div:.2f}".rstrip("0").rstrip(".")
            return f"{s}{suf}"
    return f"{x:,.0f}"


def _fmt_number(v, value_format: Optional[str] = None) -> str:
    """Format a value for a data label or tick."""
    try:
        x = float(v)
    except (TypeError, ValueError):
        return str(v)
    fmt = value_format or "auto"
    if fmt == "percent":
        return f"{x:.0f}%" if abs(x) >= 10 else f"{x:.1f}%"
    if fmt == "currency":
        return f"${x:,.0f}"
    if fmt == "int":
        return f"{int(round(x)):,}"
    if fmt == "float1":
        return f"{x:,.1f}"
    if fmt == "thousands":
        return _compact_number(x)
    ax = abs(x)
    if ax != 0 and ax < 1:
        return f"{x:.2f}"
    if ax >= 10000:
        return _compact_number(x)
    if float(x).is_integer():
        return f"{int(x):,}"
    return f"{x:,.1f}"


def _auto_rotate_xticks(ax, labels) -> None:
    """Rotate X labels when long or numerous to prevent overlap."""
    labels = [str(l) for l in (labels or [])]
    if not labels:
        return
    longest = max(len(l) for l in labels)
    if longest > 6 or len(labels) > 5:
        for t in ax.get_xticklabels():
            t.set_rotation(45)
            t.set_ha("right")
            t.set_rotation_mode("anchor")


def _annotate_value(ax, xpos, top, value, value_format) -> None:
    """Place one readable value label just past the bar end."""
    above = top >= 0
    ax.annotate(
        _fmt_number(value, value_format),
        xy=(xpos, top),
        xytext=(0, 3 if above else -3),
        textcoords="offset points",
        ha="center", va="bottom" if above else "top",
        fontsize=9, color=_VL_COLOR, fontweight="bold", clip_on=False,
    )


def _bar_value_labels(ax, rects, values, value_format, max_labels: int = 12) -> None:
    """Annotate bar tops, only when the count is legible."""
    rects = list(rects)
    if len(rects) > max_labels:
        return
    for rect, v in zip(rects, values):
        if v is None:
            continue
        ax.annotate(
            _fmt_number(v, value_format),
            xy=(rect.get_x() + rect.get_width() / 2, rect.get_height()),
            xytext=(0, 3 if rect.get_height() >= 0 else -3),
            textcoords="offset points",
            ha="center", va="bottom" if rect.get_height() >= 0 else "top",
            fontsize=9, color=_VL_COLOR, fontweight="bold", clip_on=False,
        )


def _exec_finalize(fig, ax, title, xlabel, ylabel, save_path,
                   legend_handles=None, legend_labels=None) -> None:
    """Shared styling/finish for axes-based executive charts."""
    if title:
        ax.set_title(title)
    if xlabel:
        ax.set_xlabel(xlabel)
    if ylabel:
        ax.set_ylabel(ylabel)
    ax.set_axisbelow(True)
    ax.grid(True, axis="y", color="#E9ECEF", linewidth=0.8)
    ax.grid(False, axis="x")
    ax.tick_params(axis="both", which="major", length=4, color="#444444")
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    ax.spines["bottom"].set_color("#CCCCCC")
    ax.spines["left"].set_color("#CCCCCC")
    if legend_labels:
        leg_kw = dict(loc="upper left", bbox_to_anchor=(1.01, 1.0),
                      fontsize=8, frameon=False)
        if legend_handles is not None:
            ax.legend(legend_handles, legend_labels, **leg_kw)
        else:
            ax.legend(**leg_kw)
    fig.tight_layout()
    if save_path is not None:
        fig.savefig(save_path, bbox_inches="tight", pad_inches=0.2)
    else:
        plt.show()


def _filter_kwargs(func, kwargs: dict) -> dict:
    try:
        sig = inspect.signature(func)
    except (TypeError, ValueError):
        return kwargs
    if any(p.kind == inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values()):
        return kwargs
    return {k: v for k, v in kwargs.items() if k in sig.parameters}


def slide_chart(
    chart_type: str,
    *,
    palette: str = DEFAULT_PALETTE,
    title: str = "",
    labels: Optional[List[str]] = None,
    x: Optional[List[float]] = None,
    series: Optional[List[dict]] = None,
    sizes: Optional[List[float]] = None,
    x_label: str = "",
    y_label: str = "",
    y2_label: str = "",
    value_labels: Optional[bool] = None,
    legend: Optional[bool] = None,
    value_format: Optional[str] = None,
    figsize: tuple = DEFAULT_FIGSIZE,
    save_path: Optional[Union[str, IO[bytes]]] = None,
):
    """Render one executive/presentation chart."""
    _setup()
    series = [s for s in (series or []) if s is not None]
    if not series:
        series = [{"name": "", "values": []}]
    n = len(series)
    s_colors = _themed_colors(palette, max(n, 1))
    multi = n > 1
    names = [str(s.get("name") or "") for s in series]
    show_legend = (legend if legend is not None else multi) and any(names)
    idx = np.arange(len(labels)) if labels else np.arange(
        len(series[0]["values"]) if series[0]["values"] else 0)

    if chart_type in ("pie", "doughnut"):
        vals = series[0]["values"]
        cat_labels = [str(l) for l in (labels or range(len(vals)))]
        cat_colors = _themed_colors(palette, len(vals))
        fig, ax = plt.subplots(figsize=(8, 8))

        def _autopct(pct):
            return _fmt_number(pct, "percent") if pct >= 5 else ""

        wedgeprops = dict(width=0.42) if chart_type == "doughnut" else None
        wedges, _texts, _autotexts = ax.pie(
            vals, autopct=_autopct, pctdistance=0.75, colors=cat_colors,
            startangle=90, wedgeprops=wedgeprops,
            textprops=dict(color=_VL_COLOR, fontsize=10, fontweight="bold"),
        )
        ax.axis("equal")
        if (legend if legend is not None else True):
            ax.legend(wedges, cat_labels, loc="center left",
                      bbox_to_anchor=(1.0, 0.5), fontsize=9, frameon=False)
        if title:
            ax.set_title(title, pad=18)
        fig.tight_layout()
        if save_path is not None:
            fig.savefig(save_path, bbox_inches="tight", pad_inches=0.2)
        else:
            plt.show()
        return fig, ax

    if chart_type in ("scatter", "bubble"):
        xv = x if x is not None else list(idx)
        yv = series[0]["values"]
        fig, ax = plt.subplots(figsize=figsize)
        if chart_type == "bubble" and sizes:
            smin, smax = min(sizes), max(sizes)
            rng = (smax - smin) or 1
            ss = [60 + 540 * ((s - smin) / rng) for s in sizes]
        else:
            ss = 60
        ax.scatter(xv, yv, s=ss, c=[s_colors[0]], alpha=0.7, edgecolors="white", linewidths=0.5)
        _exec_finalize(fig, ax, title, x_label, y_label, save_path)
        return fig, ax

    if chart_type == "combo":
        fig, ax = plt.subplots(figsize=figsize)
        ax2 = None
        nb = max(sum(1 for s in series if (s.get("kind") or "bar") == "bar"), 1)
        bw = 0.8 / nb
        bi = 0
        for i, s in enumerate(series):
            kind = s.get("kind") or ("bar" if i == 0 else "line")
            axis = s.get("axis") or "primary"
            target = ax
            if axis == "secondary":
                ax2 = ax2 or ax.twinx()
                target = ax2
            if kind == "bar":
                offset = (bi - (nb - 1) / 2) * bw
                target.bar(idx + offset, s["values"], width=bw,
                           color=s_colors[i], label=names[i])
                bi += 1
            else:
                target.plot(idx, s["values"], marker="o", linewidth=2.4,
                            color=s_colors[i], label=names[i])
        ax.set_xticks(idx)
        if labels:
            ax.set_xticklabels([str(l) for l in labels])
            _auto_rotate_xticks(ax, labels)
        if x_label:
            ax.set_xlabel(x_label)
        if y_label:
            ax.set_ylabel(y_label)
        if ax2 is not None and y2_label:
            ax2.set_ylabel(y2_label)
        ax.set_axisbelow(True)
        ax.grid(True, axis="y", color="#E9ECEF", linewidth=0.8)
        ax.grid(False, axis="x")
        for spine in ("top",):
            ax.spines[spine].set_visible(False)
        if ax2 is None:
            ax.spines["right"].set_visible(False)
        if title:
            ax.set_title(title)
        h1, l1 = ax.get_legend_handles_labels()
        h2, l2 = (ax2.get_legend_handles_labels() if ax2 is not None else ([], []))
        all_h, all_l = h1 + h2, l1 + l2
        if (legend if legend is not None else True) and any(all_l):
            ax.legend(all_h, all_l, loc="upper left", bbox_to_anchor=(1.10, 1.0),
                      fontsize=8, frameon=False)
        fig.tight_layout()
        if save_path is not None:
            fig.savefig(save_path, bbox_inches="tight", pad_inches=0.2)
        else:
            plt.show()
        return fig, ax

    if chart_type in ("line", "area", "stacked_area"):
        fig, ax = plt.subplots(figsize=figsize)
        xv = x if x is not None else idx
        if chart_type == "stacked_area":
            ax.stackplot(xv, *[s["values"] for s in series],
                         labels=names, colors=s_colors[:n], alpha=0.85)
        else:
            for i, s in enumerate(series):
                ax.plot(xv, s["values"], marker="o", linewidth=2.4,
                        color=s_colors[i], label=names[i])
                if chart_type == "area":
                    ax.fill_between(xv, s["values"], alpha=0.22, color=s_colors[i])
        if labels and x is None:
            ax.set_xticks(idx)
            ax.set_xticklabels([str(l) for l in labels])
            _auto_rotate_xticks(ax, labels)
        _exec_finalize(fig, ax, title, x_label, y_label, save_path,
                       legend_labels=names if show_legend else None)
        return fig, ax

    if chart_type == "hist":
        fig, ax = plt.subplots(figsize=figsize)
        line_color = _themed_colors(palette, 5)[-1]
        sns.histplot(series[0]["values"], bins="auto", color=s_colors[0],
                     edgecolor="white", alpha=0.85, kde=True,
                     line_kws=dict(linewidth=2.4), ax=ax)
        if ax.lines:
            ax.lines[-1].set_color(line_color)
        _exec_finalize(fig, ax, title, x_label, y_label or "Frecuencia", save_path)
        return fig, ax

    if chart_type == "waterfall":
        fig, ax = plt.subplots(figsize=figsize)
        vals = [float(v) for v in series[0]["values"]]
        running = 0.0
        want_vl = value_labels if value_labels is not None else (len(vals) <= 12)
        for i, v in enumerate(vals):
            color = s_colors[0] if v >= 0 else _WATERFALL_DOWN
            ax.bar(idx[i], v, bottom=running, width=0.62, color=color)
            top = running + v
            if want_vl:
                _annotate_value(ax, idx[i], top if v >= 0 else running, v, value_format)
            running = top
        if labels:
            ax.set_xticks(idx)
            ax.set_xticklabels([str(l) for l in labels])
            _auto_rotate_xticks(ax, labels)
        ax.axhline(0, color="#CCCCCC", linewidth=1.0)
        _exec_finalize(fig, ax, title, x_label, y_label, save_path)
        return fig, ax

    # bar family: bar (grouped) / stacked_bar / stacked_bar_100
    fig, ax = plt.subplots(figsize=figsize)
    if chart_type == "bar" and n == 1 and labels and len(labels) == len(series[0]["values"]):
        order = sorted(range(len(series[0]["values"])),
                       key=lambda i: series[0]["values"][i], reverse=True)
        labels = [labels[i] for i in order]
        series = [{**series[0], "values": [series[0]["values"][i] for i in order]}]

    bar_like = chart_type in ("bar", "stacked_bar", "waterfall")
    total_bars = len(idx) * (n if chart_type == "bar" else 1)
    want_vl = value_labels if value_labels is not None else (bar_like and total_bars <= 12)

    if chart_type in ("stacked_bar", "stacked_bar_100"):
        mat = np.array([[float(v) for v in s["values"]] for s in series], dtype=float)
        if chart_type == "stacked_bar_100":
            totals = mat.sum(axis=0)
            totals[totals == 0] = 1.0
            mat = mat / totals * 100.0
        bottom = np.zeros(mat.shape[1])
        for i in range(mat.shape[0]):
            ax.bar(idx, mat[i], bottom=bottom, width=0.62,
                   color=s_colors[i], label=names[i])
            if want_vl and chart_type == "stacked_bar" and total_bars * n <= 12:
                for j in range(mat.shape[1]):
                    _annotate_value(ax, idx[j], bottom[j] + mat[i][j] / 2, mat[i][j], value_format)
            bottom += mat[i]
    elif n == 1:
        cat_colors = _themed_colors(palette, len(idx))
        rects = ax.bar(idx, series[0]["values"], width=0.62, color=cat_colors)
        if want_vl:
            _bar_value_labels(ax, rects, series[0]["values"], value_format)
    else:
        bw = 0.8 / n
        for i, s in enumerate(series):
            offset = (i - (n - 1) / 2) * bw
            rects = ax.bar(idx + offset, s["values"], width=bw,
                           color=s_colors[i], label=names[i])
            if want_vl:
                _bar_value_labels(ax, rects, s["values"], value_format)

    ax.set_xticks(idx)
    if labels:
        ax.set_xticklabels([str(l) for l in labels])
        _auto_rotate_xticks(ax, labels)
    _exec_finalize(fig, ax, title, x_label, y_label, save_path,
                   legend_labels=names if show_legend else None)
    return fig, ax


# Lazy imports to avoid pulling heavy deps at package-import time
def _get_chart_types():
    from tools.pptx.seaborn.statistical import (
        hist, kde, ecdf, ridge, boxen,
        scatter, bubble, line, lmplot, lmplot_facet, logistic, resid,
        joint, joint_hex, joint_kde,
    )
    from tools.pptx.seaborn.categorical import bar, pie, count, point, box, violin, strip, swarm
    from tools.pptx.seaborn.multivariate import heatmap, clustermap, pair, pair_kde, timeseries, timeseries_facet
    return {
        "hist": hist, "kde": kde, "ecdf": ecdf, "ridge": ridge, "boxen": boxen,
        "scatter": scatter, "bubble": bubble, "line": line,
        "lmplot": lmplot, "lmplot_facet": lmplot_facet,
        "logistic": logistic, "resid": resid,
        "joint": joint, "joint_hex": joint_hex, "joint_kde": joint_kde,
        "bar": bar, "count": count, "point": point, "box": box,
        "violin": violin, "strip": strip, "swarm": swarm, "pie": pie,
        "heatmap": heatmap, "clustermap": clustermap,
        "pair": pair, "pair_kde": pair_kde,
        "timeseries": timeseries, "timeseries_facet": timeseries_facet,
    }


def chart(kind: str, df, **kwargs):
    """Universal dispatcher: chart(kind, df, **kwargs) routes to any EDA chart function."""
    CHART_TYPES = _get_chart_types()
    if kind not in CHART_TYPES:
        available = "  ".join(sorted(CHART_TYPES.keys()))
        raise ValueError(f"Tipo '{kind}' no reconocido.\nDisponibles: {available}")
    filtered_kwargs = _filter_kwargs(CHART_TYPES[kind], kwargs)
    return CHART_TYPES[kind](df, **filtered_kwargs)
