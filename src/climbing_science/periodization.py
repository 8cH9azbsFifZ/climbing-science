"""Periodization — macro, meso, and microcycle generation.

Generates training plans at three levels of granularity:
macro (annual), meso (4–8 week blocks), and micro (weekly).

Data sources:
    - Hörst 2016 (:cite:`horst2016`) — annual periodization
    - Anderson & Anderson 2014 (:cite:`anderson2014`) — mesocycle planning
    - López-Rivera 2014 (:cite:`lopez2014`) — 4-week cycles, deload principles
"""

from __future__ import annotations

from dataclasses import dataclass, field

__all__ = [
    "Phase",
    "MesoCycle",
    "MicroCycle",
    "MacroCycle",
    "generate_macrocycle",
    "generate_mesocycle",
    "generate_microcycle",
    "validate_constraints",
]


@dataclass
class Phase:
    """Training phase within a macrocycle.

    Attributes:
        name: Phase name (e.g. "base", "strength", "power", "performance", "rest").
        duration_weeks: Length of the phase in weeks.
        focus: Primary training focus description.
        intensity: Relative intensity level ("low", "moderate", "high", "max").
        volume: Relative volume level ("low", "moderate", "high").

    References:
        Hörst 2016 (:cite:`horst2016`) — phase definitions.
    """

    name: str
    duration_weeks: int
    focus: str
    intensity: str = "moderate"
    volume: str = "moderate"


@dataclass
class MesoCycle:
    """4–8 week training block with weekly progression and deload.

    Attributes:
        phase: Training phase this mesocycle belongs to.
        weeks: Number of weeks (typically 4).
        weekly_sessions: Sessions per week for each week.
        weekly_volume_tut: TUT in seconds per week for each week.
        weekly_intensity: Relative intensity descriptor per week.
        deload_week: Which week is the deload (0-indexed), or None.

    References:
        López-Rivera 2014 (:cite:`lopez2014`) — 4-week cycle model.
    """

    phase: str
    weeks: int
    weekly_sessions: list[int] = field(default_factory=list)
    weekly_volume_tut: list[float] = field(default_factory=list)
    weekly_intensity: list[str] = field(default_factory=list)
    deload_week: int | None = None


@dataclass
class MicroCycle:
    """Weekly session plan.

    Attributes:
        week_number: Week number within the mesocycle (1-based).
        sessions_per_week: Number of hangboard sessions.
        session_tut_sec: Target TUT per session in seconds.
        intensity: Relative intensity descriptor.
        is_deload: Whether this is a deload week.
        notes: Additional guidance.

    References:
        López-Rivera 2014 (:cite:`lopez2014`).
    """

    week_number: int
    sessions_per_week: int
    session_tut_sec: float
    intensity: str
    is_deload: bool = False
    notes: str = ""


@dataclass
class MacroCycle:
    """Annual training plan composed of phases.

    Attributes:
        name: Plan name / identifier.
        total_weeks: Total duration in weeks.
        phases: Ordered list of training phases.

    References:
        Hörst 2016 (:cite:`horst2016`) — annual planning model.
    """

    name: str
    total_weeks: int
    phases: list[Phase] = field(default_factory=list)


def generate_macrocycle(
    total_weeks: int = 52,
    peak_week: int | None = None,
    name: str = "annual-plan",
) -> MacroCycle:
    """Generate an annual macrocycle with standard phase distribution.

    Phase distribution follows Hörst (2016):
        - Base/Hypertrophy: ~25%
        - Max Strength: ~25%
        - Power/Power-Endurance: ~25%
        - Performance/Peak: ~15%
        - Rest/Transition: ~10%

    Args:
        total_weeks: Total plan duration in weeks (default: 52).
        peak_week: Target week for peak performance (optional).
        name: Plan identifier.

    Returns:
        MacroCycle with phases.

    References:
        Hörst 2016 (:cite:`horst2016`).

    Examples:
        >>> mc = generate_macrocycle(52)
        >>> sum(p.duration_weeks for p in mc.phases)
        52
    """
    # Standard distribution
    base_weeks = max(4, round(total_weeks * 0.25))
    strength_weeks = max(4, round(total_weeks * 0.25))
    power_weeks = max(4, round(total_weeks * 0.25))
    performance_weeks = max(2, round(total_weeks * 0.15))
    rest_weeks = total_weeks - base_weeks - strength_weeks - power_weeks - performance_weeks

    if rest_weeks < 1:
        rest_weeks = 1
        performance_weeks = total_weeks - base_weeks - strength_weeks - power_weeks - rest_weeks

    phases = [
        Phase("base", base_weeks, "General fitness, volume accumulation", "low", "high"),
        Phase("strength", strength_weeks, "Max finger strength, hangboard focus", "high", "moderate"),
        Phase("power", power_weeks, "Power-endurance, campus, limit bouldering", "high", "moderate"),
        Phase("performance", performance_weeks, "Peak performance, outdoor projects", "max", "low"),
        Phase("rest", rest_weeks, "Active recovery, cross-training", "low", "low"),
    ]

    return MacroCycle(name=name, total_weeks=total_weeks, phases=phases)


def generate_mesocycle(
    phase: str = "strength",
    weeks: int = 4,
    sessions_per_week: int = 3,
    base_tut_sec: float = 200.0,
) -> MesoCycle:
    """Generate a mesocycle with progressive overload and deload.

    Follows the López 4-week cycle model:
        Week 1: Introduction (moderate)
        Week 2: Loading (high)
        Week 3: Peak (highest)
        Week 4: Deload (reduced)

    The constraint "never increase volume, intensity, and frequency
    simultaneously" is enforced by only increasing volume across weeks
    while keeping intensity and frequency stable.

    Args:
        phase: Training phase ("base", "strength", "power", "performance").
        weeks: Number of weeks (typically 4).
        sessions_per_week: Hangboard sessions per week.
        base_tut_sec: Baseline TUT per session in seconds.

    Returns:
        MesoCycle with weekly progression.

    References:
        López-Rivera 2014 (:cite:`lopez2014`),
        Anderson & Anderson 2014 (:cite:`anderson2014`).

    Examples:
        >>> mc = generate_mesocycle("strength", 4, 3, 200.0)
        >>> mc.deload_week
        3
    """
    if weeks < 2:
        raise ValueError("Mesocycle must be at least 2 weeks")

    # Progressive volume with deload in final week
    volume_multipliers = {
        2: [1.0, 0.6],
        3: [0.85, 1.0, 0.6],
        4: [0.85, 1.0, 1.15, 0.6],
        5: [0.80, 0.90, 1.0, 1.10, 0.6],
        6: [0.75, 0.85, 0.95, 1.0, 1.10, 0.6],
        7: [0.70, 0.80, 0.90, 0.95, 1.0, 1.10, 0.6],
        8: [0.70, 0.80, 0.85, 0.90, 0.95, 1.0, 1.10, 0.6],
    }

    multipliers = volume_multipliers.get(weeks, volume_multipliers[4])
    if weeks > 8:
        multipliers = [0.6 + (0.5 * i / (weeks - 2)) for i in range(weeks - 1)] + [0.6]

    intensity_map = {
        "base": "moderate",
        "strength": "high",
        "power": "high",
        "performance": "max",
    }
    base_intensity = intensity_map.get(phase, "moderate")

    weekly_sessions = []
    weekly_volume = []
    weekly_intensity = []
    for i, mult in enumerate(multipliers):
        is_deload = i == weeks - 1
        weekly_sessions.append(max(1, sessions_per_week - 1) if is_deload else sessions_per_week)
        weekly_volume.append(round(base_tut_sec * sessions_per_week * mult, 1))
        weekly_intensity.append("low" if is_deload else base_intensity)

    return MesoCycle(
        phase=phase,
        weeks=weeks,
        weekly_sessions=weekly_sessions,
        weekly_volume_tut=weekly_volume,
        weekly_intensity=weekly_intensity,
        deload_week=weeks - 1,
    )


def generate_microcycle(
    sessions_per_week: int = 3,
    tut_per_session_sec: float = 200.0,
    intensity: str = "moderate",
    is_deload: bool = False,
    week_number: int = 1,
) -> MicroCycle:
    """Generate a weekly microcycle.

    Args:
        sessions_per_week: Number of hangboard sessions this week.
        tut_per_session_sec: Target TUT per session in seconds.
        intensity: Intensity descriptor.
        is_deload: Whether this is a deload week.
        week_number: Week number within the mesocycle.

    Returns:
        MicroCycle with session plan.

    References:
        López-Rivera 2014 (:cite:`lopez2014`).

    Examples:
        >>> mc = generate_microcycle(3, 200.0, "high", False, 2)
        >>> mc.sessions_per_week
        3
    """
    if is_deload:
        sessions_per_week = max(1, sessions_per_week - 1)
        tut_per_session_sec = round(tut_per_session_sec * 0.6, 1)
        intensity = "low"

    return MicroCycle(
        week_number=week_number,
        sessions_per_week=sessions_per_week,
        session_tut_sec=tut_per_session_sec,
        intensity=intensity,
        is_deload=is_deload,
        notes="Deload: reduce volume, maintain technique" if is_deload else "",
    )


def validate_constraints(
    volumes: list[float],
    intensities: list[float],
    frequencies: list[int],
) -> list[str]:
    """Check training progression constraints.

    The López principle: never increase volume, intensity, AND frequency
    simultaneously between consecutive weeks.

    Args:
        volumes: Weekly volume (e.g. TUT in seconds).
        intensities: Weekly intensity (e.g. %MVC or RPE).
        frequencies: Weekly session counts.

    Returns:
        List of violation messages (empty if all constraints pass).

    References:
        López-Rivera 2014 (:cite:`lopez2014`).

    Examples:
        >>> validate_constraints([100, 120, 140], [80, 85, 90], [2, 3, 4])
        ['Week 2→3: volume, intensity, and frequency all increased simultaneously']
    """
    if not (len(volumes) == len(intensities) == len(frequencies)):
        raise ValueError("All input lists must have the same length")

    violations = []
    for i in range(len(volumes) - 1):
        vol_up = volumes[i + 1] > volumes[i]
        int_up = intensities[i + 1] > intensities[i]
        freq_up = frequencies[i + 1] > frequencies[i]

        if vol_up and int_up and freq_up:
            violations.append(f"Week {i + 1}→{i + 2}: volume, intensity, and frequency all increased simultaneously")

    return violations
