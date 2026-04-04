"""Tests for climbing_science.periodization — training cycles.

Tests verify:
- Macrocycle phase distribution (Hörst 2016)
- Mesocycle progressive overload with deload (López 2014)
- Microcycle generation
- Constraint validation (López principle)
"""

import pytest

from climbing_science.periodization import (
    generate_macrocycle,
    generate_mesocycle,
    generate_microcycle,
    validate_constraints,
)


class TestMacrocycle:
    """Verify annual macrocycle generation (Hörst 2016)."""

    def test_52_week_plan(self):
        mc = generate_macrocycle(52)
        assert mc.total_weeks == 52
        assert sum(p.duration_weeks for p in mc.phases) == 52

    def test_has_all_phases(self):
        mc = generate_macrocycle(52)
        phase_names = [p.name for p in mc.phases]
        assert "base" in phase_names
        assert "strength" in phase_names
        assert "power" in phase_names
        assert "performance" in phase_names
        assert "rest" in phase_names

    def test_shorter_plan(self):
        mc = generate_macrocycle(24)
        assert sum(p.duration_weeks for p in mc.phases) == 24

    def test_phase_order(self):
        """Phases should follow logical progression."""
        mc = generate_macrocycle(52)
        names = [p.name for p in mc.phases]
        assert names.index("base") < names.index("strength")
        assert names.index("strength") < names.index("power")


class TestMesocycle:
    """Verify mesocycle generation with deload (López 2014)."""

    def test_4_week_block(self):
        mc = generate_mesocycle("strength", 4, 3, 200.0)
        assert mc.weeks == 4
        assert len(mc.weekly_sessions) == 4
        assert len(mc.weekly_volume_tut) == 4

    def test_deload_in_final_week(self):
        mc = generate_mesocycle("strength", 4, 3, 200.0)
        assert mc.deload_week == 3  # 0-indexed, last week
        # Deload volume should be less than peak
        assert mc.weekly_volume_tut[-1] < max(mc.weekly_volume_tut[:-1])

    def test_progressive_overload(self):
        """Volume should increase before deload."""
        mc = generate_mesocycle("strength", 4, 3, 200.0)
        # Weeks 1-3 should be generally increasing
        assert mc.weekly_volume_tut[2] > mc.weekly_volume_tut[0]

    def test_deload_reduces_sessions(self):
        mc = generate_mesocycle("strength", 4, 3, 200.0)
        assert mc.weekly_sessions[-1] < mc.weekly_sessions[0]

    def test_minimum_2_weeks(self):
        mc = generate_mesocycle("base", 2, 2, 100.0)
        assert mc.weeks == 2
        assert mc.deload_week == 1

    def test_invalid_weeks_raises(self):
        with pytest.raises(ValueError, match="at least 2"):
            generate_mesocycle("strength", 1)


class TestMicrocycle:
    """Verify weekly microcycle generation."""

    def test_normal_week(self):
        mc = generate_microcycle(3, 200.0, "high", False, 2)
        assert mc.sessions_per_week == 3
        assert mc.session_tut_sec == 200.0
        assert not mc.is_deload

    def test_deload_week(self):
        mc = generate_microcycle(3, 200.0, "high", True, 4)
        assert mc.is_deload
        assert mc.sessions_per_week < 3
        assert mc.session_tut_sec < 200.0
        assert mc.intensity == "low"


class TestConstraintValidation:
    """Verify López constraint: never increase vol + intensity + freq simultaneously."""

    def test_no_violations(self):
        violations = validate_constraints(
            [100, 120, 130, 80],
            [80, 85, 85, 70],
            [3, 3, 3, 2],
        )
        assert violations == []

    def test_triple_increase_detected(self):
        violations = validate_constraints(
            [100, 100, 140],
            [80, 80, 90],
            [2, 2, 4],
        )
        assert len(violations) == 1
        assert "Week 2→3" in violations[0]

    def test_double_increase_ok(self):
        """Increasing only 2 of 3 variables is allowed."""
        violations = validate_constraints(
            [100, 120],
            [80, 85],
            [3, 3],  # frequency stays same
        )
        assert violations == []

    def test_mismatched_lengths_raises(self):
        with pytest.raises(ValueError, match="same length"):
            validate_constraints([100], [80, 85], [3])
