"""Tests for climbing_science.grades — grade conversion module.

Tests verify against the IRCRA correspondence table (Draper et al. 2015).
Round-trip conversions ensure no information is lost.
"""

import pytest

from climbing_science.grades import (
    Grade,
    GradeSystem,
    compare,
    convert,
    difficulty_index,
    parse,
)


# ---------------------------------------------------------------------------
# difficulty_index
# ---------------------------------------------------------------------------


class TestDifficultyIndex:
    """Verify difficulty indices against IRCRA table (Draper et al. 2015)."""

    @pytest.mark.parametrize(
        "grade, system, expected",
        [
            ("5a", GradeSystem.FRENCH, 30),
            ("6a", GradeSystem.FRENCH, 42),
            ("7a", GradeSystem.FRENCH, 59),
            ("8a", GradeSystem.FRENCH, 76),
            ("9a", GradeSystem.FRENCH, 92),
            ("V0", GradeSystem.V_SCALE, 33),
            ("V5", GradeSystem.V_SCALE, 57),
            ("V10", GradeSystem.V_SCALE, 76),
            ("V15", GradeSystem.V_SCALE, 89),
            ("5.10a", GradeSystem.YDS, 33),
            ("5.12a", GradeSystem.YDS, 57),
            ("5.14a", GradeSystem.YDS, 78),
            ("VII", GradeSystem.UIAA, 39),
            ("IX", GradeSystem.UIAA, 57),
            ("XI", GradeSystem.UIAA, 76),
        ],
    )
    def test_known_grades(self, grade, system, expected):
        assert difficulty_index(grade, system) == expected

    def test_monotonically_increasing_french(self):
        """French grades must be strictly ordered by difficulty."""
        french_grades = ["4a", "5a", "6a", "6c+", "7a", "7c", "8a", "8c", "9a"]
        indices = [difficulty_index(g, GradeSystem.FRENCH) for g in french_grades]
        for i in range(len(indices) - 1):
            assert indices[i] < indices[i + 1], f"{french_grades[i]} >= {french_grades[i+1]}"

    def test_unknown_grade_raises(self):
        with pytest.raises(ValueError, match="not found"):
            difficulty_index("99z", GradeSystem.FRENCH)

    def test_unknown_system_handled(self):
        with pytest.raises(ValueError):
            difficulty_index("7a", "nonexistent")


# ---------------------------------------------------------------------------
# convert
# ---------------------------------------------------------------------------


class TestConvert:
    """Verify cross-system conversions against IRCRA table."""

    @pytest.mark.parametrize(
        "grade, from_sys, to_sys, expected",
        [
            # French → YDS (Draper et al. 2015)
            ("7a", GradeSystem.FRENCH, GradeSystem.YDS, "5.12b"),
            ("6a", GradeSystem.FRENCH, GradeSystem.YDS, "5.10d"),
            ("8a", GradeSystem.FRENCH, GradeSystem.YDS, "5.13d"),
            # V-Scale → UIAA
            ("V5", GradeSystem.V_SCALE, GradeSystem.UIAA, "IX"),
            ("V10", GradeSystem.V_SCALE, GradeSystem.UIAA, "XI"),
            # YDS → French
            ("5.12a", GradeSystem.YDS, GradeSystem.FRENCH, "6c+"),
            ("5.14a", GradeSystem.YDS, GradeSystem.FRENCH, "8a+"),
            # UIAA → French
            ("VII", GradeSystem.UIAA, GradeSystem.FRENCH, "5c+"),
            ("IX", GradeSystem.UIAA, GradeSystem.FRENCH, "6c+"),
            # Font → V-Scale
            ("7A", GradeSystem.FONT, GradeSystem.V_SCALE, "V6"),
            ("7C", GradeSystem.FONT, GradeSystem.V_SCALE, "V9"),
        ],
    )
    def test_known_conversions(self, grade, from_sys, to_sys, expected):
        assert convert(grade, from_sys, to_sys) == expected

    def test_round_trip_french_yds(self):
        """French → YDS → French must be identity."""
        for grade in ["5a", "6a", "7a", "8a", "9a"]:
            yds = convert(grade, GradeSystem.FRENCH, GradeSystem.YDS)
            back = convert(yds, GradeSystem.YDS, GradeSystem.FRENCH)
            assert back == grade, f"Round-trip failed: {grade} → {yds} → {back}"

    def test_round_trip_v_scale_font(self):
        """V-Scale → Font → V-Scale must be identity."""
        for grade in ["V3", "V5", "V8", "V10", "V15"]:
            font = convert(grade, GradeSystem.V_SCALE, GradeSystem.FONT)
            back = convert(font, GradeSystem.FONT, GradeSystem.V_SCALE)
            assert back == grade, f"Round-trip failed: {grade} → {font} → {back}"

    def test_no_equivalent_raises(self):
        """Low route grades have no V-Scale equivalent."""
        with pytest.raises(ValueError, match="No v_scale equivalent"):
            convert("III", GradeSystem.UIAA, GradeSystem.V_SCALE)

    def test_identity_conversion(self):
        """Converting to the same system returns the same grade."""
        assert convert("7a", GradeSystem.FRENCH, GradeSystem.FRENCH) == "7a"


# ---------------------------------------------------------------------------
# parse (auto-detection)
# ---------------------------------------------------------------------------


class TestParse:
    """Verify auto-detection of grading systems."""

    @pytest.mark.parametrize(
        "grade_str, expected_system, expected_idx",
        [
            ("5.12a", GradeSystem.YDS, 57),
            ("5.10d", GradeSystem.YDS, 42),
            ("V5", GradeSystem.V_SCALE, 57),
            ("V0", GradeSystem.V_SCALE, 33),
            ("V10", GradeSystem.V_SCALE, 76),
            ("7A", GradeSystem.FONT, 62),
            ("6C+", GradeSystem.FONT, 59),
            ("7a", GradeSystem.FRENCH, 59),
            ("6b+", GradeSystem.FRENCH, 51),
            ("VII", GradeSystem.UIAA, 39),
            ("IX+", GradeSystem.UIAA, 59),
        ],
    )
    def test_auto_detect(self, grade_str, expected_system, expected_idx):
        g = parse(grade_str)
        assert g.system == expected_system
        assert g.index == expected_idx

    def test_whitespace_tolerance(self):
        g = parse("  V5  ")
        assert g.system == GradeSystem.V_SCALE

    def test_unrecognised_raises(self):
        with pytest.raises(ValueError, match="Cannot auto-detect"):
            parse("rainbow")


# ---------------------------------------------------------------------------
# compare
# ---------------------------------------------------------------------------


class TestCompare:
    """Verify cross-system comparison."""

    def test_same_difficulty(self):
        """V5 and 6c+ are both index 57."""
        assert compare("V5", "6c+") == 0

    def test_harder(self):
        """7a (59) > V5 (57)."""
        assert compare("7a", "V5") == 1

    def test_easier(self):
        """V3 (45) < 7a (59)."""
        assert compare("V3", "7a") == -1

    def test_cross_system_ordering(self):
        """8a (76) == V10 (76)."""
        assert compare("8a", "V10") == 0


# ---------------------------------------------------------------------------
# Grade object
# ---------------------------------------------------------------------------


class TestGradeObject:
    """Grade comparison operators and repr."""

    def test_equality(self):
        a = parse("V5")
        b = parse("6c+")  # both idx=57
        assert a == b

    def test_less_than(self):
        a = parse("V3")
        b = parse("V5")
        assert a < b

    def test_repr(self):
        g = parse("7a")
        assert "7a" in repr(g)
        assert "french" in repr(g)
