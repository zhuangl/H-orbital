"""Automatic plotting parameter selection utilities.

This module provides smart defaults so most users do not need to manually set
plane/value/range for each orbital. Advanced users can still override values
from the CLI.
"""

from __future__ import annotations

import numpy as np

from .analytic import hydrogen_wavefunction, radial_wavefunction
from .constants import BOHR_RADIUS
from .modes import evaluate_mode
from .slicing import build_plane_grid, cartesian_to_spherical


def auto_extent_a0(n: int, l: int, mode: str, coverage: float = 0.99) -> float:
    """Estimate a plotting half-range in units of ``a0``.

    For ``density`` mode, use radial probability coverage.
    For signed modes (``real``, ``imag``, ``real_imag``), use radial amplitude
    support, which usually gives a tighter and more visually informative frame.

    Args:
        n: Principal quantum number.
        l: Orbital angular momentum quantum number.
        mode: Render mode used by the CLI.
        coverage: Target cumulative probability for density mode.

    Returns:
        Suggested half-range in units of Bohr radius ``a0``.
    """
    coverage = float(np.clip(coverage, 0.95, 0.999))

    # Scan window for estimating support and radial structure.
    r_max = 12.0 * (n**2) * BOHR_RADIUS
    r = np.linspace(0.0, r_max, 12000)
    radial = radial_wavefunction(n=n, l=l, r=r)

    if mode in {"density", "radial_distribution"}:
        density = (r**2) * (np.abs(radial) ** 2)
        dr = r[1] - r[0]
        cumulative = np.cumsum((density[:-1] + density[1:]) * 0.5 * dr)
        cumulative = np.insert(cumulative, 0, 0.0)
        total = cumulative[-1] if cumulative[-1] > 0.0 else 1.0
        normalized = cumulative / total
        idx = int(np.searchsorted(normalized, coverage))
        idx = min(max(idx, 1), len(r) - 1)
        raw_extent = 1.15 * (r[idx] / BOHR_RADIUS)
    else:
        abs_radial = np.abs(radial)
        peak = float(np.nanmax(abs_radial)) if abs_radial.size else 0.0
        if peak <= 0.0:
            raw_extent = 6.0
        else:
            # Keep regions where the radial amplitude is still visually relevant.
            cutoff = peak * 2e-3
            significant = np.where(abs_radial >= cutoff)[0]
            if significant.size == 0:
                support_radius = 4.0 * BOHR_RADIUS
            else:
                support_radius = r[int(significant[-1])]

            # Preserve outer nodal structure by ensuring the last node is visible.
            sign = np.sign(radial)
            node_candidates = np.where(sign[:-1] * sign[1:] < 0.0)[0]
            if node_candidates.size > 0:
                last_node = r[int(node_candidates[-1])]
                raw_extent = max(1.25 * support_radius, 1.8 * last_node) / BOHR_RADIUS
            else:
                raw_extent = 1.25 * (support_radius / BOHR_RADIUS)

    # Keep automatic range readable and avoid oversized canvases.
    # Signed fields often need a wider view to show alternating lobes.
    min_extent = 4.0
    if mode in {"density", "radial_distribution"}:
        max_extent = max(10.0, 8.0 * float(n))
    else:
        max_extent = max(10.0, (6.0 + 2.0 * float(l)) * float(n))
    return float(np.clip(raw_extent, min_extent, max_extent))


def auto_plane_and_value(n: int, l: int, m: int, mode: str, extent_a0: float) -> tuple[str, float]:
    """Choose a representative default slice plane and value.

    The algorithm evaluates the signal strength on the three central planes
    (x=0, y=0, z=0) and selects the plane with the largest non-trivial
    variation for the chosen rendering mode.

    Args:
        n: Principal quantum number.
        l: Orbital angular momentum quantum number.
        m: Magnetic quantum number.
        mode: Rendering mode.
        extent_a0: Half-range in units of ``a0`` for coarse scoring.

    Returns:
        Tuple ``(plane, value)`` where value is in units of ``a0``.
    """
    candidates = ("z", "x", "y")
    best_plane = "z"
    best_score = -1.0

    for plane in candidates:
        grid = build_plane_grid(plane=plane, value_a0=0.0, extent_a0=extent_a0, points=121)
        r, theta, phi = cartesian_to_spherical(grid.x, grid.y, grid.z)
        psi = hydrogen_wavefunction(n=n, l=l, m=m, r=r, theta=theta, phi=phi)
        mode_data = evaluate_mode(psi=psi, mode=mode)

        if mode == "real_imag":
            real_part, imag_part = mode_data
            field = np.hypot(real_part, imag_part)
        else:
            field = np.asarray(mode_data)

        # Robust score from both peak and spread to avoid degenerate planes.
        peak = float(np.nanpercentile(np.abs(field), 99.5))
        spread = float(np.nanstd(field))
        score = peak + spread

        if score > best_score:
            best_score = score
            best_plane = plane

    return best_plane, 0.0
