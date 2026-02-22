"""Command-line interface for hydrogen orbital analytic plotting.

This CLI consumes 1-3 quantum numbers and can produce:

- 2D planar slices of psi,
- radial probability distributions,
- spherical harmonic maps.

Missing ``l`` and ``m`` are automatically filled with zero.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

from .analytic import hydrogen_wavefunction, radial_wavefunction, spherical_harmonic
from .auto_settings import auto_extent_a0, auto_plane_and_value
from .constants import BOHR_RADIUS, DEFAULT_POINTS
from .modes import evaluate_mode
from .plotting import (
    plot_radial_distribution,
    plot_real_imag_dual,
    plot_spherical_harmonic_dual,
    plot_single_panel,
    resolve_colormap,
    resolve_scale,
)
from .quantum_numbers import parse_quantum_numbers
from .slicing import build_plane_grid, cartesian_to_spherical


def _build_parser() -> argparse.ArgumentParser:
    """Construct the CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="H-orbital",
        description="Plot analytic hydrogen orbital fields, radial profiles, and harmonics.",
    )
    parser.add_argument(
        "quantum_numbers",
        type=int,
        nargs="*",
        help="Provide n [l] [m], with missing values defaulting to 0.",
    )
    parser.add_argument(
        "--mode",
        choices=[
            "density",
            "real",
            "imag",
            "real_imag",
            "radial_distribution",
            "spherical_harmonic",
        ],
        default="real",
        help=(
            "Render mode: |psi|^2, Re(psi), Im(psi), Re/Im, "
            "radial distribution, or spherical harmonic."
        ),
    )
    parser.add_argument(
        "--plane",
        choices=["auto", "x", "y", "z"],
        default="auto",
        help="Select the slicing plane, or let the program auto-select it.",
    )
    parser.add_argument(
        "--value",
        type=float,
        default=None,
        help="Constant coordinate for the selected plane in a0 (auto if omitted).",
    )
    parser.add_argument(
        "--range",
        dest="extent",
        type=float,
        default=None,
        help=(
            "Half-range for each visible axis, in units of a0. "
            "If omitted, an automatic n-dependent range is used."
        ),
    )
    parser.add_argument(
        "--points",
        type=int,
        default=DEFAULT_POINTS,
        help="Number of grid samples per axis.",
    )
    parser.add_argument(
        "--cmap",
        default=None,
        help="Matplotlib colormap or presets: sample, sample_density.",
    )
    parser.add_argument(
        "--scale",
        choices=["auto", "linear", "log", "symlog"],
        default="linear",
        help="Color scaling mode. Default is linear; auto uses log/symlog heuristics.",
    )
    parser.add_argument(
        "--colorbar",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Show colorbar (default: off; use --colorbar to enable).",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output image path. Default is generated from parameters.",
    )
    parser.add_argument(
        "--show",
        action="store_true",
        help="Display the figure window in addition to saving the file.",
    )
    return parser


def _default_output_name(n: int, l: int, m: int, mode: str, plane: str, value: float) -> str:
    """Create a descriptive default output filename."""
    value_tag = str(value).replace("-", "m").replace(".", "p")
    return f"orbital_n{n}_l{l}_m{m}_{mode}_{plane}{value_tag}.png"


def main() -> None:
    """Run the H-orbital command-line workflow."""
    parser = _build_parser()
    args = parser.parse_args()

    if not args.quantum_numbers:
        parser.print_help()
        return

    try:
        qn = parse_quantum_numbers(args.quantum_numbers)
    except ValueError as exc:
        parser.error(str(exc))

    if args.points < 25:
        parser.error("--points must be at least 25 for stable contour plotting.")

    extent = (
        args.extent
        if args.extent is not None
        else auto_extent_a0(n=qn.n, l=qn.l, mode=args.mode)
    )
    if extent <= 0:
        parser.error("--range must be positive.")

    # Special mode 1: radial probability distribution P(r)=r^2|R|^2.
    if args.mode == "radial_distribution":
        output = args.output or _default_output_name(
            n=qn.n,
            l=qn.l,
            m=qn.m,
            mode=args.mode,
            plane="r",
            value=0.0,
        )
        output_path = str(Path(output))
        r_max = extent * BOHR_RADIUS
        r = np.linspace(0.0, r_max, args.points)
        radial = radial_wavefunction(n=qn.n, l=qn.l, r=r)
        radial_prob = (r**2) * (np.abs(radial) ** 2)
        title = f"Hydrogen Radial Distribution n={qn.n}, l={qn.l}"
        plot_radial_distribution(
            r_a0=r / BOHR_RADIUS,
            radial_prob=radial_prob,
            title=title,
            output_path=output_path,
            show=args.show,
        )
        print(f"Saved plot to: {output_path}")
        return

    # Special mode 2: spherical harmonic on theta-phi grid.
    if args.mode == "spherical_harmonic":
        output = args.output or _default_output_name(
            n=qn.n,
            l=qn.l,
            m=qn.m,
            mode=args.mode,
            plane="angles",
            value=0.0,
        )
        output_path = str(Path(output))
        theta = np.linspace(0.0, np.pi, args.points)
        phi = np.linspace(-np.pi, np.pi, args.points)
        phi_grid, theta_grid = np.meshgrid(phi, theta)
        ylm = spherical_harmonic(l=qn.l, m=qn.m, theta=theta_grid, phi=phi_grid)
        real_part = np.real(ylm)
        imag_part = np.imag(ylm)

        cmap = resolve_colormap(mode="real", cmap=args.cmap)
        scale = resolve_scale(mode="real", scale=args.scale)
        if scale == "log":
            parser.error("--scale log cannot represent signed spherical harmonics.")

        title_parts = [
            f"Spherical Harmonic l={qn.l}, m={qn.m}",
            "mode=spherical_harmonic",
        ]
        if scale != "linear":
            title_parts.append(f"scale={scale}")

        plot_spherical_harmonic_dual(
            phi_grid=phi_grid,
            theta_grid=theta_grid,
            real_part=real_part,
            imag_part=imag_part,
            title=" | ".join(title_parts),
            cmap=cmap,
            scale=scale,
            show_colorbar=args.colorbar,
            output_path=output_path,
            show=args.show,
        )
        print(f"Saved plot to: {output_path}")
        return

    if args.plane == "auto":
        plane, auto_value = auto_plane_and_value(
            n=qn.n,
            l=qn.l,
            m=qn.m,
            mode=args.mode,
            extent_a0=extent,
        )
    else:
        plane, auto_value = args.plane, 0.0

    value = args.value if args.value is not None else auto_value

    output = args.output or _default_output_name(
        n=qn.n,
        l=qn.l,
        m=qn.m,
        mode=args.mode,
        plane=plane,
        value=value,
    )
    output_path = str(Path(output))

    grid = build_plane_grid(
        plane=plane,
        value_a0=value,
        extent_a0=extent,
        points=args.points,
    )
    r, theta, phi = cartesian_to_spherical(grid.x, grid.y, grid.z)
    psi = hydrogen_wavefunction(qn.n, qn.l, qn.m, r=r, theta=theta, phi=phi)

    data = evaluate_mode(psi=psi, mode=args.mode)
    cmap = resolve_colormap(mode=args.mode, cmap=args.cmap)
    scale = resolve_scale(mode=args.mode, scale=args.scale)

    if args.mode == "density" and scale == "symlog":
        parser.error("--scale symlog is for signed fields; use linear or log for density.")
    if args.mode in {"real", "imag", "real_imag"} and scale == "log":
        parser.error("--scale log cannot represent signed fields; use linear or symlog.")

    title_parts = [
        f"Hydrogen Orbital n={qn.n}, l={qn.l}, m={qn.m}",
        f"mode={args.mode}",
        f"slice={plane}-plane",
    ]
    if scale != "linear":
        title_parts.append(f"scale={scale}")
    title = " | ".join(title_parts)

    if args.mode == "real_imag":
        real_part, imag_part = data
        plot_real_imag_dual(
            u=grid.u,
            v=grid.v,
            real_part=real_part,
            imag_part=imag_part,
            title=title,
            x_label=grid.u_label,
            y_label=grid.v_label,
            cmap=cmap,
            scale=scale,
            show_colorbar=args.colorbar,
            output_path=output_path,
            show=args.show,
        )
    else:
        plot_single_panel(
            u=grid.u,
            v=grid.v,
            data=data,
            mode=args.mode,
            title=title,
            x_label=grid.u_label,
            y_label=grid.v_label,
            cmap=cmap,
            scale=scale,
            show_colorbar=args.colorbar,
            output_path=output_path,
            show=args.show,
        )

    print(f"Saved plot to: {output_path}")
