"""Tests for analytic hydrogen wavefunction components."""

import numpy as np

from h_orbital.analytic import hydrogen_wavefunction
from h_orbital.constants import BOHR_RADIUS


def test_1s_wavefunction_is_purely_real() -> None:
    """For n=1,l=0,m=0, wavefunction should have zero imaginary part."""
    r = np.array([0.0, 0.5 * BOHR_RADIUS, 1.0 * BOHR_RADIUS])
    theta = np.array([0.0, np.pi / 3, np.pi / 2])
    phi = np.array([0.0, np.pi / 4, np.pi / 2])

    psi = hydrogen_wavefunction(1, 0, 0, r=r, theta=theta, phi=phi)
    assert np.allclose(np.imag(psi), 0.0, atol=1e-12)


def test_m_zero_state_has_zero_imaginary_component() -> None:
    """For m=0 states, azimuthal phase is unity and psi is real-valued."""
    r = np.array([0.3 * BOHR_RADIUS, 1.2 * BOHR_RADIUS])
    theta = np.array([np.pi / 4, np.pi / 2])
    phi = np.array([0.3, 2.1])

    psi = hydrogen_wavefunction(3, 2, 0, r=r, theta=theta, phi=phi)
    assert np.allclose(np.imag(psi), 0.0, atol=1e-12)
