"""Tests for climbing_science.signal — force-curve signal processing."""


import pytest

from climbing_science.signal import (
    best_n_second_average,
    compute_impulse,
    compute_rfd,
    detect_peaks,
    segment_repeaters,
    smooth,
)

RATE = 100.0  # 100 Hz default test sampling rate


# ---------------------------------------------------------------------------
# Helpers — synthetic signal generators
# ---------------------------------------------------------------------------


def _constant(value: float, duration_s: float, rate: float = RATE) -> list[float]:
    return [value] * int(duration_s * rate)


def _ramp(start: float, end: float, duration_s: float, rate: float = RATE) -> list[float]:
    n = int(duration_s * rate)
    if n <= 1:
        return [start]
    return [start + (end - start) * i / (n - 1) for i in range(n)]


def _triangle(peak: float, duration_s: float, rate: float = RATE) -> list[float]:
    n = int(duration_s * rate)
    mid = n // 2
    up = [peak * i / mid for i in range(mid)]
    down = [peak * (n - 1 - i) / (n - 1 - mid) for i in range(mid, n)]
    return up + down


def _step(low: float, high: float, duration_s: float, step_at_s: float, rate: float = RATE) -> list[float]:
    n = int(duration_s * rate)
    step_idx = int(step_at_s * rate)
    return [low if i < step_idx else high for i in range(n)]


def _repeater(force: float, work_s: float, rest_s: float, n_reps: int, rate: float = RATE) -> list[float]:
    """Generate clean repeater signal."""
    sig: list[float] = []
    for _ in range(n_reps):
        sig.extend([force] * int(work_s * rate))
        sig.extend([0.0] * int(rest_s * rate))
    return sig


# ---------------------------------------------------------------------------
# smooth()
# ---------------------------------------------------------------------------


class TestSmooth:
    def test_constant_unchanged(self):
        sig = _constant(50.0, 2.0)
        result = smooth(sig, RATE)
        for v in result:
            assert v == pytest.approx(50.0)

    def test_output_length_matches_input(self):
        sig = _ramp(0, 100, 1.0)
        result = smooth(sig, RATE, window_ms=100)
        assert len(result) == len(sig)

    def test_reduces_noise(self):
        import random
        random.seed(42)
        base = _constant(50.0, 2.0)
        noisy = [v + random.gauss(0, 5) for v in base]
        smoothed = smooth(noisy, RATE, window_ms=100)
        # Std of smoothed should be less than std of noisy
        mean_n = sum(noisy) / len(noisy)
        mean_s = sum(smoothed) / len(smoothed)
        std_n = (sum((v - mean_n) ** 2 for v in noisy) / len(noisy)) ** 0.5
        std_s = (sum((v - mean_s) ** 2 for v in smoothed) / len(smoothed)) ** 0.5
        assert std_s < std_n

    def test_exponential_method(self):
        sig = _constant(50.0, 1.0)
        result = smooth(sig, RATE, method="exponential")
        assert len(result) == len(sig)
        for v in result:
            assert v == pytest.approx(50.0)

    def test_single_value(self):
        assert smooth([42.0], RATE) == [42.0]

    def test_empty_raises(self):
        with pytest.raises(ValueError, match="must not be empty"):
            smooth([], RATE)

    def test_unknown_method_raises(self):
        with pytest.raises(ValueError, match="Unknown smoothing method"):
            smooth([1.0, 2.0], RATE, method="butterworth")

    def test_zero_sample_rate_raises(self):
        with pytest.raises(ValueError, match="sample_rate_hz must be > 0"):
            smooth([1.0], 0.0)


# ---------------------------------------------------------------------------
# detect_peaks()
# ---------------------------------------------------------------------------


class TestDetectPeaks:
    def test_single_triangle_one_peak(self):
        sig = [0.0] * 50 + _constant(30.0, 2.0) + [0.0] * 50
        peaks = detect_peaks(sig, RATE, min_force_kg=5.0, min_duration_s=1.0)
        assert len(peaks) == 1
        assert peaks[0].peak_value == pytest.approx(30.0)

    def test_two_separated_peaks(self):
        gap = [0.0] * 100
        pulse = _constant(40.0, 2.0)
        sig = gap + pulse + gap + pulse + gap
        peaks = detect_peaks(sig, RATE, min_force_kg=5.0, min_duration_s=1.0)
        assert len(peaks) == 2

    def test_short_pulse_filtered(self):
        sig = [0.0] * 50 + _constant(30.0, 0.5) + [0.0] * 50
        peaks = detect_peaks(sig, RATE, min_force_kg=5.0, min_duration_s=1.0)
        assert len(peaks) == 0

    def test_below_threshold_no_peaks(self):
        sig = _constant(3.0, 5.0)
        peaks = detect_peaks(sig, RATE, min_force_kg=5.0)
        assert len(peaks) == 0

    def test_constant_above_threshold(self):
        sig = _constant(50.0, 3.0)
        peaks = detect_peaks(sig, RATE, min_force_kg=5.0, min_duration_s=1.0)
        assert len(peaks) == 1
        assert peaks[0].duration_s == pytest.approx(3.0)

    def test_peak_attributes(self):
        force = 50.0
        dur = 2.0
        sig = [0.0] * 50 + _constant(force, dur) + [0.0] * 50
        peaks = detect_peaks(sig, RATE, min_force_kg=5.0, min_duration_s=1.0)
        p = peaks[0]
        assert p.peak_value == pytest.approx(force)
        assert p.mean_value == pytest.approx(force)
        assert p.duration_s == pytest.approx(dur)

    def test_zero_sample_rate_raises(self):
        with pytest.raises(ValueError):
            detect_peaks([1.0], 0.0)


# ---------------------------------------------------------------------------
# compute_rfd()
# ---------------------------------------------------------------------------


class TestComputeRFD:
    def test_linear_ramp(self):
        """Linear ramp: RFD = slope = (end-start) / duration."""
        sig = _ramp(0.0, 100.0, 1.0)
        result = compute_rfd(sig, RATE, onset_threshold_kg=1.0)
        # Slope ≈ 100 kg/s
        assert result.avg_rfd_kg_s == pytest.approx(100.0, rel=0.1)
        assert result.time_to_peak_s == pytest.approx(1.0, abs=0.05)

    def test_step_function_high_rfd(self):
        # Use a fast ramp (2 samples) instead of a perfect step to ensure
        # the 20-80% window contains at least one interval.
        sig = [0.0] * 50 + [20.0, 40.0, 60.0, 80.0] + [80.0] * 46
        result = compute_rfd(sig, RATE, onset_threshold_kg=1.0)
        assert result.peak_rfd_kg_s > 1000  # Very high instantaneous RFD

    def test_no_onset_raises(self):
        sig = _constant(0.0, 1.0)
        with pytest.raises(ValueError, match="No force onset"):
            compute_rfd(sig, RATE, onset_threshold_kg=5.0)

    def test_too_short_raises(self):
        with pytest.raises(ValueError, match="at least 2 samples"):
            compute_rfd([50.0], RATE)

    def test_onset_and_peak_indices(self):
        sig = [0.0] * 20 + _ramp(0.0, 50.0, 0.5) + _constant(50.0, 0.5)
        result = compute_rfd(sig, RATE, onset_threshold_kg=1.0)
        assert result.onset_idx >= 20
        assert result.peak_idx > result.onset_idx


# ---------------------------------------------------------------------------
# best_n_second_average()
# ---------------------------------------------------------------------------


class TestBestNSecondAverage:
    def test_constant_signal(self):
        sig = _constant(50.0, 10.0)
        assert best_n_second_average(sig, RATE, 7.0) == pytest.approx(50.0)

    def test_rectangle_in_zeros(self):
        """7s @ 50kg embedded in zeros → best 7s avg = 50."""
        sig = [0.0] * 300 + _constant(50.0, 7.0) + [0.0] * 300
        result = best_n_second_average(sig, RATE, 7.0)
        assert result == pytest.approx(50.0, abs=0.5)

    def test_signal_too_short_raises(self):
        sig = _constant(50.0, 3.0)
        with pytest.raises(ValueError, match="shorter than requested"):
            best_n_second_average(sig, RATE, 7.0)

    def test_spike_included(self):
        """Best window should include the highest region."""
        sig = _constant(20.0, 10.0)
        # Insert a 7s block of 80kg in the middle
        start = 200
        for i in range(700):
            sig[start + i] = 80.0
        result = best_n_second_average(sig, RATE, 7.0)
        assert result == pytest.approx(80.0)

    def test_3_second_window(self):
        sig = _constant(30.0, 5.0)
        assert best_n_second_average(sig, RATE, 3.0) == pytest.approx(30.0)


# ---------------------------------------------------------------------------
# compute_impulse()
# ---------------------------------------------------------------------------


class TestComputeImpulse:
    def test_constant_force(self):
        """50kg for 10s → impulse = 500 kg·s."""
        sig = _constant(50.0, 10.0)
        result = compute_impulse(sig, RATE)
        assert result == pytest.approx(500.0, abs=1.0)

    def test_triangle_impulse(self):
        """Triangle: peak 100, 10s duration → area = 100*10/2 = 500."""
        sig = _triangle(100.0, 10.0)
        result = compute_impulse(sig, RATE)
        assert result == pytest.approx(500.0, abs=5.0)

    def test_with_baseline(self):
        """50kg - 30kg baseline for 10s → 200 kg·s."""
        sig = _constant(50.0, 10.0)
        result = compute_impulse(sig, RATE, baseline_kg=30.0)
        assert result == pytest.approx(200.0, abs=1.0)

    def test_zero_force(self):
        sig = _constant(0.0, 5.0)
        assert compute_impulse(sig, RATE) == pytest.approx(0.0)

    def test_single_sample(self):
        assert compute_impulse([50.0], RATE) == 0.0

    def test_zero_sample_rate_raises(self):
        with pytest.raises(ValueError):
            compute_impulse([1.0, 2.0], 0.0)


# ---------------------------------------------------------------------------
# segment_repeaters()
# ---------------------------------------------------------------------------


class TestSegmentRepeaters:
    def test_clean_protocol(self):
        """5 reps of 7/3 → 5 SegmentedRep objects."""
        sig = _repeater(40.0, 7.0, 3.0, 5)
        reps = segment_repeaters(sig, RATE, work_s=7.0, rest_s=3.0)
        assert len(reps) == 5

    def test_rep_attributes(self):
        sig = _repeater(40.0, 7.0, 3.0, 3)
        reps = segment_repeaters(sig, RATE, work_s=7.0, rest_s=3.0)
        for rep in reps:
            assert rep.mean_force_kg == pytest.approx(40.0)
            assert rep.peak_force_kg == pytest.approx(40.0)
            assert rep.work_duration_s == pytest.approx(7.0)

    def test_rep_numbers_sequential(self):
        sig = _repeater(40.0, 7.0, 3.0, 4)
        reps = segment_repeaters(sig, RATE, work_s=7.0, rest_s=3.0)
        assert [r.rep_number for r in reps] == [1, 2, 3, 4]

    def test_empty_signal(self):
        reps = segment_repeaters([], RATE)
        assert reps == []

    def test_all_below_threshold(self):
        sig = _constant(2.0, 10.0)
        reps = segment_repeaters(sig, RATE, force_threshold_kg=5.0)
        assert reps == []

    def test_varying_force(self):
        """Reps with different forces still detected."""
        sig: list[float] = []
        forces = [50.0, 45.0, 40.0]
        for f in forces:
            sig.extend([f] * int(7.0 * RATE))
            sig.extend([0.0] * int(3.0 * RATE))
        reps = segment_repeaters(sig, RATE)
        assert len(reps) == 3
        assert reps[0].peak_force_kg == pytest.approx(50.0)
        assert reps[2].peak_force_kg == pytest.approx(40.0)
