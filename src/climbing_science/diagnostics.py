"""Diagnostics — athlete profiling, weakness identification, progress tracking.

Classifies climber level, identifies primary limiters from assessment
data, recommends training priorities, and quantifies progress between
assessments.

Data sources:
    - Draper et al. 2015 (:cite:`draper2015`) — IRCRA level classification
    - Lattice Training benchmarks — grade-to-level mapping
    - Fryer et al. 2018 (:cite:`fryer2018`) — CF/MVC ratio interpretation
    - Hörst 2016 (:cite:`horst2016`) — training priority framework
"""

from __future__ import annotations

from climbing_science.grades import GradeSystem, difficulty_index

__all__ = [
    "classify_level",
    "identify_weakness",
    "training_priority",
    "progress_delta",
]


# ---------------------------------------------------------------------------
# Level classification thresholds
# ---------------------------------------------------------------------------
# Based on Draper et al. 2015 (IRCRA) and Lattice Training.
# Uses French sport grade as the canonical reference.
#
# Difficulty index thresholds (from grades.py):
#   6a  = 42
#   6c+ = 54
#   7b  = 65
#   8a  = 76
# ---------------------------------------------------------------------------

_LEVEL_THRESHOLDS: list[tuple[int, str]] = [
    (42, "beginner"),  # below 6a
    (54, "intermediate"),  # 6a – 6c+
    (65, "advanced"),  # 7a – 7b
    (76, "elite"),  # 7b+ – 8a+
]


def classify_level(
    grade_str: str,
    system: GradeSystem = GradeSystem.FRENCH,
) -> str:
    """Classify climber level from their hardest redpoint grade.

    Level boundaries follow the IRCRA descriptors (Draper et al. 2015)
    and Lattice Training grade-to-level mapping:
        - Beginner: below 6a (French) / V2 / 5.10d
        - Intermediate: 6a – 6c+ / V2–V5 / 5.10d–5.12a
        - Advanced: 7a – 7b+ / V5–V8 / 5.12b–5.13a
        - Elite: 7c+ and above / V9+ / 5.13b+

    Args:
        grade_str: Hardest redpoint grade string.
        system: Grading system of the input.

    Returns:
        Level string: "beginner", "intermediate", "advanced", or "elite".

    References:
        Draper et al. 2015 (:cite:`draper2015`),
        Lattice Training benchmarks.

    Examples:
        >>> classify_level("6b", GradeSystem.FRENCH)
        'intermediate'
        >>> classify_level("V8", GradeSystem.V_SCALE)
        'advanced'
        >>> classify_level("5.13c", GradeSystem.YDS)
        'elite'
    """
    idx = difficulty_index(grade_str, system)

    level = "beginner"
    for threshold, label in _LEVEL_THRESHOLDS:
        if idx >= threshold:
            level = label
    return level


def identify_weakness(
    mvc_bw_ratio: float,
    cf_mvc_ratio: float | None = None,
    pull_up_ratio: float | None = None,
) -> list[str]:
    """Identify primary limiters from assessment data.

    Analyses the balance between strength, endurance, and pulling
    power to determine what limits climbing performance.

    Args:
        mvc_bw_ratio: MVC-7 / body weight ratio (e.g. 1.25 for 125%).
        cf_mvc_ratio: Critical Force / MVC-7 ratio (optional, 0–1).
        pull_up_ratio: Max pull-up added weight / body weight (optional).

    Returns:
        List of identified weaknesses, ordered by priority.

    References:
        Fryer et al. 2018 (:cite:`fryer2018`) — CF/MVC interpretation,
        Lattice Training assessment framework.

    Examples:
        >>> identify_weakness(1.0, 0.30)
        ['finger-strength', 'endurance']
        >>> identify_weakness(1.5, 0.45)
        []
    """
    weaknesses = []

    # Finger strength assessment
    if mvc_bw_ratio < 1.0:
        weaknesses.append("finger-strength")
    elif mvc_bw_ratio < 1.3:
        weaknesses.append("finger-strength-moderate")

    # Endurance assessment (if CF data available)
    if cf_mvc_ratio is not None:
        if cf_mvc_ratio < 0.35:
            weaknesses.append("endurance")
        elif cf_mvc_ratio > 0.55 and mvc_bw_ratio < 1.3:
            weaknesses.append("finger-strength-relative")

    # Pulling power (if data available)
    if pull_up_ratio is not None:
        if pull_up_ratio < 0.3:
            weaknesses.append("pulling-power")

    return weaknesses


def training_priority(
    weaknesses: list[str],
) -> str:
    """Recommend primary training focus from identified weaknesses.

    Decision tree:
        1. Finger strength deficits take priority (highest correlation
           with grade — Giles et al. 2019)
        2. Endurance deficits are secondary
        3. Pulling power is tertiary

    Args:
        weaknesses: List of weaknesses from ``identify_weakness``.

    Returns:
        Recommended training category: "max-strength", "strength-endurance",
        "endurance", "pulling", or "maintenance".

    References:
        Hörst 2016 (:cite:`horst2016`),
        Giles et al. 2019.

    Examples:
        >>> training_priority(["finger-strength", "endurance"])
        'max-strength'
        >>> training_priority(["endurance"])
        'endurance'
        >>> training_priority([])
        'maintenance'
    """
    if not weaknesses:
        return "maintenance"

    strength_keywords = ["finger-strength", "finger-strength-moderate", "finger-strength-relative"]
    if any(w in strength_keywords for w in weaknesses):
        return "max-strength"

    if "endurance" in weaknesses:
        return "endurance"

    if "pulling-power" in weaknesses:
        return "pulling"

    return "maintenance"


def progress_delta(
    old_mvc_bw: float,
    new_mvc_bw: float,
    old_grade_idx: float | None = None,
    new_grade_idx: float | None = None,
    old_cf_mvc: float | None = None,
    new_cf_mvc: float | None = None,
) -> dict[str, float]:
    """Quantify progress between two assessments.

    Computes deltas for all available metrics.  Positive values
    indicate improvement.

    Args:
        old_mvc_bw: Previous MVC-7/BW ratio.
        new_mvc_bw: Current MVC-7/BW ratio.
        old_grade_idx: Previous difficulty index (optional).
        new_grade_idx: Current difficulty index (optional).
        old_cf_mvc: Previous CF/MVC ratio (optional).
        new_cf_mvc: Current CF/MVC ratio (optional).

    Returns:
        Dictionary of metric deltas (positive = improvement).

    References:
        Lattice Training progress methodology.

    Examples:
        >>> d = progress_delta(1.20, 1.35)
        >>> d['mvc_bw_delta']
        0.15
    """
    result: dict[str, float] = {
        "mvc_bw_delta": round(new_mvc_bw - old_mvc_bw, 3),
        "mvc_bw_percent_change": round((new_mvc_bw - old_mvc_bw) / old_mvc_bw * 100, 1) if old_mvc_bw > 0 else 0.0,
    }

    if old_grade_idx is not None and new_grade_idx is not None:
        result["grade_idx_delta"] = round(new_grade_idx - old_grade_idx, 1)

    if old_cf_mvc is not None and new_cf_mvc is not None:
        result["cf_mvc_delta"] = round(new_cf_mvc - old_cf_mvc, 3)

    return result
