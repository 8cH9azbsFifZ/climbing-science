# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
