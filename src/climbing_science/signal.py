"""Force-curve signal processing — smoothing, peak detection, RFD, MVC-7.

Pure-math module for analysing time-series data from climbing force
measurement devices.  All functions operate on plain Python lists and
use only the standard library (no numpy / scipy required).

Typical sampling rates for climbing force gauges are 40–200 Hz.  A rate
of ≥ 80 Hz is recommended for accurate RFD calculation.

References:
    Levernier & Laffaye (2019) :cite:`levernier2019`
    — *Four weeks of finger grip training increases the rate of force
    development and the maximal force in elite and top world-ranking
    climbers.* JSCR, 33(9), 2471–2480.

    Jones et al. (2010) :cite:`jones2010`
    — *Critical power: implications for determination of VO2max and
    exercise tolerance.* MSSE, 42(10), 1876–1890.

    Fryer et al. (2018) :cite:`fryer2018`
    — *Forearm muscle oxidative capacity index predicts sport
    rock-climbing performance.* Eur J Appl Physiol, 118(5), 1083–1091.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

__all__ = [
    "Peak",
    "RFDResult",
    "SegmentedRep",
    "best_n_second_average",
    "compute_impulse",
    "compute_rfd",
    "detect_peaks",
    "extract_ttf",
    "segment_repeaters",
    "smooth",
]

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Peak:
    """A detected force peak in a time series.

    Attributes:
        start_idx: Index where force first exceeds the threshold.
        end_idx: Index where force drops below the threshold.
        peak_idx: Index of the maximum force value.
        peak_value: Maximum force in kg within this peak.
        duration_s: Peak duration in seconds.
        mean_value: Mean force in kg over the peak region.

    References:
        Levernier & Laffaye (2019) :cite:`levernier2019`
    """

    start_idx: int
    end_idx: int
    peak_idx: int
    peak_value: float
    duration_s: float
    mean_value: float


@dataclass(frozen=True)
class RFDResult:
    """Rate of Force Development analysis result.

    References:
        Levernier & Laffaye (2019) :cite:`levernier2019`
    """

    peak_rfd_kg_s: float
    """Maximum instantaneous RFD (kg/s) within the analysis window."""

    avg_rfd_kg_s: float
    """Average RFD (kg/s) over the analysis window."""

    time_to_peak_s: float
    """Time from force onset to peak force."""

    onset_idx: int
    """Index of detected force onset."""

    peak_idx: int
    """Index of peak force."""


@dataclass(frozen=True)
class SegmentedRep:
    """A single repetition extracted from an intermittent protocol.

    References:
        Fryer et al. (2018) :cite:`fryer2018`
    """

    rep_number: int
    start_idx: int
    end_idx: int
    work_duration_s: float
    mean_force_kg: float
    peak_force_kg: float


# ---------------------------------------------------------------------------
# Smoothing
# ---------------------------------------------------------------------------


def smooth(
    values: list[float],
    sample_rate_hz: float,
    method: str = "moving_average",
    window_ms: float = 50.0,
) -> list[float]:
    """Smooth a force signal.

    Args:
        values: Raw force values in kg.
        sample_rate_hz: Sampling rate in Hz.
        method: ``"moving_average"`` or ``"exponential"``.
        window_ms: Window size in milliseconds.

    Returns:
        Smoothed force values (same length as input).

    Raises:
        ValueError: If *values* is empty, *sample_rate_hz* ≤ 0, or
            *method* is unknown.

    References:
        Levernier & Laffaye (2019) :cite:`levernier2019`
        — used 50 ms smoothing window for force curve analysis.
    """
    if not values:
        raise ValueError("values must not be empty")
    if sample_rate_hz <= 0:
        raise ValueError(f"sample_rate_hz must be > 0, got {sample_rate_hz}")
    if method not in ("moving_average", "exponential"):
        raise ValueError(f"Unknown smoothing method: {method!r}")

    n = len(values)
    if n == 1:
        return list(values)

    window_samples = max(1, round(window_ms / 1000.0 * sample_rate_hz))

    if method == "moving_average":
        return _smooth_moving_average(values, window_samples)
    return _smooth_exponential(values, window_samples)


def _smooth_moving_average(values: list[float], window: int) -> list[float]:
    """Centred moving-average filter."""
    n = len(values)
    half = window // 2
    result: list[float] = []
    running_sum = 0.0
    # Initialise running sum for first window
    for i in range(min(window, n)):
        running_sum += values[i]

    for i in range(n):
        lo = max(0, i - half)
        hi = min(n - 1, i + half)
        count = hi - lo + 1
        s = sum(values[lo : hi + 1])
        result.append(s / count)
    return result


def _smooth_exponential(values: list[float], window: int) -> list[float]:
    """Exponential moving average (EMA)."""
    alpha = 2.0 / (window + 1)
    result = [values[0]]
    for v in values[1:]:
        result.append(alpha * v + (1 - alpha) * result[-1])
    return result


# ---------------------------------------------------------------------------
# Peak detection
# ---------------------------------------------------------------------------


def detect_peaks(
    values: list[float],
    sample_rate_hz: float,
    min_force_kg: float = 5.0,
    min_duration_s: float = 1.0,
) -> list[Peak]:
    """Detect force peaks (contiguous above-threshold regions).

    A peak is a contiguous region where force ≥ *min_force_kg* lasting
    at least *min_duration_s*.

    Args:
        values: Force values in kg.
        sample_rate_hz: Sampling rate in Hz.
        min_force_kg: Minimum force threshold.
        min_duration_s: Minimum duration for a valid peak.

    Returns:
        List of :class:`Peak` objects sorted by start index.

    References:
        Levernier & Laffaye (2019) :cite:`levernier2019`
    """
    if sample_rate_hz <= 0:
        raise ValueError(f"sample_rate_hz must be > 0, got {sample_rate_hz}")

    n = len(values)
    dt = 1.0 / sample_rate_hz
    peaks: list[Peak] = []
    i = 0

    while i < n:
        if values[i] >= min_force_kg:
            start = i
            peak_val = values[i]
            peak_idx = i
            while i < n and values[i] >= min_force_kg:
                if values[i] > peak_val:
                    peak_val = values[i]
                    peak_idx = i
                i += 1
            end = i - 1
            duration = (end - start + 1) * dt
            if duration >= min_duration_s:
                region = values[start : end + 1]
                mean_val = sum(region) / len(region)
                peaks.append(
                    Peak(
                        start_idx=start,
                        end_idx=end,
                        peak_idx=peak_idx,
                        peak_value=peak_val,
                        duration_s=duration,
                        mean_value=mean_val,
                    )
                )
        else:
            i += 1

    return peaks


# ---------------------------------------------------------------------------
# Rate of Force Development
# ---------------------------------------------------------------------------


def compute_rfd(
    values: list[float],
    sample_rate_hz: float,
    onset_threshold_kg: float = 2.0,
    window_pct: tuple[float, float] = (0.2, 0.8),
) -> RFDResult:
    """Rate of Force Development from a force curve.

    RFD = ΔF / Δt measured between *window_pct* fractions of peak
    force.

    Args:
        values: Force values in kg (single contraction).
        sample_rate_hz: Sampling rate in Hz.
        onset_threshold_kg: Threshold for force onset detection.
        window_pct: (lower, upper) fractions of peak force.

    Returns:
        :class:`RFDResult` with peak and average RFD.

    Raises:
        ValueError: If no force onset detected or signal too short.

    References:
        Levernier & Laffaye (2019) :cite:`levernier2019`
        — "RFD was calculated between 20 % and 80 % of peak force."
    """
    if sample_rate_hz <= 0:
        raise ValueError(f"sample_rate_hz must be > 0, got {sample_rate_hz}")
    if len(values) < 2:
        raise ValueError("Signal must contain at least 2 samples")

    dt = 1.0 / sample_rate_hz

    # Find onset
    onset_idx: int | None = None
    for i, v in enumerate(values):
        if v >= onset_threshold_kg:
            onset_idx = i
            break
    if onset_idx is None:
        raise ValueError(f"No force onset detected above {onset_threshold_kg} kg")

    # Find peak (after onset)
    peak_val = values[onset_idx]
    peak_idx = onset_idx
    for i in range(onset_idx, len(values)):
        if values[i] > peak_val:
            peak_val = values[i]
            peak_idx = i

    time_to_peak = (peak_idx - onset_idx) * dt

    # Analysis window
    lo_force = window_pct[0] * peak_val
    hi_force = window_pct[1] * peak_val

    lo_idx: int | None = None
    hi_idx: int | None = None
    for i in range(onset_idx, peak_idx + 1):
        if lo_idx is None and values[i] >= lo_force:
            lo_idx = i
        if hi_idx is None and values[i] >= hi_force:
            hi_idx = i

    if lo_idx is None or hi_idx is None or lo_idx == hi_idx:
        # Fallback: use onset to peak
        lo_idx = onset_idx
        hi_idx = peak_idx

    window_dt = (hi_idx - lo_idx) * dt
    if window_dt <= 0:
        window_dt = dt  # single-sample fallback

    avg_rfd = (values[hi_idx] - values[lo_idx]) / window_dt

    # Peak instantaneous RFD in the window
    max_rfd = 0.0
    for i in range(lo_idx, hi_idx):
        instant_rfd = (values[i + 1] - values[i]) / dt
        if instant_rfd > max_rfd:
            max_rfd = instant_rfd

    return RFDResult(
        peak_rfd_kg_s=max_rfd,
        avg_rfd_kg_s=avg_rfd,
        time_to_peak_s=time_to_peak,
        onset_idx=onset_idx,
        peak_idx=peak_idx,
    )


# ---------------------------------------------------------------------------
# MVC-7 extraction
# ---------------------------------------------------------------------------


def best_n_second_average(
    values: list[float],
    sample_rate_hz: float,
    n_seconds: float = 7.0,
) -> float:
    """Best (highest) average force over a sliding *n*-second window.

    This is the standard method for extracting **MVC-7** from a
    continuous force recording.

    Args:
        values: Force values in kg.
        sample_rate_hz: Sampling rate in Hz.
        n_seconds: Window duration (default 7.0 s for MVC-7).

    Returns:
        Maximum average force over any *n_seconds* window (kg).

    Raises:
        ValueError: If signal is shorter than *n_seconds*.

    References:
        Giles et al. (2006) :cite:`giles2006`
        — MVC-7 = best 7-second average from continuous hang.
    """
    if sample_rate_hz <= 0:
        raise ValueError(f"sample_rate_hz must be > 0, got {sample_rate_hz}")

    window = int(math.ceil(n_seconds * sample_rate_hz))
    n = len(values)
    if n < window:
        raise ValueError(
            f"Signal ({n} samples = {n / sample_rate_hz:.2f} s) is shorter than requested window ({n_seconds} s)"
        )

    # Sliding window via running sum
    running_sum = sum(values[:window])
    best = running_sum / window

    for i in range(1, n - window + 1):
        running_sum += values[i + window - 1] - values[i - 1]
        avg = running_sum / window
        if avg > best:
            best = avg

    return best


# ---------------------------------------------------------------------------
# Force impulse
# ---------------------------------------------------------------------------


def compute_impulse(
    values: list[float],
    sample_rate_hz: float,
    baseline_kg: float = 0.0,
) -> float:
    """Force impulse (integral) using the trapezoidal rule.

    .. math::

        I = \\int (F - F_{baseline})\\, dt

    Args:
        values: Force values in kg.
        sample_rate_hz: Sampling rate in Hz.
        baseline_kg: Baseline force to subtract (e.g. tare offset).

    Returns:
        Force impulse in kg·s.

    References:
        Jones et al. (2010) :cite:`jones2010`
        — impulse-based W′ calculation in the critical power model.
    """
    if sample_rate_hz <= 0:
        raise ValueError(f"sample_rate_hz must be > 0, got {sample_rate_hz}")
    if len(values) < 2:
        return 0.0

    dt = 1.0 / sample_rate_hz
    total = 0.0
    for i in range(1, len(values)):
        a = values[i - 1] - baseline_kg
        b = values[i] - baseline_kg
        total += (a + b) / 2.0 * dt
    return total


# ---------------------------------------------------------------------------
# Repeater segmentation
# ---------------------------------------------------------------------------


def segment_repeaters(
    values: list[float],
    sample_rate_hz: float,
    work_s: float = 7.0,
    rest_s: float = 3.0,
    force_threshold_kg: float = 5.0,
) -> list[SegmentedRep]:
    """Segment an intermittent protocol into individual repetitions.

    Designed for 7/3 repeater protocols but configurable for other
    work:rest ratios.

    Args:
        values: Force values in kg.
        sample_rate_hz: Sampling rate in Hz.
        work_s: Expected work duration in seconds.
        rest_s: Expected rest duration in seconds.
        force_threshold_kg: Minimum force to detect work phase.

    Returns:
        List of :class:`SegmentedRep` objects.

    References:
        Fryer et al. (2018) :cite:`fryer2018`
        — intermittent isometric protocol for CF measurement.
    """
    if sample_rate_hz <= 0:
        raise ValueError(f"sample_rate_hz must be > 0, got {sample_rate_hz}")

    dt = 1.0 / sample_rate_hz
    min_work_samples = max(1, int(work_s * 0.5 * sample_rate_hz))
    n = len(values)
    reps: list[SegmentedRep] = []
    i = 0
    rep_num = 0

    while i < n:
        # Find start of work phase
        if values[i] >= force_threshold_kg:
            start = i
            peak_val = values[i]
            while i < n and values[i] >= force_threshold_kg:
                if values[i] > peak_val:
                    peak_val = values[i]
                i += 1
            end = i - 1
            length = end - start + 1

            if length >= min_work_samples:
                rep_num += 1
                region = values[start : end + 1]
                mean_val = sum(region) / len(region)
                reps.append(
                    SegmentedRep(
                        rep_number=rep_num,
                        start_idx=start,
                        end_idx=end,
                        work_duration_s=length * dt,
                        mean_force_kg=mean_val,
                        peak_force_kg=peak_val,
                    )
                )
        else:
            i += 1

    return reps


# ---------------------------------------------------------------------------
# Time-to-Failure Extraction
# ---------------------------------------------------------------------------


def extract_ttf(
    values: list[float],
    sample_rate_hz: float,
    target_force_kg: float,
    drop_threshold_pct: float = 0.10,
    min_hold_s: float = 2.0,
) -> dict:
    """Extract Time-to-Failure from a raw force-time curve.

    Analyses a recorded force curve from an isometric TtF test where the
    climber attempts to sustain a target force until failure.  Detects
    the onset (force first reaches target) and failure (force permanently
    drops below threshold) to compute the actual hold duration.

    The failure threshold is ``target_force_kg × (1 - drop_threshold_pct)``.
    A brief dip shorter than ``min_hold_s`` below threshold is tolerated
    (e.g. grip readjustment) — failure is only declared when force stays
    below threshold for at least ``min_hold_s`` consecutive seconds.

    Args:
        values: Force measurements in kg.
        sample_rate_hz: Sampling rate in Hz.
        target_force_kg: Target force the climber attempted to hold (kg).
        drop_threshold_pct: Fractional drop below target that counts as
            failure (default 0.10 = 10% below target).
        min_hold_s: Minimum consecutive seconds below threshold before
            declaring failure (default 2.0s).

    Returns:
        Dict with keys:
            - ``target_force_kg``: The target force.
            - ``onset_idx``: Sample index where hold begins.
            - ``failure_idx``: Sample index of failure.
            - ``ttf_seconds``: Time-to-failure in seconds.
            - ``mean_force_kg``: Mean force during hold.
            - ``force_cv_pct``: Coefficient of variation during hold (%).

    Raises:
        ValueError: If inputs are invalid or force never reaches target.

    References:
        Rohmert 1960 (:cite:`rohmert1960`) — isometric endurance curve,
        Jones et al. 2010 (:cite:`jones2010`) — t_lim = W' / (F - CF).

    Examples:
        >>> sig = [0.0]*100 + [40.0]*500 + [10.0]*100
        >>> result = extract_ttf(sig, 100.0, 40.0)
        >>> round(result["ttf_seconds"], 1)
        5.0
    """
    if sample_rate_hz <= 0:
        raise ValueError(f"sample_rate_hz must be > 0, got {sample_rate_hz}")
    if target_force_kg <= 0:
        raise ValueError(f"target_force_kg must be > 0, got {target_force_kg}")
    if not values:
        raise ValueError("values must not be empty")
    if not 0 <= drop_threshold_pct < 1:
        raise ValueError(f"drop_threshold_pct must be in [0, 1), got {drop_threshold_pct}")

    threshold = target_force_kg * (1.0 - drop_threshold_pct)
    min_drop_samples = max(1, int(min_hold_s * sample_rate_hz))

    # Find onset: first sample at or above threshold
    onset_idx = None
    for i, v in enumerate(values):
        if v >= threshold:
            onset_idx = i
            break

    if onset_idx is None:
        raise ValueError(
            f"Force never reached threshold ({threshold:.1f} kg). Max force in signal: {max(values):.1f} kg."
        )

    # Find failure: first time force stays below threshold for min_hold_s
    failure_idx = len(values) - 1
    below_count = 0
    for i in range(onset_idx, len(values)):
        if values[i] < threshold:
            below_count += 1
            if below_count >= min_drop_samples:
                failure_idx = i - min_drop_samples + 1
                break
        else:
            below_count = 0

    # Compute metrics over the hold region
    hold_region = values[onset_idx:failure_idx]
    if not hold_region:
        raise ValueError("Hold region is empty — onset and failure overlap")

    mean_force = sum(hold_region) / len(hold_region)
    ttf_seconds = (failure_idx - onset_idx) / sample_rate_hz

    # Coefficient of variation
    if mean_force > 0 and len(hold_region) > 1:
        variance = sum((v - mean_force) ** 2 for v in hold_region) / len(hold_region)
        std_dev = math.sqrt(variance)
        cv_pct = (std_dev / mean_force) * 100.0
    else:
        cv_pct = 0.0

    return {
        "target_force_kg": target_force_kg,
        "onset_idx": onset_idx,
        "failure_idx": failure_idx,
        "ttf_seconds": round(ttf_seconds, 2),
        "mean_force_kg": round(mean_force, 2),
        "force_cv_pct": round(cv_pct, 2),
    }
