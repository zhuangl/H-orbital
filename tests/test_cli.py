"""Tests for CLI helper behavior."""

from h_orbital.auto_settings import auto_extent_a0, auto_plane_and_value
from h_orbital.cli import _build_parser, _default_output_name
from h_orbital.plotting import resolve_colormap, resolve_scale


def test_default_output_name_contains_identifiers() -> None:
    """Generated output names should encode orbital and slice metadata."""
    name = _default_output_name(2, 1, 0, "real", "z", 0.0)
    assert name.startswith("orbital_n2_l1_m0_real_z")
    assert name.endswith(".png")


def test_auto_extent_is_positive_and_grows_with_n() -> None:
    """Automatic range should be positive and generally larger for bigger n."""
    e1 = auto_extent_a0(n=1, l=0, mode="real")
    e3 = auto_extent_a0(n=3, l=1, mode="real")
    assert e1 > 0.0
    assert e3 > e1


def test_auto_extent_for_3s_real_is_not_excessive() -> None:
    """3s real-mode default extent should avoid over-zooming out."""
    e3s = auto_extent_a0(n=3, l=0, mode="real")
    assert e3s <= 20.0


def test_auto_extent_for_4d_real_allows_wider_view() -> None:
    """4d real-mode view should not be clipped too tightly."""
    e4d = auto_extent_a0(n=4, l=2, mode="real")
    assert e4d >= 28.0


def test_auto_plane_avoids_degenerate_slice_for_2p_m0_real() -> None:
    """For 2p m=0 in real mode, z=0 is degenerate and should not be selected."""
    plane, value = auto_plane_and_value(n=2, l=1, m=0, mode="real", extent_a0=8.0)
    assert plane in {"x", "y"}
    assert value == 0.0


def test_auto_scale_resolution_matches_mode() -> None:
    """Auto scale should pick log for density and symlog for signed modes."""
    assert resolve_scale(mode="density", scale="auto") == "log"
    assert resolve_scale(mode="real", scale="auto") == "symlog"


def test_density_keeps_selected_colormap_name() -> None:
    """Density mode keeps user-selected colormap name before positive-half mapping."""
    assert resolve_colormap(mode="density", cmap=None) == "RdYlBu_r"
    assert resolve_colormap(mode="density", cmap="RdYlBu_r") == "RdYlBu_r"


def test_cli_defaults_keep_real_mode_and_linear_scale() -> None:
    """User-facing defaults should stay readable without strong compression."""
    parser = _build_parser()
    args = parser.parse_args(["2"])
    assert args.mode == "real"
    assert args.scale == "linear"
    assert args.colorbar is False
    assert args.line_mode is False


def test_cli_can_disable_colorbar() -> None:
    """CLI should allow disabling the colorbar explicitly."""
    parser = _build_parser()
    args = parser.parse_args(["2", "--no-colorbar"])
    assert args.colorbar is False


def test_cli_can_enable_colorbar() -> None:
    """CLI should allow explicitly enabling colorbar."""
    parser = _build_parser()
    args = parser.parse_args(["2", "--colorbar"])
    assert args.colorbar is True


def test_cli_can_enable_line_mode() -> None:
    """CLI should allow enabling contour-only line mode."""
    parser = _build_parser()
    args = parser.parse_args(["2", "--line-mode"])
    assert args.line_mode is True


def test_parser_accepts_new_modes() -> None:
    """CLI should accept radial and spherical-harmonic special modes."""
    parser = _build_parser()
    args_radial = parser.parse_args(["3", "0", "0", "--mode", "radial_distribution"])
    args_sph = parser.parse_args(["2", "1", "1", "--mode", "spherical_harmonic"])
    assert args_radial.mode == "radial_distribution"
    assert args_sph.mode == "spherical_harmonic"
