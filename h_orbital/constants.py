"""Physical constants and numerical defaults used by the package.

All values are expressed in SI unless otherwise noted.
The current implementation uses the Bohr radius to make the analytic
hydrogen orbital formulas dimensionally correct.
"""

from __future__ import annotations

# Bohr radius in meters.
BOHR_RADIUS = 5.291_772_109_03e-11

# Default plotting range in units of a0 (dimensionless scale factor).
DEFAULT_RANGE_A0 = 3.0

# Default number of samples for each axis in the 2D grid.
DEFAULT_POINTS = 401
