# climbing-science 🧗

**Evidence-based climbing training analysis — as a Python library and CLI.**

[![CI](https://github.com/8cH9azbsFifZ/climbing-science/actions/workflows/ci.yml/badge.svg)](https://github.com/8cH9azbsFifZ/climbing-science/actions/workflows/ci.yml)
[![Docs](https://github.com/8cH9azbsFifZ/climbing-science/actions/workflows/docs.yml/badge.svg)](https://8cH9azbsFifZ.github.io/climbing-science/)
[![PyPI](https://img.shields.io/pypi/v/climbing-science)](https://pypi.org/project/climbing-science/)
[![Python](https://img.shields.io/pypi/pyversions/climbing-science)](https://pypi.org/project/climbing-science/)
[![License: GPL-3.0-or-later](https://img.shields.io/badge/license-GPL--3.0--or--later-blue.svg)](LICENSE)
[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/8cH9azbsFifZ/climbing-science/main?labpath=notebooks%2Fgrade_conversion.ipynb)

Convert grades, predict strength-to-grade, compute Critical Force, plan periodisation, pick protocols — all from peer-reviewed science, all in one `pip install`.

```bash
pip install climbing-science
```

---

## Quick Start

### Grade Conversion

```python
from climbing_science import convert, parse

convert("7a", "French", "YDS")        # → '5.11d'
convert("7a", "French", "UIAA")       # → 'VIII'
convert("V5", "V-Scale", "Font")      # → '6C'

parse("5.12a").difficulty_index        # → 19 (IRCRA universal scale)
```

### Finger Strength ↔ Grade

```python
from climbing_science import mvc7_to_grade, grade_to_mvc7, power_to_weight

mvc7_to_grade(130.0)                   # → '7a'  (130% BW → French grade)
grade_to_mvc7("7a")                    # → 128.0 (%BW needed for 7a)
power_to_weight(90.0, 72.0)            # → (125.0, 'intermediate')
```

### Critical Force & Endurance

```python
from climbing_science import critical_force, interpret_cf_ratio, cf_mvc_ratio

cf, w_prime, r2 = critical_force(
    intensities_percent_mvc=[80, 60, 45],
    tlim_seconds=[77, 136, 323],
)
# cf=34.1% MVC, w_prime=3533.7, R²=1.0

interpret_cf_ratio(cf_mvc_ratio(cf, mvc7_percent_bw=130.0))
# → {'category': 'endurance-limited', 'priority': 'Repeaters, ARC, SubHangs'}
```

### Training Load & Injury Prevention

```python
from climbing_science import rpe_to_mvc_pct, tut_per_session, overtraining_check

rpe_to_mvc_pct(8.0)                    # → 85.0 (%MVC)
tut_per_session(10.0, 1, 5)            # → 50.0 seconds
overtraining_check([400, 450, 500, 600])
# → {'acwr': 1.33, 'status': 'yellow', 'message': '...approaching high-risk zone...'}
```

### Protocol Library (21 protocols)

```python
from climbing_science import get_protocol, select_protocols, format_notation
from climbing_science.models import ClimberLevel

p = get_protocol("lopez-maxhang-maw")
format_notation(p, added_weight_kg=15.0)
# → '4× MaxHang @18mm HC W+15.0kg 10s(0):180s'

select_protocols("strength", ClimberLevel.INTERMEDIATE)
# → [lopez-maxhang-maw, lopez-maxhang-haw, horst-7-53, bechtel-ladders, ...]
```

### Diagnostics & Periodisation

```python
from climbing_science import classify_level, identify_weakness, training_priority
from climbing_science import generate_macrocycle

classify_level("7a")                            # → 'advanced'
weaknesses = identify_weakness(1.0, cf_mvc_ratio=0.30)
# → ['finger-strength-moderate', 'endurance']
training_priority(weaknesses)                   # → 'max-strength'

plan = generate_macrocycle(total_weeks=52)       # Annual plan (Hörst model)
```

---

## Command-Line Interface

```bash
# Grade conversion
climbing-science grade "7a+" --to all
#   FRENCH: 7a+
#     UIAA: VIII+
#      YDS: 5.12a

# Strength analysis from Tindeq / force gauge
climbing-science analyze --mvc7 90 --bw 72
# ═══════════════════════════════════════════
#   🧗 Climbing Strength Analysis
#   Power-to-weight:    125.0% BW
#   Predicted route:    6c+
# ═══════════════════════════════════════════

# Browse 21 hangboard protocols
climbing-science protocols --level intermediate

# Critical Force from 3-point test
climbing-science endurance --intensities 80 60 45 --durations 77 136 323
```

---

## What's Inside

| Module | What it does | Key references |
|---|---|---|
| **grades** | Convert between 5 grading systems (UIAA, French, YDS, Font, V-Scale) | Draper et al. 2015 (IRCRA) |
| **strength** | MVC-7 ↔ grade prediction, power-to-weight, Rohmert curve | Giles 2006, Rohmert 1960 |
| **endurance** | Critical Force, W', time-to-failure, CF/MVC diagnostics | Jones 2010, Fryer 2018 |
| **load** | RPE ↔ %MVC, TUT, ACWR, overtraining detection | López-Rivera 2014, Gabbett 2016 |
| **protocols** | 21 hangboard protocols with full parameters | López, Hörst, Anderson, Lattice |
| **periodization** | Macro/meso/microcycle generation | Hörst 2016, López-Rivera 2014 |
| **diagnostics** | Level classification, weakness ID, progress tracking | Draper 2015, Fryer 2018 |
| **signal** | Peak detection, RFD, impulse from force-gauge data | Levernier & Laffaye 2019 |
| **edge_depth** | Edge-depth correction factors | Amca et al. 2012 |
| **io** | Export assessments as JSON / Markdown | — |

Every function cites its source paper. Full bibliography: [`docs/references.bib`](docs/references.bib).

---

## Why This Library

- **Open source** — no paywalls, no black boxes.  Every formula traces to a published reference.
- **Deterministic** — pure functions, no side effects, tested against published benchmarks (521 tests).
- **Zero heavy dependencies** — stdlib only at runtime.  Optional `matplotlib` for plotting.
- **Dual interface** — Python API for integration, CLI for quick lookups.

---

## Interactive Notebooks

Explore the science hands-on (click the Binder badge above, or run locally):

| Notebook | Topic |
|---|---|
| [01 — My Climbing Assessment](notebooks/01_my_climbing_assessment.ipynb) | Full strength + endurance assessment |
| [02 — Rohmert Curve](notebooks/02_rohmert_curve_explained.ipynb) | Isometric fatigue model explained |
| [03 — Critical Force](notebooks/03_critical_force_analysis.ipynb) | CF/W' from 3-point test |
| [04 — Protocol Comparison](notebooks/04_protocol_comparison.ipynb) | Compare 21 hangboard protocols |
| [05 — Session Deep Dive](notebooks/05_session_deep_dive.ipynb) | Analyse a single session |
| [06 — Progress Tracker](notebooks/06_progress_tracker.ipynb) | Track gains over time |
| [07 — Edge Depth Science](notebooks/07_edge_depth_science.ipynb) | Edge-depth correction factors |

---

## Installation

```bash
pip install climbing-science            # from PyPI
```

With plotting support:

```bash
pip install "climbing-science[plot]"    # adds matplotlib
```

For development:

```bash
git clone https://github.com/8cH9azbsFifZ/climbing-science.git
cd climbing-science
pip install -e ".[dev]"
make test                               # 521 tests, ~0.3s
```

---

## Documentation

Full API reference (auto-generated from docstrings): **[User Manual](https://8cH9azbsFifZ.github.io/climbing-science/)**

---

## Contributing

```bash
make test        # run tests
make lint        # ruff check + format
make docs        # build documentation locally
make bump-patch  # release: 0.4.1 → 0.4.2
```

---

## License

GPL-3.0-or-later — see [LICENSE](LICENSE).
