"""Tests for quantum number parsing and validation."""

import pytest

from h_orbital.quantum_numbers import parse_quantum_numbers


def test_parse_single_value_defaults_l_and_m() -> None:
    """Providing only n should default l and m to zero."""
    qn = parse_quantum_numbers([2])
    assert (qn.n, qn.l, qn.m) == (2, 0, 0)


def test_parse_two_values_defaults_m_to_zero() -> None:
    """Providing n and l should default m to zero."""
    qn = parse_quantum_numbers([3, 1])
    assert (qn.n, qn.l, qn.m) == (3, 1, 0)


def test_invalid_magnitude_of_m_raises_error() -> None:
    """Magnetic quantum number must satisfy |m| <= l."""
    with pytest.raises(ValueError):
        parse_quantum_numbers([2, 1, 2])
