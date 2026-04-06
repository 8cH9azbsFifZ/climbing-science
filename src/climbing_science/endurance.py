"""Endurance models — Critical Force and anaerobic capacity (W').

Implements the Critical Power / Critical Force model adapted for
climbing-specific intermittent isometric contractions.

Data sources:
    - Jones et al. 2010 (:cite:`jones2010`) — critical power model
    - Fryer et al. 2018 (:cite:`fryer2018`) — forearm oxidative capacity
    - Giles et al. 2019 — finger-flexor critical force in climbers
    - Monod & Scherrer 1965 — original work capacity model
"""

from __future__ import annotations

__all__ = [
    "critical_force",
    "cf_mvc_ratio",
    "interpret_cf_ratio",
    "time_to_failure",
    "classify_endurance",
    "validate_ttf",
    "w_prime_balance",
]


def critical_force(
    intensities_percent_mvc: list[float],
    tlim_seconds: list[float],
) -> tuple[float, float, float]:
    """Compute Critical Force and W' from multi-intensity test data.

    Uses linear regression on the work–time relationship:
    W_total = CF × t_total + W'

    where W_total = intensity × t_lim for each test bout.

    Requires at least 2 data points (typically 3: e.g. 80%, 60%, 45% MVC).

    Args:
        intensities_percent_mvc: List of test intensities as %MVC
            (e.g. [80.0, 60.0, 45.0]).
        tlim_seconds: Corresponding cumulative hang times to failure
            in seconds (e.g. [77.0, 136.0, 323.0]).

    Returns:
        Tuple of (cf_percent_mvc, w_prime_pct_s, r_squared):
            - cf_percent_mvc: Critical Force as %MVC.
            - w_prime_pct_s: W' in %MVC × seconds.
            - r_squared: Coefficient of determination of the linear fit.

    Raises:
        ValueError: If fewer than 2 data points or mismatched lengths.

    References:
        Jones et al. 2010 (:cite:`jones2010`),
        Monod & Scherrer 1965.

    Examples:
        >>> cf, wp, r2 = critical_force([80.0, 60.0, 45.0], [77.0, 136.0, 323.0])
        >>> round(cf, 1)
        35.2
    """
    if len(intensities_percent_mvc) != len(tlim_seconds):
        raise ValueError("intensities and tlim must have the same length")
    if len(intensities_percent_mvc) < 2:
        raise ValueError("Need at least 2 data points for CF regression")

    n = len(intensities_percent_mvc)
    # W_total = intensity * tlim  (work done at each intensity)
    work = [intensities_percent_mvc[i] * tlim_seconds[i] for i in range(n)]
    t = list(tlim_seconds)

    # Linear regression: W = CF * t + W'
    # Using least squares: CF = slope, W' = intercept
    sum_t = sum(t)
    sum_w = sum(work)
    sum_tt = sum(ti * ti for ti in t)
    sum_tw = sum(t[i] * work[i] for i in range(n))

    denom = n * sum_tt - sum_t * sum_t
    if denom == 0:
        raise ValueError("Degenerate data: all tlim values are identical")

    cf = (n * sum_tw - sum_t * sum_w) / denom
    w_prime = (sum_w - cf * sum_t) / n

    # R² calculation
    mean_w = sum_w / n
    ss_tot = sum((work[i] - mean_w) ** 2 for i in range(n))
    ss_res = sum((work[i] - (cf * t[i] + w_prime)) ** 2 for i in range(n))
    r_squared = 1.0 - (ss_res / ss_tot) if ss_tot > 0 else 0.0

    return round(cf, 2), round(w_prime, 2), round(r_squared, 4)


def cf_mvc_ratio(cf_percent_mvc: float, mvc7_percent_bw: float) -> float:
    """Calculate the CF/MVC-7 ratio — the primary endurance diagnostic.

    This ratio determines whether a climber is strength-limited or
    endurance-limited, guiding training priority.

    Args:
        cf_percent_mvc: Critical Force as %MVC (from critical_force()).
        mvc7_percent_bw: MVC-7 as %BW (from strength assessment).

    Returns:
        Ratio as a float (typically 0.25–0.65).

    Raises:
        ValueError: If mvc7 is zero or negative.

    References:
        Fryer et al. 2018 (:cite:`fryer2018`),
        Lattice Training diagnostic framework.

    Examples:
        >>> cf_mvc_ratio(35.0, 100.0)
        0.35
    """
    if mvc7_percent_bw <= 0:
        raise ValueError("mvc7_percent_bw must be positive")
    if cf_percent_mvc < 0:
        raise ValueError("cf_percent_mvc must be non-negative")
    return round(cf_percent_mvc / mvc7_percent_bw, 2)


def interpret_cf_ratio(ratio: float) -> dict[str, str]:
    """Interpret the CF/MVC-7 ratio for training recommendations.

    Args:
        ratio: CF/MVC-7 ratio (0–1).

    Returns:
        Dict with keys:
            - ``category``: "strength-limited", "balanced", or "endurance-limited"
            - ``interpretation``: human-readable explanation
            - ``priority``: recommended training focus

    References:
        Fryer et al. 2018 (:cite:`fryer2018`),
        Lattice Training diagnostic framework.

    Examples:
        >>> interpret_cf_ratio(0.30)["category"]
        'endurance-limited'
        >>> interpret_cf_ratio(0.55)["category"]
        'strength-limited'
    """
    if ratio > 0.50:
        return {
            "category": "strength-limited",
            "interpretation": (
                f"CF/MVC ratio {ratio:.0%} is high — endurance is adequate. Finger strength is the primary limiter."
            ),
            "priority": "MaxHangs, limit bouldering, weighted pull-ups",
        }
    elif ratio >= 0.35:
        return {
            "category": "balanced",
            "interpretation": (
                f"CF/MVC ratio {ratio:.0%} — balanced profile. Both strength and endurance contribute roughly equally."
            ),
            "priority": "Mixed training — alternate strength and endurance blocks",
        }
    else:
        return {
            "category": "endurance-limited",
            "interpretation": (
                f"CF/MVC ratio {ratio:.0%} is low — endurance is the primary limiter. "
                "Prioritise repeaters and aerobic capacity work."
            ),
            "priority": "Repeaters (7/3), ARC training, SubHangs, density hangs",
        }


def time_to_failure(
    force_percent_mvc: float,
    cf_percent_mvc: float,
    w_prime_pct_s: float,
) -> float:
    """Predict time to failure for a given force above Critical Force.

    Based on the hyperbolic relationship:
        t_lim = W' / (F - CF)

    Only valid when force > CF.  At or below CF, endurance is
    theoretically infinite.

    Args:
        force_percent_mvc: Applied force as %MVC.
        cf_percent_mvc: Critical Force as %MVC.
        w_prime_pct_s: W' in %MVC × seconds.

    Returns:
        Predicted time to failure in seconds.

    Raises:
        ValueError: If force <= CF (infinite endurance).

    References:
        Jones et al. 2010 (:cite:`jones2010`),
        Poole et al. 2016.

    Examples:
        >>> round(time_to_failure(80.0, 35.0, 2000.0), 1)
        44.4
    """
    if force_percent_mvc <= cf_percent_mvc:
        raise ValueError(
            f"Force ({force_percent_mvc}% MVC) must exceed CF ({cf_percent_mvc}% MVC) "
            "for time-to-failure prediction. At or below CF, endurance is theoretically infinite."
        )
    if w_prime_pct_s <= 0:
        raise ValueError("W' must be positive")

    return w_prime_pct_s / (force_percent_mvc - cf_percent_mvc)


def classify_endurance(
    cf_mvc_ratio: float,
) -> str:
    """Classify athlete endurance profile from CF/MVC ratio.

    The CF/MVC ratio indicates the balance between aerobic endurance
    and maximal strength:
        - Low ratio: strength-dominant (boulderer profile)
        - High ratio: endurance-dominant (sport climber profile)

    Args:
        cf_mvc_ratio: Ratio of Critical Force to MVC-7 (0–1).

    Returns:
        Classification string: one of
        "strength-dominant", "balanced", "endurance-dominant".

    References:
        Fryer et al. 2018 (:cite:`fryer2018`).

    Examples:
        >>> classify_endurance(0.30)
        'strength-dominant'
        >>> classify_endurance(0.42)
        'balanced'
        >>> classify_endurance(0.55)
        'endurance-dominant'
    """
    if cf_mvc_ratio < 0 or cf_mvc_ratio > 1:
        raise ValueError(f"cf_mvc_ratio must be in [0, 1], got {cf_mvc_ratio}")

    if cf_mvc_ratio < 0.35:
        return "strength-dominant"
    elif cf_mvc_ratio <= 0.50:
        return "balanced"
    else:
        return "endurance-dominant"


def w_prime_balance(
    w_prime_pct_s: float,
    cf_percent_mvc: float,
    forces_percent_mvc: list[float],
    durations_sec: list[float],
) -> list[float]:
    """Track W' depletion across a series of efforts.

    Implements a simplified W' balance model for intermittent climbing.
    Each effort above CF depletes W'; rest at or below CF allows
    partial reconstitution.

    Args:
        w_prime_pct_s: Initial W' capacity in %MVC × seconds.
        cf_percent_mvc: Critical Force as %MVC.
        forces_percent_mvc: Force applied in each interval as %MVC.
        durations_sec: Duration of each interval in seconds.

    Returns:
        List of W' remaining after each interval.

    Raises:
        ValueError: If input lengths don't match.

    References:
        Skiba et al. 2012 — W' balance concept,
        Jones et al. 2010 (:cite:`jones2010`).

    Examples:
        >>> w_prime_balance(2000.0, 35.0, [80.0, 0.0, 80.0], [10.0, 60.0, 10.0])
        [1550.0, 2000.0, 1550.0]
    """
    if len(forces_percent_mvc) != len(durations_sec):
        raise ValueError("forces and durations must have the same length")

    balance = w_prime_pct_s
    result = []

    for force, duration in zip(forces_percent_mvc, durations_sec):
        if force > cf_percent_mvc:
            # Depletion
            expenditure = (force - cf_percent_mvc) * duration
            balance = max(0.0, balance - expenditure)
        else:
            # Reconstitution (simplified: full recovery up to W' max)
            # More sophisticated models use exponential recovery (Skiba 2012)
            recovery_rate = (cf_percent_mvc - force) if force < cf_percent_mvc else 0.0
            balance = min(w_prime_pct_s, balance + recovery_rate * duration)

        result.append(round(balance, 1))

    return result


def validate_ttf(
    predicted_s: float,
    actual_s: float,
) -> dict[str, object]:
    """Compare model-predicted TtF with actual measured TtF.

    Assesses how well the Critical Force model (Jones et al. 2010)
    predicts actual time-to-failure from a force-gauge test.

    Args:
        predicted_s: Model-predicted time to failure in seconds
            (from :func:`time_to_failure`).
        actual_s: Actual measured time to failure in seconds
            (from :func:`~climbing_science.signal.extract_ttf`).

    Returns:
        Dict with keys:
            - ``predicted_s``: The predicted value.
            - ``actual_s``: The actual value.
            - ``absolute_error_s``: ``|predicted - actual|``.
            - ``relative_error_pct``: Relative error as percentage of actual.
            - ``model_quality``: "excellent" (≤10%), "good" (≤20%),
              "fair" (≤35%), or "poor" (>35%).

    Raises:
        ValueError: If either value is negative.

    References:
        Jones et al. 2010 (:cite:`jones2010`) — critical power model
        predicts t_lim = W' / (F - CF).

    Examples:
        >>> validate_ttf(44.4, 42.0)["model_quality"]
        'excellent'
        >>> validate_ttf(44.4, 42.0)["absolute_error_s"]
        2.4
    """
    if predicted_s < 0:
        raise ValueError(f"predicted_s must be non-negative, got {predicted_s}")
    if actual_s < 0:
        raise ValueError(f"actual_s must be non-negative, got {actual_s}")

    abs_error = abs(predicted_s - actual_s)

    if actual_s > 0:
        rel_error = (abs_error / actual_s) * 100.0
    else:
        rel_error = float("inf") if predicted_s > 0 else 0.0

    if rel_error <= 10.0:
        quality = "excellent"
    elif rel_error <= 20.0:
        quality = "good"
    elif rel_error <= 35.0:
        quality = "fair"
    else:
        quality = "poor"

    return {
        "predicted_s": round(predicted_s, 2),
        "actual_s": round(actual_s, 2),
        "absolute_error_s": round(abs_error, 2),
        "relative_error_pct": round(rel_error, 1),
        "model_quality": quality,
    }
