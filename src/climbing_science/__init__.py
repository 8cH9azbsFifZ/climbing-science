"""Climbing Science - Open-source Python library for evidence-based climbing training analysis."""

__version__ = "0.1.0"

from climbing_science.endurance import (
    cf_mvc_ratio,
    classify_endurance,
    critical_force,
    interpret_cf_ratio,
    time_to_failure,
    w_prime_balance,
)
from climbing_science.grades import Grade, GradeSystem, compare, convert, difficulty_index, parse
from climbing_science.models import (
    AssessmentResult,
    ClimberLevel,
    ClimberProfile,
    CriticalForceTest,
    Discipline,
    EnergySystem,
    GradeRecord,
    GripType,
    MVC7Test,
    SessionLog,
)
from climbing_science.strength import (
    grade_to_mvc7,
    mvc7_to_grade,
    power_to_weight,
    rfd_from_curve,
    rohmert_conversion,
)

__all__ = [
    "__version__",
    # grades
    "Grade",
    "GradeSystem",
    "compare",
    "convert",
    "difficulty_index",
    "parse",
    # models
    "AssessmentResult",
    "ClimberLevel",
    "ClimberProfile",
    "CriticalForceTest",
    "Discipline",
    "EnergySystem",
    "GradeRecord",
    "GripType",
    "MVC7Test",
    "SessionLog",
    # strength
    "grade_to_mvc7",
    "mvc7_to_grade",
    "power_to_weight",
    "rfd_from_curve",
    "rohmert_conversion",
    # endurance
    "cf_mvc_ratio",
    "classify_endurance",
    "critical_force",
    "interpret_cf_ratio",
    "time_to_failure",
    "w_prime_balance",
]
