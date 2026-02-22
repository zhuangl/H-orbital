"""Utilities for building 2D planar slices through 3D space.

Given a selected plane (x, y, or z) and a constant value, this module creates
a 2D cartesian grid and maps it to full 3D coordinates. It also provides
conversion to spherical coordinates required by the analytic wavefunction.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .constants import BOHR_RADIUS


@dataclass(frozen=True)
class SliceGrid:
    """Container for 2D slice geometry and mapped 3D coordinates."""

    u: np.ndarray
    v: np.ndarray
    x: np.ndarray
    y: np.ndarray
    z: np.ndarray
    u_label: str
    v_label: str
    plane_label: str


def build_plane_grid(plane: str, value_a0: float, extent_a0: float, points: int) -> SliceGrid:
    """Create a 2D grid for a constant x, y, or z plane.

    Args:
        plane: One of {"x", "y", "z"}.
        value_a0: Plane location in units of Bohr radius.
        extent_a0: Half-range for visible axes in units of Bohr radius.
        points: Number of samples along each axis.

    Returns:
        SliceGrid containing 2D axes and 3D coordinate arrays in meters.
    """
    axis = np.linspace(-extent_a0, extent_a0, points)
    u, v = np.meshgrid(axis, axis)
    value = value_a0 * BOHR_RADIUS

    if plane == "x":
        x = np.full_like(u, value)
        y = u * BOHR_RADIUS
        z = v * BOHR_RADIUS
        u_label, v_label = "Y", "Z"
    elif plane == "y":
        x = u * BOHR_RADIUS
        y = np.full_like(u, value)
        z = v * BOHR_RADIUS
        u_label, v_label = "X", "Z"
    else:
        x = u * BOHR_RADIUS
        y = v * BOHR_RADIUS
        z = np.full_like(u, value)
        u_label, v_label = "X", "Y"

    return SliceGrid(
        u=u,
        v=v,
        x=x,
        y=y,
        z=z,
        u_label=u_label,
        v_label=v_label,
        plane_label=f"{plane}={value_a0:g} a0",
    )


def cartesian_to_spherical(x: np.ndarray, y: np.ndarray, z: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Convert cartesian coordinates to spherical coordinates.

    Returns:
        A tuple (r, theta, phi) where:
        - r is radial distance in meters,
        - theta is polar angle in [0, pi],
        - phi is azimuth angle in [-pi, pi].
    """
    r = np.sqrt(x**2 + y**2 + z**2)

    # Avoid division by zero at the origin by using a safe denominator.
    safe_r = np.where(r == 0.0, 1.0, r)
    theta = np.arccos(np.clip(z / safe_r, -1.0, 1.0))
    theta = np.where(r == 0.0, 0.0, theta)

    phi = np.arctan2(y, x)
    return r, theta, phi
