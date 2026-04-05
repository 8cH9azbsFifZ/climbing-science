# climbing-science — Implementation Plan

## Vision

Open-source Python library for climbing science calculations.
Fills the gap between proprietary web calculators (StrengthClimbing.com)
and raw data from Tindeq/Climbro force measurements.

**Principles:**

- Every formula with source reference (paper, book, page)
- Validated against published benchmarks (Lattice, Giles et al.)
- Zero dependencies in core (only stdlib + numpy optional)
- Compatible with Tindeq JSON from FingerForceTraining iOS app

---

## Gap Analysis

### What Exists Where

| Capability                       | Python |
| -------------------------------- | ------ |
| Rohmert curve (fatigue model)    | ❌     |
| Edge depth correction (Amca)     | ❌     |
| MVC-7 → grade prediction         | ❌     |
| Critical Force (CF/W')           | ❌     |
| Hangboard Load Calculator        | ❌     |
| Sport Climbing Level Calculator  | ❌     |
| RFD analysis                     | ❌     |
| Tindeq JSON → Assessment         | ❌     |
| Force curve signal processing    | ❌     |

### Core Gap

There is **no open, validated Python library** for climbing science calculations.
StrengthClimbing has everything as proprietary JavaScript behind a paywall.
The Copilot skills *describe* the formulas. The iOS app *measures*.
But **nobody calculates openly and reproducibly**.

---

## Architecture — Four Layers + Canonical Data Model

### Design Goal

The library shall be **device- and app-agnostic**:

- Tindeq Progressor, Climbro, Griptonite, Crane Scale, manual input — doesn't matter
- FingerForceTraining iOS, Tindeq App, Climbro App, CSV export — doesn't matter
- CLI, Jupyter Notebook, Web API, Swift embedding — doesn't matter

This requires a **canonical data model** as a lingua franca between
all sources and all calculations.

### Layer Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    Layer 4: FRONTENDS                        │
│         Concrete applications — interchangeable             │
│                                                             │
│  cli.py            CLI runner ($ climbing-science analyze)  │
│  notebook.py       Jupyter helpers (Plot, DataFrame export) │
│  report.py         Assessment report (Markdown/HTML/dict)   │
└──────────────────────────┬──────────────────────────────────┘
                           │ uses
┌──────────────────────────▼──────────────────────────────────┐
│                    Layer 3: I/O ADAPTERS                     │
│         Reads/writes external formats → canonical model     │
│                                                             │
│  adapters/                                                  │
│    tindeq.py       FingerForceTraining JSON & Tindeq App    │
│    climbro.py      Climbro CSV/JSON                         │
│    griptonite.py   Griptonite data (format TBD)             │
│    manual.py       Manual input (BW, MVC-7, hang time)      │
│    csv_generic.py  Generic CSV import (time, force)         │
└──────────────────────────┬──────────────────────────────────┘
                           │ produces/consumes
┌──────────────────────────▼──────────────────────────────────┐
│              CANONICAL DATA MODEL (datamodel.py)            │
│         Device-agnostic — the "currency" of the library     │
│                                                             │
│  ForceSample(time_s, force_kg)                              │
│  ForceSession(samples, metadata, segments?)                 │
│  AthleteProfile(weight_kg, height_cm?, fmax_r, fmax_l, ..) │
│  TestResult(mvc7_kg, cf_kg?, rfd?, grade_prediction?)       │
└──────────┬───────────────────────────────┬──────────────────┘
           │ uses                          │ uses
┌──────────▼──────────┐  ┌────────────────▼───────────────────┐
│  Layer 2: EXERCISES  │  │                                    │
│  Protocols & Plan    │  │                                    │
│                      │  │                                    │
│  protocols.py        │  │                                    │
│  hangboard_calc.py   │  │                                    │
└──────────┬───────────┘  │                                    │
           │ uses         │                                    │
┌──────────▼──────────────▼───────────────────────────────────┐
│                    Layer 1: MODELS                            │
│         Pure mathematics — no I/O, no state                  │
│                                                              │
│  rohmert.py          Isometric fatigue curve                  │
│  edge_depth.py       Edge depth correction                    │
│  critical_force.py   CF/W' from 3-point test                  │
│  strength_analyzer   MVC → grade prediction                   │
│  grades.py           Grade conversion                         │
│  signal.py           Force curve signal processing            │
└──────────────────────────────────────────────────────────────┘
```

### Why This Separation?

| Layer | Responsibility | Dependencies | Change Frequency |
| ------- | ------------- | -------------- | ------------------- |
| **Models** | Physics & mathematics | None (pure functions) | Rarely (paper-based) |
| **Data Model** | Canonical types | None (dataclasses) | Rarely |
| **Exercises** | What is being trained | Models + data model | Medium (new protocols) |
| **I/O Adapters** | Format conversion | Only data model | Medium (new devices) |
| **Frontends** | Presentation & UX | Everything | Often (CLI, Notebook, Web) |

**Rules:**

1. Each layer only knows the one below it
2. Models know nothing about protocols, devices, or UI
3. I/O Adapters import **only** the data model, never Models directly
4. Frontends orchestrate — they connect Adapter → Models → Output
5. **Everything above the data model is interchangeable**

### Canonical Data Model — The Bridge

```python
# datamodel.py — Device-agnostic, app-agnostic

from dataclasses import dataclass, field

@dataclass(frozen=True)
class ForceSample:
    """A single force measurement value."""
    time_s: float       # Seconds since session start
    force_kg: float     # Force in kg

@dataclass
class ForceSession:
    """A measurement session — regardless of where the data comes from."""
    samples: list[ForceSample]
    sample_rate_hz: float | None = None  # e.g. 80 (Tindeq), 100 (Climbro)
    metadata: dict = field(default_factory=dict)
    # metadata can contain:
    #   "device": "tindeq_progressor" | "climbro" | "manual" | ...
    #   "test_type": "mvc7" | "continuous" | "repeater" | ...
    #   "hold_type": "20mm_edge" | "18mm_edge" | "pinch" | ...
    #   "hand": "R" | "L" | "both"
    #   "date": "2026-04-01T18:30:00Z"

    @property
    def duration_s(self) -> float:
        if not self.samples:
            return 0.0
        return self.samples[-1].time_s - self.samples[0].time_s

    @property
    def peak_force_kg(self) -> float:
        return max(s.force_kg for s in self.samples) if self.samples else 0.0

@dataclass
class AthleteProfile:
    """Athlete profile — all calculations refer to this."""
    weight_kg: float
    height_cm: float | None = None
    arm_span_cm: float | None = None
    sex: str | None = None              # "M" | "F"
    fmax_right_kg: float | None = None  # MVC-7 right hand
    fmax_left_kg: float | None = None   # MVC-7 left hand
    training_mode: int = 1              # 1=no HB, 2=Repeaters, 3=MaxHangs, 4=MaxHangs+added

@dataclass
class TestResult:
    """Result of an evaluation — device-agnostic."""
    mvc7_kg: float | None = None
    mvc_bw_ratio: float | None = None
    cf_kg: float | None = None
    w_prime_kgs: float | None = None
    rfd_kg_s: float | None = None
    predicted_boulder: str | None = None
    predicted_sport: str | None = None
    assessment: str | None = None
```

**Why `frozen=True` for ForceSample?** Measurement values are immutable.
Once measured, never mutated. This makes the data hashable and thread-safe.

### Device Independence in Practice

```python
# Tindeq Progressor:
from climbing_science.adapters import tindeq
session = tindeq.load("session_20260401.json")

# Climbro:
from climbing_science.adapters import climbro
session = climbro.load("climbro_export.csv")

# Manual input (no device needed):
from climbing_science.adapters import manual
session = manual.from_mvc7_test(bodyweight_kg=65, added_kg=32, hang_time_s=7)

# Generic CSV (e.g. from Arduino force sensor):
from climbing_science.adapters import csv_generic
session = csv_generic.load("kraft_messung.csv", time_col="t_s", force_col="f_kg")

# From here everything is identical — regardless of which device:
from climbing_science.models import signal, strength_analyzer
mvc7 = signal.best_n_second_average(session, n_seconds=7.0)
grade = strength_analyzer.predict_grade(mvc7_kg=mvc7, bodyweight_kg=65)
```

### Jupyter Notebook Usage

Layers 1 + 2 are immediately usable in Jupyter — no app layer needed:

```python
# In a Jupyter Notebook:
import climbing_science.models.rohmert as rohmert
import climbing_science.models.strength_analyzer as sa
import climbing_science.models.critical_force as cf
import climbing_science.exercises.hangboard_calc as hb

# Direct calculation — no device, no file needed:
t_fail = rohmert.time_to_failure(0.80)  # 80% MVC → seconds
grade = sa.predict_grade(mvc7_kg=105, bodyweight_kg=65)
plan = hb.calculate_training_load(mvc7_kg=105, bodyweight_kg=65, protocol="lopez_maxhangs")

# With device data:
from climbing_science.adapters import tindeq
session = tindeq.load("meine_session.json")

# Plotting (Jupyter-native):
import matplotlib.pyplot as plt
times = [s.time_s for s in session.samples]
forces = [s.force_kg for s in session.samples]
plt.plot(times, forces)
plt.xlabel("Time (s)")
plt.ylabel("Force (kg)")

# Optional: Notebook helpers for common plots
from climbing_science.frontends import notebook
notebook.plot_session(session)                   # Force-time curve
notebook.plot_rohmert_curve(model="intermediate") # Fatigue model
notebook.plot_protocol_comparison(mvc7=105, bw=65) # Protocol comparison
```

---

## File Structure

```
src/climbing_science/
├── __init__.py
├── datamodel.py               # Canonical data model (ForceSample, ForceSession, ...)
│
├── models/                    # Layer 1: Pure Math
│   ├── __init__.py
│   ├── rohmert.py             # Isometric fatigue curve
│   ├── edge_depth.py          # Edge depth correction (Amca)
│   ├── critical_force.py      # CF/W' Regression
│   ├── strength_analyzer.py   # MVC → Grade prediction
│   ├── grades.py              # Grade conversion (UIAA/French/V/Font/YDS)
│   └── signal.py              # Signal processing (Smoothing, Peak Detection, RFD)
│
├── exercises/                 # Layer 2: Protocols & Planning
│   ├── __init__.py
│   ├── protocols.py           # Protocol definitions (data classes)
│   └── hangboard_calc.py      # Training loads from MVC + Protocol
│
├── adapters/                  # Layer 3: I/O Adapters (Format → Data model)
│   ├── __init__.py
│   ├── tindeq.py              # FingerForceTraining JSON & Tindeq App
│   ├── climbro.py             # Climbro CSV/JSON
│   ├── manual.py              # Manual input (no device needed)
│   └── csv_generic.py         # Generic CSV import
│
└── frontends/                 # Layer 4: Applications
    ├── __init__.py
    ├── cli.py                 # CLI runner
    ├── notebook.py            # Jupyter helpers (Plots, DataFrame export)
    └── report.py              # Assessment report (Markdown/HTML/dict)

notebooks/                         # Deliverable Jupyter analyses
├── 01_my_climbing_assessment.ipynb    # Personal overall assessment
├── 02_rohmert_curve_explained.ipynb   # Theory: Isometric fatigue
├── 03_critical_force_analysis.ipynb   # Evaluate + understand CF test
├── 04_protocol_comparison.ipynb       # Which protocol suits me?
├── 05_session_deep_dive.ipynb         # Analyze Tindeq session
├── 06_progress_tracker.ipynb          # Progress over weeks/months
└── 07_edge_depth_science.ipynb        # Why 20mm? Edge depth correction

tests/
├── test_datamodel.py
├── models/
│   ├── test_rohmert.py
│   ├── test_edge_depth.py
│   ├── test_critical_force.py
│   ├── test_strength_analyzer.py
│   ├── test_grades.py
│   └── test_signal.py
├── exercises/
│   ├── test_protocols.py
│   └── test_hangboard_calc.py
├── adapters/
│   ├── test_tindeq.py
│   ├── test_climbro.py
│   └── test_manual.py
└── frontends/
    ├── test_report.py
    └── test_notebook.py
```

---

## Modules — Layer 1: Models

### Module 1: `rohmert.py` — Isometric Fatigue Curve

**Priority:** 🔴 Foundation for everything else

**Scientific Basis:**

- Rohmert W. (1960). *Ermittlung von Erholungspausen für statische Arbeit des Menschen.*
  Internationale Zeitschrift für Angewandte Physiologie, 18, 123–164.
- Monod H., Scherrer J. (1965). *The work capacity of a synergic muscular group.*
  Ergonomics, 8(3), 329–338.

**Formulas:**

```
# Rohmert (1960) — Original
t_max = f(F/MVC)  # Time to failure as a function of relative intensity

# Classical approximation (Sjøgaard 1986 / Frey-Law & Avin 2010):
t_max(p) = a * (p / (1 - p))^b   where p = F/MVC (0..1)

# SC variant (Banaszczyk):
# 3 models: Beginner / Intermediate / Expert
# Different coefficients for fatigue resistance
# → Reverse-engineer parameters from SC website or publish own fits
```

**Functions:**

```python
def time_to_failure(force_ratio: float, model: str = "intermediate") -> float:
    """Maximum hang time at a given relative intensity (F/MVC).

    Args:
        force_ratio: Relative force (0.0 – 1.0), e.g. 0.8 for 80% MVC
        model: "beginner" | "intermediate" | "expert"

    Returns:
        Estimated time to failure in seconds

    References:
        Rohmert (1960), Sjøgaard (1986)
    """

def force_ratio_for_time(target_time: float, model: str = "intermediate") -> float:
    """Inverse: What relative intensity allows a hang for target_time seconds?"""

def mvc7_from_test(total_load_kg: float, hang_time_s: float,
                   model: str = "intermediate") -> float:
    """Converts any test hang to MVC-7 (7-second maximum).

    Example: 85 kg load, held for 23 seconds → MVC-7 = 110.5 kg
    """
```

**Tests:**

- Known points: at 100% MVC → t_max ≈ 7s, at 15% MVC → t_max > 600s
- Comparison of the 3 models: Expert holds longer at the same %MVC than Beginner
- Round-Trip: `force_ratio_for_time(time_to_failure(p)) ≈ p`
- Validation against SC Hangboard Calculator example:
  BW=65, +20kg, 15mm Edge, 23s → MVC-7 @20mm = 110.5 kg

---

### Module 2: `edge_depth.py` — Edge Depth Correction

**Priority:** 🟡 Required for correct comparisons

**Scientific Basis:**

- Amca A.M. et al. (2012). *The effect of hold depth on grip strength and endurance.*
- StrengthClimbing: 2.5%/mm correction relative to 20mm reference

**Formulas:**

```
# Linear correction (SC model):
correction_factor(edge_mm) = 1 + 0.025 * (20 - edge_mm)

# Example: 15mm Edge → Factor 1.125 (12.5% harder than 20mm)
# Example: 25mm Edge → Factor 0.875 (12.5% easier than 20mm)

# Force on reference edge:
F_20mm = F_measured * correction_factor(test_edge_mm)
```

**Functions:**

```python
def correction_factor(edge_mm: float, reference_mm: float = 20.0) -> float:
    """Correction factor for edge depth relative to reference.

    References:
        Amca et al. (2012), StrengthClimbing.com
    """

def convert_force(force_kg: float, from_edge_mm: float,
                  to_edge_mm: float) -> float:
    """Converts force between different edge depths."""
```

**Tests:**

- 20mm → 20mm: Factor = 1.0
- Symmetry: convert(convert(F, 15, 20), 20, 15) ≈ F
- Verify known values from SC Calculator

---

### Module: `grades.py` — Grade Conversion & Numerical Difficulty Index

**Priority:** 🟢 Quick win, no math, foundation for strength_analyzer

**Layer:** Models — pure lookup tables + interpolation, no I/O, no state

**Related Packages:** `pyclimb` v0.2.0 (MIT, French↔YDS only, outdated, Python ≤3.10).
We write from scratch — more complete coverage, numerical index, actively maintained.

#### Scientific Basis & References

Grade mappings between systems are **convention, not calculation**.
There is no universal formula — only historically evolved consensus tables
that **partially diverge between sources** (see section Discrepancies).

**Primary Sources (academic/institutional):**

1. **[CAI] Mandelli, G; Angriman, A (2016).** *Scales of Difficulty in Climbing.*
   Central School of Mountaineering, Club Alpino Italiano, Italy.
   Available via Semantic Scholar.
   → Most comprehensive academic source. Created for the UIAA/IFAS.
   Contains historical derivation of all systems and official comparison tables.
   **This is our primary reference for the route table.**

2. **[Draper2015] Draper, N; Giles, D; Schöffl, V; Fuss, FK; Watts, P; et al. (2015).**
   *Comparative grading scales, statistical analyses, climber descriptors
   and ability grouping.* Sports Technology, 8(3–4), 88–94.
   DOI: 10.1080/19346182.2015.1107081
   → Peer-reviewed! Defines the numeric IRCRA scale (International Rock Climbing
   Research Association) as a **unified numerical index** across all systems.
   Exactly what we need as `difficulty_index`.

3. **[FoH] The Mountaineers (2017).** *Mountaineering: The Freedom of the Hills.*
   9th ed., Appendix A: Rating Systems, pp. 563–570.
   ISBN 978-1-68051-004-1.
   → Standard reference work. Contains comparison tables YDS ↔ French ↔ UIAA.

**Primary Sources (community consensus with large N):**

4. **[MP] Mountain Project (2024).** *International Climbing Grades.*
   https://www.mountainproject.com/international-climbing-grades
   → Largest US community. Route table: YDS, French, UIAA, Ewbanks, SA, British.
   Separate boulder table: Hueco (V-Scale) ↔ Fontainebleau.
   Contains intermediate grades (5.10a/b, V3-4) which we do not adopt.

5. **[Rockfax] Rockfax Publishing (2022).** *Grade Conversions: Alpine Grading System.*
   https://rockfax.com/climbing-guides/grades/
   → Most commonly used reference in European climbing guidebooks.
   Contains route and boulder tables. Matches MP exactly from ~5.12a/7a+ onward.

6. **[theCrag] theCrag (2023).** *Grade Conversion.*
   https://www.thecrag.com/en/article/grades
   → Largest international platform with community-validated converter.
   Uses its own numerical scoring system (similar to IRCRA).

**Secondary Sources (validation & context):**

7. **[Hörst] Hörst, E (2016).** *Training for Climbing*, 3rd ed.
   Table 4.2: MVC/BW → UIAA-Grade.
   → Direct connection to strength_analyzer. Uses UIAA as standard.

8. **[Wikipedia] Wikipedia (2025).** *Grade (climbing) — Comparison tables.*
   https://en.wikipedia.org/wiki/Grade_(climbing)
   Quellen: Rockfax (2021), theCrag (2023), CAI/UIAA (2016).
   → Well-documented synthesis with explicit footnotes per cell.

9. **[Alpinist] Alpinist Magazine.** *International Grade Comparison Chart.*
   Archiviert: https://web.archive.org/web/20210330142513/http://www.alpinist.com/p//climbing_notes/grades
   → US reference, also contains ice/mixed/alpine grades.

10. **[pyclimb] pyclimb v0.2.0** (MIT, 2022). Python-Paket von ilias-ant.
    https://github.com/ilias-ant/pyclimb
    → French↔YDS only, usable as regression test.

#### Discrepancies Between Sources

Grade conversions are **not bijective and not unique**.
Sources systematically diverge — especially in the V–VIII (UIAA) range.
From approximately VIII+ / 7a+ / 5.12a, the systems converge because sport climbing
dominates internationally and routes are graded in all systems simultaneously
(Wikipedia [CAI]: "above the level of circa 5.12a, most grades closely align").

**Known Discrepancies (Route):**

| Range | Source A | Source B | Deviation |
|---------|----------|----------|------------|
| 5.11c | MP: 6c+ | Rockfax/CAI: 7a | ±½ French grade |
| UIAA VII | MP: 6b+ | Wikipedia/CAI: 6b | +/- Suffix |
| UIAA VIII- | MP: 6c | CAI: 6c/6c+ | Intermediate step |
| 5.9+ | MP: 5c | Rockfax: 5c | Agreed — but UIAA VI vs VI+ depending on source |
| 5.10d | MP: 6b+ | pyclimb: 6b+ | ✅ Agreed |

**Known Discrepancies (Boulder):**

| Range | Source A | Source B | Deviation |
|---------|----------|----------|------------|
| V0 | MP: Font 4 | CAI: Font 4 | ✅ Agreed |
| V7 | MP: 7A+ | Rockfax: 7A+ | ✅ Agreed |
| V8 | MP: 7B | Some: 7B/7B+ | ± Ambiguity |

→ From V9/7C onward, all sources are exactly identical (Draper 2015, Wikipedia [CAI]).

**Our Strategy for Discrepancies:**

1. **Primary: CAI/UIAA (Mandelli 2016)** — academic, institutional, near-peer-reviewed.
2. **Secondary: Mountain Project** — largest N, community consensus.
3. **Validation: Rockfax + theCrag** — European consensus.
4. **On conflict:** CAI table wins. Deviation is documented as a comment
   in the code (e.g. `# MP: 6c+, CAI: 7a — we follow CAI`).
5. **Test suite contains explicit discrepancy tests** that document
   which source we follow and why.

#### IRCRA Scale as Numerical Index

Draper et al. (2015) defined the **IRCRA scale** (International Rock Climbing
Research Association) as a unified numerical index for research purposes.
This scale is **exactly what we need as `difficulty_index`**:

- Monotonically increasing
- Peer-reviewed and used in >50 studies since then
- Defined for all common systems (UIAA, French, YDS, Font, V-Scale)
- Enables statistical analyses (means, regressions)

**Excerpt IRCRA Values (Draper 2015, Table 1):**

```
IRCRA  UIAA    French   YDS      Font    V-Scale
 1     I       1        5.2      -       -
 4     III     3        5.4      -       -
 7     IV+     4b       5.5      -       -
10     V+      5a       5.7      -       -
13     VI+     6a       5.10a    -       -
15     VII+    6b+      5.10d    4       V0
17     VIII    7a       5.11d    5+      V2
19     VIII+   7a+      5.12a    6A+     V3+
20     IX-     7b+      5.12c    6B+     V4+
21     IX      7c       5.12d    6C+     V5+
22     IX+     7c+      5.13a    7A      V6
23     X-      8a       5.13b    7A+     V7
24     X       8a+      5.13c    7B      V8
25     X+      8b       5.13d    7B+     V8+
26     XI-     8b+      5.14a    7C      V9
27     XI      8c       5.14b    7C+     V10
28     XI+     8c+      5.14c    8A      V11
29     XII-    9a       5.14d    8A+     V12
30     XII     9a+      5.15a    8B      V13
31     XII+    9b       5.15b    8B+     V14
32     -       9b+      5.15c    8C      V15
33     -       9c       5.15d    8C+     V16
```

**Implementation Decision:** We use the IRCRA scale as the basis for
our `difficulty_index`. Deviations from IRCRA are documented.
Advantage: We can write in publications
"difficulty index per Draper et al. (2015)" instead of "self-built".

#### Alternative Conversion Approaches

Besides lookup tables, there are also **calculated** approaches in the literature:

1. **IRCRA linear interpolation (Draper 2015).**
   The IRCRA values are constructed so that linear interpolation between
   adjacent grades is possible. We use this for `from_index()`.

2. **theCrag Score System.**
   theCrag uses its own numerical scoring (0–100+) with
   data-driven calibration from millions of logbook entries.
   Not publicly documented, but interesting for validation.

3. **Statistical approaches (community data).**
   Pollitt (2017, 8a.nu analysis) and r/climbharder surveys show
   that the *actual* difficulty can deviate from the *nominal* grade
   (regional soft-grading effects, e.g. France
   vs. Germany). Irrelevant for our library — we convert
   *nominal* grades, not *perceived* ones.

4. **Exponential fit (not recommended).**
   Some sources (e.g. climbharder wiki) attempt an exponential
   fit across all systems. This works poorly because the systems
   have different historical origins and were not mathematically
   constructed. We use explicit tables.

#### Design Decisions

1. **UIAA as internal standard.** All conversions go through UIAA as a
   hub (hub-and-spoke). Reason: UIAA is the official international
   system and is consistently used in German-language literature.
   Hörst (2016) and Lattice also use UIAA-based tables.

2. **Numerical difficulty index (difficulty_index).** Each grade receives
   a monotonically increasing float value (e.g. UIAA "7-" → 13.0, "7" → 14.0,
   "7+" → 15.0). This index enables:
   - Interpolation in strength_analyzer (MVC/BW → grade)
   - Sorting and comparison of grades
   - Arithmetic (average, difference)
   - Mapping between systems via shared index

3. **Two separate domains: Route and Boulder.**
   Route grades (UIAA, French, YDS) and boulder grades (Font, V-Scale) are
   **not directly comparable** (Wikipedia: "Font 4 / V0 corresponds roughly to
   French 6a / UIAA VI+ / YDS 5.10a as a single move").
   → Separate tables, separate enums, no implicit cross-domain mapping.

4. **No fuzzy intermediate grades.** Mountain Project lists intermediate steps
   like "5.10a/b" or "V3-4". We store only canonical grades
   (5.10a, 5.10b, ...) and provide `nearest()` for approximation.

5. **Case-insensitive input, canonical output.**
   `convert("6A+", "french", "yds")` works, output is always
   in canonical notation ("6a+").

#### Supported Grade Systems

**Route (Sport/Trad):**

| System | Enum Name | Range | Examples | Distribution |
|--------|-----------|---------|-----------|-------------|
| UIAA | `UIAA` | I – XII+ | "7-", "7", "7+", "8-" | DACH, Eastern Europe |
| French Sport | `FRENCH` | 1a – 9c | "6a+", "7b", "8c+" | Europe, worldwide |
| Yosemite Decimal | `YDS` | 5.0 – 5.15d | "5.10a", "5.12c" | North America |

**Boulder:**

| System | Enum Name | Range | Examples | Distribution |
|--------|-----------|---------|-----------|-------------|
| Fontainebleau | `FONT` | 3 – 9A | "6A+", "7C+", "8B" | Europe, worldwide |
| V-Scale (Hueco) | `V_SCALE` | V0 – V17 | "V5", "V10", "V14" | North America |

**Not in v1 (but prepared):** Ewbanks (AUS/NZ), British E-Grade, South Africa.

#### Conversion Table — Route

Primary source: CAI/Mandelli (2016), cross-validated with Mountain Project (2024),
Rockfax (2022) and Wikipedia/theCrag (2023). IRCRA index per Draper (2015).
On discrepancies: CAI value, deviation as comment.

```python
ROUTE_TABLE = [
    # (ircra, uiaa,    french,  yds)          # Source / Note
    (1,   "I",     "1",     "5.2"),           # CAI, FoH
    (2,   "II",    "2",     "5.3"),           # CAI, FoH
    (3,   "III",   "3",     "5.4"),           # CAI, FoH
    (4,   "III+",  "3+",    "5.4"),           # CAI
    (5,   "IV",    "4a",    "5.5"),           # CAI, Draper2015 (IRCRA ~5–7)
    (6,   "IV+",   "4b",    "5.6"),           # CAI
    (7,   "V-",    "4b",    "5.6"),           # CAI — V- = IV+/V transition
    (8,   "V",     "4c",    "5.7"),           # CAI, MP, Rockfax agreed
    (9,   "V+",    "5a",    "5.7+"),          # CAI, Draper2015 (IRCRA ~10)
    (10,  "VI-",   "5b",    "5.8"),           # CAI, MP agreed
    (11,  "VI",    "5c",    "5.9"),           # CAI, MP, Rockfax agreed
    (12,  "VI+",   "6a",    "5.10a"),         # CAI, MP, Rockfax agreed. Draper2015 IRCRA=13
    (13,  "VII-",  "6a+",   "5.10b"),         # CAI: 6a+. MP: 6a+. Agreed.
    (14,  "VII",   "6b",    "5.10c"),         # CAI, MP agreed. Draper2015 IRCRA≈14–15
    (15,  "VII+",  "6b+",   "5.10d"),         # CAI, MP agreed
    (16,  "VIII-", "6c",    "5.11a"),         # CAI: 6c. MP: 6c. Agreed.
    (17,  "VIII-", "6c+",   "5.11b"),         # CAI: VIII-/6c+. MP: 6c+/5.11b/c
    (18,  "VIII",  "7a",    "5.11d"),         # CAI, MP, Rockfax, Draper agreed. IRCRA=17
    (19,  "VIII+", "7a+",   "5.12a"),         # All sources agreed. IRCRA=19. Convergence point!
    (20,  "IX-",   "7b",    "5.12b"),         # CAI, MP agreed
    (21,  "IX-",   "7b+",   "5.12c"),         # CAI, MP agreed. IRCRA=20–21
    (22,  "IX",    "7c",    "5.12d"),         # CAI, MP, Rockfax agreed
    (23,  "IX+",   "7c+",   "5.13a"),         # All agreed. IRCRA=22
    (24,  "X-",    "8a",    "5.13b"),         # All agreed. IRCRA=23
    (25,  "X-",    "8a+",   "5.13c"),         # All agreed
    (26,  "X",     "8b",    "5.13d"),         # All agreed. IRCRA=25
    (27,  "X+",    "8b+",   "5.14a"),         # All agreed. IRCRA=26
    (28,  "XI-",   "8c",    "5.14b"),         # All agreed. IRCRA=27
    (29,  "XI-",   "8c+",   "5.14c"),         # All agreed
    (30,  "XI",    "9a",    "5.14d"),         # All agreed. IRCRA=29. Action Directe!
    (31,  "XI+",   "9a+",   "5.15a"),         # All agreed. IRCRA=30
    (32,  "XII-",  "9b",    "5.15b"),         # All agree. IRCRA=31
    (33,  "XII",   "9b+",   "5.15c"),         # All agree
    (34,  "XII+",  "9c",    "5.15d"),         # All agree. IRCRA≈33. Silence!
]
```

#### Conversion Table — Boulder

Primary source: CAI/Mandelli (2016), cross-validated with Rockfax (2022),
Mountain Project (2024). IRCRA index per Draper (2015).
From V9/7C: all sources exactly identical.

```python
BOULDER_TABLE = [
    # (ircra, font,    v_scale)               # Source / Note
    (11,  "3",     "VB"),                     # Draper2015 IRCRA≈10–12
    (12,  "4-",    "V0-"),                    # MP
    (13,  "4",     "V0"),                     # CAI, MP, Rockfax agree
    (14,  "4+",    "V0+"),                    # MP, Rockfax
    (15,  "5",     "V1"),                     # CAI, Draper2015 IRCRA≈15
    (16,  "5+",    "V2"),                     # CAI, MP agree
    (17,  "6A",    "V3"),                     # CAI, MP, Rockfax agree. IRCRA≈17
    (18,  "6A+",   "V3+"),                    # MP
    (19,  "6B",    "V4"),                     # CAI, MP agree. IRCRA≈19
    (20,  "6B+",   "V4+"),                    # MP
    (21,  "6C",    "V5"),                     # CAI, MP agree. IRCRA≈21
    (22,  "6C+",   "V5+"),                    # MP
    (23,  "7A",    "V6"),                     # All agree. IRCRA=22
    (24,  "7A+",   "V7"),                     # All agree. IRCRA=23
    (25,  "7B",    "V8"),                     # All agree. IRCRA=24
    (26,  "7B+",   "V8+"),                    # All agree
    (27,  "7C",    "V9"),                     # All agree. IRCRA=26. Exact from here on!
    (28,  "7C+",   "V10"),                    # All agree. IRCRA=27
    (29,  "8A",    "V11"),                    # All agree. IRCRA=28
    (30,  "8A+",   "V12"),                    # All agree. IRCRA=29
    (31,  "8B",    "V13"),                    # All agree. IRCRA=30
    (32,  "8B+",   "V14"),                    # All agree. IRCRA=31
    (33,  "8C",    "V15"),                    # All agree. IRCRA=32
    (34,  "8C+",   "V16"),                    # All agree. IRCRA=33
    (35,  "9A",    "V17"),                    # All agree. Burden of Dreams!
]
```

#### Data Types

```python
import enum
from dataclasses import dataclass


class RouteSystem(enum.Enum):
    UIAA = "UIAA"
    FRENCH = "French"
    YDS = "YDS"


class BoulderSystem(enum.Enum):
    FONT = "Font"
    V_SCALE = "V-Scale"


@dataclass(frozen=True)
class Grade:
    """Immutable grade object with system, value, and numeric index."""
    system: RouteSystem | BoulderSystem
    value: str              # Canonical string, e.g. "7a+", "V5", "VIII-"
    difficulty_index: float # Monotonically increasing difficulty value

    def __lt__(self, other: "Grade") -> bool:
        return self.difficulty_index < other.difficulty_index

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Grade):
            return NotImplemented
        return self.system == other.system and self.value == other.value

    def __hash__(self) -> int:
        return hash((self.system, self.value))

    def __str__(self) -> str:
        return self.value
```

#### Functions

```python
def convert(grade: str, from_system: str, to_system: str) -> str:
    """Converts a climbing grade between systems.

    Args:
        grade: Grade string, e.g. "7a+", "5.12a", "VIII-", "V5", "7A+"
        from_system: Source system ("UIAA", "French", "YDS", "Font", "V-Scale")
        to_system: Target system (same values)

    Returns:
        Converted grade as string in canonical notation.

    Raises:
        GradeError: Unknown system or grade not found in system.
        GradeDomainError: Route↔Boulder conversion attempted
            (e.g. French→Font is invalid).

    Example:
        >>> convert("7a+", "French", "YDS")
        '5.12a'
        >>> convert("5.12a", "YDS", "UIAA")
        'VIII+'
        >>> convert("V5", "V-Scale", "Font")
        '6C'

    References:
        Mountain Project (2024), UIAA Scale of Difficulty
    """


def parse(grade: str, system: str | None = None) -> Grade:
    """Parses a grade string into a Grade object.

    When system=None, the system is automatically detected:
    - Starts with "V" + Zahl → V-Scale
    - Starts with "5." → YDS
    - Contains Roman numerals (I–XII) with +/- → UIAA
    - Uppercase A/B/C (6A, 7B+) → Font
    - Lowercase a/b/c (6a, 7b+) → French

    Args:
        grade: Grade string
        system: Optional — forces system instead of autodetect

    Returns:
        Grade object with system, value, difficulty_index

    Example:
        >>> parse("7a+")
        Grade(system=<RouteSystem.FRENCH>, value='7a+', difficulty_index=15.5)
        >>> parse("V5")
        Grade(system=<BoulderSystem.V_SCALE>, value='V5', difficulty_index=8.0)
    """


def difficulty_index(grade: str, system: str | None = None) -> float:
    """Returns the numeric difficulty index of a grade.

    Useful for calculations in strength_analyzer:
    - Interpolation (MVC/BW-Ratio → Index → Grade)
    - Sorting and comparison
    - Averaging

    Example:
        >>> difficulty_index("7a+", "French")
        15.5
        >>> difficulty_index("VIII+", "UIAA")
        15.5
    """


def from_index(index: float, system: str) -> str:
    """Inverse: Numeric index → nearest grade in system.

    Rounds to the nearest tabulated grade (nearest-neighbor).

    Example:
        >>> from_index(15.3, "French")
        '7a'
        >>> from_index(15.7, "UIAA")
        'VIII+'
    """


def all_grades(system: str) -> list[Grade]:
    """Returns all grades of a system sorted in ascending order.

    Example:
        >>> [g.value for g in all_grades("UIAA")][:5]
        ['I', 'II', 'III', 'IV', 'IV+']
    """
```

#### Exceptions

```python
class GradeError(Exception):
    """Base class for grade errors."""

class UnknownSystemError(GradeError):
    """Unknown grade system specified."""

class UnknownGradeError(GradeError):
    """Grade does not exist in the specified system."""

class GradeDomainError(GradeError):
    """Conversion between route and boulder attempted."""
```

#### Tests (`test_grades.py`)

```python
# ============================================================
# SECTION 1: Route conversion — source-validated
# ============================================================

# French → YDS (Reference: CAI/Mandelli 2016, confirmed by MP 2024)
assert convert("6a",  "French", "YDS") == "5.10a"   # CAI, MP, Rockfax agree
assert convert("6a+", "French", "YDS") == "5.10b"   # CAI, MP, Rockfax agree
assert convert("7a",  "French", "YDS") == "5.11d"   # CAI, MP, Rockfax agree
assert convert("7a+", "French", "YDS") == "5.12a"   # All agree. Convergence point.
assert convert("8a",  "French", "YDS") == "5.13b"   # All agree
assert convert("9a",  "French", "YDS") == "5.14d"   # All agree

# YDS → French (Reference: CAI 2016, MP 2024)
assert convert("5.10a", "YDS", "French") == "6a"
assert convert("5.10d", "YDS", "French") == "6b+"
assert convert("5.12a", "YDS", "French") == "7a+"   # Convergence point
assert convert("5.14a", "YDS", "French") == "8b+"

# French → UIAA (Reference: CAI 2016 — this is the official UIAA source)
assert convert("6a",  "French", "UIAA") == "VI+"
assert convert("6b+", "French", "UIAA") == "VII+"
assert convert("7a",  "French", "UIAA") == "VIII"
assert convert("7a+", "French", "UIAA") == "VIII+"
assert convert("8a",  "French", "UIAA") == "X-"     # CAI: X-. Some: IX+.
assert convert("9a",  "French", "UIAA") == "XI"
assert convert("9c",  "French", "UIAA") == "XII+"   # Silence!

# YDS → UIAA (derived via French as hub)
assert convert("5.10a", "YDS", "UIAA") == "VI+"
assert convert("5.12a", "YDS", "UIAA") == "VIII+"
assert convert("5.14d", "YDS", "UIAA") == "XI"      # Action Directe

# UIAA → French (Reference: CAI 2016)
assert convert("VI+",  "UIAA", "French") == "6a"
assert convert("VII+", "UIAA", "French") == "6b+"
assert convert("VIII", "UIAA", "French") == "7a"
assert convert("IX",   "UIAA", "French") == "7c"
assert convert("X",    "UIAA", "French") == "8b"

# ============================================================
# SECTION 2: Boulder conversion — source-validated
# ============================================================

# Font → V-Scale (Reference: CAI 2016, Rockfax 2022, MP 2024)
assert convert("6A",  "Font", "V-Scale") == "V3"
assert convert("7A",  "Font", "V-Scale") == "V6"
assert convert("7C",  "Font", "V-Scale") == "V9"    # All exactly agree from here on
assert convert("7C+", "Font", "V-Scale") == "V10"
assert convert("8A",  "Font", "V-Scale") == "V11"
assert convert("8C",  "Font", "V-Scale") == "V15"

# V-Scale → Font (Reference: all sources)
assert convert("V5",  "V-Scale", "Font") == "6C"
assert convert("V9",  "V-Scale", "Font") == "7C"
assert convert("V10", "V-Scale", "Font") == "7C+"
assert convert("V14", "V-Scale", "Font") == "8B+"

# ============================================================
# SECTION 3: Round-Trip Tests
# ============================================================

# convert(convert(g, A, B), B, A) == g
# Holds exactly only when the mapping in the table is 1:1.
# From VIII+ / 7a+ / 5.12a this is the case (all sources converge).
for grade in ["7a+", "8a", "8b", "8c", "9a", "9b", "9c"]:
    assert convert(convert(grade, "French", "YDS"), "YDS", "French") == grade
    assert convert(convert(grade, "French", "UIAA"), "UIAA", "French") == grade

for grade in ["V6", "V7", "V8", "V9", "V10", "V11", "V14", "V17"]:
    assert convert(convert(grade, "V-Scale", "Font"), "Font", "V-Scale") == grade

# ============================================================
# SECTION 4: Domain separation
# ============================================================

# Route → Boulder must raise GradeDomainError
with pytest.raises(GradeDomainError):
    convert("7a", "French", "Font")      # Sport → Boulder forbidden

with pytest.raises(GradeDomainError):
    convert("V5", "V-Scale", "YDS")      # Boulder → Sport forbidden

with pytest.raises(GradeDomainError):
    convert("VIII", "UIAA", "V-Scale")   # Route → Boulder forbidden

# ============================================================
# SECTION 5: IRCRA Index (Draper et al. 2015)
# ============================================================

# Monotonically increasing within each system
for system in ["UIAA", "French", "YDS", "Font", "V-Scale"]:
    grades = all_grades(system)
    for i in range(len(grades) - 1):
        assert grades[i].difficulty_index < grades[i+1].difficulty_index, \
            f"{system}: {grades[i]} >= {grades[i+1]}"

# Same IRCRA index across route systems
# (Core assertion of Draper 2015: the index is cross-system)
assert difficulty_index("7a+", "French") == difficulty_index("5.12a", "YDS")
assert difficulty_index("7a+", "French") == difficulty_index("VIII+", "UIAA")
assert difficulty_index("9a",  "French") == difficulty_index("5.14d", "YDS")
assert difficulty_index("9a",  "French") == difficulty_index("XI", "UIAA")

# Same IRCRA index across boulder systems
assert difficulty_index("7A",  "Font") == difficulty_index("V6", "V-Scale")
assert difficulty_index("8A",  "Font") == difficulty_index("V11", "V-Scale")
assert difficulty_index("9A",  "Font") == difficulty_index("V17", "V-Scale")

# Verify IRCRA values against Draper (2015) Table 1
assert difficulty_index("VIII", "UIAA") == 18     # Draper: IRCRA=17–18
assert difficulty_index("VIII+","UIAA") == 19     # Draper: IRCRA=19
assert difficulty_index("XI",  "UIAA") == 30      # Draper: IRCRA=29–30

# ============================================================
# SECTION 6: from_index (Inverse)
# ============================================================

# Exact matches
assert from_index(19, "French") == "7a+"
assert from_index(19, "YDS") == "5.12a"
assert from_index(19, "UIAA") == "VIII+"

# Interpolation: Index between two grades → nearest
assert from_index(18.4, "French") == "7a"    # closer to 18
assert from_index(18.6, "French") == "7a+"   # closer to 19
assert from_index(29.6, "UIAA") == "XI"      # closer to 30
assert from_index(30.4, "UIAA") == "XI"      # still at 30

# ============================================================
# SECTION 7: Autodetect (parse without system specification)
# ============================================================

assert parse("V5").system == BoulderSystem.V_SCALE
assert parse("VB").system == BoulderSystem.V_SCALE
assert parse("5.12a").system == RouteSystem.YDS
assert parse("5.9").system == RouteSystem.YDS
assert parse("VIII+").system == RouteSystem.UIAA
assert parse("XII-").system == RouteSystem.UIAA
assert parse("7a+").system == RouteSystem.FRENCH    # Lowercase → French
assert parse("7A+").system == BoulderSystem.FONT    # Uppercase → Font

# ============================================================
# SECTION 8: Case-insensitive Input
# ============================================================

assert convert("7A+", "French", "YDS") == convert("7a+", "French", "YDS")
assert convert("viii+", "UIAA", "French") == convert("VIII+", "UIAA", "French")
assert convert("v5", "V-Scale", "Font") == convert("V5", "V-Scale", "Font")

# ============================================================
# SECTION 9: Error Handling
# ============================================================

with pytest.raises(UnknownGradeError):
    convert("13a", "French", "YDS")          # Does not exist
with pytest.raises(UnknownGradeError):
    convert("V99", "V-Scale", "Font")        # Does not exist
with pytest.raises(UnknownSystemError):
    convert("7a", "Ewbanks", "YDS")          # v1 not supported
with pytest.raises(UnknownSystemError):
    convert("7a", "French", "Saxon")         # v1 not supported

# Identity conversion (same system)
assert convert("7a+", "French", "French") == "7a+"
assert convert("V5", "V-Scale", "V-Scale") == "V5"
assert convert("VIII+", "UIAA", "UIAA") == "VIII+"

# ============================================================
# SECTION 10: Historical reference points
# (Serves as "sanity check" — these facts are undisputed)
# ============================================================

# Silence (Ondra 2017): 9c / 5.15d / XII+ — hardest free climb ever
assert convert("9c", "French", "YDS") == "5.15d"
assert convert("9c", "French", "UIAA") == "XII+"

# Action Directe (Güllich 1991): 9a / 5.14d / XI — first 9a
assert convert("9a", "French", "YDS") == "5.14d"
assert convert("9a", "French", "UIAA") == "XI"

# Hubble (Moon 1990): 8c+ / 5.14c — first 8c+
assert convert("8c+", "French", "YDS") == "5.14c"

# Punks in the Gym (1985): 8b+ / 5.14a — first 8b+ (Wikipedia)
assert convert("8b+", "French", "YDS") == "5.14a"

# Burden of Dreams (Nalle 2016): 9A / V17 — hardest boulder ever
assert convert("9A", "Font", "V-Scale") == "V17"

# Midnight Lightning (Kauk 1978): 7B / V8 — iconic boulder
assert convert("7B", "Font", "V-Scale") == "V8"

# ============================================================
# SECTION 11: Discrepancy documentation
# Explicit tests documenting which source we follow.
# Each test contains a comment with the alternative values.
# ============================================================

# 5.11c: MP says 6c+, CAI says 6c+/7a. We follow CAI: 6c+
assert convert("5.11b", "YDS", "French") == "6c+"   # CAI: VIII-/6c+

# UIAA VIII- ↔ French: CAI says 6c, MP says 6c. Agree.
assert convert("VIII-", "UIAA", "French") == "6c"

# 8a ↔ UIAA: CAI says X-, some older sources say IX+.
# We follow CAI (2016).
assert convert("8a", "French", "UIAA") == "X-"      # CAI: X-

# ============================================================
# SECTION 12: Regression against pyclimb v0.2.0
# pyclimb only has French↔YDS. We verify all 34 entries
# and document deviations.
# ============================================================

# pyclimb French→YDS mapping (complete):
PYCLIMB_FRENCH_TO_YDS = {
    "5a": "5.8", "5b": "5.9", "5c": "5.10a",
    "6a": "5.10a", "6a+": "5.10b", "6b": "5.10c", "6b+": "5.10d",
    "6c": "5.11b", "6c+": "5.11c",
    "7a": "5.11d", "7a+": "5.12a", "7b": "5.12b", "7b+": "5.12c",
    "7c": "5.12d", "7c+": "5.13a",
    "8a": "5.13b", "8a+": "5.13c", "8b": "5.13d", "8b+": "5.14a",
    "8c": "5.14b", "8c+": "5.14c",
    "9a": "5.14d", "9a+": "5.15a", "9b": "5.15b", "9b+": "5.15c",
    "9c": "5.15d",
}

# We expect agreement from 7a+ (convergence zone).
# Below that, deviations may occur (documented):
KNOWN_DEVIATIONS = {
    # pyclimb: 5c→5.10a, we: 5c→5.9 (CAI table). ±1 subgrade.
    "5c": ("5.10a", "5.9"),   # (pyclimb, us)
    # pyclimb: 6c→5.11b, we: 6c→5.11a (CAI). ±1 subgrade.
    "6c": ("5.11b", "5.11a"),
}

for french, expected_yds in PYCLIMB_FRENCH_TO_YDS.items():
    our_result = convert(french, "French", "YDS")
    if french in KNOWN_DEVIATIONS:
        pyclimb_val, our_expected = KNOWN_DEVIATIONS[french]
        assert our_result == our_expected, \
            f"Deviation at {french}: expected {our_expected} (CAI), got {our_result}"
    else:
        assert our_result == expected_yds, \
            f"Regression vs pyclimb at {french}: expected {expected_yds}, got {our_result}"
```

#### Implementation Notes

1. **Internally as Dict-of-Dicts.** Each table is converted into fast
   lookup dictionaries on import:
   `_ROUTE_BY_FRENCH["7a+"] → (15.0, "VIII", "7a", "5.11d")`

2. **Zero Dependencies.** Only stdlib (enum, dataclasses). No numpy needed.

3. **Extensible.** New systems (Ewbanks, British E-Grade, Saxon)
   only require a new column in the table + new enum value.
   The logic remains identical.

4. **Validation against pyclimb.** All French↔YDS values from pyclimb v0.2.0
   used as regression tests. Document and justify deviations.

5. **Canonical notation.** Output is always exactly as in the table:
   - UIAA: Roman numerals + optional "+"/"-" (e.g. "VII+", "IX-")
   - French: Arabic numeral + lowercase letter + optional "+" (e.g. "7a+")
   - YDS: "5." + number, from 5.10 with lowercase letter (e.g. "5.10a")
   - Font: Arabic numeral + uppercase letter + optional "+" (e.g. "7A+")
   - V-Scale: "V" + number (e.g. "V5"), special case "VB" (= V-easy)

---

### Module 3: `signal.py` — Force-Curve Signal Processing

**Priority:** 🟡 Foundation for Tindeq analysis

**Layer:** Models — pure mathematics on time series, no I/O

**Functions:**

```python
def smooth(values: list[float], timestamps_us: list[int],
           method: str = "moving_average",
           window_ms: int = 50) -> list[float]:
    """Smooths a force signal. Methods: moving_average, exponential."""

def detect_peaks(values: list[float], timestamps_us: list[int],
                 min_value: float = 5.0,
                 min_duration_s: float = 1.0) -> list[Peak]:
    """Detects force peaks (for automatic segmentation).

    Returns:
        List of Peak(start_idx, end_idx, peak_idx, peak_value, duration_s)
    """

def compute_rfd(values: list[float], timestamps_us: list[int],
                window: tuple[float, float] = (0.2, 0.8)) -> RFDResult:
    """Rate of Force Development: force rise in the 20–80% window.

    Returns:
        RFDResult(peak_rfd_kg_s, time_to_peak_s, avg_rfd_kg_s)
    """

def best_n_second_average(values: list[float], timestamps_us: list[int],
n_seconds: float = 7.0) -> float:
    """Best average over a sliding N-second window.

    Central for MVC-7 extraction.
    """

def compute_impulse(values: list[float], timestamps_us: list[int]) -> float:
    """Force impulse (integral: kg·s) via trapezoidal rule."""
```

**Tests:**

- Constant signal → Smoothing changes nothing
- Triangle pulse → Peak Detection finds exactly one peak
- Linear ramp → RFD is exactly the slope
- Rectangle 7s @ 50kg → best_7s_average = 50.0
- Known impulse: 10s @ 50kg → impulse = 500 kg·s

---

### Module 4: `strength_analyzer.py` — Grade Prediction from Finger Strength

**Priority:** 🔴 Core feature

**Layer:** Models — uses Rohmert + Edge-Depth + Grades, no I/O

**Scientific Basis:**

- Giles D. et al. (2019). *The Determination of Finger-Flexor Critical Force in Rock Climbers.*
  Int J Sports Physiol Perform, 1–8.
- Hörst E. (2016). *Training for Climbing.* 3rd ed., Table 4.2 (MVC/BW → Grade)
- Lattice Training Assessment Benchmarks (n=436)
- r/climbharder Survey 2017 (n=555)
- StrengthClimbing: toclimb8a.shinyapps.io/maxtograde

**Data Sources for Regression:**

```
# Per-Hand MVC/BW → UIAA Grade (interpolated from Hörst §4.2)
# This table is the core of the Analyzer:
GRADE_TABLE = {
    # MVC_per_hand_%BW : UIAA_grade
    50:  "5",      # ~V0
    60:  "6-",     # ~V1
    65:  "6",      # ~V2
    70:  "6+",     # ~V3
    75:  "7-",     # ~V4
    80:  "7",      # ~V5
    85:  "7+",     # ~V6
    90:  "8-",     # ~V7
    95:  "8",      # ~V8
    100: "8+",     # ~V9
    105: "9-",     # ~V10
    110: "9",      # ~V11
    115: "9+",     # ~V12
    120: "10-",    # ~V13
    130: "10",     # ~V14
    140: "10+",    # ~V15
}
# NOTE: SC uses 2-hand total, Lattice as well.
# Hörst §4.2 gives per-hand values.
# → Clear documentation of which convention is used!
```

**Functions:**

```python
def predict_grade(mvc7_kg: float, bodyweight_kg: float,
                  edge_mm: float = 20,
                  training_mode: int = 1,
                  height_cm: float | None = None,
                  arm_span_cm: float | None = None) -> GradeResult:
    """Predicts climbing grade from finger strength.

    Args:
        mvc7_kg: MVC-7 total load (BW + added weight) in kg
        bodyweight_kg: Body weight in kg
        edge_mm: Test edge depth (5–35mm)
        training_mode: 1=no hangboard, 2=Repeaters, 3=MaxHangs, 4=MaxHangs+added
        height_cm: Optional — for ape index correction
        arm_span_cm: Optional — for ape index correction

    Returns:
        GradeResult with boulder_grade, sport_grade, mvc_bw_ratio,
        assessment_text, training_recommendations
    """

@dataclass
class GradeResult:
    boulder_uiaa: str          # e.g. "8-"
    boulder_font: str          # e.g. "7A"
    boulder_v: str             # e.g. "V7"
    sport_french: str | None   # e.g. "7b+" (if CF available)
    mvc_bw_ratio: float        # e.g. 1.62
    mvc_bw_per_hand: float     # e.g. 0.81
    percentile: str            # e.g. "Advanced"
    assessment: str            # Free-text assessment
```

**Tests:**

- Reproduce known Lattice benchmarks
- Verify SC Analyzer examples (from website)
- Edge cases: beginner (ratio < 0.5), elite (ratio > 1.4)

---

### Module 4: `critical_force.py` — Critical Force & W'

**Priority:** 🔴 Only open CF model

**Scientific Basis:**

- Monod H., Scherrer J. (1965). *The work capacity of a synergic muscular group.*
- Giles D. et al. (2019). *Finger-Flexor Critical Force in Rock Climbers.*
- Poole D.C. et al. (2016). *Critical Power: An Important Fatigue Threshold.*
  Medicine & Science in Sports & Exercise, 48(11), 2320–2334.

**Model:**

```
# Critical Power / Critical Force concept:
# t_lim = W' / (P - CF)
# where: t_lim = Time to failure, P = Power/Force, CF = Critical Force, W' = Anaerobic capacity

# Rearranged for 7/3 Repeaters (intermittent protocol):
# Tlim_total(P) = W' / (P_eff - CF)
# P_eff accounts for work/rest ratio (7s on / 3s off)

# 3-point test:
# t80 = cumulative hang time at 80% MVC-7 (7/3 Repeaters to failure)
# t60 = cumulative hang time at 60% MVC-7
# t45 = cumulative hang time at 45% MVC-7 (or 50%/55%)
#
# Linear regression: W_total = CF * t_total + W'
# → CF = slope, W' = y-intercept
```

**Functions:**

```python
def calculate_cf(mvc7_kg: float, bodyweight_kg: float,
                 t80_s: float, t60_s: float,
                 t_low_s: float, low_pct: float = 0.45,
                 edge_mm: float = 20) -> CFResult:
    """Calculates Critical Force from 3-point test.

    Args:
        mvc7_kg: MVC-7 total load in kg
        bodyweight_kg: Body weight
        t80_s: Cumulative hang time at 80% MVC (7/3 Repeaters)
        t60_s: Cumulative hang time at 60% MVC
        t_low_s: Cumulative hang time at low_pct MVC
        low_pct: Third test point (0.45, 0.50 or 0.55)
        edge_mm: Test edge (10–35mm)

    Returns:
        CFResult with CF, W', CF/BW ratio, assessment
    """

@dataclass
class CFResult:
    cf_kg: float               # Critical Force in kg
    w_prime_kgs: float         # Anaerobic capacity in kg·s
    cf_bw_ratio: float         # CF / Bodyweight
    cf_mvc_ratio: float        # CF / MVC-7 (typical 0.35–0.55)
    predicted_sport_grade: str # French grade based on CF
    endurance_assessment: str  # "Below average" / "Average" / "Above average"
    training_load_cf_kg: float # Recommended load for CF training
    r_squared: float           # Goodness of linear fit
```

**Tests:**

- SC demo dataset: BW=65, MVC-7=105, t80=77, t60=136, t45=323
- Giles et al. (2019) published CF values for different performance groups
- R² > 0.95 for good test data
- CF must always be < MVC-7

---

---

## Modules — Layer 2: Exercises

### Module 5: `protocols.py` — Protocol Definitions

**Priority:** 🟡 Pure data, no logic

**Layer:** Exercises — describes *what* is trained, not *how* it is calculated

```python
@dataclass(frozen=True)
class HangboardProtocol:
    """Immutable protocol definition."""
    id: str
    name: str
    author: str
    intensity_range: tuple[float, float]  # %MVC-7, e.g. (0.88, 1.04)
    hang_s: float
    rest_s: float
    sets: int
    reps: int | None                      # None = "to failure"
    set_rest_s: float
    energy_system: str                    # "alactic" | "lactic" | "aerobic"
    notes: str

PROTOCOLS: dict[str, HangboardProtocol] = {
    "lopez_maxhangs":      HangboardProtocol("lopez_maxhangs", "Eva López MaxHangs (MAW)", "López", (0.88, 1.04), 10, 180, 4, 1, 180, "alactic", "..."),
    "lopez_inthangs":      HangboardProtocol("lopez_inthangs", "Eva López IntHangs", "López", (0.60, 0.80), 10, 5, 4, 4, 60, "lactic", "..."),
    "lopez_subhangs":      HangboardProtocol("lopez_subhangs", "Eva López SubHangs", "López", (0.55, 0.85), 30, 120, 3, 1, 120, "lactic", "..."),
    "horst_7_53":          HangboardProtocol("horst_7_53", 'Eric Hörst "7-53"', "Hörst", (0.92, 0.97), 7, 53, 3, 3, 180, "alactic", "..."),
    "bechtel_ladders":     HangboardProtocol("bechtel_ladders", "Steve Bechtel 3-6-9 Ladders", "Bechtel", (0.88, 0.95), 12, 180, 3, 1, 180, "alactic", "..."),
    "repeaters_7_3":       HangboardProtocol("repeaters_7_3", "7/3 Repeaters", "Industry", (0.40, 0.80), 7, 3, 6, 6, 180, "lactic", "..."),
    "endurance_repeaters": HangboardProtocol("endurance_repeaters", "Endurance Repeaters", "Industry", (0.25, 0.60), 7, 3, 1, None, 0, "aerobic", "..."),
    "density_hangs":       HangboardProtocol("density_hangs", "Tyler Nelson Density Hangs", "Nelson", (0.50, 0.80), 20, 10, 5, 1, 120, "lactic", "..."),
    "one_arm_hangs":       HangboardProtocol("one_arm_hangs", "One-Arm Hangs", "Webb-Parsons", (0.94, 1.06), 7, 180, 3, 1, 180, "alactic", "..."),
}
```

**Important:** Protocols are *data*, not computations. They know nothing
about Rohmert or Edge-Depth. They only describe structure and intensity ranges.

---

### Module 6: `hangboard_calc.py` — Training Load Calculator

**Priority:** 🟡 Highest everyday utility

**Layer:** Exercises — connects protocol definitions with model calculations

**Dependencies:** `models.rohmert`, `models.edge_depth`, `exercises.protocols`

```python
def calculate_training_load(mvc7_kg: float, bodyweight_kg: float,
                            protocol: str | HangboardProtocol,
                            edge_mm: float = 20,
                            model: str = "intermediate") -> TrainingPlan:
    """Calculates exact training loads for a given protocol.

    Uses Rohmert for time-to-failure and Edge-Depth for edge correction.
    The protocol provides only the structure (sets, reps, intensity).

    Returns:
        TrainingPlan with added_load_kg, tut_per_set, total_tut, difficulty
    """

def compare_protocols(mvc7_kg: float, bodyweight_kg: float,
                      protocols: list[str] | None = None) -> list[ProtocolComparison]:
    """Compares multiple protocols side by side (TUT, volume, load)."""
```

**Tests:**

- SC Hangboard Calculator example: BW=65, +20kg, 15mm, 23s → MVC-7@20mm = 110.5 kg
- Verify protocol-specific loads against SC results
- Edge conversion: same relative intensity on different edges

---

## Modules — Layer 3: I/O Adapters

### Module 7: `adapters/tindeq.py` — Tindeq Progressor Adapter

**Priority:** 🟡 Primary adapter (for FingerForceTraining iOS app)

**Layer:** Adapter — reads Tindeq-specific JSON, produces canonical ForceSession

**Dependencies:** Only `datamodel.py`

```python
def load(path: str) -> ForceSession:
    """Loads FingerForceTraining JSON → canonical ForceSession.

    Handles:
    - UInt64 timestamps (new sessions) and UInt32 (legacy)
    - Segments (optional, if present)
    - Metadata mapping: testType, holdType, hand → metadata dict
    """

def load_all(directory: str) -> list[ForceSession]:
    """Loads all sessions from a directory (iCloud export)."""
```

### Module 8: `adapters/manual.py` — Manual Input

**Priority:** 🟡 For users without a force gauge

```python
def from_mvc7_test(bodyweight_kg: float, added_kg: float,
                   hang_time_s: float = 7.0,
                   edge_mm: float = 20) -> TestResult:
    """Creates TestResult from manual MVC-7 measurement (stopwatch + weight)."""

def from_repeater_test(bodyweight_kg: float,
                       mvc7_kg: float,
                       t80_s: float, t60_s: float,
                       t_low_s: float, low_pct: float = 0.45) -> TestResult:
    """Creates TestResult from manual CF test (3-point)."""
```

### Module 9: `adapters/csv_generic.py` — Generic CSV Import

```python
def load(path: str, time_col: str = "time_s",
         force_col: str = "force_kg",
         delimiter: str = ",") -> ForceSession:
    """Loads arbitrary CSV with time/force columns."""
```

---

## Modules — Layer 4: Frontends

### Module 10: `frontends/report.py` — Assessment Report

**Priority:** 🟢 End-to-end result

**Layer:** Frontend — orchestrates Adapter → Models → Output

```python
def generate(session: ForceSession, profile: AthleteProfile,
             edge_mm: float = 20) -> AssessmentReport:
    """Complete assessment report from session + profile.

    Pipeline:
    1. signal.best_n_second_average → MVC-7
    2. strength_analyzer.predict_grade → Grade
    3. hangboard_calc → Training recommendations
    4. Optional: critical_force → Endurance
    """

def to_markdown(report: AssessmentReport) -> str:
    """Renders report as Markdown (for Jupyter, CLI, export)."""

def to_dict(report: AssessmentReport) -> dict:
    """Report as dict (for JSON export, web API)."""
```

### Module 11: `frontends/notebook.py` — Jupyter Helpers

**Priority:** 🟢 Nice-to-have, high wow factor

**Dependencies:** matplotlib (optional), pandas (optional)

```python
def plot_session(session: ForceSession, **kwargs) -> None:
    """Force-time curve with automatic peak marking."""

def plot_rohmert_curve(models: list[str] | None = None) -> None:
    """Rohmert fatigue curves for all models overlaid."""

def plot_protocol_comparison(mvc7_kg: float, bodyweight_kg: float) -> None:
    """Bar chart: All protocols compared (TUT, load, volume)."""

def session_to_dataframe(session: ForceSession):
    """Converts ForceSession → pandas DataFrame (for custom analysis)."""
```

### Module 12: `frontends/cli.py` — CLI Runner

**Priority:** 🟢 Optional

```bash
# Example calls:
$ climbing-science analyze --mvc7 105 --bw 65 --edge 20
$ climbing-science plan --mvc7 105 --bw 65 --protocol lopez_maxhangs
$ climbing-science report session.json --bw 65
$ climbing-science grade "7a+" --to uiaa
```

---

## Dependency Graph

```
Layer 1 — MODELS (pure functions, no I/O)
┌──────────┐  ┌───────────┐
│ grades   │  │ rohmert   │ ← Foundation
└──────────┘  └─────┬─────┘
                    │
              ┌─────┴─────┐
              ▼           ▼
         ┌──────────┐ ┌───────────────────┐
         │edge_depth│ │strength_analyzer  │
         └──────────┘ │(rohmert + grades) │
              │       └───────────────────┘
              │
         ┌────┘   ┌──────────────────┐
         │        │ critical_force   │ (standalone)
         │        └──────────────────┘
         │
         ▼
    ┌──────────┐
    │ signal   │ (standalone, pure math)
    └──────────┘

DATA MODEL (datamodel.py — the bridge)
    ForceSample, ForceSession, AthleteProfile, TestResult

Layer 2 — EXERCISES (protocol data + calculation)
┌──────────────┐    ┌────────────────────────────┐
│ protocols    │───▶│ hangboard_calc             │
│ (pure data)  │    │ (protocols + rohmert + edge)│
└──────────────┘    └────────────────────────────┘

Layer 3 — ADAPTERS (format → data model)
┌──────────┐ ┌─────────┐ ┌─────────┐ ┌─────────────┐
│ tindeq   │ │ climbro │ │ manual  │ │ csv_generic │
└──────────┘ └─────────┘ └─────────┘ └─────────────┘

Layer 4 — FRONTENDS (applications)
┌──────────┐  ┌──────────┐  ┌──────────┐
│ cli      │  │ report   │  │ notebook │
└──────────┘  └──────────┘  └──────────┘
```

## Implementation Order

**Layer 0 (Foundation):**

0. **`datamodel.py`** — Canonical data types, everything builds on this

**Layer 1 (bottom-up):**

1. **`models/grades.py`** — Lookup tables, no math, quick win
2. **`models/rohmert.py`** — Mathematical foundation, easily testable
3. **`models/edge_depth.py`** — Simple, does not directly require Rohmert
4. **`models/signal.py`** — Smoothing, Peak Detection, RFD (pure math)
5. **`models/strength_analyzer.py`** — Uses Rohmert + Edge + Grades, first "wow"
6. **`models/critical_force.py`** — Standalone model, linear regression

**Layer 2:**

7. **`exercises/protocols.py`** — Pure data classes, immediately testable
8. **`exercises/hangboard_calc.py`** — Connects protocols with models

**Layer 3:**

9. **`adapters/tindeq.py`** — JSON parsing for FingerForceTraining
10. **`adapters/manual.py`** — Manual input for users without a device
11. **`adapters/csv_generic.py`** — Generic import

**Layer 4 + Notebooks:**

12. **`frontends/report.py`** — End-to-end assessment
13. **`frontends/notebook.py`** — Jupyter helpers (plots, DataFrame)
14. **`frontends/cli.py`** — Interactive CLI
15. **Example Notebooks** — Deliverable analyses (see below)

---

## Example Notebooks — Interactive Analyses with References

The notebooks are the **main product** for end users. They combine:
- Real calculations with the library
- Explanatory Markdown cells with scientific references
- Interactive plots
- Immediately executable with your own data (just change the numbers at the top)

### File Structure

```
notebooks/
├── 01_my_climbing_assessment.ipynb    # Personal overall assessment
├── 02_rohmert_curve_explained.ipynb   # Theory: Isometric fatigue
├── 03_critical_force_analysis.ipynb   # Analyze + understand CF test
├── 04_protocol_comparison.ipynb       # Which protocol fits me?
├── 05_session_deep_dive.ipynb         # Analyze Tindeq session
├── 06_progress_tracker.ipynb          # Progress over weeks/months
└── 07_edge_depth_science.ipynb        # Why 20mm? Edge depth correction
```

### Notebook 1: `01_my_climbing_assessment.ipynb`

**Title:** *"How strong am I really? — Personal Climbing Assessment"*

**Target audience:** Any climber who wants to learn about their strengths and weaknesses

```markdown
# 🧗 My Personal Climbing Assessment

## Input — Your Data
*(Only adjust this cell, then run all cells)*
```

```python
# === YOUR DATA ===
BODYWEIGHT_KG = 72
HEIGHT_CM = 178
MVC7_KG = 105          # Total load (BW + added weight), 7s hang, 20mm edge
TEST_EDGE_MM = 20
TRAINING_MODE = 3      # 1=no HB, 2=Repeaters, 3=MaxHangs, 4=MaxHangs+added

# Optional: Endurance data (for CF analysis)
T80_S = 77             # Cumulative hang time at 80% MVC (7/3 Repeaters)
T60_S = 136            # at 60% MVC
T45_S = 323            # at 45% MVC
```

```markdown
## 1. Finger Strength Analysis

Your MVC-7 (Maximum Voluntary Contraction over 7 seconds) is the
most important single indicator for climbing performance. It correlates more strongly
with climbing grade than any other measurable parameter
*(Hörst 2016, p. 47; Giles et al. 2019)*.
```

```python
from climbing_science.models import strength_analyzer, grades

result = strength_analyzer.predict_grade(
    mvc7_kg=MVC7_KG, bodyweight_kg=BODYWEIGHT_KG,
    edge_mm=TEST_EDGE_MM, training_mode=TRAINING_MODE
)

print(f"MVC/BW Ratio:       {result.mvc_bw_ratio:.1%}")
print(f"Predicted Boulder:  {result.boulder_uiaa} ({result.boulder_font} / {result.boulder_v})")
print(f"Einordnung:         {result.percentile}")
```

```markdown
### What Does Your MVC/BW Ratio Mean?

| Ratio | Classification | Boulder (UIAA) | Reference |
|-------|------------|-----------------|----------|
| < 1.0 | Beginner   | ≤ 6+           | Hörst 2016, Tab. 4.2 |
| 1.0–1.3 | Intermediate | 7- bis 8-   | Lattice (n=436) |
| 1.3–1.6 | Advanced   | 8 bis 9-       | r/climbharder 2017 |
| > 1.6 | Elite      | ≥ 9            | Giles et al. 2019 |

> *"Finger strength explained 14% of variance in climbing performance,
>  while technique and mental factors accounted for 78%."*
> — Meta-analysis based on Hörst (2016), Lattice Data
```

```python
# Visualization: Where do you stand?
from climbing_science.frontends import notebook
notebook.plot_strength_benchmark(
    mvc_bw_ratio=result.mvc_bw_ratio,
    highlight_grade=result.boulder_uiaa
)
```

```markdown
## 2. Endurance Analysis (Critical Force)

Critical Force (CF) is the endurance equivalent of MVC-7.
CF describes the force that you can *theoretically hold indefinitely*
before aerobic capacity is exhausted *(Monod & Scherrer 1965)*.

For climbers, CF is measured via intermittent 7/3 repeaters at
various intensities *(Giles et al. 2019)*.
```

```python
from climbing_science.models import critical_force

cf = critical_force.calculate_cf(
    mvc7_kg=MVC7_KG, bodyweight_kg=BODYWEIGHT_KG,
    t80_s=T80_S, t60_s=T60_S, t_low_s=T45_S
)

print(f"Critical Force:     {cf.cf_kg:.1f} kg ({cf.cf_bw_ratio:.1%} BW)")
print(f"W' (Anaerob):       {cf.w_prime_kgs:.0f} kg·s")
print(f"CF/MVC Ratio:       {cf.cf_mvc_ratio:.1%}")
print(f"Predicted Sport:    {cf.predicted_sport_grade}")
print(f"Fit quality (R²):  {cf.r_squared:.3f}")
```

```python
# Visualize CF regression
notebook.plot_critical_force(cf, mvc7_kg=MVC7_KG, bodyweight_kg=BODYWEIGHT_KG)
```

```markdown
### CF/MVC Ratio — Strength vs. Endurance Profile

| CF/MVC Ratio | Profile | Typical for |
|-------------|--------|-------------|
| < 0.35 | Pure Boulderer | Strong fingers, little endurance |
| 0.35–0.45 | Balanced | Good foundation for both |
| > 0.45 | Endurance-dominant | Strong endurance, relatively little max strength |

> *"The relationship between CF and sport climbing grade was r = 0.82."*
> — Giles D. et al. (2019), Int J Sports Physiol Perform
```

```markdown
## 3. Weakness Analysis & Training Recommendation
```

```python
from climbing_science.exercises import hangboard_calc

# Where is the biggest lever?
weaknesses = []
if result.mvc_bw_ratio < 1.3:
    weaknesses.append("🔴 Fingerkraft ist der limitierende Faktor")
if cf.cf_mvc_ratio < 0.38:
    weaknesses.append("🔴 Aerobe Ausdauer deutlich unter Durchschnitt")
if cf.cf_mvc_ratio > 0.50 and result.mvc_bw_ratio < 1.3:
    weaknesses.append("🟡 Good endurance, but strength is not keeping up")

for w in weaknesses:
    print(w)

# Recommend suitable protocols
plan = hangboard_calc.calculate_training_load(
    mvc7_kg=MVC7_KG, bodyweight_kg=BODYWEIGHT_KG,
    protocol="lopez_maxhangs"
)
print(f"\n📋 López MaxHangs @90%: {plan.added_load_kg:+.1f} kg auf {TEST_EDGE_MM}mm")
```

```markdown
## References

1. Rohmert W. (1960). Ermittlung von Erholungspausen für statische Arbeit
   des Menschen. *Int Z Angew Physiol*, 18, 123–164.
2. Monod H., Scherrer J. (1965). The work capacity of a synergic muscular
   group. *Ergonomics*, 8(3), 329–338.
3. Giles D. et al. (2019). The Determination of Finger-Flexor Critical
   Force in Rock Climbers. *Int J Sports Physiol Perform*, 1–8.
4. Hörst E. (2016). *Training for Climbing.* 3rd ed., Falcon Guides.
5. Lattice Training Assessment Benchmarks (n=436). latticetraining.com.
6. r/climbharder Survey 2017 (n=555).
```

---

### Notebook 2: `02_rohmert_curve_explained.ipynb`

**Title:** *"The Physics Behind the Hangboard — Rohmert's Fatigue Curve"*

**Contents:**

- Original paper Rohmert (1960) explained — what was measured, why
- Mathematical derivation of the curve (Sjøgaard 1986, Frey-Law & Avin 2010)
- Interactive plot: %MVC vs. Time-to-Failure for 3 models
- Why "Expert" holds longer than "Beginner" — physiological explanation
- Practical application: "I hold 23s at +20kg — what is my MVC-7?"
- Comparison with SC Hangboard Calculator results

```python
# Interactive: Plot Rohmert curve
from climbing_science.models import rohmert
from climbing_science.frontends import notebook

notebook.plot_rohmert_curve(models=["beginner", "intermediate", "expert"])

# Plot your own data point:
my_ratio = 0.80  # 80% MVC
my_time = rohmert.time_to_failure(my_ratio, model="intermediate")
print(f"At {my_ratio:.0%} MVC you can hold for approx. {my_time:.0f} seconds (Intermediate)")
```

---

### Notebook 3: `03_critical_force_analysis.ipynb`

**Title:** *"Critical Force — Measuring and Understanding Your Aerobic Climbing Capacity"*

**Contents:**

- What is Critical Force? (Monod & Scherrer 1965 → Climbing)
- The 3-point test protocol step by step
- Linear regression visualized (Work vs. Time, CF = slope)
- W' explained: Your "anaerobic tank" in kg·s
- CF/BW benchmarks per grade (Giles et al. 2019, Lattice)
- What trains CF? Endurance Repeaters, Density Hangs
- SC Calculator comparison (demo dataset)

---

### Notebook 4: `04_protocol_comparison.ipynb`

**Title:** *"Which Hangboard Protocol Suits Me?"*

**Contents:**

- All 9 protocols at a glance (author, intensity, energy system)
- Interactive comparison: enter your own MVC-7 → loads for each protocol
- TUT comparison: Which protocol delivers how much volume?
- Decision tree: Weakness → recommended protocol
- References per protocol (López 2012, Hörst 2016, Nelson, Bechtel)

```python
from climbing_science.exercises import hangboard_calc
notebook.plot_protocol_comparison(mvc7_kg=105, bodyweight_kg=72)
```

---

### Notebook 5: `05_session_deep_dive.ipynb`

**Title:** *"Analyzing a Tindeq Session — Force Curve Under the Microscope"*

**Contents:**

- Load session (Tindeq JSON, Climbro CSV or generic)
- Plot force-time curve with segment markers
- Peak Detection: Automatic MVC-7 extraction
- RFD analysis: How fast do you build force?
- Comparison: Session A vs. Session B (progression)
- Signal quality: Detecting noise, artifacts

---

### Notebook 6: `06_progress_tracker.ipynb`

**Title:** *"Tracking Progress — Weeks and Months at a Glance"*

**Contents:**

- Load all sessions from a directory
- Plot MVC-7 progression over time
- Trend analysis: Linear fit + projection
- CF progression (if CF tests are available)
- Training volume (TUT) per week
- Warning on stagnation or overtraining

---

### Notebook 7: `07_edge_depth_science.ipynb`

**Title:** *"Why 20mm? — The Science of Edge Depth Correction"*

**Contents:**

- Amca et al. (2012): What was measured?
- The 2.5%/mm model explained and derived
- Interactive: Force on 15mm → what would that be on 20mm?
- Limitations of the model: Where does the linear correction become inaccurate?
- Recommendation: When to use which edge depth for testing

---

### Design Principles for Notebooks

1. **Input at the top, result below** — User only changes one cell
2. **Every calculation explained** — Markdown cell before every code cell
3. **References inline** — Every claim backed with (Author Year)
4. **Reference list at the end** — Complete bibliography
5. **Plots over tables** — Visual where possible
6. **Benchmark context** — "Where do you stand?" always with comparison data
7. **No magic numbers** — Every constant documented with source
8. **Copy-paste ready** — Notebooks work standalone without installation pain

### Dependencies for Notebooks

```toml
# In pyproject.toml unter [project.optional-dependencies]
notebooks = [
    "jupyter>=1.0",
    "matplotlib>=3.8",
    "pandas>=2.0",
    "ipywidgets>=8.0",    # Optional: Slider for interactive input
]
```

---

## References

1. Rohmert W. (1960). Ermittlung von Erholungspausen für statische Arbeit des Menschen. Int Z Angew Physiol, 18, 123–164.
2. Monod H., Scherrer J. (1965). The work capacity of a synergic muscular group. Ergonomics, 8(3), 329–338.
3. Giles D. et al. (2019). Finger-Flexor Critical Force in Rock Climbers. Int J Sports Physiol Perform.
4. Amca A.M. et al. (2012). Effect of hold depth on grip strength and endurance.
5. Hörst E. (2016). Training for Climbing. 3rd ed., Falcon Guides.
6. Poole D.C. et al. (2016). Critical Power: An Important Fatigue Threshold. Med Sci Sports Exerc, 48(11).
7. López-Rivera E., González-Badillo J.J. (2012). The effects of two maximum grip strength training methods. JSCR, 26(4), 1078–1085.
8. Lattice Training Assessment Data (n=436). latticetraining.com.
9. Sjøgaard G. (1986). Intramuscular changes during long-term contraction. In: The Ergonomics of Working Postures.
10. Frey-Law L.A., Avin K.G. (2010). Endurance time is joint-specific. Muscle & Nerve, 42(5), 799–807.
11. Banaszczyk J. StrengthClimbing.com — Finger Strength Analyzer, Hangboard Calculator, CF Calculator.
