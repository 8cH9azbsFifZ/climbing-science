"""Tests for climbing_science.adapters.manual — manual input adapter."""

import pytest

from climbing_science.adapters.manual import (
    from_bodyweight_hang,
    from_mvc7_test,
    from_repeater_test,
    quick_profile,
)
from climbing_science.models import ClimberLevel, GripType


class TestFromMVC7Test:
    """Tests for from_mvc7_test()."""

    def test_standard_7s_20mm(self):
        """Standard test: 7s hang, 20mm, no conversion needed."""
        result = from_mvc7_test(body_weight_kg=72.0, added_weight_kg=20.0)
        assert result.body_weight_kg == 72.0
        assert result.total_force_kg == pytest.approx(92.0)
        assert result.edge_size_mm == 20
        assert result.grip_type == GripType.HALF_CRIMP

    def test_non_standard_duration_converts(self):
        """Non-7s hang triggers Rohmert conversion."""
        result_7s = from_mvc7_test(72.0, added_weight_kg=20.0, hang_time_s=7.0)
        result_10s = from_mvc7_test(72.0, added_weight_kg=20.0, hang_time_s=10.0)
        # 10s hold should convert to higher MVC-7 equivalent
        assert result_10s.total_force_kg > result_7s.total_force_kg

    def test_non_standard_edge_normalises(self):
        """Non-20mm edge triggers edge depth correction."""
        result_20 = from_mvc7_test(72.0, added_weight_kg=20.0, edge_mm=20.0)
        result_15 = from_mvc7_test(72.0, added_weight_kg=20.0, edge_mm=15.0)
        # 15mm is harder, so normalised value should be higher
        assert result_15.total_force_kg > result_20.total_force_kg
        assert result_15.edge_size_mm == 20  # normalised to reference

    def test_pulley_assist_negative_weight(self):
        result = from_mvc7_test(72.0, added_weight_kg=-10.0)
        assert result.total_force_kg == pytest.approx(62.0)

    def test_zero_bodyweight_raises(self):
        with pytest.raises(ValueError, match="body_weight_kg must be > 0"):
            from_mvc7_test(0.0, 20.0)

    def test_zero_hang_time_raises(self):
        with pytest.raises(ValueError, match="hang_time_s must be > 0"):
            from_mvc7_test(72.0, hang_time_s=0.0)

    def test_custom_grip_type(self):
        result = from_mvc7_test(72.0, grip_type=GripType.OPEN_HAND)
        assert result.grip_type == GripType.OPEN_HAND

    def test_percent_bw_computed(self):
        result = from_mvc7_test(72.0, added_weight_kg=20.0)
        expected_pct = round(92.0 / 72.0 * 100, 1)
        assert result.percent_bw == pytest.approx(expected_pct)


class TestFromRepeaterTest:
    """Tests for from_repeater_test()."""

    def test_basic_3point(self):
        """Basic 3-point CF test produces valid result."""
        result = from_repeater_test(
            body_weight_kg=72.0,
            mvc7_kg=92.0,
            t80_s=77.0,
            t60_s=136.0,
            t_low_s=323.0,
        )
        assert result.cf_absolute_kg > 0
        assert result.cf_percent_bw is not None
        assert result.cf_percent_bw > 0
        assert result.w_prime_kj is not None
        assert result.cf_mvc_ratio is not None
        assert 0 < result.cf_mvc_ratio < 1.0

    def test_cf_less_than_mvc(self):
        """CF should always be less than MVC."""
        result = from_repeater_test(72.0, 92.0, 77.0, 136.0, 323.0)
        assert result.cf_absolute_kg < 92.0

    def test_zero_bodyweight_raises(self):
        with pytest.raises(ValueError, match="body_weight_kg must be > 0"):
            from_repeater_test(0.0, 92.0, 77.0, 136.0, 323.0)

    def test_zero_time_raises(self):
        with pytest.raises(ValueError, match="t80_s must be > 0"):
            from_repeater_test(72.0, 92.0, 0.0, 136.0, 323.0)

    def test_custom_low_pct(self):
        result = from_repeater_test(72.0, 92.0, 77.0, 136.0, 323.0, low_pct=0.40)
        assert result.cf_absolute_kg > 0


class TestFromBodyweightHang:
    """Tests for from_bodyweight_hang()."""

    def test_delegates_to_mvc7_test(self):
        """Should produce a valid MVC7Test with zero added weight."""
        result = from_bodyweight_hang(72.0, hang_time_s=30.0)
        assert result.body_weight_kg == 72.0
        # A 30s hang is sub-maximal, so estimated MVC-7 force > BW
        assert result.total_force_kg > 72.0

    def test_short_hang_lower_estimate(self):
        result_short = from_bodyweight_hang(72.0, hang_time_s=10.0)
        result_long = from_bodyweight_hang(72.0, hang_time_s=30.0)
        # Longer sub-maximal hold → higher estimated MVC-7
        assert result_long.total_force_kg > result_short.total_force_kg


class TestQuickProfile:
    """Tests for quick_profile()."""

    def test_basic_profile(self):
        p = quick_profile("Test", 72.0, 5.0)
        assert p.name == "Test"
        assert p.body_weight_kg == 72.0
        assert p.experience_years == 5.0
        assert p.level == ClimberLevel.INTERMEDIATE

    def test_with_height(self):
        p = quick_profile("Test", 72.0, 5.0, height_cm=178.0)
        assert p.height_cm == 178.0
