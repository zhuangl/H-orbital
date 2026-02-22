"""Plotting helpers for hydrogen orbital slice visualization.

This module centralizes plotting style, colormap handling, and figure layout.
It supports both single-panel and real+imag dual-panel output.
"""

from __future__ import annotations

from dataclasses import dataclass

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LogNorm, SymLogNorm


@dataclass(frozen=True)
class PlotStyle:
    """Rendering style settings for generated figures."""

    cmap: str
    levels: int = 21
    contour_levels: int = 8


def resolve_colormap(mode: str, cmap: str | None) -> str:
    """Resolve a colormap name from user choice and rendering mode.

    Special preset names:
    - ``sample``: image-like diverging palette (RdYlBu_r)
    - ``sample_density``: warm sequential palette (YlOrRd)
    """
    if cmap:
        if cmap == "sample":
            return "RdYlBu_r"
        if cmap == "sample_density":
            return "YlOrRd"
        return cmap

    if mode == "density":
        return "YlOrRd"
    return "RdYlBu_r"


def resolve_scale(mode: str, scale: str) -> str:
    """Resolve plotting scale mode with smart defaults.

    - ``density`` defaults to ``log``
    - Signed modes default to ``symlog``
    """
    if scale == "auto":
        return "log" if mode == "density" else "symlog"
    return scale


def _signed_limits(data: np.ndarray) -> float:
    """Return symmetric absolute limit for signed color scaling."""
    peak = float(np.nanmax(np.abs(data)))
    return peak if peak > 0.0 else 1.0


def plot_single_panel(
    u: np.ndarray,
    v: np.ndarray,
    data: np.ndarray,
    mode: str,
    title: str,
    x_label: str,
    y_label: str,
    cmap: str,
    scale: str,
    show_colorbar: bool,
    output_path: str,
    show: bool,
) -> None:
    """Render one field as a contourf plot with optional zero contour."""
    style = PlotStyle(cmap=cmap)
    fig, ax = plt.subplots(figsize=(7.4, 6.4), dpi=150)
    if mode == "density":
        if scale == "log":
            positive = data[data > 0.0]
            vmax = float(np.nanmax(data)) if data.size else 1.0
            if positive.size == 0 or vmax <= 0.0:
                filled = ax.contourf(u, v, data, levels=style.levels, cmap=style.cmap)
            else:
                vmin = max(float(np.nanmin(positive)), vmax * 1e-7)
                levels = np.geomspace(vmin, vmax, style.levels)
                norm = LogNorm(vmin=vmin, vmax=vmax)
                filled = ax.contourf(u, v, data, levels=levels, cmap=style.cmap, norm=norm)
        else:
            filled = ax.contourf(u, v, data, levels=style.levels, cmap=style.cmap)
    else:
        vlim = _signed_limits(data)
        if scale == "symlog":
            linthresh = max(vlim * 1e-3, 1e-16)
            neg = -np.geomspace(linthresh, vlim, style.levels // 2)[::-1]
            pos = np.geomspace(linthresh, vlim, style.levels // 2)
            levels = np.concatenate((neg, [0.0], pos))
            norm = SymLogNorm(
                linthresh=linthresh,
                linscale=1.0,
                vmin=-vlim,
                vmax=vlim,
                base=10,
            )
            filled = ax.contourf(u, v, data, levels=levels, cmap=style.cmap, norm=norm)
        else:
            levels = np.linspace(-vlim, vlim, style.levels)
            filled = ax.contourf(u, v, data, levels=levels, cmap=style.cmap)

        # Draw the nodal contour where the selected field is zero.
        ax.contour(u, v, data, levels=[0.0], colors="gray", linewidths=0.9)

    ax.set_title(title)
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    ax.set_aspect("equal")
    ax.grid(alpha=0.18)
    if show_colorbar:
        fig.colorbar(filled, ax=ax)
    fig.tight_layout()
    fig.savefig(output_path)

    if show:
        plt.show()
    plt.close(fig)


def plot_real_imag_dual(
    u: np.ndarray,
    v: np.ndarray,
    real_part: np.ndarray,
    imag_part: np.ndarray,
    title: str,
    x_label: str,
    y_label: str,
    cmap: str,
    scale: str,
    show_colorbar: bool,
    output_path: str,
    show: bool,
) -> None:
    """Render real and imaginary parts in a side-by-side two-panel figure."""
    fig, axes = plt.subplots(1, 2, figsize=(12.4, 5.5), dpi=150, constrained_layout=True)
    global_lim = max(_signed_limits(real_part), _signed_limits(imag_part))
    if scale == "symlog":
        linthresh = max(global_lim * 1e-3, 1e-16)
        neg = -np.geomspace(linthresh, global_lim, 10)[::-1]
        pos = np.geomspace(linthresh, global_lim, 10)
        levels = np.concatenate((neg, [0.0], pos))
        norm = SymLogNorm(
            linthresh=linthresh,
            linscale=1.0,
            vmin=-global_lim,
            vmax=global_lim,
            base=10,
        )
    else:
        levels = np.linspace(-global_lim, global_lim, 21)
        norm = None

    for ax, data, panel_title in (
        (axes[0], real_part, "Real Part"),
        (axes[1], imag_part, "Imaginary Part"),
    ):
        filled = ax.contourf(u, v, data, levels=levels, cmap=cmap, norm=norm)
        ax.contour(u, v, data, levels=[0.0], colors="gray", linewidths=0.9)
        ax.set_title(f"{title}\n{panel_title}")
        ax.set_xlabel(x_label)
        ax.set_ylabel(y_label)
        ax.set_aspect("equal")
        ax.grid(alpha=0.18)
        if show_colorbar:
            fig.colorbar(filled, ax=ax)

    fig.savefig(output_path)
    if show:
        plt.show()
    plt.close(fig)


def plot_radial_distribution(
    r_a0: np.ndarray,
    radial_prob: np.ndarray,
    title: str,
    output_path: str,
    show: bool,
) -> None:
    """Render the radial probability distribution P(r)=r^2|R_{n,l}(r)|^2."""
    fig, ax = plt.subplots(figsize=(7.6, 5.2), dpi=150)
    ax.plot(r_a0, radial_prob, color="#1f4e79", linewidth=2.0)
    ax.set_title(title)
    ax.set_xlabel("r / a0")
    ax.set_ylabel(r"$r^2|R_{n,l}(r)|^2$")
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(output_path)
    if show:
        plt.show()
    plt.close(fig)


def plot_spherical_harmonic_dual(
    phi_grid: np.ndarray,
    theta_grid: np.ndarray,
    real_part: np.ndarray,
    imag_part: np.ndarray,
    title: str,
    cmap: str,
    scale: str,
    show_colorbar: bool,
    output_path: str,
    show: bool,
) -> None:
    """Render Re(Y_l^m) and Im(Y_l^m) on a theta-phi grid."""
    fig, axes = plt.subplots(1, 2, figsize=(12.4, 5.5), dpi=150, constrained_layout=True)
    global_lim = max(_signed_limits(real_part), _signed_limits(imag_part))

    if scale == "symlog":
        linthresh = max(global_lim * 1e-3, 1e-16)
        neg = -np.geomspace(linthresh, global_lim, 10)[::-1]
        pos = np.geomspace(linthresh, global_lim, 10)
        levels = np.concatenate((neg, [0.0], pos))
        norm = SymLogNorm(
            linthresh=linthresh,
            linscale=1.0,
            vmin=-global_lim,
            vmax=global_lim,
            base=10,
        )
    else:
        levels = np.linspace(-global_lim, global_lim, 21)
        norm = None

    phi_over_pi = phi_grid / np.pi
    theta_over_pi = theta_grid / np.pi

    for ax, data, panel_title in (
        (axes[0], real_part, "Re(Y_l^m)"),
        (axes[1], imag_part, "Im(Y_l^m)"),
    ):
        filled = ax.contourf(phi_over_pi, theta_over_pi, data, levels=levels, cmap=cmap, norm=norm)
        ax.contour(phi_over_pi, theta_over_pi, data, levels=[0.0], colors="gray", linewidths=0.8)
        ax.set_title(f"{title}\n{panel_title}")
        ax.set_xlabel("phi / pi")
        ax.set_ylabel("theta / pi")
        ax.grid(alpha=0.18)
        if show_colorbar:
            fig.colorbar(filled, ax=ax)

    fig.savefig(output_path)
    if show:
        plt.show()
    plt.close(fig)
