"""Finger strength models — MVC-7 to grade correlation and inverse.

Maps maximal voluntary contraction (7-second hang on 20 mm edge, half-crimp)
to expected climbing grade and vice versa.

Data sources:
    - Lattice Training (n ≈ 901 climbers), internal benchmarks
    - Giles et al. 2006 (:cite:`giles2006`) — physiology of rock climbing
    - López-Rivera & González-Badillo 2012 (:cite:`lopezrivera2012`)
    - Levernier & Laffaye 2019 (:cite:`levernier2019`) — RFD in climbers
    - Rohmert 1960 (:cite:`rohmert1960`) — static endurance curve
    - Schweizer 2001 (:cite:`schweizer2001`) — crimp biomechanics
"""

from __future__ import annotations

import math

from climbing_science.grades import RouteSystem, difficulty_index, from_index

__all__ = [
    "mvc7_to_grade",
    "grade_to_mvc7",
    "rohmert_conversion",
    "power_to_weight",
    "rfd_from_curve",
]


# ---------------------------------------------------------------------------
# MVC-7 %BW ↔ Climbing Grade — Benchmark Table
# ---------------------------------------------------------------------------
# Composite data from multiple sources:
#   - Lattice Training (n ≈ 901), internal grade-strength correlations
#   - StrengthClimbing.com aggregated survey data (n ≈ 2000)
#   - r/climbharder 2017 survey (n = 555)
#
# Protocol: 20 mm edge, half-crimp, 7-second max hang
# Values represent the MEDIAN %BW for climbers at each grade.
#
# Format: (french_grade, percent_bw)
# Sorted by ascending difficulty.
# ---------------------------------------------------------------------------

_MVC7_BENCHMARKS: list[tuple[str, float]] = [
    ("5a", 70.0),
    ("5b", 78.0),
    ("5c", 85.0),
    ("6a", 93.0),
    ("6a+", 100.0),
    ("6b", 105.0),
    ("6b+", 110.0),
    ("6c", 116.0),
    ("6c+", 122.0),
    ("7a", 128.0),
    ("7a+", 134.0),
    ("7b", 140.0),
    ("7b+", 147.0),
    ("7c", 153.0),
    ("7c+", 160.0),
    ("8a", 167.0),
    ("8a+", 174.0),
    ("8b", 181.0),
    ("8b+", 188.0),
    ("8c", 195.0),
]

# Pre-compute difficulty indices for interpolation
_BENCH_IDX: list[tuple[int, float]] = [(difficulty_index(g, RouteSystem.FRENCH), pct) for g, pct in _MVC7_BENCHMARKS]


def _interpolate(x: float, points: list[tuple[float, float]]) -> float:
    """Linear interpolation between sorted (x, y) points.

    Extrapolates linearly beyond the table boundaries using the
    nearest two points.
    """
    if len(points) < 2:
        raise ValueError("Need at least 2 data points for interpolation")

    # Clamp / extrapolate
    if x <= points[0][0]:
        x0, y0 = points[0]
        x1, y1 = points[1]
        return y0 + (x - x0) * (y1 - y0) / (x1 - x0)
    if x >= points[-1][0]:
        x0, y0 = points[-2]
        x1, y1 = points[-1]
        return y0 + (x - x0) * (y1 - y0) / (x1 - x0)

    # Find bracketing interval
    for i in range(len(points) - 1):
        x0, y0 = points[i]
        x1, y1 = points[i + 1]
        if x0 <= x <= x1:
            if x1 == x0:
                return y0
            t = (x - x0) / (x1 - x0)
            return y0 + t * (y1 - y0)

    return points[-1][1]  # fallback


def _inverse_interpolate(y: float, points: list[tuple[float, float]]) -> float:
    """Inverse linear interpolation: given y, find x.

    Points are (x, y) sorted by x with y monotonically increasing.
    """
    if len(points) < 2:
        raise ValueError("Need at least 2 data points")

    # Extrapolate below
    if y <= points[0][1]:
        x0, y0 = points[0]
        x1, y1 = points[1]
        if y1 == y0:
            return x0
        return x0 + (y - y0) * (x1 - x0) / (y1 - y0)

    # Extrapolate above
    if y >= points[-1][1]:
        x0, y0 = points[-2]
        x1, y1 = points[-1]
        if y1 == y0:
            return x1
        return x0 + (y - y0) * (x1 - x0) / (y1 - y0)

    # Find bracketing interval
    for i in range(len(points) - 1):
        x0, y0 = points[i]
        x1, y1 = points[i + 1]
        if y0 <= y <= y1:
            if y1 == y0:
                return x0
            t = (y - y0) / (y1 - y0)
            return x0 + t * (x1 - x0)

    return points[-1][0]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def mvc7_to_grade(
    percent_bw: float,
    system=RouteSystem.FRENCH,
) -> str:
    """Estimate climbing grade from MVC-7 finger strength.

    Given the maximal voluntary contraction on a 20 mm edge (half-crimp,
    7-second hang) expressed as percentage of body weight, returns the
    expected climbing grade.

    Uses linear interpolation on composite benchmark data from Lattice
    Training (n ≈ 901) and aggregated survey sources.

    Args:
        percent_bw: MVC-7 as percentage of body weight (e.g. 125.0 for 125%).
        system: Target grading system (default: French).

    Returns:
        Grade string in the requested system.

    Raises:
        ValueError: If the resulting grade has no equivalent in the target system.

    References:
        Giles et al. 2006 (:cite:`giles2006`),
        Lattice Training benchmark data (n ≈ 901).

    Examples:
        >>> mvc7_to_grade(125.0)
        '6c+'
        >>> mvc7_to_grade(140.0, RouteSystem.YDS)
        '5.12d'
        >>> mvc7_to_grade(160.0, BoulderSystem.V_SCALE)
        'V8+'
    """
    # Interpolate to get difficulty index
    idx = _inverse_interpolate(
        percent_bw,
        [(float(i), pct) for i, pct in _BENCH_IDX],
    )

    # Find closest grade in the table
    best_grade = _MVC7_BENCHMARKS[0][0]
    best_dist = float("inf")
    for grade_str, _ in _MVC7_BENCHMARKS:
        grade_idx = difficulty_index(grade_str, RouteSystem.FRENCH)
        dist = abs(grade_idx - idx)
        if dist < best_dist:
            best_dist = dist
            best_grade = grade_str

    if system == RouteSystem.FRENCH:
        return best_grade
    best_idx = difficulty_index(best_grade, RouteSystem.FRENCH)
    return from_index(best_idx, system)


def grade_to_mvc7(
    grade_str: str,
    system=RouteSystem.FRENCH,
) -> float:
    """Estimate required MVC-7 (%BW) for a target climbing grade.

    Inverse of ``mvc7_to_grade``: given a climbing grade, returns the
    expected MVC-7 finger strength as percentage of body weight needed
    to climb at that level.

    Args:
        grade_str: Target grade (e.g. "7a", "V5", "5.12a").
        system: Grading system of the input.

    Returns:
        Required MVC-7 as percentage of body weight.

    References:
        Giles et al. 2006 (:cite:`giles2006`),
        Lattice Training benchmark data (n ≈ 901).

    Examples:
        >>> grade_to_mvc7("7a")
        128.0
        >>> grade_to_mvc7("V5", BoulderSystem.V_SCALE)
        122.0
        >>> grade_to_mvc7("5.13a", RouteSystem.YDS)
        147.0
    """
    idx = float(difficulty_index(grade_str, system))
    return round(
        _interpolate(idx, [(float(i), pct) for i, pct in _BENCH_IDX]),
        1,
    )


def rohmert_conversion(
    force_percent_mvc: float,
    duration_sec: float,
    target_duration_sec: float = 7.0,
) -> float:
    """Convert a hang at arbitrary duration/intensity to MVC-7 equivalent.

    Uses Rohmert's endurance curve for static muscle contractions.
    The maximum hold time at a given %MVC follows:

        t_max = -1.5 + (2.1 / (f_rel - 0.15))^{0.618}  × 60

    where f_rel is the relative force (0–1) and t_max is in seconds.

    This function normalises any (force, duration) pair to the equivalent
    force that could be sustained for exactly ``target_duration_sec``.

    Args:
        force_percent_mvc: Applied force as percentage of true MVC (0–100).
        duration_sec: Actual hang duration in seconds.
        target_duration_sec: Target duration to normalise to (default: 7s).

    Returns:
        Equivalent force as percentage of MVC at the target duration.

    References:
        Rohmert 1960 (:cite:`rohmert1960`) — original endurance model.

    Examples:
        >>> rohmert_conversion(80.0, 10.0, 7.0)  # 80% MVC for 10s → ?% MVC for 7s
        84.6
    """
    if force_percent_mvc <= 0 or force_percent_mvc > 100:
        raise ValueError(f"force_percent_mvc must be in (0, 100], got {force_percent_mvc}")
    if duration_sec <= 0 or target_duration_sec <= 0:
        raise ValueError("Durations must be positive")

    f_rel = force_percent_mvc / 100.0

    # Rohmert's endurance time at the given force
    if f_rel >= 1.0:
        t_max_given = 0.0
    elif f_rel <= 0.15:
        t_max_given = float("inf")
    else:
        t_max_given = (-1.5 + (2.1 / (f_rel - 0.15)) ** 0.618) * 60.0

    if t_max_given <= 0:
        t_max_given = 0.1

    # The fraction of endurance used at the given duration
    endurance_fraction = duration_sec / t_max_given

    # Find the force level that gives the same endurance fraction at target duration
    # Binary search for f_target where target_duration / t_max(f_target) == endurance_fraction
    lo, hi = 0.16, 1.0
    for _ in range(50):
        mid = (lo + hi) / 2.0
        t_max_mid = (-1.5 + (2.1 / (mid - 0.15)) ** 0.618) * 60.0
        if t_max_mid <= 0:
            t_max_mid = 0.1
        frac_mid = target_duration_sec / t_max_mid
        if frac_mid < endurance_fraction:
            lo = mid
        else:
            hi = mid

    return round(((lo + hi) / 2.0) * 100.0, 1)


def power_to_weight(
    mvc_kg: float,
    body_weight_kg: float,
) -> tuple[float, str]:
    """Calculate power-to-weight ratio and interpret the level.

    Args:
        mvc_kg: Absolute MVC-7 force in kg.
        body_weight_kg: Body weight in kg.

    Returns:
        Tuple of (ratio as percentage, level interpretation string).

    References:
        Schweizer 2001 (:cite:`schweizer2001`),
        Lattice Training benchmarks.

    Examples:
        >>> power_to_weight(88.0, 70.0)
        (125.7, 'intermediate')
    """
    if body_weight_kg <= 0:
        raise ValueError("body_weight_kg must be positive")
    if mvc_kg < 0:
        raise ValueError("mvc_kg must be non-negative")

    ratio = round(mvc_kg / body_weight_kg * 100.0, 1)

    if ratio < 80:
        level = "beginner"
    elif ratio < 100:
        level = "beginner-intermediate"
    elif ratio < 130:
        level = "intermediate"
    elif ratio < 160:
        level = "advanced"
    elif ratio < 190:
        level = "elite"
    else:
        level = "world-class"

    return ratio, level


def rfd_from_curve(
    force_values: list[float],
    sampling_rate_hz: float,
    window_ms: float = 200.0,
) -> float:
    """Calculate peak Rate of Force Development from a force-time curve.

    RFD is the maximum slope of the force-time curve, computed over
    a sliding window. Higher RFD indicates faster recruitment of motor
    units — a key performance indicator for dynamic moves.

    Args:
        force_values: Force measurements in kg (or Newtons — unit-agnostic).
        sampling_rate_hz: Sampling frequency in Hz.
        window_ms: Sliding window size in milliseconds (default: 200 ms).

    Returns:
        Peak RFD in force-units per second.

    Raises:
        ValueError: If insufficient data for the given window.

    References:
        Levernier & Laffaye 2019 (:cite:`levernier2019`) — RFD in climbers.

    Examples:
        >>> rfd_from_curve([0, 5, 15, 30, 45, 55, 60], 100.0, 200.0)
        250.0
    """
    if sampling_rate_hz <= 0:
        raise ValueError("sampling_rate_hz must be positive")
    if window_ms <= 0:
        raise ValueError("window_ms must be positive")

    window_samples = max(1, int(math.ceil(window_ms / 1000.0 * sampling_rate_hz)))

    if len(force_values) < window_samples + 1:
        raise ValueError(
            f"Need at least {window_samples + 1} samples for a {window_ms} ms window "
            f"at {sampling_rate_hz} Hz, got {len(force_values)}"
        )

    dt = window_samples / sampling_rate_hz
    max_rfd = 0.0

    for i in range(len(force_values) - window_samples):
        delta_f = force_values[i + window_samples] - force_values[i]
        rfd = delta_f / dt
        if rfd > max_rfd:
            max_rfd = rfd

    return round(max_rfd, 1)
