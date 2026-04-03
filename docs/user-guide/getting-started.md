# Getting Started

## Installation

```bash
pip install climbing-science
```

Or for development (includes docs, testing, linting):

```bash
git clone https://github.com/8cH9azbsFifZ/climbing-science.git
cd climbing-science
pip install -e ".[dev]"
```

## First Assessment: Where Do I Stand?

The simplest entry point is a **finger strength assessment**.  All you need is
a hangboard with a 20 mm edge and a way to measure added weight (a sling + plates,
or a pulley system for assistance).

### Step 1: Measure Your MVC-7

Hang with both hands on a 20 mm edge in **half-crimp** position for **7 seconds**.
Add weight until you can just barely hold for 7 seconds.

```python
from climbing_science.models import MVC7Test

test = MVC7Test(
    body_weight_kg=70.0,
    added_weight_kg=18.0,  # sling + plates
)
print(f"Total force: {test.total_force_kg} kg")
print(f"Strength:    {test.percent_bw}% BW")
```

```
Total force: 88.0 kg
Strength:    125.7% BW
```

### Step 2: What Grade Can I Expect?

```python
from climbing_science.strength import mvc7_to_grade, grade_to_mvc7
from climbing_science.grades import GradeSystem

# Your current level
grade = mvc7_to_grade(125.7)
print(f"Expected grade: {grade}")  # → 6c+

# Same in other systems
print(f"YDS:  {mvc7_to_grade(125.7, GradeSystem.YDS)}")    # → 5.12a
print(f"UIAA: {mvc7_to_grade(125.7, GradeSystem.UIAA)}")   # → IX
```

### Step 3: What Do I Need for My Target Grade?

```python
# Target: 7a
required = grade_to_mvc7("7a")
print(f"Required MVC-7 for 7a: {required}% BW")  # → 128.0% BW

# How much added weight is that at 70 kg?
bw = 70.0
added_kg = bw * (required / 100.0) - bw
print(f"Added weight needed: {added_kg:.1f} kg")  # → 19.6 kg
```

### Step 4: Classify Your Level

```python
from climbing_science.strength import power_to_weight

ratio, level = power_to_weight(mvc_kg=88.0, body_weight_kg=70.0)
print(f"Power-to-weight: {ratio}% BW → {level}")  # → 125.7% BW → intermediate
```

## Next Steps

- **[Hangboard Training](hangboard-training.md)** — How to use Rohmert's curve for training load calculation
- **[Grade Prediction](grade-prediction.md)** — Deep dive into the MVC-7 → grade model
- **[Rohmert Curve (Science)](../science/rohmert-curve.md)** — The math behind endurance normalisation
