"""Tkinter GUI for interactive hydrogen orbital plotting.

The interface provides:

- A top panel with common parameters.
- An advanced settings dialog for detailed controls.
- A central Matplotlib canvas updated by a Plot button.
- Export actions for PNG and SVG.
- A bottom range slider to control the spatial plotting extent.
"""

from __future__ import annotations

import tkinter as tk
from dataclasses import dataclass
from tkinter import filedialog, messagebox, ttk
from typing import Any

import numpy as np
from matplotlib import cm
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.colors import LogNorm, Normalize, SymLogNorm, TwoSlopeNorm
from matplotlib.figure import Figure

from .analytic import hydrogen_wavefunction, radial_wavefunction, spherical_harmonic
from .auto_settings import auto_plane_and_value
from .constants import BOHR_RADIUS
from .modes import evaluate_mode
from .plotting import resolve_colormap, resolve_density_cmap, resolve_scale
from .quantum_numbers import parse_quantum_numbers
from .slicing import build_plane_grid, cartesian_to_spherical


COLORMAP_CHOICES = (
    "RdYlBu_r",
    "RdBu_r",
    "coolwarm",
    "seismic",
    "bwr",
    "Spectral_r",
    "PiYG",
    "PRGn",
    "BrBG",
    "viridis",
    "plasma",
    "magma",
    "cividis",
    "turbo",
)


@dataclass
class AdvancedSettings:
    """Container for advanced plotting parameters."""

    points: int = 401
    cmap: str = "RdYlBu_r"
    scale: str = "linear"
    show_nodal: bool = True
    line_mode: bool = False


class AdvancedDialog(tk.Toplevel):
    """Modal dialog for editing advanced plotting options."""

    def __init__(self, master: tk.Tk, settings: AdvancedSettings, mode: str) -> None:
        super().__init__(master)
        self.title("Advanced Settings")
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()

        self._result: AdvancedSettings | None = None

        self.points_var = tk.StringVar(value=str(settings.points))
        self.cmap_var = tk.StringVar(value=settings.cmap)
        self.scale_var = tk.StringVar(value=settings.scale)
        self.show_nodal_var = tk.BooleanVar(value=settings.show_nodal)
        self.line_mode_var = tk.BooleanVar(value=settings.line_mode)

        form = ttk.Frame(self, padding=12)
        form.grid(row=0, column=0, sticky="nsew")

        ttk.Label(form, text="Grid points").grid(row=0, column=0, sticky="w", pady=4)
        ttk.Entry(form, textvariable=self.points_var, width=16).grid(row=0, column=1, sticky="w", pady=4)

        ttk.Label(form, text="Colormap").grid(row=1, column=0, sticky="w", pady=4)
        ttk.Combobox(
            form,
            values=COLORMAP_CHOICES,
            textvariable=self.cmap_var,
            width=16,
            state="normal",
        ).grid(row=1, column=1, sticky="w", pady=4)

        ttk.Checkbutton(form, text="Line mode (contours only)", variable=self.line_mode_var).grid(
            row=2,
            column=0,
            columnspan=2,
            sticky="w",
            pady=4,
        )

        ttk.Label(form, text="Scale").grid(row=3, column=0, sticky="w", pady=4)
        scale_values = ("linear", "auto", "log") if mode == "density" else ("linear", "auto", "log", "symlog")
        if mode == "density" and self.scale_var.get() == "symlog":
            self.scale_var.set("linear")

        ttk.Combobox(
            form,
            values=scale_values,
            textvariable=self.scale_var,
            width=13,
            state="readonly",
        ).grid(row=3, column=1, sticky="w", pady=4)

        nodal_check = ttk.Checkbutton(form, text="Draw nodal lines", variable=self.show_nodal_var)
        nodal_check.grid(row=4, column=0, columnspan=2, sticky="w", pady=4)
        if mode == "density":
            nodal_check.state(["disabled"])

        button_row = ttk.Frame(form)
        button_row.grid(row=5, column=0, columnspan=2, sticky="e", pady=(10, 0))
        ttk.Button(button_row, text="Cancel", command=self.destroy).grid(row=0, column=0, padx=4)
        ttk.Button(button_row, text="Apply", command=self._apply).grid(row=0, column=1, padx=4)

    @property
    def result(self) -> AdvancedSettings | None:
        """Return updated settings when the dialog closes with Apply."""
        return self._result

    def _apply(self) -> None:
        """Validate and commit advanced settings from dialog fields."""
        try:
            points = int(self.points_var.get())
            if points < 50:
                raise ValueError
        except ValueError:
            messagebox.showerror("Invalid value", "Grid points must be an integer >= 50.", parent=self)
            return

        self._result = AdvancedSettings(
            points=points,
            cmap=self.cmap_var.get().strip(),
            scale=self.scale_var.get().strip() or "linear",
            show_nodal=bool(self.show_nodal_var.get()),
            line_mode=bool(self.line_mode_var.get()),
        )
        self.destroy()


class OrbitalApp:
    """Main GUI application for interactive hydrogen orbital plots."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("H-orbital UI")
        self.root.geometry("920x760")

        self.settings = AdvancedSettings()

        # Common controls.
        self.n_var = tk.IntVar(value=2)
        self.l_var = tk.IntVar(value=1)
        self.m_var = tk.IntVar(value=0)
        self.mode_var = tk.StringVar(value="real")
        self.plane_var = tk.StringVar(value="auto")
        self.value_var = tk.StringVar(value="0")
        self.range_var = tk.DoubleVar(value=20.0)
        self.show_colorbar_var = tk.BooleanVar(value=False)
        self._slider_after_id: str | None = None

        self._build_layout()
        self._plot_current()

    def _build_layout(self) -> None:
        """Create all GUI widgets and container frames."""
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)

        top = ttk.Frame(self.root, padding=(10, 8))
        top.grid(row=0, column=0, sticky="ew")

        ttk.Label(top, text="n").grid(row=0, column=0, padx=4, pady=2)
        ttk.Spinbox(top, from_=1, to=12, width=5, textvariable=self.n_var).grid(row=0, column=1, padx=4, pady=2)

        ttk.Label(top, text="l").grid(row=0, column=2, padx=4, pady=2)
        ttk.Spinbox(top, from_=0, to=11, width=5, textvariable=self.l_var).grid(row=0, column=3, padx=4, pady=2)

        ttk.Label(top, text="m").grid(row=0, column=4, padx=4, pady=2)
        ttk.Spinbox(top, from_=-11, to=11, width=5, textvariable=self.m_var).grid(row=0, column=5, padx=4, pady=2)

        ttk.Label(top, text="mode").grid(row=0, column=6, padx=(12, 4), pady=2)
        ttk.Combobox(
            top,
            values=(
                "real",
                "imag",
                "density",
                "real_imag",
                "radial_distribution",
                "spherical_harmonic",
            ),
            textvariable=self.mode_var,
            width=18,
            state="readonly",
        ).grid(row=0, column=7, padx=4, pady=2, sticky="w")

        ttk.Label(top, text="plane").grid(row=1, column=0, padx=(4, 4), pady=2)
        ttk.Combobox(
            top,
            values=("auto", "x", "y", "z"),
            textvariable=self.plane_var,
            width=8,
            state="readonly",
        ).grid(row=1, column=1, padx=4, pady=2)

        ttk.Label(top, text="value (a0)").grid(row=1, column=2, padx=(8, 4), pady=2)
        ttk.Entry(top, textvariable=self.value_var, width=8).grid(row=1, column=3, padx=4, pady=2)

        ttk.Checkbutton(
            top,
            text="Colorbar",
            variable=self.show_colorbar_var,
            command=lambda: self._plot_current(show_errors=False),
        ).grid(row=1, column=4, padx=(12, 4), pady=2)
        ttk.Button(top, text="Advanced", command=self._open_advanced).grid(row=1, column=5, padx=(8, 4), pady=2)
        ttk.Button(top, text="Plot", command=self._plot_current).grid(row=1, column=6, padx=4, pady=2)

        export_row = ttk.Frame(top)
        export_row.grid(row=1, column=7, columnspan=2, padx=4, pady=2, sticky="w")
        ttk.Button(export_row, text="Export PNG", command=lambda: self._export("png")).grid(row=0, column=0, padx=(0, 4))
        ttk.Button(export_row, text="Export SVG", command=lambda: self._export("svg")).grid(row=0, column=1, padx=(0, 0))

        mid = ttk.Frame(self.root, padding=(10, 0, 10, 0))
        mid.grid(row=1, column=0, sticky="nsew")
        mid.columnconfigure(0, weight=1)
        mid.rowconfigure(0, weight=1)

        self.figure = Figure(figsize=(8, 6), dpi=120)
        self.canvas = FigureCanvasTkAgg(self.figure, master=mid)
        self.canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")

        bottom = ttk.Frame(self.root, padding=(12, 8))
        bottom.grid(row=2, column=0, sticky="ew")
        bottom.columnconfigure(1, weight=1)

        ttk.Label(bottom, text="Range (a0)").grid(row=0, column=0, sticky="w", padx=(0, 8))
        ttk.Scale(bottom, from_=4.0, to=80.0, variable=self.range_var, command=self._on_slider).grid(
            row=0,
            column=1,
            sticky="ew",
        )
        self.range_label = ttk.Label(bottom, text=f"{self.range_var.get():.1f}")
        self.range_label.grid(row=0, column=2, sticky="e", padx=(8, 0))

    def _on_slider(self, _: str) -> None:
        """Update range label and auto-refresh plot with short debounce."""
        self.range_label.configure(text=f"{self.range_var.get():.1f}")
        if self._slider_after_id is not None:
            self.root.after_cancel(self._slider_after_id)
        self._slider_after_id = self.root.after(160, lambda: self._plot_current(show_errors=False))

    def _open_advanced(self) -> None:
        """Open the advanced settings dialog and apply changes if confirmed."""
        dialog = AdvancedDialog(self.root, self.settings, mode=self.mode_var.get())
        self.root.wait_window(dialog)
        if dialog.result is not None:
            self.settings = dialog.result
            self._plot_current()

    def _export(self, fmt: str) -> None:
        """Export current figure as PNG or SVG."""
        suffix = f".{fmt}"
        path = filedialog.asksaveasfilename(
            title=f"Export as {fmt.upper()}",
            defaultextension=suffix,
            filetypes=[(fmt.upper(), f"*{suffix}")],
        )
        if not path:
            return
        self.figure.savefig(path)
        messagebox.showinfo("Export complete", f"Saved figure to:\n{path}")

    def _plot_current(self, show_errors: bool = True) -> None:
        """Generate and draw the plot from current UI state."""
        self._slider_after_id = None
        try:
            qn = parse_quantum_numbers([self.n_var.get(), self.l_var.get(), self.m_var.get()])
            value = float(self.value_var.get())
        except ValueError as exc:
            if show_errors:
                messagebox.showerror("Input error", str(exc))
            return

        mode = self.mode_var.get()
        extent = float(self.range_var.get())
        points = self.settings.points
        cmap = resolve_colormap(mode="real" if mode == "spherical_harmonic" else mode, cmap=self.settings.cmap or None)
        scale = resolve_scale(mode="real" if mode == "spherical_harmonic" else mode, scale=self.settings.scale)

        self.figure.clear()

        try:
            if mode == "radial_distribution":
                self._plot_radial(qn.n, qn.l, extent, points)
            elif mode == "spherical_harmonic":
                self._plot_spherical_harmonic(qn.l, qn.m, points, cmap, scale)
            else:
                self._plot_slice(qn.n, qn.l, qn.m, mode, extent, points, cmap, scale, value)
        except ValueError as exc:
            if show_errors:
                messagebox.showerror("Plot error", str(exc))
            return

        self.canvas.draw_idle()

    def _plot_radial(self, n: int, l: int, extent: float, points: int) -> None:
        """Draw radial probability distribution on a single axis."""
        r = np.linspace(0.0, extent * BOHR_RADIUS, points)
        radial = radial_wavefunction(n=n, l=l, r=r)
        radial_prob = (r**2) * (np.abs(radial) ** 2)

        ax = self.figure.add_subplot(111)
        ax.plot(r / BOHR_RADIUS, radial_prob, color="#1f4e79", linewidth=2.0)
        ax.set_title(f"Hydrogen Radial Distribution n={n}, l={l}")
        ax.set_xlabel("r / a0")
        ax.set_ylabel(r"$r^2|R_{n,l}(r)|^2$")
        ax.grid(alpha=0.25)

    def _plot_spherical_harmonic(self, l: int, m: int, points: int, cmap: str, scale: str) -> None:
        """Draw real and imaginary parts of spherical harmonic on angle grid."""
        if scale == "log":
            raise ValueError("Log scale is incompatible with signed spherical harmonics.")

        theta = np.linspace(0.0, np.pi, points)
        phi = np.linspace(-np.pi, np.pi, points)
        phi_grid, theta_grid = np.meshgrid(phi, theta)
        ylm = spherical_harmonic(l=l, m=m, theta=theta_grid, phi=phi_grid)

        ax1 = self.figure.add_subplot(121)
        ax2 = self.figure.add_subplot(122)
        title = f"Spherical Harmonic l={l}, m={m}"
        self._draw_signed_field(
            ax1,
            phi_grid / np.pi,
            theta_grid / np.pi,
            np.real(ylm),
            cmap,
            scale,
            self.settings.line_mode,
        )
        self._draw_signed_field(
            ax2,
            phi_grid / np.pi,
            theta_grid / np.pi,
            np.imag(ylm),
            cmap,
            scale,
            self.settings.line_mode,
        )
        ax1.set_title(f"{title}\nRe(Y)")
        ax2.set_title(f"{title}\nIm(Y)")
        for ax in (ax1, ax2):
            ax.set_xlabel("phi / pi")
            ax.set_ylabel("theta / pi")

    def _plot_slice(
        self,
        n: int,
        l: int,
        m: int,
        mode: str,
        extent: float,
        points: int,
        cmap: str,
        scale: str,
        value: float,
    ) -> None:
        """Draw planar slice plots for wavefunction-based modes."""
        line_mode = self.settings.line_mode
        if mode == "density" and scale == "symlog":
            scale = "linear"
        if mode in {"real", "imag", "real_imag"} and scale == "log":
            raise ValueError("Log scale cannot represent signed fields. Use linear/symlog.")

        plane_choice = self.plane_var.get()
        if plane_choice == "auto":
            plane, auto_value = auto_plane_and_value(n=n, l=l, m=m, mode=mode, extent_a0=extent)
            value = auto_value
            self.value_var.set(f"{value:g}")
        else:
            plane = plane_choice

        grid = build_plane_grid(plane=plane, value_a0=value, extent_a0=extent, points=points)
        r, theta, phi = cartesian_to_spherical(grid.x, grid.y, grid.z)
        psi = hydrogen_wavefunction(n=n, l=l, m=m, r=r, theta=theta, phi=phi)
        data = evaluate_mode(psi=psi, mode=mode)

        title = f"Hydrogen Orbital n={n}, l={l}, m={m} | mode={mode} | slice={plane}-plane"
        if scale != "linear":
            title += f" | scale={scale}"

        if mode == "real_imag":
            real_part, imag_part = data
            ax1 = self.figure.add_subplot(121)
            ax2 = self.figure.add_subplot(122)
            self._draw_signed_field(ax1, grid.u, grid.v, real_part, cmap, scale, line_mode)
            self._draw_signed_field(ax2, grid.u, grid.v, imag_part, cmap, scale, line_mode)
            ax1.set_title(f"{title}\nReal Part")
            ax2.set_title(f"{title}\nImaginary Part")
            for ax in (ax1, ax2):
                ax.set_xlabel(grid.u_label)
                ax.set_ylabel(grid.v_label)
                ax.set_aspect("equal")
        elif mode == "density":
            ax = self.figure.add_subplot(111)
            self._draw_density_field(ax, grid.u, grid.v, np.asarray(data), cmap, scale, line_mode)
            ax.set_title(title)
            ax.set_xlabel(grid.u_label)
            ax.set_ylabel(grid.v_label)
            ax.set_aspect("equal")
        else:
            ax = self.figure.add_subplot(111)
            self._draw_signed_field(ax, grid.u, grid.v, np.asarray(data), cmap, scale, line_mode)
            ax.set_title(title)
            ax.set_xlabel(grid.u_label)
            ax.set_ylabel(grid.v_label)
            ax.set_aspect("equal")

    def _draw_density_field(
        self,
        ax: Any,
        x: np.ndarray,
        y: np.ndarray,
        data: np.ndarray,
        cmap: str,
        scale: str,
        line_mode: bool,
    ) -> None:
        """Draw non-negative scalar field with linear or log scaling."""
        if line_mode:
            vmax = float(np.nanmax(data)) if data.size else 1.0
            den_cmap = cm.get_cmap(cmap)
            den_norm = Normalize(vmin=0.0, vmax=vmax if vmax > 0.0 else 1.0)
            levels = np.linspace(0.12 * vmax, vmax, 8)
            for level in levels:
                color = den_cmap(den_norm(level))
                ax.contour(x, y, data, levels=[level], colors=[color], linewidths=1.2, linestyles="solid")
            filled = None
        elif scale == "log":
            density_cmap = resolve_density_cmap(cmap)
            positive = data[data > 0.0]
            vmax = float(np.nanmax(data)) if data.size else 1.0
            if positive.size == 0 or vmax <= 0.0:
                filled = ax.contourf(x, y, data, levels=21, cmap=density_cmap)
            else:
                vmin = max(float(np.nanmin(positive)), vmax * 1e-7)
                levels = np.geomspace(vmin, vmax, 21)
                filled = ax.contourf(x, y, data, levels=levels, cmap=density_cmap, norm=LogNorm(vmin=vmin, vmax=vmax))
        else:
            density_cmap = resolve_density_cmap(cmap)
            vmax = float(np.nanmax(data)) if data.size else 1.0
            levels = np.linspace(0.0, vmax if vmax > 0.0 else 1.0, 21)
            filled = ax.contourf(x, y, data, levels=levels, cmap=density_cmap)
        ax.grid(alpha=0.18)
        if self.show_colorbar_var.get():
            if line_mode:
                vmax = float(np.nanmax(data)) if data.size else 1.0
                den_cmap = cm.get_cmap(cmap)
                den_norm = Normalize(vmin=0.0, vmax=vmax if vmax > 0.0 else 1.0)
                self.figure.colorbar(cm.ScalarMappable(norm=den_norm, cmap=den_cmap), ax=ax)
            elif filled is not None:
                self.figure.colorbar(filled, ax=ax)

    def _draw_signed_field(
        self,
        ax: Any,
        x: np.ndarray,
        y: np.ndarray,
        data: np.ndarray,
        cmap: str,
        scale: str,
        line_mode: bool,
    ) -> None:
        """Draw signed scalar field with linear or symlog scaling and zero contour."""
        vlim = float(np.nanmax(np.abs(data)))
        vlim = vlim if vlim > 0.0 else 1.0

        if line_mode:
            levels = np.linspace(0.12 * vlim, vlim, 8)
            base_cmap = cm.get_cmap(cmap)
            norm = TwoSlopeNorm(vmin=-vlim, vcenter=0.0, vmax=vlim)
            for level in levels:
                pos_color = base_cmap(norm(level))
                neg_color = base_cmap(norm(-level))
                ax.contour(x, y, data, levels=[level], colors=[pos_color], linewidths=1.2, linestyles="solid")
                ax.contour(x, y, data, levels=[-level], colors=[neg_color], linewidths=1.2, linestyles="dashed")
            filled = None
        elif scale == "symlog":
            linthresh = max(vlim * 1e-3, 1e-16)
            neg = -np.geomspace(linthresh, vlim, 10)[::-1]
            pos = np.geomspace(linthresh, vlim, 10)
            levels = np.concatenate((neg, [0.0], pos))
            norm = SymLogNorm(linthresh=linthresh, linscale=1.0, vmin=-vlim, vmax=vlim, base=10)
            filled = ax.contourf(x, y, data, levels=levels, cmap=cmap, norm=norm)
        else:
            levels = np.linspace(-vlim, vlim, 21)
            filled = ax.contourf(x, y, data, levels=levels, cmap=cmap)

        if self.settings.show_nodal:
            ax.contour(x, y, data, levels=[0.0], colors="#a8a8a8", linewidths=0.9)
        ax.grid(alpha=0.18)
        if self.show_colorbar_var.get():
            if line_mode:
                self.figure.colorbar(
                    cm.ScalarMappable(norm=TwoSlopeNorm(vmin=-vlim, vcenter=0.0, vmax=vlim), cmap=cm.get_cmap(cmap)),
                    ax=ax,
                )
            elif filled is not None:
                self.figure.colorbar(filled, ax=ax)


def main() -> None:
    """Launch the GUI application."""
    root = tk.Tk()
    app = OrbitalApp(root)
    # Keep a reference to avoid being optimized away.
    _ = app
    root.mainloop()
