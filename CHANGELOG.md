# Changelog

All notable changes to this project are documented in this file.

## [1.5.0] - 2026-02-23

- Refined GUI layout spacing and sizing for a tighter top control panel.
- Added colorbar visibility toggle in both GUI and CLI (`--colorbar/--no-colorbar`).
- Added advanced `Draw nodal lines` option (disabled for density mode).
- Added advanced `Line mode (contours only)` option and CLI flag (`--line-mode`).
- Updated line-mode rendering:
  - signed fields use solid/dashed contours with colormap-consistent intensity,
  - density fields support contour-only line rendering with matching colorbar.
- Improved density rendering to use the positive half of selected colormaps.
- Updated license metadata to include author information.

## [1.0.0] - 2026-02-22

- Implemented analytic hydrogen wavefunction plotting from quantum numbers.
- Added CLI modes: `real`, `imag`, `density`, `real_imag`.
- Added extra CLI modes: `radial_distribution`, `spherical_harmonic`.
- Added auto-selection for slice plane and range.
- Added GUI application with:
  - top common controls,
  - advanced settings dialog,
  - central plot panel,
  - bottom range slider,
  - PNG/SVG export.
- Added tests for parser, analytic behavior, and CLI settings.
