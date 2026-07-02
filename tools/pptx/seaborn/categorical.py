"""Categorical EDA chart functions."""

import warnings
from typing import List, Optional, Union

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from tools.pptx.seaborn import (
    DEFAULT_FIGSIZE,
    DEFAULT_PALETTE,
    _finalize,
    _setup,
    _themed_colors,
)

warnings.filterwarnings("ignore")


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
    n_cat = df[hue].nunique() if hue else df[x].nunique()
    kw = dict(data=df, hue=hue, palette=_themed_colors(palette, n_cat),
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
    total = sum(sizes)

    def _autopct(pct):
        return f"{pct:.1f}%" if pct >= 4 else ""

    ax.pie(sizes, labels=labels, autopct=_autopct if total else "%.1f%%",
           pctdistance=0.72, labeldistance=1.15,
           colors=_themed_colors(palette, len(sizes)), startangle=90)
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
