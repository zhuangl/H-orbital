# H-orbital

`H-orbital` is a small Python package and CLI tool that plots 2D slices of
hydrogen atomic orbitals from quantum numbers `(n, l, m)`.

This project is a teaching utility for Zhuang Lin's *Structural Chemistry*
course.

![H-orbital UI Example](H-orbital%20UI.png)

The implementation uses the **analytic quantum-mechanical solution**:

\[
\psi_{n,l,m}(r,\theta,\phi)=R_{n,l}(r)Y_l^m(\theta,\phi)
\]

No numerical Schrodinger solver is used.

## Features

- CLI input with 1 to 3 quantum numbers: `n [l] [m]`
- Missing quantum numbers default to zero
- Rendering modes:
  - `density` for \(|\psi|^2\)
  - `real` for \(\Re(\psi)\)
  - `imag` for \(\Im(\psi)\)
  - `real_imag` for side-by-side real/imag plots
  - `radial_distribution` for \(r^2|R_{n,l}(r)|^2\) vs \(r\)
  - `spherical_harmonic` for side-by-side \(\Re(Y_l^m)\) and \(\Im(Y_l^m)\)
- Smart defaults for `plane`, `value`, and `range` if omitted
- Default color scaling is linear (`--scale linear`)
- Optional manual slice plane control by CLI:
  - `--plane x --value c` (plane `x=c`)
  - `--plane y --value c` (plane `y=c`)
  - `--plane z --value c` (plane `z=c`)
- Select colormap (`--cmap`), default is `RdYlBu_r`
- Optional contour-only line rendering via `--line-mode`
  - signed fields: positive solid lines and negative dashed lines
  - line colors come from the selected colormap's positive/negative ends
  - density fields: solid contour lines only (no filled surface)
- Density mode uses the positive-value half of the selected colormap, so zero stays near blank and higher values become progressively darker.
- Colorbar toggle: `--colorbar` / `--no-colorbar` (default: off)

## Install Dependencies

Create and activate a virtual environment, then install:

```bash
python -m pip install -e .
```

This installs required libraries from `pyproject.toml`.

## Usage

Run from repository root:

```bash
./H-orbital 2 1 0
```

## GUI Usage

Launch the graphical interface:

```bash
./H-orbital-ui
```

GUI layout:

- Top panel: common parameters (`n`, `l`, `m`, `mode`, `plane`, `value`) and `Plot`
- Top panel: includes a `Colorbar` toggle switch
- `Advanced` dialog: finer controls (`points`, `colormap`, `scale`, `Draw nodal lines`)
  with common colormap options and custom Matplotlib names
  - `Line mode (contours only)` toggle is available below colormap
  - in `density` mode, `symlog` is disabled
- Middle area: interactive Matplotlib plot canvas
- Bottom slider: range control in units of `a0`
- Export button: choose PNG, SVG, or PDF in one save dialog (default PDF)

If you run without arguments, the command prints full help:

```bash
./H-orbital
```

Examples:

```bash
# 1s orbital, defaults l=0, m=0
./H-orbital 1

# Real part of 2p(m=0) on z=0 plane
./H-orbital 2 1 0 --mode real --plane z --value 0

# Probability density of 3d(m=1) on y=0.5 a0 plane
./H-orbital 3 2 1 --mode density --plane y --value 0.5 --scale log

# Two-panel real and imaginary parts
./H-orbital 3 2 2 --mode real_imag --plane z --value 0 --cmap RdYlBu_r --scale symlog

# Contour-only line mode with colormap endpoint colors
./H-orbital 4 2 0 --mode real --line-mode --cmap coolwarm

# Radial distribution (independent of plane/value)
./H-orbital 3 0 0 --mode radial_distribution

# Spherical harmonic map (angles only, independent of plane/value)
./H-orbital 3 2 1 --mode spherical_harmonic --scale symlog
```

## Output Naming

If `--output` is not provided, a filename is generated automatically, e.g.:

`orbital_n2_l1_m0_real_z0p0.png`

## Notes on Units

- Input `--value` and `--range` are in units of Bohr radius `a0`.
- `--value` means the constant coordinate of the selected slicing plane.
  - Example: `--plane x --value 0` means plotting the plane `x = 0 * a0`.
- If `--plane` is omitted (default `auto`), the tool picks a central plane
  (`x=0`, `y=0`, or `z=0`) that best reveals structure for the selected mode.
- If `--value` is omitted, the tool uses `0` in the selected plane.
- If `--range` is omitted, the tool estimates a range from radial probability
  support and mode-aware heuristics to avoid clipping while preventing
  excessive zoom-out.
- In `radial_distribution` and `spherical_harmonic` modes, `--plane` and
  `--value` are not used.
- If `--scale` is omitted, the default is `linear`.
- You can still choose `--scale log` (good for `density`) or
  `--scale symlog` (good for signed fields).
- Internal wavefunction formulas are evaluated in SI meters.

## Development

Run tests:

```bash
pytest
```

Run a single test:

```bash
pytest tests/test_quantum_numbers.py::test_parse_single_value_defaults_l_and_m
```

## Version

Current stable version: `1.5.1`.

## License

This project is distributed under the MIT License. See `LICENSE`.
