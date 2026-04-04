"""Grade conversion between climbing grading systems.

Supports five systems in two domains:

* **Route** (Sport/Trad): UIAA, French, YDS
* **Boulder**: Fontainebleau (Font), V-Scale (Hueco)

Cross-domain conversion (e.g. French to Font) is forbidden and raises
:class:`GradeDomainError`.

References:
    - Draper N, et al. (2015). Sports Technology 8(3-4), 88-94.
    - Mandelli G, Angriman A (2016). Scales of Difficulty. CAI.
    - Mountain Project (2024). International Climbing Grades.
    - Rockfax Publishing (2022). Grade Conversions.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Union

__all__ = [
    "RouteSystem", "BoulderSystem", "GradeSystem", "Grade",
    "GradeError", "UnknownSystemError", "UnknownGradeError", "GradeDomainError",
    "convert", "parse", "compare", "difficulty_index", "from_index", "all_grades",
]


class GradeError(Exception):
    """Base class for grade-related errors."""

class UnknownSystemError(GradeError):
    """Raised when the grading system is not recognised."""

class UnknownGradeError(GradeError):
    """Raised when a grade string is not found in the specified system."""

class GradeDomainError(GradeError):
    """Raised when converting between route and boulder domains."""


class RouteSystem(str, Enum):
    """Route (sport/trad) grading systems."""
    UIAA = "UIAA"
    FRENCH = "French"
    YDS = "YDS"


class BoulderSystem(str, Enum):
    """Boulder grading systems."""
    FONT = "Font"
    V_SCALE = "V-Scale"


GradeSystem = Union[RouteSystem, BoulderSystem]

_ROUTE_SYSTEMS = set(RouteSystem)
_BOULDER_SYSTEMS = set(BoulderSystem)


def _resolve_system(name):
    normalised = name.strip().lower().replace("-", "").replace("_", "")
    for sys in list(RouteSystem) + list(BoulderSystem):
        candidate = sys.value.lower().replace("-", "").replace("_", "")
        if normalised == candidate or normalised == sys.name.lower():
            return sys
    raise UnknownSystemError(f"Unknown grading system: '{name}'")


def _is_route(system):
    return system in _ROUTE_SYSTEMS


def _is_boulder(system):
    return system in _BOULDER_SYSTEMS


# Route: (ircra, uiaa, french, yds)
_ROUTE_TABLE = [
    (1, "I", "1", "5.2"), (2, "II", "2", "5.3"),
    (3, "III", "3", "5.4"), (4, "III+", "3+", "5.4+"),
    (5, "IV", "4a", "5.5"), (6, "IV+", "4b", "5.6"),
    (7, "V-", "4b+", "5.6+"), (8, "V", "4c", "5.7"),
    (9, "V+", "5a", "5.7+"), (10, "VI-", "5b", "5.8"),
    (11, "VI", "5c", "5.9"), (12, "VI+", "6a", "5.10a"),
    (13, "VII-", "6a+", "5.10b"), (14, "VII", "6b", "5.10c"),
    (15, "VII+", "6b+", "5.10d"),
    (16, "VIII-", "6c", "5.11a"),    # CAI: 6c
    (17, "VIII-", "6c+", "5.11b"),   # CAI: VIII-/6c+
    (18, "VIII", "7a", "5.11d"),
    (19, "VIII+", "7a+", "5.12a"),   # Convergence point
    (20, "IX-", "7b", "5.12b"), (21, "IX-", "7b+", "5.12c"),
    (22, "IX", "7c", "5.12d"),
    (23, "IX+", "7c+", "5.13a"),
    (24, "X-", "8a", "5.13b"), (25, "X-", "8a+", "5.13c"),
    (26, "X", "8b", "5.13d"),
    (27, "X+", "8b+", "5.14a"),
    (28, "XI-", "8c", "5.14b"), (29, "XI-", "8c+", "5.14c"),
    (30, "XI", "9a", "5.14d"),       # Action Directe
    (31, "XI+", "9a+", "5.15a"),
    (32, "XII-", "9b", "5.15b"), (33, "XII", "9b+", "5.15c"),
    (34, "XII+", "9c", "5.15d"),     # Silence
]

# Boulder: (ircra, font, v_scale)
_BOULDER_TABLE = [
    (11, "3", "VB"), (12, "4-", "V0-"), (13, "4", "V0"), (14, "4+", "V0+"),
    (15, "5", "V1"), (16, "5+", "V2"),
    (17, "6A", "V3"), (18, "6A+", "V3+"),
    (19, "6B", "V4"), (20, "6B+", "V4+"),
    (21, "6C", "V5"), (22, "6C+", "V5+"),
    (23, "7A", "V6"), (24, "7A+", "V7"),
    (25, "7B", "V8"), (26, "7B+", "V8+"),
    (27, "7C", "V9"), (28, "7C+", "V10"),
    (29, "8A", "V11"), (30, "8A+", "V12"),
    (31, "8B", "V13"), (32, "8B+", "V14"),
    (33, "8C", "V15"), (34, "8C+", "V16"),
    (35, "9A", "V17"),
]

_ROUTE_COL = {RouteSystem.UIAA: 1, RouteSystem.FRENCH: 2, RouteSystem.YDS: 3}
_ROUTE_LOOKUP = {}
for _sys, _col in _ROUTE_COL.items():
    _ROUTE_LOOKUP[_sys] = {}
    for _i, _row in enumerate(_ROUTE_TABLE):
        _key = _row[_col].lower()
        if _key not in _ROUTE_LOOKUP[_sys]:
            _ROUTE_LOOKUP[_sys][_key] = _i

_BOULDER_COL = {BoulderSystem.FONT: 1, BoulderSystem.V_SCALE: 2}
_BOULDER_LOOKUP = {}
for _sys, _col in _BOULDER_COL.items():
    _BOULDER_LOOKUP[_sys] = {}
    for _i, _row in enumerate(_BOULDER_TABLE):
        _key = _row[_col].lower()
        if _key not in _BOULDER_LOOKUP[_sys]:
            _BOULDER_LOOKUP[_sys][_key] = _i

_PATTERNS = [
    (RouteSystem.YDS, re.compile(r"^5\.\d{1,2}[a-d]?\+?$", re.IGNORECASE)),
    (BoulderSystem.V_SCALE, re.compile(r"^(VB|V\d{1,2})\+?-?$", re.IGNORECASE)),
    (BoulderSystem.FONT, re.compile(r"^\d[A-C]?\+?-?$")),
    (RouteSystem.FRENCH, re.compile(r"^\d[a-c]\+?$")),
    (RouteSystem.UIAA, re.compile(r"^[IVX]{1,5}[-+]?$", re.IGNORECASE)),
]


@dataclass(frozen=True)
class Grade:
    """An immutable climbing grade with system and IRCRA difficulty index."""
    system: Union[RouteSystem, BoulderSystem]
    value: str
    difficulty_index: int

    def __lt__(self, other):
        if not isinstance(other, Grade): return NotImplemented
        return self.difficulty_index < other.difficulty_index

    def __le__(self, other):
        if not isinstance(other, Grade): return NotImplemented
        return self.difficulty_index <= other.difficulty_index

    def __gt__(self, other):
        if not isinstance(other, Grade): return NotImplemented
        return self.difficulty_index > other.difficulty_index

    def __ge__(self, other):
        if not isinstance(other, Grade): return NotImplemented
        return self.difficulty_index >= other.difficulty_index

    def __str__(self):
        return self.value


def _find_route_row(grade_str, system):
    normalised = grade_str.strip().lower()
    lookup = _ROUTE_LOOKUP.get(system)
    if lookup is None:
        raise UnknownSystemError(f"Unknown route system: {system}")
    idx = lookup.get(normalised)
    if idx is None:
        raise UnknownGradeError(f"Grade '{grade_str}' not found in {system.value} system.")
    return idx


def _find_boulder_row(grade_str, system):
    normalised = grade_str.strip().lower()
    lookup = _BOULDER_LOOKUP.get(system)
    if lookup is None:
        raise UnknownSystemError(f"Unknown boulder system: {system}")
    idx = lookup.get(normalised)
    if idx is None:
        raise UnknownGradeError(f"Grade '{grade_str}' not found in {system.value} system.")
    return idx


def difficulty_index(grade_str, system):
    """Return the IRCRA difficulty index for a grade."""
    sys = system if isinstance(system, (RouteSystem, BoulderSystem)) else _resolve_system(system)
    if _is_route(sys):
        row = _find_route_row(grade_str, sys)
        return _ROUTE_TABLE[row][0]
    else:
        row = _find_boulder_row(grade_str, sys)
        return _BOULDER_TABLE[row][0]


def convert(grade_str, from_system, to_system):
    """Convert a grade from one system to another."""
    from_sys = from_system if isinstance(from_system, (RouteSystem, BoulderSystem)) else _resolve_system(from_system)
    to_sys = to_system if isinstance(to_system, (RouteSystem, BoulderSystem)) else _resolve_system(to_system)

    if _is_route(from_sys) and _is_boulder(to_sys):
        raise GradeDomainError(f"Cannot convert route grade ({from_sys.value}) to boulder system ({to_sys.value}).")
    if _is_boulder(from_sys) and _is_route(to_sys):
        raise GradeDomainError(f"Cannot convert boulder grade ({from_sys.value}) to route system ({to_sys.value}).")

    if from_sys == to_sys:
        if _is_route(from_sys):
            row_idx = _find_route_row(grade_str, from_sys)
            return _ROUTE_TABLE[row_idx][_ROUTE_COL[from_sys]]
        else:
            row_idx = _find_boulder_row(grade_str, from_sys)
            return _BOULDER_TABLE[row_idx][_BOULDER_COL[from_sys]]

    if _is_route(from_sys):
        src_row = _find_route_row(grade_str, from_sys)
        return _ROUTE_TABLE[src_row][_ROUTE_COL[to_sys]]

    src_row = _find_boulder_row(grade_str, from_sys)
    return _BOULDER_TABLE[src_row][_BOULDER_COL[to_sys]]


def parse(grade_str):
    """Auto-detect the grading system and return a Grade object."""
    cleaned = grade_str.strip()
    for system, pattern in _PATTERNS:
        if pattern.match(cleaned):
            try:
                if _is_route(system):
                    row_idx = _find_route_row(cleaned, system)
                    row = _ROUTE_TABLE[row_idx]
                    return Grade(system=system, value=row[_ROUTE_COL[system]], difficulty_index=row[0])
                else:
                    row_idx = _find_boulder_row(cleaned, system)
                    row = _BOULDER_TABLE[row_idx]
                    return Grade(system=system, value=row[_BOULDER_COL[system]], difficulty_index=row[0])
            except (UnknownGradeError, UnknownSystemError):
                continue
    raise UnknownGradeError(f"Cannot auto-detect grading system for '{grade_str}'")


def compare(a, b):
    """Compare two grades from any system by their IRCRA index."""
    ga, gb = parse(a), parse(b)
    if ga.difficulty_index < gb.difficulty_index: return -1
    if ga.difficulty_index > gb.difficulty_index: return 1
    return 0


def from_index(index, system):
    """Return the nearest grade for a given IRCRA difficulty index."""
    sys = system if isinstance(system, (RouteSystem, BoulderSystem)) else _resolve_system(system)
    if _is_route(sys):
        col, table = _ROUTE_COL[sys], _ROUTE_TABLE
    else:
        col, table = _BOULDER_COL[sys], _BOULDER_TABLE
    best_row = min(table, key=lambda row: (abs(row[0] - index), -row[0]))
    return best_row[col]


def all_grades(system):
    """Return all grades in a system, sorted by difficulty (ascending)."""
    sys = system if isinstance(system, (RouteSystem, BoulderSystem)) else _resolve_system(system)
    if _is_route(sys):
        col = _ROUTE_COL[sys]
        return [Grade(system=sys, value=row[col], difficulty_index=row[0]) for row in _ROUTE_TABLE]
    else:
        col = _BOULDER_COL[sys]
        return [Grade(system=sys, value=row[col], difficulty_index=row[0]) for row in _BOULDER_TABLE]
