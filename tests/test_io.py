"""Tests for climbing_science.io — data import/export.

Tests verify:
- Force-gauge CSV parsing
- Session JSON round-trip
- Assessment report generation (Markdown and JSON)
"""

import json
from datetime import date

import pytest

from climbing_science.io import (
    export_assessment_json,
    export_assessment_markdown,
    export_session_json,
    import_session_json,
    read_force_csv,
)
from climbing_science.models import (
    ClimberProfile,
    ExerciseLog,
    MVC7Test,
    SessionLog,
)


class TestReadForceCsv:
    """Verify force-gauge CSV parsing."""

    def test_basic_csv(self):
        data = "time_s,force_kg\n0.0,0.0\n0.1,5.2\n0.2,10.1"
        result = read_force_csv(data)
        assert len(result) == 3
        assert result[0] == (0.0, 0.0)
        assert result[1] == (0.1, 5.2)
        assert result[2] == (0.2, 10.1)

    def test_custom_columns(self):
        data = "t,f\n0.0,1.0\n0.5,2.0"
        result = read_force_csv(data, time_col="t", force_col="f")
        assert len(result) == 2

    def test_semicolon_delimiter(self):
        data = "time_s;force_kg\n0.0;5.0\n1.0;10.0"
        result = read_force_csv(data, delimiter=";")
        assert len(result) == 2
        assert result[1] == (1.0, 10.0)

    def test_missing_time_column(self):
        with pytest.raises(ValueError, match="Time column"):
            read_force_csv("force_kg\n5.0\n10.0")

    def test_missing_force_column(self):
        with pytest.raises(ValueError, match="Force column"):
            read_force_csv("time_s\n0.0\n0.1")

    def test_extra_columns_ignored(self):
        data = "time_s,force_kg,temperature\n0.0,5.0,22.1\n1.0,10.0,22.2"
        result = read_force_csv(data)
        assert len(result) == 2
        assert result[0] == (0.0, 5.0)


class TestSessionJsonRoundTrip:
    """Verify session JSON export/import round-trip."""

    def test_minimal_session(self):
        s = SessionLog(date=date(2026, 4, 3), climber_name="test")
        json_str = export_session_json(s)
        s2 = import_session_json(json_str)
        assert s2.climber_name == "test"
        assert s2.date == date(2026, 4, 3)

    def test_session_with_exercises(self):
        s = SessionLog(
            date=date(2026, 4, 3),
            climber_name="test",
            exercises=[
                ExerciseLog(
                    protocol_id="lopez-maxhang-maw",
                    sets_completed=4,
                    loads_kg=[88.0, 88.0, 88.0, 88.0],
                    rpe=8.0,
                ),
            ],
            overall_rpe=8.0,
        )
        json_str = export_session_json(s)
        s2 = import_session_json(json_str)
        assert len(s2.exercises) == 1
        assert s2.exercises[0].sets_completed == 4
        assert s2.overall_rpe == 8.0

    def test_json_is_valid(self):
        s = SessionLog(date=date(2026, 4, 3), climber_name="test")
        json_str = export_session_json(s)
        parsed = json.loads(json_str)
        assert parsed["climber_name"] == "test"


class TestAssessmentMarkdown:
    """Verify Markdown report generation."""

    def test_minimal_report(self):
        p = ClimberProfile(name="Test Climber", body_weight_kg=70.0, experience_years=3)
        md = export_assessment_markdown(p)
        assert "# Climbing Assessment" in md
        assert "Test Climber" in md
        assert "70.0 kg" in md

    def test_with_mvc_test(self):
        p = ClimberProfile(name="Test", body_weight_kg=70.0, experience_years=3)
        mvc = MVC7Test(body_weight_kg=70.0, added_weight_kg=18.0)
        md = export_assessment_markdown(p, mvc_test=mvc)
        assert "MVC-7" in md
        assert "88.0" in md

    def test_with_weaknesses(self):
        p = ClimberProfile(name="Test", body_weight_kg=70.0, experience_years=3)
        md = export_assessment_markdown(p, weaknesses=["finger-strength", "endurance"])
        assert "finger-strength" in md
        assert "endurance" in md


class TestAssessmentJson:
    """Verify JSON assessment export."""

    def test_minimal(self):
        p = ClimberProfile(name="Test", body_weight_kg=70.0, experience_years=3)
        j = export_assessment_json(p)
        data = json.loads(j)
        assert data["profile"]["name"] == "Test"

    def test_with_all_fields(self):
        p = ClimberProfile(name="Test", body_weight_kg=70.0, experience_years=3)
        mvc = MVC7Test(body_weight_kg=70.0, added_weight_kg=18.0)
        j = export_assessment_json(
            p,
            mvc_test=mvc,
            grade_prediction="7a",
            level="advanced",
            weaknesses=["endurance"],
            priority="endurance",
        )
        data = json.loads(j)
        assert data["grade_prediction"] == "7a"
        assert data["level"] == "advanced"
        assert data["weaknesses"] == ["endurance"]
