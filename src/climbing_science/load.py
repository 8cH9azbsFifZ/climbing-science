"""Training load calculation — TUT, RPE, ACWR, and overtraining detection.

Quantifies training stress from hangboard and climbing sessions:
- Time Under Tension (TUT) per set, session, and week
- RPE ↔ %MVC ↔ Effort Level conversions
- Acute:Chronic Workload Ratio (ACWR) for injury prevention
- Margin to Failure for progression steering

Data sources:
    - López-Rivera 2014 (:cite:`lopez2014`) — TUT methodology, Effort Levels
    - Gabbett 2016 (:cite:`gabbett2016`) — ACWR framework
    - Rohmert 1960 (:cite:`rohmert1960`) — static endurance baseline
"""

from __future__ import annotations

__all__ = [
    "tut_per_set",
    "tut_per_session",
    "rpe_to_mvc_pct",
    "mvc_pct_to_rpe",
    "effort_level_to_mvc_pct",
    "acwr",
    "overtraining_check",
    "margin_to_failure",
    "weekly_load",
]


# ---------------------------------------------------------------------------
# RPE ↔ %MVC ↔ Effort Level mapping
# ---------------------------------------------------------------------------
# López Effort Level scale maps subjective effort to objective %MVC.
# Interpolated from López-Rivera 2014 (:cite:`lopez2014`).
#
# Format: (effort_level_percent, approximate_mvc_percent)
# ---------------------------------------------------------------------------

_EL_TO_MVC: list[tuple[float, float]] = [
    (50.0, 50.0),
    (60.0, 60.0),
    (70.0, 70.0),
    (75.0, 75.0),
    (80.0, 80.0),
    (85.0, 85.0),
    (90.0, 90.0),
    (95.0, 95.0),
    (100.0, 100.0),
]

# RPE (1-10 Borg CR-10 scale) to approximate %MVC
_RPE_TO_MVC: list[tuple[float, float]] = [
    (1.0, 20.0),
    (2.0, 30.0),
    (3.0, 40.0),
    (4.0, 50.0),
    (5.0, 60.0),
    (6.0, 70.0),
    (7.0, 75.0),
    (8.0, 85.0),
    (9.0, 92.0),
    (10.0, 100.0),
]


def _lerp(x: float, table: list[tuple[float, float]]) -> float:
    """Linear interpolation on a sorted (x, y) table."""
    if x <= table[0][0]:
        return table[0][1]
    if x >= table[-1][0]:
        return table[-1][1]
    for i in range(len(table) - 1):
        x0, y0 = table[i]
        x1, y1 = table[i + 1]
        if x0 <= x <= x1:
            t = (x - x0) / (x1 - x0) if x1 != x0 else 0.0
            return y0 + t * (y1 - y0)
    return table[-1][1]


def _inverse_lerp(y: float, table: list[tuple[float, float]]) -> float:
    """Inverse interpolation: given y, find x."""
    if y <= table[0][1]:
        return table[0][0]
    if y >= table[-1][1]:
        return table[-1][0]
    for i in range(len(table) - 1):
        x0, y0 = table[i]
        x1, y1 = table[i + 1]
        if y0 <= y <= y1:
            t = (y - y0) / (y1 - y0) if y1 != y0 else 0.0
            return x0 + t * (x1 - x0)
    return table[-1][0]


# ---------------------------------------------------------------------------
# TUT (Time Under Tension)
# ---------------------------------------------------------------------------


def tut_per_set(
    hang_duration_sec: float,
    reps_per_set: int,
    rest_between_reps_sec: float = 0.0,
) -> float:
    """Calculate Time Under Tension for a single set.

    TUT counts only the time the muscle is loaded (hang time),
    not the rest between reps.

    Args:
        hang_duration_sec: Duration of each hang in seconds.
        reps_per_set: Number of hangs per set.
        rest_between_reps_sec: Unused for TUT (documented for clarity).

    Returns:
        TUT in seconds for one set.

    References:
        López-Rivera 2014 (:cite:`lopez2014`).

    Examples:
        >>> tut_per_set(10.0, 1)
        10.0
        >>> tut_per_set(7.0, 6)
        42.0
    """
    if hang_duration_sec <= 0:
        raise ValueError("hang_duration_sec must be positive")
    if reps_per_set < 1:
        raise ValueError("reps_per_set must be >= 1")
    return round(hang_duration_sec * reps_per_set, 1)


def tut_per_session(
    hang_duration_sec: float,
    reps_per_set: int,
    num_sets: int,
) -> float:
    """Calculate total TUT for a hangboard session.

    Args:
        hang_duration_sec: Duration of each hang.
        reps_per_set: Hangs per set.
        num_sets: Number of sets.

    Returns:
        Total TUT in seconds.

    References:
        López-Rivera 2014 (:cite:`lopez2014`).

    Examples:
        >>> tut_per_session(10.0, 1, 4)
        40.0
        >>> tut_per_session(7.0, 6, 5)
        210.0
    """
    if num_sets < 1:
        raise ValueError("num_sets must be >= 1")
    return round(tut_per_set(hang_duration_sec, reps_per_set) * num_sets, 1)


# ---------------------------------------------------------------------------
# RPE ↔ %MVC conversions
# ---------------------------------------------------------------------------


def rpe_to_mvc_pct(rpe: float) -> float:
    """Convert RPE (1–10) to approximate %MVC.

    Uses the modified Borg CR-10 scale adapted for climbing.

    Args:
        rpe: Rating of Perceived Exertion (1–10).

    Returns:
        Approximate %MVC.

    References:
        López-Rivera 2014 (:cite:`lopez2014`) — Effort Level scale.

    Examples:
        >>> rpe_to_mvc_pct(8.0)
        85.0
    """
    if rpe < 1.0 or rpe > 10.0:
        raise ValueError(f"RPE must be in [1, 10], got {rpe}")
    return round(_lerp(rpe, _RPE_TO_MVC), 1)


def mvc_pct_to_rpe(mvc_pct: float) -> float:
    """Convert %MVC to approximate RPE (1–10).

    Inverse of ``rpe_to_mvc_pct()``.

    Args:
        mvc_pct: Force as percentage of MVC.

    Returns:
        Approximate RPE on 1–10 scale.

    References:
        López-Rivera 2014 (:cite:`lopez2014`).

    Examples:
        >>> mvc_pct_to_rpe(85.0)
        8.0
    """
    if mvc_pct < 0 or mvc_pct > 100:
        raise ValueError(f"mvc_pct must be in [0, 100], got {mvc_pct}")
    return round(_inverse_lerp(mvc_pct, _RPE_TO_MVC), 1)


def effort_level_to_mvc_pct(effort_level: float) -> float:
    """Convert López Effort Level (%) to %MVC.

    The Effort Level scale is approximately 1:1 with %MVC
    in the 50–100% range, but this function allows for
    future non-linear refinements.

    Args:
        effort_level: López Effort Level (50–100%).

    Returns:
        Corresponding %MVC.

    References:
        López-Rivera 2014 (:cite:`lopez2014`).

    Examples:
        >>> effort_level_to_mvc_pct(90.0)
        90.0
    """
    if effort_level < 0 or effort_level > 100:
        raise ValueError(f"effort_level must be in [0, 100], got {effort_level}")
    return round(_lerp(effort_level, _EL_TO_MVC), 1)


# ---------------------------------------------------------------------------
# ACWR and overtraining
# ---------------------------------------------------------------------------


def acwr(acute_load: float, chronic_load: float) -> float:
    """Calculate Acute:Chronic Workload Ratio.

    ACWR = acute_load / chronic_load

    The "sweet spot" is 0.8–1.3. Below 0.8 indicates detraining;
    above 1.5 indicates high injury risk.

    Args:
        acute_load: Training load for the current week (e.g. total TUT).
        chronic_load: Average training load over past 4 weeks.

    Returns:
        ACWR ratio.

    Raises:
        ValueError: If chronic_load is zero.

    References:
        Gabbett 2016 (:cite:`gabbett2016`) — training-injury paradox.

    Examples:
        >>> acwr(600.0, 500.0)
        1.2
    """
    if chronic_load <= 0:
        raise ValueError("chronic_load must be positive")
    if acute_load < 0:
        raise ValueError("acute_load must be non-negative")
    return round(acute_load / chronic_load, 2)


def overtraining_check(
    weekly_loads: list[float],
) -> dict[str, object]:
    """Assess overtraining risk from recent weekly training loads.

    Computes ACWR from the most recent week vs the 4-week rolling average,
    and returns a traffic-light assessment.

    Args:
        weekly_loads: List of weekly TUT values (most recent last).
            Needs at least 2 weeks of data.

    Returns:
        Dict with keys:
            - ``acwr``: the computed ratio
            - ``status``: "green", "yellow", or "red"
            - ``message``: human-readable recommendation

    References:
        Gabbett 2016 (:cite:`gabbett2016`).

    Examples:
        >>> overtraining_check([400, 450, 500, 600])["status"]
        'green'
    """
    if len(weekly_loads) < 2:
        raise ValueError("Need at least 2 weeks of data")

    acute = weekly_loads[-1]
    chronic_weeks = weekly_loads[max(0, len(weekly_loads) - 5) : -1]
    chronic = sum(chronic_weeks) / len(chronic_weeks) if chronic_weeks else acute

    if chronic <= 0:
        return {
            "acwr": 0.0,
            "status": "yellow",
            "message": "No baseline load — cannot compute ACWR. Start tracking.",
        }

    ratio = round(acute / chronic, 2)

    if ratio < 0.8:
        return {
            "acwr": ratio,
            "status": "yellow",
            "message": f"ACWR {ratio} — undertraining. Load is well below baseline. Risk of detraining.",
        }
    elif ratio <= 1.3:
        return {
            "acwr": ratio,
            "status": "green",
            "message": f"ACWR {ratio} — sweet spot. Training load is well managed.",
        }
    elif ratio <= 1.5:
        return {
            "acwr": ratio,
            "status": "yellow",
            "message": f"ACWR {ratio} — caution. Approaching high-risk zone. Consider reducing volume.",
        }
    else:
        return {
            "acwr": ratio,
            "status": "red",
            "message": f"ACWR {ratio} — high injury risk! Reduce load immediately.",
        }


def margin_to_failure(
    actual_hang_sec: float,
    max_hang_sec: float,
) -> float:
    """Calculate Margin to Failure (MTF) for progression steering.

    MTF = max_hang - actual_hang. Used in López MaxHang methodology
    to determine when to increase load.

    Progression rule: when MTF consistently > 5s, increase load.

    Args:
        actual_hang_sec: Prescribed hang duration.
        max_hang_sec: Maximum possible hang duration at current load.

    Returns:
        Margin to failure in seconds.

    References:
        López-Rivera 2014 (:cite:`lopez2014`).

    Examples:
        >>> margin_to_failure(10.0, 13.0)
        3.0
    """
    if actual_hang_sec <= 0 or max_hang_sec <= 0:
        raise ValueError("Durations must be positive")
    return round(max_hang_sec - actual_hang_sec, 1)


def weekly_load(
    sessions: list[dict[str, float]],
) -> dict[str, float]:
    """Aggregate weekly training volume from session data.

    Args:
        sessions: List of dicts with keys:
            - ``tut_sec``: total TUT for the session
            - ``rpe``: session RPE (1–10)

    Returns:
        Dict with:
            - ``total_tut_sec``: sum of all session TUT
            - ``num_sessions``: number of sessions
            - ``avg_rpe``: average RPE across sessions
            - ``training_load``: sum of (TUT × RPE) — session load metric

    References:
        Gabbett 2016 (:cite:`gabbett2016`).

    Examples:
        >>> weekly_load([{"tut_sec": 120, "rpe": 8}, {"tut_sec": 90, "rpe": 7}])
        {'total_tut_sec': 210.0, 'num_sessions': 2, 'avg_rpe': 7.5, 'training_load': 1590.0}
    """
    if not sessions:
        return {"total_tut_sec": 0.0, "num_sessions": 0, "avg_rpe": 0.0, "training_load": 0.0}

    total_tut = sum(s["tut_sec"] for s in sessions)
    avg_rpe = sum(s["rpe"] for s in sessions) / len(sessions)
    training_load = sum(s["tut_sec"] * s["rpe"] for s in sessions)

    return {
        "total_tut_sec": round(total_tut, 1),
        "num_sessions": len(sessions),
        "avg_rpe": round(avg_rpe, 1),
        "training_load": round(training_load, 1),
    }
