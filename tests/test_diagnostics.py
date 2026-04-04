"""Tests for climbing_science.diagnostics — athlete profiling.

Tests verify:
- Level classification (Draper et al. 2015, Lattice)
- Weakness identification from assessment data
- Training priority recommendations
- Progress quantification
"""

import pytest

from climbing_science.diagnostics import (
    classify_level,
    identify_weakness,
    progress_delta,
    training_priority,
)
from climbing_science.grades import BoulderSystem, RouteSystem


class TestClassifyLevel:
    """Verify level classification against IRCRA descriptors.

    Reference (Draper et al. 2015):
        Beginner: below 6a / V2
        Intermediate: 6a–6c+ / V2–V5
        Advanced: 7a–7b+ / V5–V8
        Elite: 7c+ and above / V9+
    """

    @pytest.mark.parametrize(
        "grade, system, expected",
        [
            ("5a", RouteSystem.FRENCH, "beginner"),
            ("5c", RouteSystem.FRENCH, "beginner"),
            ("6a", RouteSystem.FRENCH, "intermediate"),
            ("6b+", RouteSystem.FRENCH, "intermediate"),
            ("6c+", RouteSystem.FRENCH, "intermediate"),
            ("7a", RouteSystem.FRENCH, "advanced"),
            ("7b", RouteSystem.FRENCH, "advanced"),
            ("7c", RouteSystem.FRENCH, "elite"),
            ("8a", RouteSystem.FRENCH, "elite"),
        ],
    )
    def test_french_grades(self, grade, system, expected):
        assert classify_level(grade, system) == expected

    def test_v_scale(self):
        assert classify_level("V0", BoulderSystem.V_SCALE) == "intermediate"
        assert classify_level("V5", BoulderSystem.V_SCALE) == "advanced"
        assert classify_level("V8", BoulderSystem.V_SCALE) == "elite"
        assert classify_level("V10", BoulderSystem.V_SCALE) == "elite"

    def test_yds(self):
        assert classify_level("5.10a", RouteSystem.YDS) == "intermediate"
        assert classify_level("5.12a", RouteSystem.YDS) == "advanced"
        assert classify_level("5.13a", RouteSystem.YDS) == "elite"
        assert classify_level("5.14a", RouteSystem.YDS) == "elite"


class TestIdentifyWeakness:
    """Verify weakness identification from assessment data."""

    def test_low_strength(self):
        """MVC/BW < 1.0 → finger strength weakness."""
        weaknesses = identify_weakness(0.9)
        assert "finger-strength" in weaknesses

    def test_low_endurance(self):
        """CF/MVC < 0.35 → endurance weakness."""
        weaknesses = identify_weakness(1.3, cf_mvc_ratio=0.30)
        assert "endurance" in weaknesses

    def test_balanced_athlete(self):
        """Strong fingers + good endurance → no weaknesses."""
        weaknesses = identify_weakness(1.5, cf_mvc_ratio=0.45)
        assert weaknesses == []

    def test_relative_strength_deficit(self):
        """Good endurance but weak fingers."""
        weaknesses = identify_weakness(1.1, cf_mvc_ratio=0.58)
        assert "finger-strength-relative" in weaknesses

    def test_pulling_power_deficit(self):
        weaknesses = identify_weakness(1.5, pull_up_ratio=0.2)
        assert "pulling-power" in weaknesses


class TestTrainingPriority:
    """Verify training priority recommendations."""

    def test_strength_priority(self):
        assert training_priority(["finger-strength", "endurance"]) == "max-strength"

    def test_endurance_priority(self):
        assert training_priority(["endurance"]) == "endurance"

    def test_pulling_priority(self):
        assert training_priority(["pulling-power"]) == "pulling"

    def test_no_weakness(self):
        assert training_priority([]) == "maintenance"


class TestProgressDelta:
    """Verify progress quantification between assessments."""

    def test_strength_improvement(self):
        d = progress_delta(1.20, 1.35)
        assert d["mvc_bw_delta"] == pytest.approx(0.15, abs=0.001)
        assert d["mvc_bw_percent_change"] > 0

    def test_grade_improvement(self):
        d = progress_delta(1.20, 1.35, old_grade_idx=59.0, new_grade_idx=65.0)
        assert d["grade_idx_delta"] == 6.0

    def test_endurance_change(self):
        d = progress_delta(1.20, 1.25, old_cf_mvc=0.35, new_cf_mvc=0.40)
        assert d["cf_mvc_delta"] == pytest.approx(0.05, abs=0.001)

    def test_no_change(self):
        d = progress_delta(1.30, 1.30)
        assert d["mvc_bw_delta"] == 0.0
        assert d["mvc_bw_percent_change"] == 0.0
