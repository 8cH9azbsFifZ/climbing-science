"""Tests for climbing_science.load — training load calculations.

Tests verify against:
    - López TUT methodology (López-Rivera 2014)
    - Gabbett ACWR thresholds (Gabbett 2016)
    - RPE ↔ %MVC mapping (modified Borg CR-10)
"""

import pytest

from climbing_science.load import (
    acwr,
    effort_level_to_mvc_pct,
    margin_to_failure,
    mvc_pct_to_rpe,
    overtraining_check,
    rpe_to_mvc_pct,
    tut_per_session,
    tut_per_set,
    weekly_load,
)

# ---------------------------------------------------------------------------
# TUT — Time Under Tension (López 2014)
# ---------------------------------------------------------------------------


class TestTUT:
    """Verify TUT calculations against López protocol examples.

    Reference: MaxHang = 10s × 1 rep × 4 sets = 40s TUT/session.
    7/3 Repeater = 7s × 6 reps × 5 sets = 210s TUT/session.
    """

    def test_maxhang_single_set(self):
        assert tut_per_set(10.0, 1) == 10.0

    def test_repeater_single_set(self):
        """7s × 6 reps = 42s TUT per set."""
        assert tut_per_set(7.0, 6) == 42.0

    def test_maxhang_session(self):
        """10s × 1 rep × 4 sets = 40s."""
        assert tut_per_session(10.0, 1, 4) == 40.0

    def test_repeater_session(self):
        """7s × 6 reps × 5 sets = 210s."""
        assert tut_per_session(7.0, 6, 5) == 210.0

    def test_invalid_duration_raises(self):
        with pytest.raises(ValueError):
            tut_per_set(0.0, 1)

    def test_invalid_reps_raises(self):
        with pytest.raises(ValueError):
            tut_per_set(10.0, 0)


# ---------------------------------------------------------------------------
# RPE ↔ %MVC (López Effort Level scale)
# ---------------------------------------------------------------------------


class TestRPEConversion:
    """Verify RPE ↔ %MVC mapping.

    Reference: RPE 8 ≈ 85% MVC (López methodology).
    """

    @pytest.mark.parametrize(
        "rpe, expected_mvc",
        [
            (1.0, 20.0),
            (5.0, 60.0),
            (8.0, 85.0),
            (10.0, 100.0),
        ],
    )
    def test_rpe_to_mvc(self, rpe, expected_mvc):
        assert rpe_to_mvc_pct(rpe) == expected_mvc

    def test_round_trip(self):
        """rpe_to_mvc → mvc_to_rpe should be identity at known points."""
        for rpe in [3.0, 5.0, 8.0, 10.0]:
            mvc = rpe_to_mvc_pct(rpe)
            recovered = mvc_pct_to_rpe(mvc)
            assert recovered == pytest.approx(rpe, abs=0.5)

    def test_invalid_rpe_raises(self):
        with pytest.raises(ValueError):
            rpe_to_mvc_pct(0.0)
        with pytest.raises(ValueError):
            rpe_to_mvc_pct(11.0)

    def test_effort_level(self):
        """EL 90% ≈ 90% MVC (approximately 1:1)."""
        assert effort_level_to_mvc_pct(90.0) == 90.0


# ---------------------------------------------------------------------------
# ACWR — Gabbett 2016
# ---------------------------------------------------------------------------


class TestACWR:
    """Verify ACWR against Gabbett thresholds.

    Sweet spot: 0.8–1.3
    Danger zone: > 1.5
    """

    def test_sweet_spot(self):
        assert acwr(600.0, 500.0) == 1.2

    def test_ratio_1(self):
        assert acwr(500.0, 500.0) == 1.0

    def test_zero_chronic_raises(self):
        with pytest.raises(ValueError):
            acwr(500.0, 0.0)

    def test_high_ratio(self):
        assert acwr(1000.0, 500.0) == 2.0


class TestOvertrainingCheck:
    """Verify traffic-light overtraining assessment."""

    def test_green_zone(self):
        result = overtraining_check([400, 450, 500, 550])
        assert result["status"] == "green"
        assert 0.8 <= result["acwr"] <= 1.3

    def test_yellow_spike(self):
        result = overtraining_check([400, 400, 400, 600])
        assert result["status"] in ("green", "yellow")

    def test_red_zone(self):
        """Doubling load → ACWR ≈ 2.0 → red."""
        result = overtraining_check([300, 300, 300, 900])
        assert result["status"] == "red"
        assert result["acwr"] > 1.5

    def test_undertraining(self):
        """Halving load → ACWR ≈ 0.5 → yellow."""
        result = overtraining_check([600, 600, 600, 200])
        assert result["status"] == "yellow"
        assert result["acwr"] < 0.8

    def test_insufficient_data_raises(self):
        with pytest.raises(ValueError, match="at least 2"):
            overtraining_check([500])


# ---------------------------------------------------------------------------
# Margin to Failure (López 2014)
# ---------------------------------------------------------------------------


class TestMarginToFailure:
    """Verify MTF calculation for progression decisions."""

    def test_typical_mtf(self):
        """10s hang, max 13s → MTF = 3s."""
        assert margin_to_failure(10.0, 13.0) == 3.0

    def test_zero_margin(self):
        """At limit → MTF = 0."""
        assert margin_to_failure(10.0, 10.0) == 0.0

    def test_negative_margin(self):
        """Failed to complete → negative MTF."""
        assert margin_to_failure(10.0, 8.0) == -2.0

    def test_invalid_raises(self):
        with pytest.raises(ValueError):
            margin_to_failure(0.0, 10.0)


# ---------------------------------------------------------------------------
# Weekly Load aggregation
# ---------------------------------------------------------------------------


class TestWeeklyLoad:
    """Verify weekly load aggregation."""

    def test_two_sessions(self):
        result = weekly_load(
            [
                {"tut_sec": 120.0, "rpe": 8.0},
                {"tut_sec": 90.0, "rpe": 7.0},
            ]
        )
        assert result["total_tut_sec"] == 210.0
        assert result["num_sessions"] == 2
        assert result["avg_rpe"] == 7.5
        assert result["training_load"] == 120.0 * 8.0 + 90.0 * 7.0

    def test_empty_sessions(self):
        result = weekly_load([])
        assert result["total_tut_sec"] == 0.0
        assert result["num_sessions"] == 0
