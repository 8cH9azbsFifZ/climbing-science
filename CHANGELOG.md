# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
