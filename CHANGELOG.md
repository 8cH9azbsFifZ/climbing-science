# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

- **Data attribution** — All Lattice Training references now explicitly clarify
  that only publicly available summary statistics (blog, podcasts, social media)
  were used. No proprietary datasets are included. Composite benchmark tables
  are documented as an independent synthesis from multiple public sources.

## [0.4.0] — 2026-04-06

### Added

- **frontends/cli** — Command-line interface with 4 subcommands: `grade` (convert between systems), `analyze` (MVC-7 strength analysis), `protocols` (list/filter hangboard protocols), `endurance` (Critical Force from 3-point test). Entry point: `climbing-science`.
- **notebooks** — 6 new example notebooks: Personal Assessment (01), Rohmert Curve (02), Critical Force (03), Protocol Comparison (04), Session Deep Dive (05), Progress Tracker (06), Edge Depth Science (07).
- 12 CLI tests covering all subcommands.

### Fixed

- **CLI** — Correct API usage for `power_to_weight()` (tuple return), `critical_force()` (tuple return), `interpret_cf_ratio()` (dict keys), grade system name mapping (`v` → `v-scale`).

### Changed

- **PLAN.md** — Updated to reflect actual implementation state: flat module structure, correct coverage numbers, 3 extra modules (diagnostics, periodization, io).
- **CHANGELOG** — Added missing `[0.3.2]` section, cleaned up unreleased entries.

## [0.3.4] — 2026-04-06

### Added

- **notebooks** — 5 example notebooks: Rohmert curve, Edge Depth comparison, Protocol Comparison, Climbing Assessment, Critical Force analysis, Session Deep Dive.
- **cli** — `climbing-science` CLI entry point with `grade`, `analyze`, and `protocols` subcommands.
- **pre-commit** — `.pre-commit-config.yaml` for local ruff check + format enforcement.

### Fixed

- **signal** — ruff formatting fix in `signal.py` (f-string line join).

## [0.3.3] — 2026-04-06

### Added

- **signal** — `extract_ttf()` function: extracts actual Time-to-Failure from raw force-time curves. Detects hold onset and failure point with configurable drop threshold and dip tolerance. Returns TtF, mean force, and coefficient of variation. References: Rohmert 1960, Jones et al. 2010.
- **endurance** — `validate_ttf()` function: compares model-predicted TtF (from `time_to_failure()`) with actual measured TtF. Returns absolute/relative error and model quality rating (excellent/good/fair/poor). Reference: Jones et al. 2010.
- **models** — `TtFResult` Pydantic model for structured TtF extraction results.
- **protocols** — `ttf-endurance-3pt` protocol: standard 3-point Time-to-Failure test at 80%, 60%, 45% MVC with 5–10 min rest between bouts. Reference: Jones et al. 2010, Fryer et al. 2018.

### Changed

- **PLAN** — Updated PLAN.md to reflect actual implementation state (flat module structure, correct coverage numbers, extra modules).

## [0.3.2] — 2026-04-06

### Added

- **strength** — `StrengthModel` enum with `COMPOSITE` (default, route-grade) and `MAXTOGRADE` (crowd-sourced bouldering survey, n ≈ 2 000+, V1–V17) prediction models. New `model` keyword parameter on `mvc7_to_grade()` and `grade_to_mvc7()`.
- **references** — Added `maxtograde2020` and `banaszczyk2020` BibTeX entries.

### Fixed

- **models** — Moved `fmax_right_kg`, `fmax_left_kg`, and `training_mode` from `AthleteProfile` to `TestResult`. Athlete profile now contains only immutable properties; measurement data belongs in test results.
- Resolved all ruff lint errors (unused imports/variables, import sorting).
- Applied ruff formatting to 8 files.
- Removed deprecated license classifier (PEP 639).

## [0.3.1] — 2026-04-06

### Fixed

- **grades** — Full Google-style docstrings with Args, Returns, Raises, References, Examples for all 6 public functions (`convert`, `parse`, `compare`, `difficulty_index`, `from_index`, `all_grades`) and expanded class docs (`Grade`, `RouteSystem`, `BoulderSystem`). Added type annotations.
- **__init__** — Added 8 missing re-exports (`BoulderSystem`, `RouteSystem`, `GradeError`, `UnknownGradeError`, `UnknownSystemError`, `GradeDomainError`, `all_grades`, `from_index`).
- **io** — Added References sections to all 5 public functions.
- **models** — Expanded docstrings for `Discipline`, `GripType`, `PullUpTest` with Members/Attributes/References.
- **signal** — Expanded `Peak` dataclass docstring with Attributes/References.
- **protocols** — Added References to `format_notation()`.
- **adapters/tindeq** — Added References to `extract_peaks()` and `load_all()`.
- **adapters/manual** — Added References to `quick_profile()`, Examples to `from_bodyweight_hang()`.
- **frontends/notebook** — Added References to `session_to_dataframe()`.

## [0.3.0] — 2026-04-05

### Added

- **edge_depth** — Edge depth correction based on Amca et al. (2012). Linear 2.5 %/mm model: `correction_factor`, `convert_force`, `normalize_to_reference`, `estimate_force_at_depth`. Full correction factor table in science docs.
- **signal** — Force-curve signal processing (pure stdlib, no NumPy): `smooth` (moving avg / EMA), `detect_peaks`, `compute_rfd` (Levernier 2019), `best_n_second_average` (MVC-7 extraction), `compute_impulse`, `segment_repeaters` (7/3 protocol segmentation).
- **adapters/manual** — Manual input adapter for climbers without a force gauge: `from_mvc7_test` (with Rohmert + edge depth normalisation), `from_repeater_test` (3-point CF protocol), `from_bodyweight_hang`, `quick_profile`.
- **adapters/tindeq** — Tindeq Progressor JSON adapter: `load` / `load_all` (FFT format, simple format, bare array), `extract_mvc7`, `extract_peaks`. Auto-detects sample rate from timestamps.
- **frontends/notebook** — Jupyter helpers (optional matplotlib): `plot_force_session`, `plot_rohmert_curve`, `plot_strength_benchmark`, `plot_protocol_comparison`, `session_to_dataframe`.
- `[notebooks]` optional dependency group (matplotlib, pandas, jupyter).
- Science docs for edge depth correction and signal processing with formulas and reference tables.
- API docs for all new modules.
- BibTeX entry for Amca et al. (2012).

## [0.2.0] — 2026-04-05

### Added

- **M2: endurance** — Critical Force regression (Jones 2010), W' balance (Skiba 2012), time-to-failure, endurance classification, CF/MVC ratio interpretation.
- **M3: load** — TUT calculation, RPE↔%MVC conversion (López 2014), ACWR (Gabbett 2016), overtraining check, margin-to-failure.
- **M4: protocols** — Registry of 24 hangboard protocols (López, Hörst, Anderson, Nelson, Lattice, etc.) covering all energy systems. Selection and formatting utilities.
- **M5: periodization** — Macrocycle, mesocycle, and microcycle generation with deload weeks. López constraint validation (never increase vol+intensity+freq simultaneously).
- **M6: diagnostics** — Level classification from redpoint grade (IRCRA/Draper 2015), weakness identification from assessment metrics, training priority decision tree, progress delta tracking.
- **M7: io** — CSV force-gauge file parsing, SessionLog JSON round-trip, assessment Markdown and JSON export.
- **grades rewrite** — RouteSystem/BoulderSystem separation, IRCRA-based grade table with domain separation (route ↔ boulder).
- Full `__init__.py` re-exports for all 9 modules (grades, models, strength, endurance, load, protocols, periodization, diagnostics, io).
- PyPI packaging: `make build`, publish workflow on `v*` tags, MANIFEST.in, py.typed marker.
- Comprehensive test suite: 363 tests, 94% coverage.

## [0.1.0] — 2026-04-03

### Added

- Initial project structure with `pyproject.toml`, CI, and auto-generated documentation.
- `docs/references.bib` — master bibliography with 18 peer-reviewed sources.
- Design document and requirements specification.
- MkDocs configuration with mkdocstrings for API auto-generation.
- GitHub Actions CI pipeline (test, lint, docs).
- Automatic versioning with `bump-my-version`.
- Makefile for common development tasks.
- **M0: grades** — grade conversion between UIAA, French, YDS, V-Scale, Font (Draper 2015).
- **M0: models** — Pydantic v2 data models (ClimberProfile, MVC7Test, SessionLog, Protocol, Injury).
- **M1: strength** — MVC-7 ↔ grade correlation (Lattice n≈901), Rohmert curve, RFD, power-to-weight.
- User Guide: Getting Started, Hangboard Training, Grade Prediction.
- Science Pages: Rohmert Curve, Critical Force, Grade Conversion.
