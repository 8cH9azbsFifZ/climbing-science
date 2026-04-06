"""Manual input adapter — create assessment data without a force gauge.

For climbers who test with a bathroom scale, a hangboard, a stopwatch,
and added weight (belt or pulley).  Produces the same canonical data
structures as device-based adapters so the full analysis pipeline can
be used.

References:
    Giles et al. (2006) :cite:`giles2006` — MVC-7 test protocol.
    Jones et al. (2010) :cite:`jones2010` — Critical Force / W' model.
    Rohmert (1960) :cite:`rohmert1960` — isometric fatigue curve.
"""

from __future__ import annotations

from climbing_science.edge_depth import normalize_to_reference
from climbing_science.endurance import critical_force
from climbing_science.models import (
    ClimberProfile,
    CriticalForceTest,
    GripType,
    MVC7Test,
)
from climbing_science.strength import rohmert_conversion

__all__ = [
    "from_mvc7_test",
    "from_repeater_test",
    "from_bodyweight_hang",
    "quick_profile",
]


def from_mvc7_test(
    body_weight_kg: float,
    added_weight_kg: float = 0.0,
    hang_time_s: float = 7.0,
    edge_mm: float = 20.0,
    grip_type: GripType = GripType.HALF_CRIMP,
) -> MVC7Test:
    """Create an MVC-7 test result from manual measurement.

    If the hang was not exactly 7 s, the Rohmert fatigue curve is used
    to normalise the result to a 7-second equivalent.

    Args:
        body_weight_kg: Body weight at time of test (kg).
        added_weight_kg: Added weight (positive) or pulley assist (negative).
        hang_time_s: Actual hang duration in seconds.
        edge_mm: Edge depth in mm.
        grip_type: Grip position used.

    Returns:
        :class:`~climbing_science.models.MVC7Test` with computed fields.

    Raises:
        ValueError: If body_weight_kg ≤ 0 or hang_time_s ≤ 0.

    References:
        Giles et al. (2006) :cite:`giles2006`,
        Rohmert (1960) :cite:`rohmert1960`.
    """
    if body_weight_kg <= 0:
        raise ValueError(f"body_weight_kg must be > 0, got {body_weight_kg}")
    if hang_time_s <= 0:
        raise ValueError(f"hang_time_s must be > 0, got {hang_time_s}")

    total_force = body_weight_kg + added_weight_kg

    # Normalise to 7 s using Rohmert curve if duration differs
    if abs(hang_time_s - 7.0) > 0.5:
        total_force = rohmert_conversion(total_force, hang_time_s)

    # Normalise to 20 mm reference edge
    if abs(edge_mm - 20.0) > 0.5:
        total_force = normalize_to_reference(total_force, edge_mm)
        edge_mm = 20.0

    return MVC7Test(
        edge_size_mm=int(round(edge_mm)),
        grip_type=grip_type,
        body_weight_kg=body_weight_kg,
        added_weight_kg=round(total_force - body_weight_kg, 2),
        total_force_kg=round(total_force, 2),
    )


def from_repeater_test(
    body_weight_kg: float,
    mvc7_kg: float,
    t80_s: float,
    t60_s: float,
    t_low_s: float,
    low_pct: float = 0.45,
) -> CriticalForceTest:
    """Create a Critical Force test result from manual 3-point protocol.

    The climber performs 7/3 intermittent repeaters to failure at three
    intensities (typically 80 %, 60 %, 45 % MVC) and records cumulative
    hang time.

    Args:
        body_weight_kg: Body weight (kg).
        mvc7_kg: MVC-7 total force (kg).
        t80_s: Cumulative hang time at 80 % MVC until failure.
        t60_s: Cumulative hang time at 60 % MVC until failure.
        t_low_s: Cumulative hang time at low intensity until failure.
        low_pct: Fraction of MVC for the low-intensity bout (default 0.45).

    Returns:
        :class:`~climbing_science.models.CriticalForceTest`.

    Raises:
        ValueError: If any time ≤ 0 or body_weight_kg ≤ 0.

    References:
        Jones et al. (2010) :cite:`jones2010`,
        Fryer et al. (2018) :cite:`fryer2018`.
    """
    if body_weight_kg <= 0:
        raise ValueError(f"body_weight_kg must be > 0, got {body_weight_kg}")
    for label, val in [("t80_s", t80_s), ("t60_s", t60_s), ("t_low_s", t_low_s)]:
        if val <= 0:
            raise ValueError(f"{label} must be > 0, got {val}")

    intensities = [0.80, 0.60, low_pct]
    times = [t80_s, t60_s, t_low_s]
    forces = [pct * mvc7_kg for pct in intensities]

    # critical_force() expects %MVC intensities, returns (cf_%mvc, w'_%mvc·s, r²)
    intensities_pct = [pct * 100.0 for pct in intensities]
    cf_pct_mvc, w_prime_pct_s, _r2 = critical_force(intensities_pct, times)
    cf_kg = cf_pct_mvc / 100.0 * mvc7_kg
    w_prime_kj = w_prime_pct_s / 100.0 * mvc7_kg / 1000.0

    return CriticalForceTest(
        cf_absolute_kg=round(cf_kg, 2),
        cf_percent_bw=round(cf_kg / body_weight_kg * 100, 1) if body_weight_kg > 0 else None,
        w_prime_kj=round(w_prime_kj, 3),
        cf_mvc_ratio=round(cf_kg / mvc7_kg, 3) if mvc7_kg > 0 else None,
    )


def from_bodyweight_hang(
    body_weight_kg: float,
    hang_time_s: float,
    edge_mm: float = 20.0,
    grip_type: GripType = GripType.HALF_CRIMP,
) -> MVC7Test:
    """Create MVC-7 test from a max-duration bodyweight-only hang.

    Useful for beginners who cannot add weight — the Rohmert curve
    converts the longer hold time into an estimated MVC-7.

    Args:
        body_weight_kg: Body weight (kg).
        hang_time_s: Maximum hang duration achieved (seconds).
        edge_mm: Edge depth in mm.
        grip_type: Grip position used.

    Returns:
        :class:`~climbing_science.models.MVC7Test` with estimated values.

    References:
        Rohmert (1960) :cite:`rohmert1960`.

    Examples:
        >>> mvc = from_bodyweight_hang(70.0, 30.0)
        >>> mvc.edge_size_mm
        20
    """
    return from_mvc7_test(
        body_weight_kg=body_weight_kg,
        added_weight_kg=0.0,
        hang_time_s=hang_time_s,
        edge_mm=edge_mm,
        grip_type=grip_type,
    )


def quick_profile(
    name: str,
    body_weight_kg: float,
    experience_years: float,
    height_cm: float | None = None,
) -> ClimberProfile:
    """Create a minimal ClimberProfile for quick assessments.

    Args:
        name: Athlete name or pseudonym.
        body_weight_kg: Current body weight (kg).
        experience_years: Years of climbing experience.
        height_cm: Height in cm (optional).

    Returns:
        :class:`~climbing_science.models.ClimberProfile`.

    References:
        Profile schema follows Draper et al. (2015) :cite:`draper2015`
        — IRCRA athlete descriptors.

    Examples:
        >>> p = quick_profile("Test", 70.0, 3.0)
        >>> p.name
        'Test'
    """
    return ClimberProfile(
        name=name,
        body_weight_kg=body_weight_kg,
        experience_years=experience_years,
        height_cm=height_cm,
    )
