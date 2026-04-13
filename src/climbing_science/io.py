"""Data I/O — import/export for force-gauge data, sessions, and reports.

Handles CSV import for common force-gauge formats, JSON session log
round-trips, and assessment report export in Markdown and JSON.
"""

from __future__ import annotations

import csv
import io
import json

from climbing_science.models import (
    ClimberProfile,
    MVC7Test,
    SessionLog,
)

__all__ = [
    "read_force_csv",
    "export_session_json",
    "import_session_json",
    "export_assessment_markdown",
    "export_assessment_json",
]


def read_force_csv(
    source: str,
    time_col: str = "time_s",
    force_col: str = "force_kg",
    delimiter: str = ",",
) -> list[tuple[float, float]]:
    """Parse a force-gauge CSV file into time-force pairs.

    Handles common CSV formats from Tindeq, Climbro, and generic
    force gauges.  Expects at minimum a time column and a force column.

    Args:
        source: CSV content as string (not file path).
        time_col: Name of the time column.
        force_col: Name of the force column.
        delimiter: CSV delimiter character.

    Returns:
        List of (time_seconds, force_kg) tuples.

    Raises:
        ValueError: If required columns are missing.

    References:
        Input format follows Tindeq Progressor CSV conventions
        (80 Hz sampling, :cite:`levernier2019`).

    Examples:
        >>> data = "time_s,force_kg\\n0.0,0.0\\n0.1,5.2\\n0.2,10.1"
        >>> read_force_csv(data)
        [(0.0, 0.0), (0.1, 5.2), (0.2, 10.1)]
    """
    reader = csv.DictReader(io.StringIO(source), delimiter=delimiter)

    if reader.fieldnames is None:
        raise ValueError("CSV has no header row")

    if time_col not in reader.fieldnames:
        raise ValueError(f"Time column '{time_col}' not found. Available columns: {', '.join(reader.fieldnames)}")
    if force_col not in reader.fieldnames:
        raise ValueError(f"Force column '{force_col}' not found. Available columns: {', '.join(reader.fieldnames)}")

    result = []
    for row in reader:
        try:
            t = float(row[time_col])
            f = float(row[force_col])
            result.append((t, f))
        except (ValueError, KeyError) as e:
            raise ValueError(f"Error parsing row: {row}") from e

    return result


def export_session_json(session: SessionLog) -> str:
    """Export a SessionLog to JSON string.

    Args:
        session: Session log to export.

    Returns:
        JSON string representation.

    References:
        Schema follows :class:`~climbing_science.models.SessionLog`
        (López 2014 :cite:`lopez2014` methodology).

    Examples:
        >>> from datetime import date
        >>> s = SessionLog(date=date(2026, 4, 3), climber_name="test")
        >>> json_str = export_session_json(s)
        >>> '"climber_name": "test"' in json_str
        True
    """
    return session.model_dump_json(indent=2)


def import_session_json(json_str: str) -> SessionLog:
    """Import a SessionLog from JSON string.

    Args:
        json_str: JSON string to parse.

    Returns:
        Validated SessionLog instance.

    Raises:
        ValidationError: If JSON doesn't match SessionLog schema.

    References:
        Schema follows :class:`~climbing_science.models.SessionLog`
        (López 2014 :cite:`lopez2014` methodology).

    Examples:
        >>> from datetime import date
        >>> s = SessionLog(date=date(2026, 4, 3), climber_name="test")
        >>> s2 = import_session_json(export_session_json(s))
        >>> s2.climber_name
        'test'
    """
    return SessionLog.model_validate_json(json_str)


def export_assessment_markdown(
    profile: ClimberProfile,
    mvc_test: MVC7Test | None = None,
    grade_prediction: str | None = None,
    level: str | None = None,
    weaknesses: list[str] | None = None,
    priority: str | None = None,
) -> str:
    """Generate a Markdown assessment report.

    Args:
        profile: Climber profile data.
        mvc_test: MVC-7 test result (optional).
        grade_prediction: Predicted grade string (optional).
        level: Classified level (optional).
        weaknesses: Identified weaknesses (optional).
        priority: Training priority (optional).

    Returns:
        Markdown-formatted report string.

    References:
        Assessment structure follows published best practice
        and Giles et al. (2006) :cite:`giles2006` MVC-7 protocol.
        >>> '# Climbing Assessment' in md
        True
    """
    lines = [
        "# Climbing Assessment",
        "",
        f"**Climber:** {profile.name}",
        f"**Body Weight:** {profile.body_weight_kg} kg",
        f"**Experience:** {profile.experience_years} years",
        f"**Level:** {profile.level.value}",
        "",
    ]

    if mvc_test is not None:
        lines.extend(
            [
                "## Finger Strength (MVC-7)",
                "",
                f"- Edge: {mvc_test.edge_size_mm} mm",
                f"- Grip: {mvc_test.grip_type.value}",
                f"- Total Force: {mvc_test.total_force_kg} kg",
                f"- %BW: {mvc_test.percent_bw}%",
                "",
            ]
        )

    if grade_prediction is not None:
        lines.extend(
            [
                f"**Predicted Grade:** {grade_prediction}",
                "",
            ]
        )

    if level is not None:
        lines.extend(
            [
                f"**Classification:** {level}",
                "",
            ]
        )

    if weaknesses:
        lines.extend(
            [
                "## Identified Weaknesses",
                "",
            ]
        )
        for w in weaknesses:
            lines.append(f"- {w}")
        lines.append("")

    if priority is not None:
        lines.extend(
            [
                f"**Training Priority:** {priority}",
                "",
            ]
        )

    lines.extend(
        [
            "---",
            "*Generated by climbing-science*",
        ]
    )

    return "\n".join(lines)


def export_assessment_json(
    profile: ClimberProfile,
    mvc_test: MVC7Test | None = None,
    grade_prediction: str | None = None,
    level: str | None = None,
    weaknesses: list[str] | None = None,
    priority: str | None = None,
) -> str:
    """Export assessment data as JSON.

    Args:
        profile: Climber profile data.
        mvc_test: MVC-7 test result (optional).
        grade_prediction: Predicted grade (optional).
        level: Classified level (optional).
        weaknesses: Identified weaknesses (optional).
        priority: Training priority (optional).

    Returns:
        JSON string.

    References:
        Assessment structure follows published best practice
        and Giles et al. (2006) :cite:`giles2006` MVC-7 protocol.
        >>> '"name": "Test"' in j
        True
    """
    data: dict = {
        "profile": json.loads(profile.model_dump_json()),
    }

    if mvc_test is not None:
        data["mvc7_test"] = json.loads(mvc_test.model_dump_json())

    if grade_prediction is not None:
        data["grade_prediction"] = grade_prediction

    if level is not None:
        data["level"] = level

    if weaknesses is not None:
        data["weaknesses"] = weaknesses

    if priority is not None:
        data["training_priority"] = priority

    return json.dumps(data, indent=2, default=str)
