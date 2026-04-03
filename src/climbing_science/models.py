"""Pydantic data models for climbing-science.

Defines the core domain objects used across all modules:
- ClimberProfile, Assessment, SessionLog, Protocol, Injury.

All models are JSON-serialisable and produce JSON Schema via Pydantic v2.
"""

from __future__ import annotations

from datetime import date
from enum import Enum

from pydantic import BaseModel, Field

__all__ = [
    "ClimberLevel",
    "Discipline",
    "GripType",
    "EnergySystem",
    "ClimberProfile",
    "GradeRecord",
    "AssessmentResult",
    "MVC7Test",
    "CriticalForceTest",
    "PullUpTest",
    "SessionLog",
    "ExerciseLog",
    "ProtocolParams",
    "ProtocolDefinition",
    "ProgressionRule",
    "InjuryRecord",
    "WeeklyVolume",
]


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class ClimberLevel(str, Enum):
    """Athlete classification based on experience and grade.

    References:
        Draper et al. 2015 (:cite:`draper2015`) — IRCRA descriptors.
        Lattice Training grade-to-level mapping.
    """

    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    ELITE = "elite"


class Discipline(str, Enum):
    """Climbing discipline."""

    BOULDERING = "bouldering"
    SPORT = "sport"
    TRAD = "trad"
    SPEED = "speed"


class GripType(str, Enum):
    """Grip positions for hangboard testing and training."""

    HALF_CRIMP = "half_crimp"
    FULL_CRIMP = "full_crimp"
    OPEN_HAND = "open_hand"
    THREE_FINGER_DRAG = "three_finger_drag"


class EnergySystem(str, Enum):
    """Metabolic energy systems relevant to climbing.

    References:
        Hörst 2016 (:cite:`horst2016`) — energy system classification.
    """

    ALACTIC = "alactic"
    LACTIC = "lactic"
    AEROBIC = "aerobic"


# ---------------------------------------------------------------------------
# Grade Records
# ---------------------------------------------------------------------------


class GradeRecord(BaseModel):
    """A climbing grade in a specific system.

    Attributes:
        grade: Grade string (e.g. "7a", "V5").
        system: Grading system identifier (e.g. "french", "v_scale").
    """

    grade: str
    system: str = "french"


# ---------------------------------------------------------------------------
# Climber Profile
# ---------------------------------------------------------------------------


class ClimberProfile(BaseModel):
    """Complete athlete profile for assessment and planning.

    Attributes:
        name: Athlete identifier (can be pseudonym).
        body_weight_kg: Current body weight in kg.
        height_cm: Height in cm (optional).
        ape_index: Ape index ratio (wingspan / height), typically 0.96–1.04.
        experience_years: Years of climbing experience.
        level: Classification (beginner/intermediate/advanced/elite).
        primary_discipline: Main climbing discipline.
        boulder_redpoint: Hardest boulder sent.
        route_redpoint: Hardest route sent.
        boulder_onsight: Hardest boulder onsighted.
        route_onsight: Hardest route onsighted.
    """

    name: str
    body_weight_kg: float = Field(gt=0, description="Body weight in kg")
    height_cm: float | None = Field(default=None, gt=0)
    ape_index: float | None = Field(default=None, gt=0)
    experience_years: float = Field(ge=0)
    level: ClimberLevel = ClimberLevel.INTERMEDIATE
    primary_discipline: Discipline = Discipline.BOULDERING
    boulder_redpoint: GradeRecord | None = None
    route_redpoint: GradeRecord | None = None
    boulder_onsight: GradeRecord | None = None
    route_onsight: GradeRecord | None = None


# ---------------------------------------------------------------------------
# Assessment Models
# ---------------------------------------------------------------------------


class MVC7Test(BaseModel):
    """Maximal Voluntary Contraction — 7-second test result.

    The gold-standard finger strength test: 7s max hang on a 20mm edge
    in half-crimp position.

    Attributes:
        edge_size_mm: Edge depth (standard: 20mm).
        grip_type: Grip position used.
        body_weight_kg: Body weight at time of test.
        added_weight_kg: External weight added (negative for pulley assist).
        total_force_kg: body_weight_kg + added_weight_kg.
        percent_bw: total_force_kg / body_weight_kg * 100.

    References:
        Giles et al. 2006 (:cite:`giles2006`),
        López-Rivera & González-Badillo 2012 (:cite:`lopezrivera2012`).
    """

    edge_size_mm: int = 20
    grip_type: GripType = GripType.HALF_CRIMP
    body_weight_kg: float = Field(gt=0)
    added_weight_kg: float = 0.0
    total_force_kg: float | None = None
    percent_bw: float | None = None

    def model_post_init(self, __context: object) -> None:
        if self.total_force_kg is None:
            self.total_force_kg = self.body_weight_kg + self.added_weight_kg
        if self.percent_bw is None and self.body_weight_kg > 0:
            self.percent_bw = round(self.total_force_kg / self.body_weight_kg * 100, 1)


class CriticalForceTest(BaseModel):
    """Critical Force test result from multi-intensity repeater protocol.

    References:
        Jones et al. 2010 (:cite:`jones2010`),
        Fryer et al. 2018 (:cite:`fryer2018`).
    """

    cf_absolute_kg: float = Field(ge=0, description="Critical Force in kg")
    cf_percent_bw: float | None = Field(default=None, ge=0)
    w_prime_kj: float | None = Field(default=None, ge=0, description="W' anaerobic capacity")
    cf_mvc_ratio: float | None = Field(default=None, ge=0, le=1.0)


class PullUpTest(BaseModel):
    """Max pull-up test result."""

    max_reps: int = Field(ge=0)
    added_weight_kg: float = 0.0
    body_weight_kg: float = Field(gt=0)


class AssessmentResult(BaseModel):
    """Complete assessment battery result.

    Attributes:
        date: Date of the assessment.
        climber_name: Reference to climber profile.
        mvc7: MVC-7 test result.
        critical_force: CF test result (optional).
        pull_ups: Pull-up test result (optional).
        notes: Free-text notes.

    References:
        Testing protocol follows Lattice Research recommendations
        and López methodology.
    """

    date: date
    climber_name: str
    mvc7: MVC7Test | None = None
    critical_force: CriticalForceTest | None = None
    pull_ups: PullUpTest | None = None
    notes: str = ""


# ---------------------------------------------------------------------------
# Training Session Models
# ---------------------------------------------------------------------------


class ExerciseLog(BaseModel):
    """Single exercise within a training session.

    Attributes:
        protocol_id: Reference to protocol definition.
        sets_completed: Number of sets actually completed.
        loads_kg: Load per set (list of floats).
        durations_sec: Duration per set (list of floats).
        rpe: Perceived exertion (1–10) for this exercise.
        notes: Free-text notes.
    """

    protocol_id: str
    sets_completed: int = Field(ge=0)
    loads_kg: list[float] = Field(default_factory=list)
    durations_sec: list[float] = Field(default_factory=list)
    rpe: float | None = Field(default=None, ge=1, le=10)
    notes: str = ""


class SessionLog(BaseModel):
    """Complete training session log.

    Attributes:
        date: Session date.
        climber_name: Reference to climber profile.
        session_type: Type of session (e.g. "hangboard", "climbing", "antagonist").
        exercises: List of exercise logs.
        overall_rpe: Session-level RPE (1–10).
        finger_soreness: Pre-session finger soreness (0–5).
        subjective_recovery: Subjective recovery score (1–10).
        notes: Free-text notes.
    """

    date: date
    climber_name: str
    session_type: str = "hangboard"
    exercises: list[ExerciseLog] = Field(default_factory=list)
    overall_rpe: float | None = Field(default=None, ge=1, le=10)
    finger_soreness: int | None = Field(default=None, ge=0, le=5)
    subjective_recovery: int | None = Field(default=None, ge=1, le=10)
    notes: str = ""


# ---------------------------------------------------------------------------
# Protocol Models
# ---------------------------------------------------------------------------


class ProgressionRule(BaseModel):
    """Week-by-week progression for a training protocol.

    References:
        López 2014 (:cite:`lopez2014`) — 4-week cycle progression.
    """

    duration_weeks: int = Field(ge=1)
    volume_per_week: list[int] = Field(description="Sets per week for each week")
    intensity_change: str = "maintain"


class ProtocolParams(BaseModel):
    """Session parameters for a hangboard protocol.

    Attributes:
        edge_size_mm: Edge depth in mm.
        grip_type: Grip position.
        hang_duration_sec: Duration of each hang repetition.
        rest_between_reps_sec: Rest between reps within a set.
        reps_per_set: Repetitions per set.
        rest_between_sets_sec: Rest between sets.
        sets: Number of sets.
        intensity_percent_mvc: Target intensity as %MVC range.
    """

    edge_size_mm: int = 20
    grip_type: GripType = GripType.HALF_CRIMP
    hang_duration_sec: float = Field(gt=0)
    rest_between_reps_sec: float = Field(ge=0)
    reps_per_set: int = Field(ge=1)
    rest_between_sets_sec: float = Field(ge=0)
    sets: int = Field(ge=1)
    intensity_percent_mvc: tuple[float, float] = (80.0, 100.0)


class ProtocolDefinition(BaseModel):
    """Full definition of a hangboard training protocol.

    Attributes:
        id: Unique protocol identifier (e.g. "lopez-maxhang-maw").
        name: Human-readable name.
        author: Protocol author/source.
        energy_system: Targeted energy system.
        min_level: Minimum athlete level.
        params: Default session parameters.
        progression: Week-by-week progression rule.
        reference_key: BibTeX key for the source paper.

    References:
        Protocol sources documented per-protocol in ``docs/references.bib``.
    """

    id: str
    name: str
    author: str
    energy_system: EnergySystem = EnergySystem.ALACTIC
    min_level: ClimberLevel = ClimberLevel.INTERMEDIATE
    params: ProtocolParams
    progression: ProgressionRule | None = None
    reference_key: str = ""


# ---------------------------------------------------------------------------
# Injury & Load Tracking
# ---------------------------------------------------------------------------


class InjuryRecord(BaseModel):
    """Injury tracking record.

    References:
        Schöffl et al. 2003 (:cite:`schoffl2006`) — pulley injury grading.
        Vagy 2016 (:cite:`vagy2016`) — 4-phase rehab model.
    """

    date_onset: date
    location: str
    side: str = "bilateral"
    severity_grade: str = ""
    severity_0_5: int = Field(ge=0, le=5)
    rehab_phase: str = "mobility"
    notes: str = ""
    cleared_date: date | None = None


class WeeklyVolume(BaseModel):
    """Aggregated weekly training volume.

    References:
        Gabbett 2016 (:cite:`gabbett2016`) — ACWR framework.
    """

    week_start: date
    total_tut_sec: float = Field(ge=0, description="Total time under tension in seconds")
    num_sessions: int = Field(ge=0)
    avg_rpe: float | None = Field(default=None, ge=1, le=10)
    avg_finger_soreness: float | None = Field(default=None, ge=0, le=5)
