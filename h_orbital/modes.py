"""Rendering mode transformations for complex wavefunction values.

Supported modes:

- density: |psi|^2
- real: Re(psi)
- imag: Im(psi)
- real_imag: returns both Re(psi) and Im(psi)
"""

from __future__ import annotations

import numpy as np


SIGNED_MODES = {"real", "imag", "real_imag"}


def evaluate_mode(psi: np.ndarray, mode: str) -> np.ndarray | tuple[np.ndarray, np.ndarray]:
    """Convert complex wavefunction values into requested render data.

    Args:
        psi: Complex wavefunction array.
        mode: One of ``density``, ``real``, ``imag``, ``real_imag``.

    Returns:
        A single real-valued array for most modes, or a tuple (real, imag)
        for ``real_imag``.
    """
    if mode == "density":
        return np.abs(psi) ** 2
    if mode == "real":
        return np.real(psi)
    if mode == "imag":
        return np.imag(psi)
    if mode == "real_imag":
        return np.real(psi), np.imag(psi)
    raise ValueError(f"Unsupported render mode: {mode}")
