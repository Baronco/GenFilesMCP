"""Statistical and relational EDA chart functions."""

import warnings
from typing import List, Optional, Union

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from tools.pptx.seaborn import (
    DEFAULT_FIGSIZE,
    DEFAULT_PALETTE,
    _finalize,
    _setup,
)

warnings.filterwarnings("ignore")


def hist(
    df: pd.DataFrame,
    x: str,
    hue: Optional[str] = None,
    bins: Union[int, str] = "auto",
    kde: bool = True,
    stat: str = "count",
    multiple: str = "layer",
    palette: str = DEFAULT_PALETTE,
    title: str = "",
    xlabel: str = "",
    ylabel: str = "",
    figsize: tuple = DEFAULT_FIGSIZE,
    save_path: Optional[str] = None,
):
    """Histograma con KDE opcional. stat: 'count'|'frequency'|'density'|'probability'"""
    _setup()
    fig, ax = plt.subplots(figsize=figsize)
    sns.histplot(data=df, x=x, hue=hue, bins=bins, kde=kde,
                 stat=stat, multiple=multiple, palette=palette, ax=ax)
    _finalize(fig, ax, title or f"Histograma: {x}",
              xlabel or x, ylabel or stat.capitalize(), save_path)
    return fig, ax


def kde(
    df: pd.DataFrame,
    x: str,
    y: Optional[str] = None,
    hue: Optional[str] = None,
    bins: Union[int, str] = "auto",
    multiple: str = "layer",
    fill: bool = False,
    palette: str = DEFAULT_PALETTE,
    kernel: str = "gau",
    bw_adjust: float = 1.0,
    kernels: Optional[List[str]] = None,
    bw_adjusts: Optional[List[float]] = None,
    title: str = "",
    xlabel: str = "",
    ylabel: str = "Densidad",
    figsize: tuple = DEFAULT_FIGSIZE,
    save_path: Optional[str] = None,
):
    """Curva de densidad 1D o KDE bivariado si se pasa y."""
    _setup()
    fig, ax = plt.subplots(figsize=figsize)
    if kernels is not None:
        if bw_adjusts is None:
            bw_adjusts = [bw_adjust] * len(kernels)
        if len(bw_adjusts) != len(kernels):
            raise ValueError("bw_adjusts must have the same length as kernels")
        palette_colors = sns.color_palette(palette, n_colors=len(kernels))
        if y is None:
            sns.histplot(data=df, x=x, hue=hue, stat="density", bins=bins,
                         element="bars", fill=True, alpha=0.35,
                         color="#d0d0d0" if hue is None else None,
                         edgecolor="#999999" if hue is None else None,
                         palette=palette, ax=ax)
            for idx, kern in enumerate(kernels):
                sns.kdeplot(data=df, x=x, hue=hue, multiple=multiple, fill=False,
                            palette=[palette_colors[idx]], kernel=kern,
                            bw_adjust=bw_adjusts[idx], linewidth=2.2, cut=1, ax=ax,
                            label=f"{kern}")
        else:
            for idx, kern in enumerate(kernels):
                sns.kdeplot(data=df, x=x, y=y, hue=hue, multiple=multiple, fill=False,
                            palette=[palette_colors[idx]], kernel=kern,
                            bw_adjust=bw_adjusts[idx], linewidth=2.2, cut=1, ax=ax,
                            label=f"{kern}")
    else:
        if y is None:
            sns.histplot(data=df, x=x, hue=hue, stat="density", bins=bins,
                         element="bars", fill=True, alpha=0.35,
                         color="#d0d0d0" if hue is None else None,
                         edgecolor="#999999" if hue is None else None,
                         palette=palette, ax=ax)
            sns.kdeplot(data=df, x=x, hue=hue, multiple=multiple,
                        fill=fill, palette=palette, kernel=kernel,
                        bw_adjust=bw_adjust, linewidth=2.2, cut=1, ax=ax)
        else:
            sns.kdeplot(data=df, x=x, y=y, hue=hue, multiple=multiple,
                        fill=fill, palette=palette, kernel=kernel,
                        bw_adjust=bw_adjust, linewidth=2.2, cut=1, ax=ax)
    _finalize(fig, ax, title or f"KDE: {x}" + (f" vs {y}" if y else ""),
              xlabel or x, ylabel, save_path)
    return fig, ax


def ecdf(
    df: pd.DataFrame,
    x: str,
    hue: Optional[str] = None,
    stat: str = "proportion",
    palette: str = DEFAULT_PALETTE,
    title: str = "",
    xlabel: str = "",
    ylabel: str = "",
    figsize: tuple = DEFAULT_FIGSIZE,
    save_path: Optional[str] = None,
):
    """Distribución acumulada empírica (ECDF). stat: 'proportion'|'count'|'percent'"""
    _setup()
    fig, ax = plt.subplots(figsize=figsize)
    sns.ecdfplot(data=df, x=x, hue=hue, stat=stat, palette=palette, ax=ax)
    _finalize(fig, ax, title or f"ECDF: {x}",
              xlabel or x, ylabel or stat.capitalize(), save_path)
    return fig, ax


def ridge(
    df: pd.DataFrame,
    x: str,
    group: str,
    palette: str = "coolwarm",
    overlap: float = 0.5,
    title: str = "",
    xlabel: str = "",
    figsize: tuple = (10, 8),
    save_path: Optional[str] = None,
):
    """Ridge plot: distribuciones de x apiladas por group. overlap controla el solapamiento."""
    _setup()
    groups = df[group].unique()
    n = len(groups)
    palette_colors = sns.color_palette(palette, n)
    fig, axes = plt.subplots(n, 1, figsize=figsize, gridspec_kw={"hspace": -overlap})
    for i, (grp, ax) in enumerate(zip(groups, axes)):
        data_grp = df[df[group] == grp][x].dropna()
        sns.kdeplot(data_grp, fill=True, alpha=0.8, color=palette_colors[i], ax=ax)
        ax.set_xlim(df[x].min(), df[x].max())
        ax.set_yticks([])
        ax.set_ylabel(str(grp), rotation=0, ha="right", va="center", fontsize=9)
        ax.patch.set_alpha(0)
        if i < n - 1:
            ax.set_xlabel("")
            ax.set_xticks([])
        for spine in ["top", "right", "left"]:
            ax.spines[spine].set_visible(False)
    axes[-1].set_xlabel(xlabel or x)
    fig.suptitle(title or f"Ridge plot: {x} por {group}", y=1.01)
    fig.tight_layout()
    if save_path:
        fig.savefig(save_path, bbox_inches="tight", pad_inches=0.2)
        if isinstance(save_path, str):
            print(f"✓ Guardado: {save_path}")
    else:
        plt.show()
    return fig, axes


def boxen(
    df: pd.DataFrame,
    x: str,
    y: str,
    hue: Optional[str] = None,
    palette: str = DEFAULT_PALETTE,
    title: str = "",
    xlabel: str = "",
    ylabel: str = "",
    figsize: tuple = DEFAULT_FIGSIZE,
    save_path: Optional[str] = None,
):
    """Boxen plot (letter-value). Muestra más cuantiles que el boxplot. Ideal para n grande."""
    _setup()
    fig, ax = plt.subplots(figsize=figsize)
    sns.boxenplot(data=df, x=x, y=y, hue=hue, palette=palette, ax=ax)
    _finalize(fig, ax, title or f"Boxen: {y} por {x}",
              xlabel or x, ylabel or y, save_path)
    return fig, ax


def scatter(
    df: pd.DataFrame,
    x: str,
    y: str,
    hue: Optional[str] = None,
    size: Optional[str] = None,
    style: Optional[str] = None,
    palette: str = DEFAULT_PALETTE,
    alpha: float = 0.8,
    fit_reg: bool = False,
    title: str = "",
    xlabel: str = "",
    ylabel: str = "",
    figsize: tuple = DEFAULT_FIGSIZE,
    save_path: Optional[str] = None,
    **kwargs,
):
    """Dispersión. Hasta 5 dimensiones: x, y, hue, size, style."""
    _setup()
    fig, ax = plt.subplots(figsize=figsize)
    sns.scatterplot(data=df, x=x, y=y, hue=hue, size=size, style=style,
                    palette=palette, alpha=alpha, ax=ax, **kwargs)
    if fit_reg:
        try:
            sns.regplot(data=df, x=x, y=y, scatter=False, ax=ax, truncate=False, color="red")
        except Exception:
            pass
    _finalize(fig, ax, title or f"Dispersión: {y} vs {x}",
              xlabel or x, ylabel or y, save_path)
    return fig, ax


def bubble(
    df: pd.DataFrame,
    x: str,
    y: str,
    size: str,
    hue: Optional[str] = None,
    palette: str = DEFAULT_PALETTE,
    alpha: float = 0.7,
    sizes: tuple = (20, 400),
    title: str = "",
    xlabel: str = "",
    ylabel: str = "",
    figsize: tuple = DEFAULT_FIGSIZE,
    save_path: Optional[str] = None,
):
    """Bubble chart: scatter donde el tamaño de cada punto codifica una variable numérica."""
    _setup()
    fig, ax = plt.subplots(figsize=figsize)
    sns.scatterplot(data=df, x=x, y=y, size=size, hue=hue,
                    palette=palette, alpha=alpha, sizes=sizes, ax=ax)
    _finalize(fig, ax, title or f"Bubble: {y} vs {x} (tamaño={size})",
              xlabel or x, ylabel or y, save_path)
    return fig, ax


def line(
    df: pd.DataFrame,
    x: str,
    y: Union[str, List[str]],
    hue: Optional[str] = None,
    markers: bool = True,
    dashes: bool = True,
    ci: int = 95,
    palette: str = DEFAULT_PALETTE,
    title: str = "",
    xlabel: str = "",
    ylabel: str = "",
    figsize: tuple = DEFAULT_FIGSIZE,
    save_path: Optional[str] = None,
):
    """Líneas con banda de confianza. y puede ser str o lista de columnas."""
    _setup()
    fig, ax = plt.subplots(figsize=figsize)
    if isinstance(y, list):
        df_melt = df.melt(id_vars=[x], value_vars=y, var_name="_var", value_name="_val")
        sns.lineplot(data=df_melt, x=x, y="_val", hue="_var",
                     markers=markers, dashes=dashes, palette=palette, ax=ax)
        ax.set_ylabel(ylabel or "Valor")
    else:
        sns.lineplot(data=df, x=x, y=y, hue=hue, markers=markers, dashes=dashes,
                     errorbar=("ci", ci) if ci else None, palette=palette, ax=ax)
        ax.set_ylabel(ylabel or y)
    _finalize(fig, ax, title or f"Línea: {y} vs {x}", xlabel or x, "", save_path)
    return fig, ax


def lmplot(
    df: pd.DataFrame,
    x: str,
    y: str,
    hue: Optional[str] = None,
    ci: int = 95,
    order: int = 1,
    scatter: bool = True,
    palette: str = DEFAULT_PALETTE,
    line_kws: Optional[dict] = None,
    title: str = "",
    figsize: tuple = DEFAULT_FIGSIZE,
    save_path: Optional[str] = None,
):
    """Regresión lineal (o polinomial) con banda de confianza."""
    _setup()
    g = sns.lmplot(data=df, x=x, y=y, hue=hue, ci=ci, order=order,
                   scatter=scatter, palette=palette, line_kws=line_kws,
                   height=figsize[1], aspect=figsize[0] / figsize[1])
    if title:
        g.figure.suptitle(title, y=1.02)
    g.figure.tight_layout()
    if save_path:
        g.figure.savefig(save_path, bbox_inches="tight")
        if isinstance(save_path, str):
            print(f"✓ Guardado: {save_path}")
    else:
        plt.show()
    return g


def lmplot_facet(
    df: pd.DataFrame,
    x: str,
    y: str,
    col: str,
    hue: Optional[str] = None,
    col_wrap: int = 3,
    ci: int = 95,
    palette: str = DEFAULT_PALETTE,
    line_kws: Optional[dict] = None,
    title: str = "",
    save_path: Optional[str] = None,
):
    """Regresión lineal en facetas: una sub-gráfica por valor de col."""
    _setup()
    g = sns.lmplot(data=df, x=x, y=y, col=col, hue=hue,
                   col_wrap=col_wrap, ci=ci, palette=palette, line_kws=line_kws)
    if title:
        g.figure.suptitle(title, y=1.02)
    g.figure.tight_layout()
    if save_path:
        g.figure.savefig(save_path, bbox_inches="tight")
        if isinstance(save_path, str):
            print(f"✓ Guardado: {save_path}")
    else:
        plt.show()
    return g


def logistic(
    df: pd.DataFrame,
    x: str,
    y: str,
    hue: Optional[str] = None,
    ci: int = 95,
    palette: str = DEFAULT_PALETTE,
    title: str = "",
    xlabel: str = "",
    ylabel: str = "",
    figsize: tuple = DEFAULT_FIGSIZE,
    save_path: Optional[str] = None,
):
    """Regresión logística. y debe ser binaria (0/1). Muestra P(y=1) en función de x."""
    _setup()
    try:
        g = sns.lmplot(data=df, x=x, y=y, hue=hue, ci=ci,
                       logistic=True, palette=palette,
                       height=figsize[1], aspect=figsize[0] / figsize[1])
    except Exception as exc:
        if "statsmodels" in str(exc).lower() or "logistic=True" in str(exc):
            x_arr = np.asarray(df[x], dtype=float)
            y_arr = np.asarray(df[y], dtype=float)
            if set(np.unique(y_arr)) <= {0.0, 1.0}:
                def sigmoid(z):
                    """Logistic sigmoid function used for logistic-regression curve fitting."""
                    return 1 / (1 + np.exp(-z))
                X = np.vstack([np.ones_like(x_arr), x_arr]).T
                w = np.zeros(2)
                for _ in range(100):
                    p = sigmoid(X @ w)
                    W = np.diag(p * (1 - p))
                    grad = X.T @ (p - y_arr)
                    H = X.T @ W @ X
                    try:
                        delta = np.linalg.solve(H, grad)
                    except np.linalg.LinAlgError:
                        break
                    w -= delta
                fig, ax = plt.subplots(figsize=figsize)
                ax.scatter(x_arr, y_arr, alpha=0.6)
                xs = np.linspace(x_arr.min(), x_arr.max(), 200)
                ax.plot(xs, sigmoid(np.column_stack([np.ones_like(xs), xs]) @ w), color="red", linewidth=2)
                _finalize(fig, ax, title or f"Regresión logística: {y} ~ {x}",
                          xlabel or x, ylabel or y, save_path)
                return fig, ax
        raise
    if title:
        g.figure.suptitle(title or f"Regresión logística: {y} ~ {x}", y=1.02)
    g.figure.tight_layout()
    if save_path:
        g.figure.savefig(save_path, bbox_inches="tight")
        if isinstance(save_path, str):
            print(f"✓ Guardado: {save_path}")
    else:
        plt.show()
    return g


def resid(
    df: pd.DataFrame,
    x: str,
    y: str,
    lowess: bool = False,
    title: str = "",
    figsize: tuple = DEFAULT_FIGSIZE,
    save_path: Optional[str] = None,
):
    """Gráfico de residuos de la regresión lineal y~x."""
    _setup()
    fig, ax = plt.subplots(figsize=figsize)
    sns.residplot(data=df, x=x, y=y, lowess=lowess, ax=ax, scatter_kws={"alpha": 0.6})
    _finalize(fig, ax, title or f"Residuos: {y} ~ {x}",
              xlabel=x, ylabel="Residuo", save_path=save_path)
    return fig, ax


def joint(
    df: pd.DataFrame,
    x: str,
    y: str,
    kind: str = "scatter",
    hue: Optional[str] = None,
    palette: str = DEFAULT_PALETTE,
    title: str = "",
    figsize: tuple = (8, 8),
    save_path: Optional[str] = None,
):
    """Joint plot: gráfico central + distribuciones marginales."""
    _setup()
    g = sns.jointplot(data=df, x=x, y=y, kind=kind, hue=hue,
                      palette=palette, height=figsize[0])
    if title:
        g.figure.suptitle(title, y=1.02)
    g.figure.tight_layout()
    if save_path:
        g.figure.savefig(save_path, bbox_inches="tight")
        if isinstance(save_path, str):
            print(f"✓ Guardado: {save_path}")
    else:
        plt.show()
    return g


def joint_hex(
    df: pd.DataFrame,
    x: str,
    y: str,
    palette: str = "Blues",
    title: str = "",
    figsize: tuple = (8, 8),
    save_path: Optional[str] = None,
):
    """Joint plot con hexbin. Ideal para datasets grandes con solapamiento de puntos."""
    return joint(df, x, y, kind="hex", palette=palette,
                 title=title or f"Hexbin: {y} vs {x}",
                 figsize=figsize, save_path=save_path)


def joint_kde(
    df: pd.DataFrame,
    x: str,
    y: str,
    hue: Optional[str] = None,
    palette: str = DEFAULT_PALETTE,
    title: str = "",
    figsize: tuple = (8, 8),
    save_path: Optional[str] = None,
):
    """Joint plot con KDE bivariado central y KDE en márgenes."""
    return joint(df, x, y, kind="kde", hue=hue, palette=palette,
                 title=title or f"KDE conjunto: {y} vs {x}",
                 figsize=figsize, save_path=save_path)
