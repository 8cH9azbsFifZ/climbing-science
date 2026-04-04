# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **M2: endurance** — Critical Force regression (Jones 2010), W' balance (Skiba 2012), time-to-failure, endurance classification, CF/MVC ratio interpretation.
- **M3: load** — TUT calculation, RPE↔%MVC conversion (López 2018), ACWR (Gabbett 2016), overtraining check, margin-to-failure.
- **M4: protocols** — Registry of 20 hangboard protocols (López, Hörst, Anderson, Nelson, Lattice, etc.) covering all energy systems. Selection and formatting utilities.
- **M5: periodization** — Macrocycle, mesocycle, and microcycle generation with deload weeks. López constraint validation (never increase vol+intensity+freq simultaneously).
- **M6: diagnostics** — Level classification from redpoint grade (IRCRA/Draper 2015), weakness identification from assessment metrics, training priority decision tree, progress delta tracking.
- **M7: io** — CSV force-gauge file parsing, SessionLog JSON round-trip, assessment Markdown and JSON export.
- Full `__init__.py` re-exports for all 8 modules (grades, models, strength, endurance, load, protocols, periodization, diagnostics, io).
- Comprehensive test suite: 246 tests, 94% coverage.
- MkDocs nav updated with all API reference pages.

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
