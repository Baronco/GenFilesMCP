"""
charts.py  —  Módulo completo de visualización para EDA
========================================================
Todas las funciones reciben un DataFrame de pandas + parámetros mínimos.
Diseñado para que un LLM solo pase los datos y el tipo de gráfico.

ÍNDICE DE FUNCIONES
───────────────────
DISTRIBUCIONES
  hist(df, x, ...)                  Histograma + KDE opcional
  kde(df, x, y, ...)                Densidad 1D o 2D
  ecdf(df, x, ...)                  Distribución acumulada empírica
  ridge(df, x, group, ...)          Ridge plot (distribuciones apiladas)
  boxen(df, x, y, ...)              Boxen plot (letter-value, datasets grandes)

RELACIONES
  scatter(df, x, y, ...)            Dispersión simple o con tamaño/color
  bubble(df, x, y, size, ...)       Bubble chart (scatter con tamaño como variable)
  line(df, x, y, ...)               Líneas, acepta múltiples columnas en y
  lmplot(df, x, y, ...)             Regresión lineal con banda de confianza
  lmplot_facet(df, x, y, col, ...)  Regresión por grupos en facetas
  logistic(df, x, y, ...)           Regresión logística (y binaria 0/1)
  resid(df, x, y, ...)              Gráfico de residuos
  joint(df, x, y, ...)              Joint plot (scatter + distribuciones marginales)
  joint_hex(df, x, y, ...)          Joint plot con hexbin (datasets grandes)
  joint_kde(df, x, y, ...)          Joint plot con KDE bivariado

CATEGÓRICOS
  bar(df, x, y, ...)                Barras con CI
  count(df, x, ...)                 Conteo de categorías
  point(df, x, y, ...)              Point plot (medias + CI)
  box(df, x, y, ...)                Box plot
  violin(df, x, y, ...)             Violin plot
  strip(df, x, y, ...)              Strip plot (puntos individuales)
  swarm(df, x, y, ...)              Swarm plot (sin solapamiento)

MATRICES / MULTIVARIADO
  heatmap(df, ...)                  Mapa de calor de correlaciones
  clustermap(df, ...)               Heatmap con clustering jerárquico
  pair(df, ...)                     Pairplot (matriz de relaciones)
  pair_kde(df, ...)                 PairGrid con KDE en diagonal

SERIES DE TIEMPO
  timeseries(df, x, y, ...)         Líneas con banda de error por tiempo
  timeseries_facet(df, x, y, ...)   Serie de tiempo en facetas por grupo

UNIVERSAL
  chart(kind, df, ...)              Función única — despacha a cualquiera

USO RÁPIDO (para el LLM)
─────────────────────────
    from charts import chart
    chart("bar",       df, x="ciudad",   y="ventas",  palette="Blues")
    chart("lmplot",    df, x="edad",     y="salario", hue="genero")
    chart("heatmap",   df)
    chart("joint",     df, x="peso",     y="altura",  kind="reg")
    chart("ridge",     df, x="ingreso",  group="pais")
    chart("clustermap",df)
"""

import warnings
import inspect
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib as mpl
from cycler import cycler
from matplotlib.ticker import MaxNLocator
from typing import IO, Optional, Union, List
from io import BytesIO

warnings.filterwarnings("ignore")

# ─────────────────────────────────────────────
# Configuración global
# ─────────────────────────────────────────────
DEFAULT_PALETTE  = "tab10"
DEFAULT_FIGSIZE  = (10, 6)
DEFAULT_STYLE    = "ticks"
DEFAULT_CONTEXT  = "notebook"


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
        fig.savefig(save_path, bbox_inches="tight")
        if isinstance(save_path, str):
            print(f"✓ Guardado: {save_path}")
    else:
        plt.show()


# ══════════════════════════════════════════════
# DISTRIBUCIONES
# ══════════════════════════════════════════════

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
    """Curva de densidad 1D o KDE bivariado si se pasa y.

    En 1D dibuja el histograma de densidad y la curva KDE.
    """
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
                sns.kdeplot(
                    data=df,
                    x=x,
                    hue=hue,
                    multiple=multiple,
                    fill=False,
                    palette=[palette_colors[idx]],
                    kernel=kern,
                    bw_adjust=bw_adjusts[idx],
                    linewidth=2.2,
                    cut=1,
                    ax=ax,
                    label=f"{kern}",
                )
        else:
            for idx, kern in enumerate(kernels):
                sns.kdeplot(
                    data=df,
                    x=x,
                    y=y,
                    hue=hue,
                    multiple=multiple,
                    fill=False,
                    palette=[palette_colors[idx]],
                    kernel=kern,
                    bw_adjust=bw_adjusts[idx],
                    linewidth=2.2,
                    cut=1,
                    ax=ax,
                    label=f"{kern}",
                )
    else:
        if y is None:
            sns.histplot(data=df, x=x, hue=hue, stat="density", bins=bins,
                         element="bars", fill=True, alpha=0.35,
                         color="#d0d0d0" if hue is None else None,
                         edgecolor="#999999" if hue is None else None,
                         palette=palette, ax=ax)
            sns.kdeplot(data=df, x=x, hue=hue, multiple=multiple,
                        fill=fill, palette=palette, kernel=kernel,
                        bw_adjust=bw_adjust, linewidth=2.2,
                        cut=1, ax=ax)
        else:
            sns.kdeplot(data=df, x=x, y=y, hue=hue, multiple=multiple,
                        fill=fill, palette=palette, kernel=kernel,
                        bw_adjust=bw_adjust, linewidth=2.2,
                        cut=1, ax=ax)
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

    fig, axes = plt.subplots(n, 1, figsize=figsize,
                             gridspec_kw={"hspace": -overlap})

    for i, (grp, ax) in enumerate(zip(groups, axes)):
        data_grp = df[df[group] == grp][x].dropna()
        sns.kdeplot(data_grp, fill=True, alpha=0.8,
                    color=palette_colors[i], ax=ax)
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
        fig.savefig(save_path, bbox_inches="tight")
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


# ══════════════════════════════════════════════
# RELACIONES
# ══════════════════════════════════════════════

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
            sns.regplot(data=df, x=x, y=y, scatter=False, ax=ax,
                        truncate=False, color="red")
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
        df_melt = df.melt(id_vars=[x], value_vars=y,
                          var_name="_var", value_name="_val")
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
    """
    Regresión lineal (o polinomial) con banda de confianza.
    order=1 lineal, order=2 cuadrática, etc.
    """
    _setup()
    g = sns.lmplot(data=df, x=x, y=y, hue=hue, ci=ci, order=order,
                   scatter=scatter, palette=palette,
                   line_kws=line_kws,
                   height=figsize[1], aspect=figsize[0]/figsize[1])
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
                   col_wrap=col_wrap, ci=ci, palette=palette,
                   line_kws=line_kws)
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
                       height=figsize[1], aspect=figsize[0]/figsize[1])
    except Exception as exc:
        if "statsmodels" in str(exc).lower() or "logistic=True" in str(exc):
            x_arr = np.asarray(df[x], dtype=float)
            y_arr = np.asarray(df[y], dtype=float)
            if set(np.unique(y_arr)) <= {0.0, 1.0}:
                def sigmoid(z):
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
                _finalize(fig, ax, title or f"Regresión logística: {y} ~ {x}", xlabel or x, ylabel or y, save_path)
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
    """
    Gráfico de residuos de la regresión lineal y~x.
    Detecta heterocedasticidad, no-linealidades y outliers.
    lowess=True agrega suavizado LOWESS a la línea de referencia.
    """
    _setup()
    fig, ax = plt.subplots(figsize=figsize)
    sns.residplot(data=df, x=x, y=y, lowess=lowess, ax=ax,
                  scatter_kws={"alpha": 0.6})
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
    """
    Joint plot: gráfico central + distribuciones marginales.
    kind: 'scatter'|'kde'|'hist'|'hex'|'reg'|'resid'
    """
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


# ══════════════════════════════════════════════
# CATEGÓRICOS
# ══════════════════════════════════════════════

def bar(
    df: pd.DataFrame,
    x: str,
    y: str,
    hue: Optional[str] = None,
    orient: str = "v",
    ci: int = 95,
    palette: str = DEFAULT_PALETTE,
    title: str = "",
    xlabel: str = "",
    ylabel: str = "",
    figsize: tuple = DEFAULT_FIGSIZE,
    save_path: Optional[str] = None,
):
    """Barras con intervalo de confianza. orient: 'v' vertical | 'h' horizontal."""
    _setup()
    fig, ax = plt.subplots(figsize=figsize)
    kw = dict(data=df, hue=hue, palette=palette,
              errorbar=("ci", ci) if ci else None, ax=ax)
    if orient == "h":
        sns.barplot(x=y, y=x, **kw)
    else:
        sns.barplot(x=x, y=y, **kw)
    _finalize(fig, ax, title or f"Barras: {y} por {x}",
              xlabel or (y if orient == "h" else x),
              ylabel or (x if orient == "h" else y), save_path)
    return fig, ax


def pie(
    df: pd.DataFrame,
    x: str,
    y: str,
    palette: str = DEFAULT_PALETTE,
    title: str = "",
    figsize: tuple = (8, 8),
    save_path: Optional[str] = None,
):
    """Pie chart: categorias en x y valores en y."""
    _setup()
    labels = df[x].astype(str)
    sizes = df[y]
    fig, ax = plt.subplots(figsize=figsize)
    ax.pie(sizes, labels=labels, autopct="%.1f%%", colors=sns.color_palette(palette, len(sizes)), startangle=90)
    ax.axis("equal")
    _finalize(fig, ax, title or f"Pie: {y} por {x}", "", "", save_path)
    return fig, ax


def count(
    df: pd.DataFrame,
    x: str,
    hue: Optional[str] = None,
    orient: str = "v",
    order: Optional[List] = None,
    palette: str = DEFAULT_PALETTE,
    title: str = "",
    xlabel: str = "",
    ylabel: str = "Conteo",
    figsize: tuple = DEFAULT_FIGSIZE,
    save_path: Optional[str] = None,
):
    """Conteo de frecuencias de una variable categórica."""
    _setup()
    fig, ax = plt.subplots(figsize=figsize)
    if orient == "h":
        sns.countplot(data=df, y=x, hue=hue, order=order, palette=palette, ax=ax)
    else:
        sns.countplot(data=df, x=x, hue=hue, order=order, palette=palette, ax=ax)
    _finalize(fig, ax, title or f"Conteo: {x}", xlabel or x, ylabel, save_path)
    return fig, ax


def point(
    df: pd.DataFrame,
    x: str,
    y: str,
    hue: Optional[str] = None,
    ci: int = 95,
    palette: str = DEFAULT_PALETTE,
    markers: Union[str, list] = "o",
    linestyles: Union[str, list] = "-",
    title: str = "",
    xlabel: str = "",
    ylabel: str = "",
    figsize: tuple = DEFAULT_FIGSIZE,
    save_path: Optional[str] = None,
):
    """Point plot: medias por categoría con IC. Útil para detectar interacciones."""
    _setup()
    fig, ax = plt.subplots(figsize=figsize)
    sns.pointplot(data=df, x=x, y=y, hue=hue,
                  errorbar=("ci", ci) if ci else None,
                  palette=palette, markers=markers,
                  linestyles=linestyles, ax=ax)
    _finalize(fig, ax, title or f"Point: {y} por {x}",
              xlabel or x, ylabel or y, save_path)
    return fig, ax


def box(
    df: pd.DataFrame,
    x: str,
    y: str,
    hue: Optional[str] = None,
    notch: bool = False,
    orient: str = "v",
    palette: str = DEFAULT_PALETTE,
    title: str = "",
    xlabel: str = "",
    ylabel: str = "",
    figsize: tuple = DEFAULT_FIGSIZE,
    save_path: Optional[str] = None,
):
    """Box plot. notch=True muestra IC de la mediana. orient: 'v'|'h'."""
    _setup()
    fig, ax = plt.subplots(figsize=figsize)
    if orient == "h":
        sns.boxplot(data=df, x=y, y=x, hue=hue, notch=notch, palette=palette, ax=ax)
    else:
        sns.boxplot(data=df, x=x, y=y, hue=hue, notch=notch, palette=palette, ax=ax)
    _finalize(fig, ax, title or f"Box: {y} por {x}",
              xlabel or x, ylabel or y, save_path)
    return fig, ax


def violin(
    df: pd.DataFrame,
    x: str,
    y: str,
    hue: Optional[str] = None,
    inner: str = "box",
    split: bool = False,
    palette: str = DEFAULT_PALETTE,
    title: str = "",
    xlabel: str = "",
    ylabel: str = "",
    figsize: tuple = DEFAULT_FIGSIZE,
    save_path: Optional[str] = None,
):
    """Violin plot. inner: 'box'|'quart'|'point'|'stick'|None. split: dividir por hue."""
    _setup()
    fig, ax = plt.subplots(figsize=figsize)
    sns.violinplot(data=df, x=x, y=y, hue=hue,
                   inner=inner, split=split, palette=palette, ax=ax)
    _finalize(fig, ax, title or f"Violin: {y} por {x}",
              xlabel or x, ylabel or y, save_path)
    return fig, ax


def strip(
    df: pd.DataFrame,
    x: str,
    y: str,
    hue: Optional[str] = None,
    jitter: bool = True,
    alpha: float = 0.7,
    palette: str = DEFAULT_PALETTE,
    title: str = "",
    xlabel: str = "",
    ylabel: str = "",
    figsize: tuple = DEFAULT_FIGSIZE,
    save_path: Optional[str] = None,
):
    """Strip plot: todos los puntos individuales por categoría."""
    _setup()
    fig, ax = plt.subplots(figsize=figsize)
    sns.stripplot(data=df, x=x, y=y, hue=hue,
                  jitter=jitter, alpha=alpha, palette=palette, ax=ax)
    _finalize(fig, ax, title or f"Strip: {y} por {x}",
              xlabel or x, ylabel or y, save_path)
    return fig, ax


def swarm(
    df: pd.DataFrame,
    x: str,
    y: str,
    hue: Optional[str] = None,
    size: float = 4.0,
    palette: str = DEFAULT_PALETTE,
    title: str = "",
    xlabel: str = "",
    ylabel: str = "",
    figsize: tuple = DEFAULT_FIGSIZE,
    save_path: Optional[str] = None,
):
    """Swarm plot: puntos sin solapamiento. Ideal para n < 500."""
    _setup()
    fig, ax = plt.subplots(figsize=figsize)
    sns.swarmplot(data=df, x=x, y=y, hue=hue, size=size, palette=palette, ax=ax)
    _finalize(fig, ax, title or f"Swarm: {y} por {x}",
              xlabel or x, ylabel or y, save_path)
    return fig, ax


# ══════════════════════════════════════════════
# MATRICES / MULTIVARIADO
# ══════════════════════════════════════════════

def heatmap(
    df: pd.DataFrame,
    columns: Optional[List[str]] = None,
    method: str = "pearson",
    annot: bool = True,
    fmt: str = ".2f",
    palette: str = "coolwarm",
    vmin: float = -1.0,
    vmax: float = 1.0,
    mask_upper: bool = False,
    matrix: bool = False,
    title: str = "",
    figsize: tuple = (10, 8),
    save_path: Optional[str] = None,
):
    """
    Heatmap de correlaciones o matriz de valores directa.
    method: 'pearson'|'spearman'|'kendall'.
    mask_upper=True muestra solo el triángulo inferior.
    """
    _setup()
    if matrix:
        corr = df
    else:
        data = df[columns] if columns else df.select_dtypes("number")
        corr = data.corr(method=method)
    mask = np.triu(np.ones_like(corr, dtype=bool)) if mask_upper else None
    fig, ax = plt.subplots(figsize=figsize)
    sns.heatmap(corr, annot=annot, fmt=fmt, cmap=palette,
                vmin=vmin, vmax=vmax, square=True,
                linewidths=0.5, mask=mask, ax=ax)
    _finalize(fig, ax, title or ("Matriz" if matrix else f"Correlaciones ({method})"), "", "", save_path)
    return fig, ax


def clustermap(
    df: pd.DataFrame,
    columns: Optional[List[str]] = None,
    method: str = "pearson",
    palette: str = "coolwarm",
    annot: bool = True,
    fmt: str = ".2f",
    matrix: bool = False,
    title: str = "",
    figsize: tuple = (10, 10),
    save_path: Optional[str] = None,
):
    """Clustermap: heatmap con clustering jerárquico. Agrupa variables correlacionadas."""
    _setup()
    if matrix:
        corr = df
    else:
        data = df[columns] if columns else df.select_dtypes("number")
        corr = data.corr(method=method)
    g = sns.clustermap(corr, cmap=palette, annot=annot, fmt=fmt,
                       vmin=-1, vmax=1, figsize=figsize, linewidths=0.5)
    if title:
        g.figure.suptitle(title, y=1.02)
    if save_path:
        g.figure.savefig(save_path, bbox_inches="tight")
        if isinstance(save_path, str):
            print(f"✓ Guardado: {save_path}")
    else:
        plt.show()
    return g


def pair(
    df: pd.DataFrame,
    columns: Optional[List[str]] = None,
    hue: Optional[str] = None,
    palette: str = DEFAULT_PALETTE,
    diag_kind: str = "kde",
    kind: str = "scatter",
    corner: bool = False,
    title: str = "",
    save_path: Optional[str] = None,
):
    """
    Pairplot: matriz de relaciones entre variables numéricas.
    diag_kind: 'kde'|'hist'. kind: 'scatter'|'kde'|'reg'. corner: solo triángulo inferior.
    """
    _setup()
    cols = (columns or []) + ([hue] if hue else [])
    data = df[cols] if cols else df
    g = sns.pairplot(data, hue=hue, palette=palette,
                     diag_kind=diag_kind, kind=kind, corner=corner)
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


def pair_kde(
    df: pd.DataFrame,
    columns: Optional[List[str]] = None,
    hue: Optional[str] = None,
    palette: str = DEFAULT_PALETTE,
    title: str = "",
    save_path: Optional[str] = None,
):
    """PairGrid con KDE en diagonal, scatter arriba y KDE abajo. Más detallado que pair()."""
    _setup()
    cols = columns or df.select_dtypes("number").columns.tolist()
    data = df[cols + [hue]].copy() if hue else df[cols].copy()
    g = sns.PairGrid(data, hue=hue, palette=palette)
    g.map_upper(sns.scatterplot, alpha=0.5, s=15)
    g.map_lower(sns.kdeplot, fill=True, alpha=0.4,
                common_norm=False, warn_singular=False)
    g.map_diag(sns.kdeplot, fill=True, warn_singular=False)
    if hue:
        g.add_legend()
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


# ══════════════════════════════════════════════
# SERIES DE TIEMPO
# ══════════════════════════════════════════════

def timeseries(
    df: pd.DataFrame,
    x: str,
    y: Union[str, List[str]],
    hue: Optional[str] = None,
    ci: int = 95,
    markers: bool = False,
    palette: str = DEFAULT_PALETTE,
    title: str = "",
    xlabel: str = "",
    ylabel: str = "",
    figsize: tuple = (12, 5),
    save_path: Optional[str] = None,
):
    """Serie de tiempo con banda de confianza. y puede ser str o lista de columnas."""
    _setup()
    fig, ax = plt.subplots(figsize=figsize)
    if isinstance(y, list):
        df_melt = df.melt(id_vars=[x], value_vars=y,
                          var_name="_var", value_name="_val")
        sns.lineplot(data=df_melt, x=x, y="_val", hue="_var",
                     markers=markers, palette=palette, ax=ax)
        ax.set_ylabel(ylabel or "Valor")
    else:
        sns.lineplot(data=df, x=x, y=y, hue=hue,
                     errorbar=("ci", ci) if ci else None,
                     markers=markers, palette=palette, ax=ax)
        ax.set_ylabel(ylabel or y)
    ax.xaxis.set_major_locator(MaxNLocator(nbins=8))
    plt.xticks(rotation=30, ha="right")
    _finalize(fig, ax, title or f"Serie de tiempo: {y}", xlabel or x, "", save_path)
    return fig, ax


def timeseries_facet(
    df: pd.DataFrame,
    x: str,
    y: str,
    col: str,
    hue: Optional[str] = None,
    col_wrap: int = 3,
    palette: str = DEFAULT_PALETTE,
    title: str = "",
    figsize: tuple = (5, 4),
    save_path: Optional[str] = None,
):
    """Series de tiempo en facetas: una sub-gráfica por valor de col."""
    _setup()
    g = sns.FacetGrid(df, col=col, hue=hue, col_wrap=col_wrap,
                      palette=palette,
                      height=figsize[1], aspect=figsize[0]/figsize[1])
    g.map(sns.lineplot, x, y)
    g.set_titles(col_template="{col_name}")
    g.set_xticklabels(rotation=30)
    if hue:
        g.add_legend()
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


# ══════════════════════════════════════════════
# FUNCIÓN UNIVERSAL
# ══════════════════════════════════════════════

CHART_TYPES = {
    # Distribuciones
    "hist":              hist,
    "kde":               kde,
    "ecdf":              ecdf,
    "ridge":             ridge,
    "boxen":             boxen,
    # Relaciones
    "scatter":           scatter,
    "bubble":            bubble,
    "line":              line,
    "lmplot":            lmplot,
    "lmplot_facet":      lmplot_facet,
    "logistic":          logistic,
    "resid":             resid,
    "joint":             joint,
    "joint_hex":         joint_hex,
    "joint_kde":         joint_kde,
    # Categóricos
    "bar":               bar,
    "count":             count,
    "point":             point,
    "box":               box,
    "violin":            violin,
    "strip":             strip,
    "swarm":             swarm,
    "pie":               pie,
    # Matrices
    "heatmap":           heatmap,
    "clustermap":        clustermap,
    "pair":              pair,
    "pair_kde":          pair_kde,
    # Series de tiempo
    "timeseries":        timeseries,
    "timeseries_facet":  timeseries_facet,
}


def _filter_kwargs(func, kwargs: dict) -> dict:
    try:
        sig = inspect.signature(func)
    except (TypeError, ValueError):
        return kwargs

    if any(p.kind == inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values()):
        return kwargs

    return {k: v for k, v in kwargs.items() if k in sig.parameters}


def chart(kind: str, df: pd.DataFrame, **kwargs):
    """
    Función universal: el LLM solo necesita kind + df + kwargs del gráfico.

    Distribuciones : hist, kde, ecdf, ridge, boxen
    Relaciones     : scatter, bubble, line, lmplot, lmplot_facet,
                     logistic, resid, joint, joint_hex, joint_kde
    Categóricos    : bar, count, point, box, violin, strip, swarm
    Matrices       : heatmap, clustermap, pair, pair_kde
    Series tiempo  : timeseries, timeseries_facet

    Ejemplos
    --------
    chart("bar",             df, x="ciudad",  y="ventas",   palette="Blues")
    chart("lmplot",          df, x="edad",    y="salario",  hue="genero")
    chart("lmplot_facet",    df, x="edad",    y="salario",  col="depto")
    chart("logistic",        df, x="score",   y="compro")
    chart("resid",           df, x="precio",  y="demanda",  lowess=True)
    chart("joint",           df, x="peso",    y="altura",   kind="reg")
    chart("joint_hex",       df, x="lat",     y="lon")
    chart("ecdf",            df, x="ingreso", hue="region")
    chart("ridge",           df, x="ingreso", group="pais")
    chart("boxen",           df, x="mes",     y="valor")
    chart("bubble",          df, x="gdp",     y="life_exp", size="population")
    chart("heatmap",         df, method="spearman", mask_upper=True)
    chart("clustermap",      df)
    chart("pair_kde",        df, hue="especie")
    chart("timeseries",      df, x="fecha",   y="precio")
    chart("timeseries_facet",df, x="fecha",   y="ventas",   col="region")
    """
    if kind not in CHART_TYPES:
        available = "  ".join(sorted(CHART_TYPES.keys()))
        raise ValueError(
            f"Tipo '{kind}' no reconocido.\nDisponibles: {available}"
        )
    filtered_kwargs = _filter_kwargs(CHART_TYPES[kind], kwargs)
    return CHART_TYPES[kind](df, **filtered_kwargs)
