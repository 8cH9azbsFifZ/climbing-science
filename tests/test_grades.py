"""Tests for climbing_science.grades - grade conversion module.

Tests verify against grade correspondence tables from:
- Mandelli & Angriman 2016 (CAI/UIAA official)
- Draper et al. 2015 (IRCRA scale)
- Mountain Project 2024 (community consensus)
- Rockfax 2022 (European standard)
"""

import pytest

from climbing_science.grades import (
    BoulderSystem,
    Grade,
    GradeDomainError,
    GradeError,
    RouteSystem,
    UnknownGradeError,
    UnknownSystemError,
    all_grades,
    compare,
    convert,
    difficulty_index,
    from_index,
    parse,
)


class TestRouteConversion:
    @pytest.mark.parametrize(
        "grade, from_sys, to_sys, expected",
        [
            ("6a", "French", "YDS", "5.10a"),
            ("6a+", "French", "YDS", "5.10b"),
            ("7a", "French", "YDS", "5.11d"),
            ("7a+", "French", "YDS", "5.12a"),
            ("8a", "French", "YDS", "5.13b"),
            ("9a", "French", "YDS", "5.14d"),
            ("5.10a", "YDS", "French", "6a"),
            ("5.10d", "YDS", "French", "6b+"),
            ("5.12a", "YDS", "French", "7a+"),
            ("5.14a", "YDS", "French", "8b+"),
            ("6a", "French", "UIAA", "VI+"),
            ("6b+", "French", "UIAA", "VII+"),
            ("7a", "French", "UIAA", "VIII"),
            ("7a+", "French", "UIAA", "VIII+"),
            ("8a", "French", "UIAA", "X-"),
            ("9a", "French", "UIAA", "XI"),
            ("9c", "French", "UIAA", "XII+"),
            ("5.10a", "YDS", "UIAA", "VI+"),
            ("5.12a", "YDS", "UIAA", "VIII+"),
            ("5.14d", "YDS", "UIAA", "XI"),
            ("VI+", "UIAA", "French", "6a"),
            ("VII+", "UIAA", "French", "6b+"),
            ("VIII", "UIAA", "French", "7a"),
            ("IX", "UIAA", "French", "7c"),
            ("X", "UIAA", "French", "8b"),
        ],
    )
    def test_route_conversion(self, grade, from_sys, to_sys, expected):
        assert convert(grade, from_sys, to_sys) == expected


class TestBoulderConversion:
    @pytest.mark.parametrize(
        "grade, from_sys, to_sys, expected",
        [
            ("6A", "Font", "V-Scale", "V3"),
            ("7A", "Font", "V-Scale", "V6"),
            ("7C", "Font", "V-Scale", "V9"),
            ("7C+", "Font", "V-Scale", "V10"),
            ("8A", "Font", "V-Scale", "V11"),
            ("8C", "Font", "V-Scale", "V15"),
            ("V5", "V-Scale", "Font", "6C"),
            ("V9", "V-Scale", "Font", "7C"),
            ("V10", "V-Scale", "Font", "7C+"),
            ("V14", "V-Scale", "Font", "8B+"),
        ],
    )
    def test_boulder_conversion(self, grade, from_sys, to_sys, expected):
        assert convert(grade, from_sys, to_sys) == expected


class TestRoundTrip:
    @pytest.mark.parametrize("grade", ["7a+", "8a", "8b", "8c", "9a", "9b", "9c"])
    def test_french_yds(self, grade):
        assert convert(convert(grade, "French", "YDS"), "YDS", "French") == grade

    @pytest.mark.parametrize("grade", ["7a+", "8a", "8b", "8c", "9a", "9b", "9c"])
    def test_french_uiaa(self, grade):
        assert convert(convert(grade, "French", "UIAA"), "UIAA", "French") == grade

    @pytest.mark.parametrize("grade", ["V6", "V7", "V8", "V9", "V10", "V11", "V14", "V17"])
    def test_v_scale_font(self, grade):
        assert convert(convert(grade, "V-Scale", "Font"), "Font", "V-Scale") == grade


class TestDomainSeparation:
    def test_french_to_font(self):
        with pytest.raises(GradeDomainError):
            convert("7a", "French", "Font")

    def test_v_to_yds(self):
        with pytest.raises(GradeDomainError):
            convert("V5", "V-Scale", "YDS")

    def test_uiaa_to_v(self):
        with pytest.raises(GradeDomainError):
            convert("VIII", "UIAA", "V-Scale")

    def test_font_to_french(self):
        with pytest.raises(GradeDomainError):
            convert("7A", "Font", "French")

    def test_hierarchy(self):
        assert issubclass(GradeDomainError, GradeError)


class TestIRCRAIndex:
    @pytest.mark.parametrize("system", ["UIAA", "French", "YDS", "Font", "V-Scale"])
    def test_monotonic(self, system):
        grades = all_grades(system)
        for i in range(len(grades) - 1):
            assert grades[i].difficulty_index < grades[i + 1].difficulty_index

    @pytest.mark.parametrize(
        "ga, sa, gb, sb",
        [
            ("7a+", "French", "5.12a", "YDS"),
            ("7a+", "French", "VIII+", "UIAA"),
            ("9a", "French", "5.14d", "YDS"),
            ("9a", "French", "XI", "UIAA"),
            ("7A", "Font", "V6", "V-Scale"),
            ("8A", "Font", "V11", "V-Scale"),
            ("9A", "Font", "V17", "V-Scale"),
        ],
    )
    def test_cross_system_equality(self, ga, sa, gb, sb):
        assert difficulty_index(ga, sa) == difficulty_index(gb, sb)

    @pytest.mark.parametrize(
        "grade, sys, ircra",
        [
            ("VIII", "UIAA", 18),
            ("VIII+", "UIAA", 19),
            ("XI", "UIAA", 30),
        ],
    )
    def test_known_values(self, grade, sys, ircra):
        assert difficulty_index(grade, sys) == ircra


class TestFromIndex:
    @pytest.mark.parametrize(
        "idx, sys, expected",
        [
            (19, "French", "7a+"),
            (19, "YDS", "5.12a"),
            (19, "UIAA", "VIII+"),
            (23, "V-Scale", "V6"),
            (29, "Font", "8A"),
        ],
    )
    def test_exact(self, idx, sys, expected):
        assert from_index(idx, sys) == expected

    @pytest.mark.parametrize(
        "idx, sys, expected",
        [
            (18.4, "French", "7a"),
            (18.6, "French", "7a+"),
            (29.6, "UIAA", "XI"),
            (30.4, "UIAA", "XI"),
        ],
    )
    def test_nearest(self, idx, sys, expected):
        assert from_index(idx, sys) == expected

    def test_tie_harder(self):
        assert from_index(18.5, "French") == "7a+"


class TestParse:
    @pytest.mark.parametrize(
        "grade, expected_sys",
        [
            ("V5", BoulderSystem.V_SCALE),
            ("VB", BoulderSystem.V_SCALE),
            ("5.12a", RouteSystem.YDS),
            ("5.9", RouteSystem.YDS),
            ("VIII+", RouteSystem.UIAA),
            ("XII-", RouteSystem.UIAA),
            ("7a+", RouteSystem.FRENCH),
            ("7A+", BoulderSystem.FONT),
        ],
    )
    def test_detect(self, grade, expected_sys):
        assert parse(grade).system == expected_sys

    def test_grade_object(self):
        g = parse("7a+")
        assert isinstance(g, Grade) and g.value == "7a+" and g.difficulty_index == 19

    def test_whitespace(self):
        g = parse("  V5  ")
        assert g.system == BoulderSystem.V_SCALE and g.value == "V5"

    def test_unknown(self):
        with pytest.raises(UnknownGradeError):
            parse("rainbow")


class TestCaseInsensitive:
    def test_french(self):
        assert convert("7A+", "French", "YDS") == convert("7a+", "French", "YDS")

    def test_uiaa(self):
        assert convert("viii+", "UIAA", "French") == convert("VIII+", "UIAA", "French")

    def test_v_scale(self):
        assert convert("v5", "V-Scale", "Font") == convert("V5", "V-Scale", "Font")


class TestErrorHandling:
    def test_unknown_grade(self):
        with pytest.raises(UnknownGradeError):
            convert("13a", "French", "YDS")

    def test_unknown_v(self):
        with pytest.raises(UnknownGradeError):
            convert("V99", "V-Scale", "Font")

    def test_unknown_from_sys(self):
        with pytest.raises(UnknownSystemError):
            convert("7a", "Ewbanks", "YDS")

    def test_unknown_to_sys(self):
        with pytest.raises(UnknownSystemError):
            convert("7a", "French", "Saxon")

    def test_hierarchy(self):
        assert issubclass(UnknownGradeError, GradeError)
        assert issubclass(UnknownSystemError, GradeError)

    @pytest.mark.parametrize("g, s", [("7a+", "French"), ("V5", "V-Scale"), ("VIII+", "UIAA")])
    def test_identity(self, g, s):
        assert convert(g, s, s) == g


class TestHistorical:
    def test_silence(self):
        assert convert("9c", "French", "YDS") == "5.15d"
        assert convert("9c", "French", "UIAA") == "XII+"

    def test_action_directe(self):
        assert convert("9a", "French", "YDS") == "5.14d"
        assert convert("9a", "French", "UIAA") == "XI"

    def test_hubble(self):
        assert convert("8c+", "French", "YDS") == "5.14c"

    def test_punks(self):
        assert convert("8b+", "French", "YDS") == "5.14a"

    def test_burden_of_dreams(self):
        assert convert("9A", "Font", "V-Scale") == "V17"

    def test_midnight_lightning(self):
        assert convert("7B", "Font", "V-Scale") == "V8"


class TestDiscrepancies:
    def test_5_11b_to_french(self):
        assert convert("5.11b", "YDS", "French") == "6c+"

    def test_viii_minus_to_french(self):
        assert convert("VIII-", "UIAA", "French") == "6c"

    def test_8a_to_uiaa(self):
        assert convert("8a", "French", "UIAA") == "X-"


class TestPyclimbRegression:
    PYCLIMB = {
        "5a": "5.8",
        "5b": "5.9",
        "5c": "5.10a",
        "6a": "5.10a",
        "6a+": "5.10b",
        "6b": "5.10c",
        "6b+": "5.10d",
        "6c": "5.11b",
        "6c+": "5.11c",
        "7a": "5.11d",
        "7a+": "5.12a",
        "7b": "5.12b",
        "7b+": "5.12c",
        "7c": "5.12d",
        "7c+": "5.13a",
        "8a": "5.13b",
        "8a+": "5.13c",
        "8b": "5.13d",
        "8b+": "5.14a",
        "8c": "5.14b",
        "8c+": "5.14c",
        "9a": "5.14d",
        "9a+": "5.15a",
        "9b": "5.15b",
        "9b+": "5.15c",
        "9c": "5.15d",
    }
    DEVIATIONS = {
        "5a": "5.7+",
        "5b": "5.8",
        "5c": "5.9",
        "6c": "5.11a",
        "6c+": "5.11b",
    }

    @pytest.mark.parametrize("french", list(PYCLIMB.keys()))
    def test_regression(self, french):
        result = convert(french, "French", "YDS")
        if french in self.DEVIATIONS:
            assert result == self.DEVIATIONS[french]
        else:
            assert result == self.PYCLIMB[french]


class TestGradeObject:
    def test_frozen(self):
        with pytest.raises(AttributeError):
            parse("7a+").value = "8a"

    def test_ordering(self):
        a, b = parse("V3"), parse("V5")
        assert a < b and b > a and a <= b and b >= a and a != b

    def test_eq(self):
        assert parse("V5") == parse("V5")

    def test_str(self):
        assert str(parse("7a+")) == "7a+"

    def test_repr(self):
        assert "7a+" in repr(parse("7a+")) and "French" in repr(parse("7a+"))


class TestCompare:
    def test_equal(self):
        assert compare("7a+", "5.12a") == 0

    def test_harder(self):
        assert compare("8a", "V6") == 1

    def test_easier(self):
        assert compare("V3", "7a+") == -1

    def test_cross_domain(self):
        assert compare("8c", "7C+") == 0


class TestAllGrades:
    @pytest.mark.parametrize(
        "sys, n",
        [
            ("UIAA", 34),
            ("French", 34),
            ("YDS", 34),
            ("Font", 25),
            ("V-Scale", 25),
        ],
    )
    def test_count(self, sys, n):
        assert len(all_grades(sys)) == n

    def test_bounds_uiaa(self):
        g = all_grades("UIAA")
        assert g[0].value == "I" and g[-1].value == "XII+"

    def test_bounds_v(self):
        g = all_grades("V-Scale")
        assert g[0].value == "VB" and g[-1].value == "V17"

    def test_grade_types(self):
        assert all(isinstance(g, Grade) for g in all_grades("French"))

    def test_string_sys(self):
        assert len(all_grades("french")) == 34

    def test_enum_sys(self):
        assert len(all_grades(RouteSystem.FRENCH)) == 34


class TestStringAcceptance:
    def test_convert_str(self):
        assert convert("7a+", "French", "YDS") == "5.12a"

    def test_convert_enum(self):
        assert convert("7a+", RouteSystem.FRENCH, RouteSystem.YDS) == "5.12a"

    def test_convert_mixed(self):
        assert convert("7a+", "French", RouteSystem.YDS) == "5.12a"

    def test_di_str(self):
        assert difficulty_index("7a+", "French") == 19

    def test_di_enum(self):
        assert difficulty_index("7a+", RouteSystem.FRENCH) == 19

    def test_fi_str(self):
        assert from_index(19, "French") == "7a+"

    def test_fi_enum(self):
        assert from_index(19, RouteSystem.FRENCH) == "7a+"
