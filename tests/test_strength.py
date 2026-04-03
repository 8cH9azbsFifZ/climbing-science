"""Tests for climbing_science.strength — finger strength models.

Tests verify against published benchmark data:
    - MVC-7 → grade correlation (Lattice n≈901)
    - Rohmert endurance curve (Rohmert 1960 original data)
    - RFD calculation (Levernier & Laffaye 2019)
    - Power-to-weight classification (Lattice benchmarks)
"""

import pytest

from climbing_science.grades import GradeSystem
from climbing_science.strength import (
    grade_to_mvc7,
    mvc7_to_grade,
    power_to_weight,
    rfd_from_curve,
    rohmert_conversion,
)

# ---------------------------------------------------------------------------
# mvc7_to_grade — Lattice benchmark verification
# ---------------------------------------------------------------------------


class TestMvc7ToGrade:
    """Verify MVC-7 → grade mapping against Lattice benchmarks (n≈901).

    Reference values:
        70 %BW → ~5a (beginner)
        100%BW → ~6a+ (intermediate threshold)
        128%BW → ~7a (strong intermediate)
        140%BW → ~7b (advanced)
        167%BW → ~8a (elite)
    """

    @pytest.mark.parametrize(
        "percent_bw, expected_french",
        [
            (70.0, "5a"),
            (93.0, "6a"),
            (100.0, "6a+"),
            (128.0, "7a"),
            (140.0, "7b"),
            (167.0, "8a"),
            (195.0, "8c"),
        ],
    )
    def test_exact_benchmarks(self, percent_bw, expected_french):
        """Exact benchmark values must return the matching grade."""
        assert mvc7_to_grade(percent_bw) == expected_french

    @pytest.mark.parametrize(
        "percent_bw, expected_french",
        [
            (125.0, "6c+"),  # just below 7a (128)
            (135.0, "7a+"),  # between 7a (128) and 7b (140)
            (155.0, "7c"),  # between 7b+ (147) and 7c+ (160)
        ],
    )
    def test_interpolated_values(self, percent_bw, expected_french):
        """Interpolated values should snap to nearest grade."""
        assert mvc7_to_grade(percent_bw) == expected_french

    def test_different_grade_systems(self):
        """Conversion to other systems should work."""
        assert mvc7_to_grade(128.0, GradeSystem.YDS) == "5.12b"
        assert mvc7_to_grade(128.0, GradeSystem.UIAA) == "IX+"

    def test_monotonically_increasing(self):
        """Higher %BW must never produce a lower grade."""
        from climbing_science.grades import difficulty_index

        prev_idx = 0
        for pct in range(70, 200, 5):
            grade = mvc7_to_grade(float(pct))
            idx = difficulty_index(grade, GradeSystem.FRENCH)
            assert idx >= prev_idx, f"Grade decreased at {pct}%BW: {grade}"
            prev_idx = idx


# ---------------------------------------------------------------------------
# grade_to_mvc7 — inverse function
# ---------------------------------------------------------------------------


class TestGradeToMvc7:
    """Verify grade → MVC-7 inverse mapping.

    Must be consistent with mvc7_to_grade at benchmark points.
    """

    @pytest.mark.parametrize(
        "french_grade, expected_pct",
        [
            ("5a", 70.0),
            ("6a", 93.0),
            ("6a+", 100.0),
            ("7a", 128.0),
            ("7b", 140.0),
            ("8a", 167.0),
            ("8c", 195.0),
        ],
    )
    def test_exact_benchmarks(self, french_grade, expected_pct):
        """Benchmark grades must return exact %BW values."""
        assert grade_to_mvc7(french_grade) == expected_pct

    def test_inverse_consistency(self):
        """grade_to_mvc7(mvc7_to_grade(x)) ≈ x at benchmark points."""
        for pct in [93.0, 128.0, 140.0, 167.0]:
            grade = mvc7_to_grade(pct)
            recovered = grade_to_mvc7(grade)
            assert recovered == pytest.approx(pct, abs=1.0), f"Round-trip failed: {pct} → {grade} → {recovered}"

    def test_different_systems(self):
        """Grade from any system should work."""
        assert grade_to_mvc7("V5", GradeSystem.V_SCALE) == pytest.approx(122.0, abs=1.0)
        assert grade_to_mvc7("5.12b", GradeSystem.YDS) == pytest.approx(128.0, abs=1.0)

    def test_monotonically_increasing(self):
        """Higher grades must require higher MVC-7."""
        grades = ["5a", "6a", "6c+", "7a", "7b", "7c+", "8a", "8c"]
        pcts = [grade_to_mvc7(g) for g in grades]
        for i in range(len(pcts) - 1):
            assert pcts[i] < pcts[i + 1], f"{grades[i]} ({pcts[i]}) >= {grades[i + 1]} ({pcts[i + 1]})"


# ---------------------------------------------------------------------------
# rohmert_conversion — Rohmert 1960 endurance curve
# ---------------------------------------------------------------------------


class TestRohmertConversion:
    """Verify Rohmert curve normalisation.

    Reference: at higher %MVC, shorter hold times are expected.
    A 10s hang at 80% MVC should convert to a HIGHER %MVC at 7s,
    because 7s is easier to sustain.

    Key property: converting to a SHORTER duration always increases
    the equivalent %MVC (you can hold more for less time).
    """

    def test_shorter_duration_increases_force(self):
        """Converting 10s → 7s must yield higher %MVC."""
        result = rohmert_conversion(80.0, 10.0, 7.0)
        assert result > 80.0, f"Expected > 80%, got {result}%"

    def test_longer_duration_decreases_force(self):
        """Converting 7s → 10s must yield lower %MVC."""
        result = rohmert_conversion(80.0, 7.0, 10.0)
        assert result < 80.0, f"Expected < 80%, got {result}%"

    def test_same_duration_identity(self):
        """Converting to same duration should return approximately the same force."""
        result = rohmert_conversion(80.0, 7.0, 7.0)
        assert result == pytest.approx(80.0, abs=1.0)

    def test_low_force_long_duration(self):
        """Low force (30%) can be held much longer — converting to 7s should increase."""
        result = rohmert_conversion(30.0, 60.0, 7.0)
        assert result > 30.0

    def test_boundary_100_percent(self):
        """100% MVC can only be held instantaneously."""
        # At 100% MVC, converting from 1s to 7s should give a much lower value
        result = rohmert_conversion(99.0, 1.0, 7.0)
        assert result < 99.0

    def test_invalid_force_raises(self):
        with pytest.raises(ValueError, match="force_percent_mvc"):
            rohmert_conversion(0.0, 10.0, 7.0)
        with pytest.raises(ValueError, match="force_percent_mvc"):
            rohmert_conversion(101.0, 10.0, 7.0)

    def test_invalid_duration_raises(self):
        with pytest.raises(ValueError, match="Durations"):
            rohmert_conversion(80.0, -1.0, 7.0)


# ---------------------------------------------------------------------------
# power_to_weight — Schweizer 2001 / Lattice benchmarks
# ---------------------------------------------------------------------------


class TestPowerToWeight:
    """Verify power-to-weight ratio classification.

    Reference thresholds from Lattice Training:
        <80%  → beginner
        80-99% → beginner-intermediate
        100-129% → intermediate
        130-159% → advanced
        160-189% → elite
        190%+ → world-class
    """

    @pytest.mark.parametrize(
        "mvc_kg, bw_kg, expected_ratio, expected_level",
        [
            (49.0, 70.0, 70.0, "beginner"),
            (63.0, 70.0, 90.0, "beginner-intermediate"),
            (84.0, 70.0, 120.0, "intermediate"),
            (98.0, 70.0, 140.0, "advanced"),
            (119.0, 70.0, 170.0, "elite"),
            (140.0, 70.0, 200.0, "world-class"),
        ],
    )
    def test_classifications(self, mvc_kg, bw_kg, expected_ratio, expected_level):
        ratio, level = power_to_weight(mvc_kg, bw_kg)
        assert ratio == expected_ratio
        assert level == expected_level

    def test_zero_weight_raises(self):
        with pytest.raises(ValueError):
            power_to_weight(88.0, 0.0)


# ---------------------------------------------------------------------------
# rfd_from_curve — Levernier & Laffaye 2019
# ---------------------------------------------------------------------------


class TestRfdFromCurve:
    """Verify Rate of Force Development calculation.

    Reference: elite climbers produce RFD > 300 N/s (Levernier 2019).
    A linear ramp of 10 kg/s at 100 Hz should yield RFD = 10 kg/s × window.
    """

    def test_linear_ramp(self):
        """10 kg/s ramp: RFD over 200ms window = 10 kg/s."""
        # 100 Hz, 1 second, linear 0→10 kg
        force = [i * 0.1 for i in range(101)]  # 0.0, 0.1, ..., 10.0
        rfd = rfd_from_curve(force, 100.0, 200.0)
        assert rfd == pytest.approx(10.0, abs=0.5)

    def test_step_function(self):
        """Step from 0 to 50 kg: RFD = 50 / window_duration."""
        force = [0.0] * 50 + [50.0] * 50
        rfd = rfd_from_curve(force, 100.0, 200.0)
        assert rfd == pytest.approx(250.0, abs=1.0)

    def test_constant_force_zero_rfd(self):
        """Constant force → RFD = 0."""
        force = [20.0] * 100
        rfd = rfd_from_curve(force, 100.0, 200.0)
        assert rfd == 0.0

    def test_insufficient_data_raises(self):
        with pytest.raises(ValueError, match="Need at least"):
            rfd_from_curve([1.0, 2.0], 1000.0, 200.0)

    def test_invalid_sampling_rate_raises(self):
        with pytest.raises(ValueError):
            rfd_from_curve([1.0, 2.0, 3.0], 0.0, 200.0)
