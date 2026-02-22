"""Hydrogen orbital visualization package.

This package provides an analytic (closed-form) implementation of the
hydrogenic wavefunction

    psi_{n,l,m}(r, theta, phi) = R_{n,l}(r) * Y_l^m(theta, phi)

and utilities to render 2D planar slices from command-line inputs.
"""

from .analytic import hydrogen_wavefunction
from .quantum_numbers import QuantumNumbers, parse_quantum_numbers

__version__ = "1.0.0"

__all__ = ["QuantumNumbers", "parse_quantum_numbers", "hydrogen_wavefunction", "__version__"]
