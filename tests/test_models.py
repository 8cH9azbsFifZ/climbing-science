"""Tests for climbing_science.models — Pydantic data models.

Tests verify:
- Model instantiation and validation
- JSON round-trip serialisation
- Computed fields (MVC-7 percent_bw, total_force)
- Boundary conditions and validation errors
"""

import pytest
from datetime import date

from climbing_science.models import (
    AssessmentResult,
    ClimberLevel,
    ClimberProfile,
    CriticalForceTest,
    Discipline,
    EnergySystem,
    ExerciseLog,
    GradeRecord,
    GripType,
    InjuryRecord,
    MVC7Test,
    ProgressionRule,
    ProtocolDefinition,
    ProtocolParams,
    PullUpTest,
    SessionLog,
    WeeklyVolume,
)


# ---------------------------------------------------------------------------
# ClimberProfile
# ---------------------------------------------------------------------------


class TestClimberProfile:
    """Verify climber profile creation, validation, and serialisation."""

    def test_minimal_profile(self):
        p = ClimberProfile(
            name="test_climber",
            body_weight_kg=70.0,
            experience_years=3.0,
        )
        assert p.level == ClimberLevel.INTERMEDIATE
        assert p.primary_discipline == Discipline.BOULDERING

    def test_full_profile(self):
        p = ClimberProfile(
            name="test_climber",
            body_weight_kg=72.5,
            height_cm=178.0,
            ape_index=1.01,
            experience_years=5.0,
            level=ClimberLevel.ADVANCED,
            primary_discipline=Discipline.SPORT,
            boulder_redpoint=GradeRecord(grade="V7", system="v_scale"),
            route_redpoint=GradeRecord(grade="7b+", system="french"),
        )
        assert p.boulder_redpoint.grade == "V7"
        assert p.height_cm == 178.0

    def test_json_round_trip(self):
        p = ClimberProfile(
            name="test_climber",
            body_weight_kg=70.0,
            experience_years=3.0,
            level=ClimberLevel.ADVANCED,
        )
        json_str = p.model_dump_json()
        p2 = ClimberProfile.model_validate_json(json_str)
        assert p2.name == p.name
        assert p2.level == p.level
        assert p2.body_weight_kg == p.body_weight_kg

    def test_negative_weight_rejected(self):
        with pytest.raises(Exception):
            ClimberProfile(name="x", body_weight_kg=-5, experience_years=1)

    def test_negative_experience_rejected(self):
        with pytest.raises(Exception):
            ClimberProfile(name="x", body_weight_kg=70, experience_years=-1)


# ---------------------------------------------------------------------------
# MVC7Test — computed fields
# ---------------------------------------------------------------------------


class TestMVC7Test:
    """Verify MVC-7 test model with auto-computed fields.

    Reference benchmark: 70kg climber + 18kg added = 88kg total = 125.7% BW.
    This corresponds to approximately V5–V6 (Giles et al. 2019).
    """

    def test_auto_compute_total_force(self):
        t = MVC7Test(body_weight_kg=70.0, added_weight_kg=18.0)
        assert t.total_force_kg == 88.0

    def test_auto_compute_percent_bw(self):
        t = MVC7Test(body_weight_kg=70.0, added_weight_kg=18.0)
        assert t.percent_bw == pytest.approx(125.7, abs=0.1)

    def test_pulley_assist_negative_weight(self):
        """Pulley-assisted hang: added_weight_kg < 0."""
        t = MVC7Test(body_weight_kg=70.0, added_weight_kg=-10.0)
        assert t.total_force_kg == 60.0
        assert t.percent_bw == pytest.approx(85.7, abs=0.1)

    def test_bodyweight_only(self):
        t = MVC7Test(body_weight_kg=65.0)
        assert t.total_force_kg == 65.0
        assert t.percent_bw == 100.0

    def test_explicit_override(self):
        """If total_force_kg is explicitly set, it is not overridden."""
        t = MVC7Test(body_weight_kg=70.0, added_weight_kg=18.0, total_force_kg=90.0)
        assert t.total_force_kg == 90.0

    def test_default_edge_and_grip(self):
        t = MVC7Test(body_weight_kg=70.0)
        assert t.edge_size_mm == 20
        assert t.grip_type == GripType.HALF_CRIMP


# ---------------------------------------------------------------------------
# CriticalForceTest
# ---------------------------------------------------------------------------


class TestCriticalForceTest:
    """Verify Critical Force test model.

    Reference: CF/MVC ratio of 0.35–0.50 is typical for intermediate
    climbers (Fryer et al. 2018).
    """

    def test_basic_creation(self):
        cf = CriticalForceTest(
            cf_absolute_kg=30.0,
            cf_percent_bw=42.9,
            cf_mvc_ratio=0.34,
        )
        assert cf.cf_absolute_kg == 30.0
        assert cf.cf_mvc_ratio == 0.34

    def test_ratio_bounds(self):
        with pytest.raises(Exception):
            CriticalForceTest(cf_absolute_kg=30.0, cf_mvc_ratio=1.5)


# ---------------------------------------------------------------------------
# SessionLog
# ---------------------------------------------------------------------------


class TestSessionLog:
    """Verify session logging with exercises."""

    def test_session_with_exercises(self):
        session = SessionLog(
            date=date(2026, 4, 3),
            climber_name="test",
            exercises=[
                ExerciseLog(
                    protocol_id="lopez-maxhang-maw",
                    sets_completed=4,
                    loads_kg=[88.0, 88.0, 88.0, 88.0],
                    durations_sec=[10.0, 10.0, 10.0, 10.0],
                    rpe=8.0,
                ),
            ],
            overall_rpe=8.0,
            finger_soreness=1,
        )
        assert len(session.exercises) == 1
        assert session.exercises[0].sets_completed == 4

    def test_rpe_bounds(self):
        with pytest.raises(Exception):
            SessionLog(
                date=date(2026, 1, 1),
                climber_name="test",
                overall_rpe=11,
            )

    def test_finger_soreness_bounds(self):
        with pytest.raises(Exception):
            SessionLog(
                date=date(2026, 1, 1),
                climber_name="test",
                finger_soreness=6,
            )

    def test_json_round_trip(self):
        session = SessionLog(
            date=date(2026, 4, 3),
            climber_name="test",
            exercises=[
                ExerciseLog(
                    protocol_id="test-protocol",
                    sets_completed=3,
                ),
            ],
        )
        json_str = session.model_dump_json()
        s2 = SessionLog.model_validate_json(json_str)
        assert s2.date == session.date
        assert len(s2.exercises) == 1


# ---------------------------------------------------------------------------
# ProtocolDefinition
# ---------------------------------------------------------------------------


class TestProtocolDefinition:
    """Verify protocol model with López MaxHang as reference.

    Reference: López MAW protocol — 10s hang, 3–5 min rest, 2–5 sets,
    75–103% MVC (López-Rivera 2014).
    """

    def test_lopez_maxhang_maw(self):
        proto = ProtocolDefinition(
            id="lopez-maxhang-maw",
            name="MaxHangs Medium Added Weight",
            author="Eva López",
            energy_system=EnergySystem.ALACTIC,
            min_level=ClimberLevel.INTERMEDIATE,
            params=ProtocolParams(
                edge_size_mm=18,
                hang_duration_sec=10.0,
                rest_between_reps_sec=0.0,
                reps_per_set=1,
                rest_between_sets_sec=180.0,
                sets=4,
                intensity_percent_mvc=(75.0, 103.0),
            ),
            progression=ProgressionRule(
                duration_weeks=4,
                volume_per_week=[2, 3, 4, 4],
            ),
            reference_key="lopezrivera2012",
        )
        assert proto.params.hang_duration_sec == 10.0
        assert proto.progression.volume_per_week == [2, 3, 4, 4]
        assert proto.reference_key == "lopezrivera2012"


# ---------------------------------------------------------------------------
# InjuryRecord
# ---------------------------------------------------------------------------


class TestInjuryRecord:
    """Verify injury tracking model.

    Reference: Schöffl grading system for pulley injuries (Schöffl et al. 2003).
    """

    def test_pulley_injury(self):
        injury = InjuryRecord(
            date_onset=date(2026, 3, 15),
            location="A2 pulley",
            side="right ring finger",
            severity_grade="II",
            severity_0_5=2,
            rehab_phase="strength",
        )
        assert injury.severity_grade == "II"
        assert injury.cleared_date is None

    def test_severity_bounds(self):
        with pytest.raises(Exception):
            InjuryRecord(
                date_onset=date(2026, 1, 1),
                location="finger",
                severity_0_5=6,
            )


# ---------------------------------------------------------------------------
# WeeklyVolume
# ---------------------------------------------------------------------------


class TestWeeklyVolume:
    """Verify weekly volume model.

    Reference benchmark: Intermediate climbers typically accumulate
    600–1200s TUT/week (López methodology).
    """

    def test_typical_week(self):
        vol = WeeklyVolume(
            week_start=date(2026, 3, 30),
            total_tut_sec=840.0,
            num_sessions=3,
            avg_rpe=7.5,
        )
        assert vol.total_tut_sec == 840.0
        assert 600 <= vol.total_tut_sec <= 1200  # López intermediate range
