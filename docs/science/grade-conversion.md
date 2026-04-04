# Grade Conversion — Science

## The IRCRA Standard

The International Rock Climbing Research Association (IRCRA) published a position
statement (Draper et al. 2015) standardising the comparison of climbing grades
across different systems worldwide.

Every grade in this library maps to an **IRCRA difficulty index** (integers 1-35),
which serves as the canonical comparison axis.

## Two Domains

Climbing grades fall into two separate domains:

### Route Grades (lead / top-rope)

| System | Region | Range | Example |
|--------|--------|-------|---------|
| **UIAA** | Central Europe | I - XII+ | VII+, X- |
| **French** | Europe (sport) | 1 - 9c | 7a, 8b+ |
| **YDS** | North America | 5.0 - 5.15d | 5.12a, 5.14c |

### Boulder Grades

| System | Region | Range | Example |
|--------|--------|-------|---------|
| **Font** (Fontainebleau) | Europe | 3 - 9A | 7A, 8B+ |
| **V-Scale** (Hueco) | Worldwide | V0 - V17 | V5, V10 |

!!! warning "Domain Separation"
    Converting between route and boulder systems (e.g. French -> V-Scale)
    raises a `GradeDomainError`. Use `from_index()` for cross-domain
    difficulty comparison.

## Difficulty Index

All grades map to an **IRCRA difficulty index** (1-35), which allows
cross-system comparison:

```python
from climbing_science.grades import parse, compare

# Are these the same difficulty?
print(compare("V5", "6c+"))  # compares by IRCRA index
print(compare("8a", "V10"))  # cross-domain comparison works
```

## French vs Font Disambiguation

French sport grades and Fontainebleau boulder grades overlap in notation
(both use numbers + letters). The library disambiguates by **case**:

- **Lowercase** -> French sport: `7a`, `6b+`, `8c`
- **Uppercase** -> Font boulder: `7A`, `6B+`, `8C`

## Usage

```python
from climbing_science.grades import convert, RouteSystem, BoulderSystem

# Within route domain: French -> YDS
print(convert("7a", "French", "YDS"))  # -> "5.11d"

# Within boulder domain: V-Scale -> Font
print(convert("V5", "V-Scale", "Font"))  # -> "7A"

# Cross-domain via index
from climbing_science.grades import from_index, difficulty_index
idx = difficulty_index("7a", "French")
print(from_index(idx, BoulderSystem.V_SCALE))  # approximate boulder equivalent
```

## Primary Sources

| Source | Used for |
|--------|----------|
| Draper et al. 2015 | IRCRA numerical index (1-35) |
| CAI / Mandelli 2016 | UIAA official conversion tables |
| Mountain Project 2024 | Community consensus cross-check |
| Rockfax 2022 | European standard cross-check |
