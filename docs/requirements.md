# Requirements Specification — climbing-science

> **Status:** Living document. Updated with each new module.

## 1 Functional Requirements

### FR-01: Grade Conversion (M0)

| ID | Requirement | Acceptance Criteria | Reference |
|----|------------|-------------------|-----------|
| FR-01.1 | Convert between UIAA, French, YDS, V-Scale, Fontainebleau | Round-trip: `convert(convert(g, A, B), B, A) == g` | Draper et al. 2015 |
| FR-01.2 | Auto-detect grade system from string | `parse("7a")` → French, `parse("V5")` → V-Scale | — |
| FR-01.3 | Compare grades across systems | `compare("7a", "V5")` returns ordering | IRCRA 2015 |
| FR-01.4 | Numeric difficulty index (0–100) | Monotonically increasing with difficulty | IRCRA 2015 |

### FR-02: Data Models (M0)

| ID | Requirement | Acceptance Criteria | Reference |
|----|------------|-------------------|-----------|
| FR-02.1 | ClimberProfile with validation | Pydantic model, JSON-serialisable | — |
| FR-02.2 | Assessment result model | Stores MVC-7, CF, grade, body weight | — |
| FR-02.3 | SessionLog model | Protocol, sets, loads, RPE, notes | — |
| FR-02.4 | Protocol model | Parameters, notation, progression rules | — |

### FR-03: Finger Strength (M1)

| ID | Requirement | Acceptance Criteria | Reference |
|----|------------|-------------------|-----------|
| FR-03.1 | MVC-7 to climbing grade | ±1 grade accuracy vs Lattice benchmark (n=901) | Giles et al. 2019 |
| FR-03.2 | Grade to required MVC-7 | Inverse of FR-03.1 | derived |
| FR-03.3 | Rohmert curve normalisation | Convert any hang duration to MVC-7 equivalent | Rohmert 1960 |
| FR-03.4 | Rate of Force Development | RFD from time-series data | Levernier & Laffaye 2019 |
| FR-03.5 | Power-to-weight ratio | MVC/BW with level interpretation | Schweizer 2001 |

### FR-04: Endurance (M2)

| ID | Requirement | Acceptance Criteria | Reference |
|----|------------|-------------------|-----------|
| FR-04.1 | Critical Force from test data | Linear regression on multi-intensity repeater data | Jones et al. 2010 |
| FR-04.2 | W' (anaerobic capacity) | y-intercept of CF regression | Jones et al. 2010 |
| FR-04.3 | CF/MVC ratio interpretation | Classify: endurance-limited / balanced / strength-limited | Fryer et al. 2018 |
| FR-04.4 | Time-to-failure prediction | Given force > CF, predict exhaustion time | Critical Power Model |

### FR-05: Training Load (M3)

| ID | Requirement | Acceptance Criteria | Reference |
|----|------------|-------------------|-----------|
| FR-05.1 | Time Under Tension calculation | TUT per set, session, week from protocol params | López 2014 |
| FR-05.2 | RPE ↔ %MVC conversion | Bidirectional mapping with Effort Levels | López EL scale |
| FR-05.3 | ACWR calculation | Acute:Chronic workload ratio from session history | Gabbett 2016 |
| FR-05.4 | Overtraining warning | Traffic-light system from volume trends | Gabbett 2016 |

### FR-06: Protocol Library (M4)

| ID | Requirement | Acceptance Criteria | Reference |
|----|------------|-------------------|-----------|
| FR-06.1 | Protocol registry | ≥20 hangboard protocols with full parameters | diverse |
| FR-06.2 | Protocol selection | Input: weakness + level + equipment → protocol | Coaching logic |
| FR-06.3 | Standard notation | `3x MAXHang @20 mm W+10kg 10(3):180s` format | — |
| FR-06.4 | Week-by-week progression | Volume/intensity progression per protocol | López 4-week cycle |

### FR-07: Periodization (M5)

| ID | Requirement | Acceptance Criteria | Reference |
|----|------------|-------------------|-----------|
| FR-07.1 | Macrocycle generation | Annual plan with phases | Hörst 2016 |
| FR-07.2 | Mesocycle generation | 4–8 week blocks with deload | López, Anderson 2014 |
| FR-07.3 | Microcycle generation | Weekly session plan | — |
| FR-07.4 | Constraint validation | Never increase volume + intensity + frequency simultaneously | López principle |

### FR-08: Diagnostics (M6)

| ID | Requirement | Acceptance Criteria | Reference |
|----|------------|-------------------|-----------|
| FR-08.1 | Level classification | Beginner / Intermediate / Advanced / Elite | Lattice, Draper |
| FR-08.2 | Weakness identification | Primary limiter from assessments | CF/MVC ratio, Pull/MVC |
| FR-08.3 | Training priority | Recommended protocol category | Decision tree |
| FR-08.4 | Progress quantification | Delta between two assessments | — |

### FR-09: Data I/O (M7)

| ID | Requirement | Acceptance Criteria | Reference |
|----|------------|-------------------|-----------|
| FR-09.1 | Force-gauge CSV import | Parse common force-gauge CSV formats | — |
| FR-09.2 | JSON session log import | Validate and parse session logs | — |
| FR-09.3 | Report export | Assessment → Markdown/JSON | — |
| FR-09.4 | Plan export | Periodization → JSON/iCal | — |

---

## 2 Non-Functional Requirements

| ID | Category | Requirement |
|----|----------|------------|
| NFR-01 | **Traceability** | Every public function docstring contains a BibTeX key referencing `docs/references.bib`. |
| NFR-02 | **Testing** | ≥90% line coverage. Tests compare against published data, not invented values. |
| NFR-03 | **Performance** | All calculations complete in <100ms for single-athlete data. |
| NFR-04 | **Portability** | Python 3.10+ on Linux, macOS, Windows. No compiled extensions. |
| NFR-05 | **Documentation** | Auto-generated API docs from docstrings. User manual updated on every push. |
| NFR-06 | **Versioning** | Semantic versioning. Changelog maintained in `CHANGELOG.md`. |
| NFR-07 | **Dependencies** | Minimal: only `pydantic` required. All others optional. |
| NFR-08 | **Reproducibility** | Given identical inputs, all functions produce identical outputs. No randomness without explicit seed. |
