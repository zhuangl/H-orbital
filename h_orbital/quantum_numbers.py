"""Parsing and validation utilities for hydrogen quantum numbers.

The CLI accepts one, two, or three positional values in this order:

- n: principal quantum number (required)
- l: orbital angular momentum quantum number (optional, default 0)
- m: magnetic quantum number (optional, default 0)

Validation follows hydrogenic constraints:

- n >= 1
- 0 <= l <= n - 1
- -l <= m <= l
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class QuantumNumbers:
    """Container for a validated (n, l, m) triple."""

    n: int
    l: int
    m: int


def parse_quantum_numbers(values: list[int]) -> QuantumNumbers:
    """Parse and validate one to three quantum numbers.

    Args:
        values: Positional integer values provided by the command line.

    Returns:
        A validated QuantumNumbers instance.

    Raises:
        ValueError: If the number of inputs is not 1..3 or if constraints fail.
    """
    if not 1 <= len(values) <= 3:
        raise ValueError("Please provide 1 to 3 quantum numbers: n [l] [m].")

    # Fill omitted quantum numbers with zeros as requested.
    padded = values + [0] * (3 - len(values))
    n, l, m = padded

    if n < 1:
        raise ValueError("Principal quantum number n must be >= 1.")
    if l < 0:
        raise ValueError("Angular momentum quantum number l must be >= 0.")
    if l > n - 1:
        raise ValueError("Angular momentum quantum number l must satisfy l <= n - 1.")
    if abs(m) > l:
        raise ValueError("Magnetic quantum number m must satisfy |m| <= l.")

    return QuantumNumbers(n=n, l=l, m=m)
