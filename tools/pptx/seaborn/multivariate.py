"""Multivariate, matrix, and time-series EDA chart functions."""

import warnings
from typing import List, Optional, Union

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.ticker import MaxNLocator

from tools.pptx.seaborn import (
    DEFAULT_PALETTE,
    _finalize,
    _setup,
)

warnings.filterwarnings("ignore")


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
    """Heatmap de correlaciones o matriz de valores directa."""
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
    """Pairplot: matriz de relaciones entre variables numéricas."""
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
    """PairGrid con KDE en diagonal, scatter arriba y KDE abajo."""
    _setup()
    cols = columns or df.select_dtypes("number").columns.tolist()
    data = df[cols + [hue]].copy() if hue else df[cols].copy()
    g = sns.PairGrid(data, hue=hue, palette=palette)
    g.map_upper(sns.scatterplot, alpha=0.5, s=15)
    g.map_lower(sns.kdeplot, fill=True, alpha=0.4, common_norm=False, warn_singular=False)
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
        df_melt = df.melt(id_vars=[x], value_vars=y, var_name="_var", value_name="_val")
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
                      height=figsize[1], aspect=figsize[0] / figsize[1])
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
