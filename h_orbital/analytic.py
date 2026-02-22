"""Analytic hydrogen wavefunction implementation.

This module implements closed-form expressions from quantum mechanics:

1) Radial wavefunction R_{n,l}(r)
2) Spherical harmonic Y_l^m(theta, phi)
3) Full wavefunction psi_{n,l,m}(r, theta, phi)

No numerical eigen-solver is used. The implementation only evaluates
analytic formulas with special functions (associated Laguerre and Legendre).
"""

from __future__ import annotations

import math

import numpy as np
from scipy.special import eval_genlaguerre, lpmv

from .constants import BOHR_RADIUS


def radial_wavefunction(n: int, l: int, r: np.ndarray) -> np.ndarray:
    """Evaluate the analytic hydrogen radial function R_{n,l}(r).

    Formula used:

        R_{n,l}(r) = N * exp(-rho/2) * rho^l * L_{n-l-1}^{2l+1}(rho)
        rho = 2r / (n a0)
        N = (2 / (n a0))^(3/2) * sqrt((n-l-1)! / (2n (n+l)!))

    Args:
        n: Principal quantum number.
        l: Orbital angular momentum quantum number.
        r: Radial distance array in meters.

    Returns:
        Real-valued array with the same shape as ``r``.
    """
    rho = 2.0 * r / (n * BOHR_RADIUS)
    prefactor = (2.0 / (n * BOHR_RADIUS)) ** 1.5
    norm = math.sqrt(math.factorial(n - l - 1) / (2.0 * n * math.factorial(n + l)))
    laguerre = eval_genlaguerre(n - l - 1, 2 * l + 1, rho)
    return prefactor * norm * np.exp(-rho / 2.0) * np.power(rho, l) * laguerre


def spherical_harmonic(l: int, m: int, theta: np.ndarray, phi: np.ndarray) -> np.ndarray:
    """Evaluate the normalized spherical harmonic Y_l^m(theta, phi).

    The implementation uses SciPy's associated Legendre function ``lpmv`` and
    explicit normalization constants. This follows the Condon-Shortley phase
    convention used in physics.

    Args:
        l: Orbital angular momentum quantum number.
        m: Magnetic quantum number.
        theta: Polar angle in [0, pi].
        phi: Azimuth angle in [-pi, pi].

    Returns:
        Complex array with the same shape as ``theta`` and ``phi``.
    """
    m_abs = abs(m)
    normalization = math.sqrt(
        ((2 * l + 1) / (4.0 * math.pi))
        * (math.factorial(l - m_abs) / math.factorial(l + m_abs))
    )

    # lpmv includes the Condon-Shortley phase factor (-1)^m for m >= 0.
    p_lm = lpmv(m_abs, l, np.cos(theta))
    y_positive = normalization * p_lm * np.exp(1j * m_abs * phi)

    if m >= 0:
        return y_positive

    # Relation for negative m:
    # Y_l^{-m} = (-1)^m * conjugate(Y_l^{m}).
    return ((-1) ** m_abs) * np.conjugate(y_positive)


def hydrogen_wavefunction(
    n: int,
    l: int,
    m: int,
    r: np.ndarray,
    theta: np.ndarray,
    phi: np.ndarray,
) -> np.ndarray:
    """Compute the full analytic hydrogen wavefunction psi_{n,l,m}.

    Args:
        n: Principal quantum number.
        l: Orbital angular momentum quantum number.
        m: Magnetic quantum number.
        r: Radial distance array in meters.
        theta: Polar angle array in radians.
        phi: Azimuth angle array in radians.

    Returns:
        Complex-valued array psi_{n,l,m}(r, theta, phi).
    """
    radial = radial_wavefunction(n=n, l=l, r=r)
    angular = spherical_harmonic(l=l, m=m, theta=theta, phi=phi)
    return radial * angular
