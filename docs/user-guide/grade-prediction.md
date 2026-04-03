# Grade Prediction from Finger Strength

## How It Works

The `mvc7_to_grade()` function maps your MVC-7 finger strength (as % of body weight)
to an expected climbing grade. The inverse, `grade_to_mvc7()`, tells you what strength
you need for a target grade.

## The Data Behind It

The mapping is based on composite benchmark data from multiple sources:

| Source | Sample Size | Method |
|--------|------------|--------|
| Lattice Training | n ≈ 901 | Lab-tested MVC-7 + verified climbing grade |
| Aggregated survey data | n ≈ 2000 | Self-reported MVC-7 + grade |
| r/climbharder 2017 | n = 555 | Community survey |

All measurements follow the same protocol:
**20 mm edge, half-crimp, 7-second maximum hang.**

## Benchmark Table

| Grade (French) | MVC-7 (%BW) | Grade (YDS) | Grade (V-Scale) |
|----------------|-------------|-------------|-----------------|
| 5a | 70% | 5.9 | — |
| 6a | 93% | 5.10d | V2 |
| 6a+ | 100% | 5.11a | V3 |
| 6c+ | 122% | 5.12a | V5 |
| 7a | 128% | 5.12b | V5+ |
| 7b | 140% | 5.12d | V7 |
| 7c+ | 160% | 5.13b | V8+ |
| 8a | 167% | 5.13d | V10 |
| 8c | 195% | 5.14d | V14 |

## Usage

### Forward: Strength → Grade

```python
from climbing_science.strength import mvc7_to_grade
from climbing_science.grades import GradeSystem

# 70 kg climber, can add 25 kg → 135.7% BW
grade = mvc7_to_grade(135.7)
print(f"Expected: {grade}")  # → 7a+

# In other systems
print(mvc7_to_grade(135.7, GradeSystem.YDS))      # → 5.12c
print(mvc7_to_grade(135.7, GradeSystem.V_SCALE))   # → V6
```

### Inverse: Target Grade → Required Strength

```python
from climbing_science.strength import grade_to_mvc7

# What MVC-7 do I need for 7b?
required = grade_to_mvc7("7b")
print(f"Required: {required}% BW")  # → 140.0

# For any system
from climbing_science.grades import GradeSystem
required = grade_to_mvc7("5.13a", GradeSystem.YDS)
print(f"Required for 5.13a: {required}% BW")  # → 147.0
```

### Training Target Calculation

```python
from climbing_science.strength import grade_to_mvc7

target_grade = "7a"
body_weight = 70.0

required_pct = grade_to_mvc7(target_grade)
required_kg = body_weight * required_pct / 100.0
added_weight = required_kg - body_weight

print(f"Target: {target_grade}")
print(f"Required MVC-7: {required_pct}% BW = {required_kg:.1f} kg total")
print(f"Added weight needed: {added_weight:.1f} kg")
```

## Limitations

!!! warning "Strength Is Not Everything"
    Finger strength (MVC-7) explains roughly **50–60% of climbing performance
    variance** (Giles et al. 2006).  Other factors include:

    - **Technique** (foot placement, body positioning, reading sequences)
    - **Endurance** (Critical Force / CF, see [Critical Force](../science/critical-force.md))
    - **Body composition** (power-to-weight ratio)
    - **Mental skills** (fear management, route reading)
    - **Flexibility** (hip opening, shoulder mobility)

    A climber with 130% BW MVC-7 and excellent technique may outperform
    a climber with 150% BW and poor technique.

## References

- Giles, L.V. et al. (2006). *The physiology of rock climbing.* \[cite:giles2006\]
- Lattice Training benchmark data (n ≈ 901).
- López-Rivera, E. & González-Badillo, J.J. (2012). \[cite:lopezrivera2012\]
