"""Climbing Science - Open-source Python library for evidence-based climbing training analysis."""

__version__ = "0.2.0"

from climbing_science.diagnostics import (
    classify_level,
    identify_weakness,
    progress_delta,
    training_priority,
)
from climbing_science.edge_depth import (
    CORRECTION_RATE,
    MAX_EDGE_MM,
    MIN_EDGE_MM,
    REFERENCE_EDGE_MM,
    convert_force,
    correction_factor,
    estimate_force_at_depth,
    normalize_to_reference,
)
from climbing_science.endurance import (
    cf_mvc_ratio,
    classify_endurance,
    critical_force,
    interpret_cf_ratio,
    time_to_failure,
    w_prime_balance,
)
from climbing_science.grades import (
    Grade,
    GradeSystem,
    compare,
    convert,
    difficulty_index,
    parse,
)
from climbing_science.io import (
    export_assessment_json,
    export_assessment_markdown,
    read_force_csv,
)
from climbing_science.load import (
    acwr,
    effort_level_to_mvc_pct,
    margin_to_failure,
    mvc_pct_to_rpe,
    overtraining_check,
    rpe_to_mvc_pct,
    tut_per_session,
    tut_per_set,
    weekly_load,
)
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
from climbing_science.periodization import (
    MacroCycle,
    MesoCycle,
    MicroCycle,
    generate_macrocycle,
    generate_mesocycle,
    generate_microcycle,
    validate_constraints,
)
from climbing_science.protocols import (
    format_notation,
    get_protocol,
    list_protocols,
    select_protocols,
)
from climbing_science.signal import (
    Peak,
    RFDResult,
    SegmentedRep,
    best_n_second_average,
    compute_impulse,
    compute_rfd,
    detect_peaks,
    segment_repeaters,
    smooth,
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
    "BoulderSystem",
    "Grade",
    "GradeDomainError",
    "GradeError",
    "GradeSystem",
    "RouteSystem",
    "UnknownGradeError",
    "UnknownSystemError",
    "all_grades",
    "compare",
    "convert",
    "difficulty_index",
    "from_index",
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
    # signal
    "Peak",
    "RFDResult",
    "SegmentedRep",
    "best_n_second_average",
    "compute_impulse",
    "compute_rfd",
    "detect_peaks",
    "segment_repeaters",
    "smooth",
    # strength
    "grade_to_mvc7",
    "mvc7_to_grade",
    "power_to_weight",
    "rfd_from_curve",
    "rohmert_conversion",
    # edge_depth
    "CORRECTION_RATE",
    "MAX_EDGE_MM",
    "MIN_EDGE_MM",
    "REFERENCE_EDGE_MM",
    "convert_force",
    "correction_factor",
    "estimate_force_at_depth",
    "normalize_to_reference",
    # endurance
    "cf_mvc_ratio",
    "classify_endurance",
    "critical_force",
    "interpret_cf_ratio",
    "time_to_failure",
    "w_prime_balance",
    # load
    "acwr",
    "effort_level_to_mvc_pct",
    "margin_to_failure",
    "mvc_pct_to_rpe",
    "overtraining_check",
    "rpe_to_mvc_pct",
    "tut_per_session",
    "tut_per_set",
    "weekly_load",
    # protocols
    "format_notation",
    "get_protocol",
    "list_protocols",
    "select_protocols",
    # periodization
    "MacroCycle",
    "MesoCycle",
    "MicroCycle",
    "generate_macrocycle",
    "generate_mesocycle",
    "generate_microcycle",
    "validate_constraints",
    # diagnostics
    "classify_level",
    "identify_weakness",
    "progress_delta",
    "training_priority",
    # io
    "export_assessment_json",
    "export_assessment_markdown",
    "read_force_csv",
]
