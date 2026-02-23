"""Plotting helpers for hydrogen orbital slice visualization.

This module centralizes plotting style, colormap handling, and figure layout.
It supports both single-panel and real+imag dual-panel output.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
from matplotlib import cm
from matplotlib.colors import LinearSegmentedColormap, LogNorm, Normalize, SymLogNorm, TwoSlopeNorm


@dataclass(frozen=True)
class PlotStyle:
    """Rendering style settings for generated figures."""

    cmap: str
    levels: int = 21
    contour_levels: int = 8


def resolve_colormap(mode: str, cmap: str | None) -> str:
    """Resolve a colormap name from user choice and rendering mode.
    """
    if cmap:
        return cmap

    if mode == "density":
        return "RdYlBu_r"
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


def _positive_half_colormap(cmap_name: str) -> LinearSegmentedColormap:
    """Return the positive-value half of a colormap for density rendering.

    This keeps density non-negative visual semantics while still respecting the
    user's colormap choice. For diverging maps, it uses the upper half.
    """
    base = cm.get_cmap(cmap_name)
    samples = np.linspace(0.5, 1.0, 256)
    return LinearSegmentedColormap.from_list(f"{cmap_name}_positive", base(samples))


def resolve_density_cmap(cmap_name: str) -> LinearSegmentedColormap:
    """Public helper for density rendering colormap resolution."""
    return _positive_half_colormap(cmap_name)


def _draw_line_mode_signed(
    ax: Any,
    x: np.ndarray,
    y: np.ndarray,
    data: np.ndarray,
    vlim: float,
    cmap_name: str,
    show_nodal: bool,
) -> None:
    """Draw contour-only signed field using colormap endpoint colors.

    Positive contours use solid lines and negative contours use dashed lines.
    Colors are sampled from the selected colormap by contour level, so line
    intensity corresponds to function magnitude and matches the colorbar.
    """
    if vlim <= 0.0:
        return

    base_cmap = cm.get_cmap(cmap_name)
    norm = TwoSlopeNorm(vmin=-vlim, vcenter=0.0, vmax=vlim)
    base_levels = np.linspace(0.12 * vlim, vlim, 8)

    for level in base_levels:
        pos_color = base_cmap(norm(level))
        neg_color = base_cmap(norm(-level))
        ax.contour(x, y, data, levels=[level], colors=[pos_color], linewidths=1.2, linestyles="solid")
        ax.contour(x, y, data, levels=[-level], colors=[neg_color], linewidths=1.2, linestyles="dashed")

    if show_nodal:
        ax.contour(x, y, data, levels=[0.0], colors="#a8a8a8", linewidths=0.9)


def _draw_line_mode_density(
    ax: Any,
    x: np.ndarray,
    y: np.ndarray,
    data: np.ndarray,
    vmax: float,
    cmap_name: str,
) -> None:
    """Draw contour-only density field with colormap-driven solid line levels."""
    if vmax <= 0.0:
        return

    cmap = cm.get_cmap(cmap_name)
    norm = Normalize(vmin=0.0, vmax=vmax)
    levels = np.linspace(0.12 * vmax, vmax, 8)
    for level in levels:
        color = cmap(norm(level))
        ax.contour(x, y, data, levels=[level], colors=[color], linewidths=1.2, linestyles="solid")


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
    line_mode: bool,
    show_colorbar: bool,
    output_path: str,
    show: bool,
    show_nodal: bool = True,
) -> None:
    """Render one field as a contourf plot with optional zero contour."""
    style = PlotStyle(cmap=cmap)
    fig, ax = plt.subplots(figsize=(7.4, 6.4), dpi=150)
    vlim = 1.0
    if mode == "density":
        if line_mode:
            vmax = float(np.nanmax(data)) if data.size else 1.0
            _draw_line_mode_density(ax=ax, x=u, y=v, data=data, vmax=vmax, cmap_name=cmap)
            filled = None
        elif scale == "log":
            density_cmap = _positive_half_colormap(style.cmap)
            positive = data[data > 0.0]
            vmax = float(np.nanmax(data)) if data.size else 1.0
            if positive.size == 0 or vmax <= 0.0:
                filled = ax.contourf(u, v, data, levels=style.levels, cmap=density_cmap)
            else:
                vmin = max(float(np.nanmin(positive)), vmax * 1e-7)
                levels = np.geomspace(vmin, vmax, style.levels)
                norm = LogNorm(vmin=vmin, vmax=vmax)
                filled = ax.contourf(u, v, data, levels=levels, cmap=density_cmap, norm=norm)
        else:
            density_cmap = _positive_half_colormap(style.cmap)
            vmax = float(np.nanmax(data)) if data.size else 1.0
            levels = np.linspace(0.0, vmax if vmax > 0.0 else 1.0, style.levels)
            filled = ax.contourf(u, v, data, levels=levels, cmap=density_cmap)
    else:
        vlim = _signed_limits(data)
        if line_mode:
            _draw_line_mode_signed(
                ax=ax,
                x=u,
                y=v,
                data=data,
                vlim=vlim,
                cmap_name=cmap,
                show_nodal=show_nodal,
            )
            filled = None
        elif scale == "symlog":
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
        if not line_mode and show_nodal:
            ax.contour(u, v, data, levels=[0.0], colors="#a8a8a8", linewidths=0.9)

    ax.set_title(title)
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    ax.set_aspect("equal")
    ax.grid(alpha=0.18)
    if show_colorbar:
        if line_mode:
            if mode == "density":
                vmax = float(np.nanmax(data)) if data.size else 1.0
                fig.colorbar(cm.ScalarMappable(norm=Normalize(vmin=0.0, vmax=vmax), cmap=cm.get_cmap(cmap)), ax=ax)
            else:
                fig.colorbar(cm.ScalarMappable(norm=TwoSlopeNorm(vmin=-vlim, vcenter=0.0, vmax=vlim), cmap=cm.get_cmap(cmap)), ax=ax)
        elif filled is not None:
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
    line_mode: bool,
    show_colorbar: bool,
    output_path: str,
    show: bool,
    show_nodal: bool = True,
) -> None:
    """Render real and imaginary parts in a side-by-side two-panel figure."""
    fig, axes = plt.subplots(1, 2, figsize=(12.4, 5.5), dpi=150, constrained_layout=True)
    global_lim = max(_signed_limits(real_part), _signed_limits(imag_part))
    if line_mode:
        levels = None
        norm = None
    elif scale == "symlog":
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
        if line_mode:
            _draw_line_mode_signed(
                ax=ax,
                x=u,
                y=v,
                data=data,
                vlim=global_lim,
                cmap_name=cmap,
                show_nodal=show_nodal,
            )
            filled = None
        else:
            filled = ax.contourf(u, v, data, levels=levels, cmap=cmap, norm=norm)
            if show_nodal:
                ax.contour(u, v, data, levels=[0.0], colors="#a8a8a8", linewidths=0.9)
        ax.set_title(f"{title}\n{panel_title}")
        ax.set_xlabel(x_label)
        ax.set_ylabel(y_label)
        ax.set_aspect("equal")
        ax.grid(alpha=0.18)
        if show_colorbar:
            if line_mode:
                fig.colorbar(
                    cm.ScalarMappable(norm=TwoSlopeNorm(vmin=-global_lim, vcenter=0.0, vmax=global_lim), cmap=cm.get_cmap(cmap)),
                    ax=ax,
                )
            elif filled is not None:
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
    line_mode: bool,
    show_colorbar: bool,
    output_path: str,
    show: bool,
    show_nodal: bool = True,
) -> None:
    """Render Re(Y_l^m) and Im(Y_l^m) on a theta-phi grid."""
    fig, axes = plt.subplots(1, 2, figsize=(12.4, 5.5), dpi=150, constrained_layout=True)
    global_lim = max(_signed_limits(real_part), _signed_limits(imag_part))

    if line_mode:
        levels = None
        norm = None
    elif scale == "symlog":
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
        if line_mode:
            _draw_line_mode_signed(
                ax=ax,
                x=phi_over_pi,
                y=theta_over_pi,
                data=data,
                vlim=global_lim,
                cmap_name=cmap,
                show_nodal=show_nodal,
            )
            filled = None
        else:
            filled = ax.contourf(phi_over_pi, theta_over_pi, data, levels=levels, cmap=cmap, norm=norm)
            if show_nodal:
                ax.contour(phi_over_pi, theta_over_pi, data, levels=[0.0], colors="#a8a8a8", linewidths=0.8)
        ax.set_title(f"{title}\n{panel_title}")
        ax.set_xlabel("phi / pi")
        ax.set_ylabel("theta / pi")
        ax.grid(alpha=0.18)
        if show_colorbar:
            if line_mode:
                fig.colorbar(
                    cm.ScalarMappable(norm=TwoSlopeNorm(vmin=-global_lim, vcenter=0.0, vmax=global_lim), cmap=cm.get_cmap(cmap)),
                    ax=ax,
                )
            elif filled is not None:
                fig.colorbar(filled, ax=ax)

    fig.savefig(output_path)
    if show:
        plt.show()
    plt.close(fig)
