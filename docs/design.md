# Design Document — climbing-science

> **Status:** Living document — auto-generated sections are rebuilt on every CI run.

## 1 Purpose

`climbing-science` is an open-source Python library that translates peer-reviewed
climbing-physiology research into validated, reusable algorithms.

### 1.1 Design Goals

| # | Goal | Rationale |
|---|------|-----------|
| G1 | **Traceability** | Every public function cites its source (BibTeX key → `docs/references.bib`). |
| G2 | **Reproducibility** | Pure functions, deterministic output, no hidden state. |
| G3 | **Validation** | Unit tests compare against published benchmarks with stated tolerance. |
| G4 | **Composability** | Small, focused modules that can be combined into end-to-end pipelines. |
| G5 | **Accessibility** | `pip install climbing-science` — no external services, no API keys. |

### 1.2 Non-Goals

- GUI or web interface (this is a library).
- Real-time sensor communication (consumers handle I/O, we handle math).
- Proprietary algorithms without published source.

## 2 Architecture

```
climbing-science/
├── src/climbing_science/
│   ├── __init__.py          # version, public API re-exports
│   ├── grades.py            # M0: grade conversion (Draper 2015)
│   ├── models.py            # M0: Pydantic data models
│   ├── strength.py          # M1: MVC-7, Rohmert, RFD
│   ├── endurance.py         # M2: critical force, W'
│   ├── load.py              # M3: TUT, RPE, ACWR
│   ├── protocols.py         # M4: protocol registry & selection
│   ├── periodization.py     # M5: macro/meso/micro cycles
│   ├── diagnostics.py       # M6: athlete profiling & weakness
│   └── io.py                # M7: data import/export
├── tests/                   # mirrors src/ structure
├── docs/
│   ├── references.bib       # master bibliography
│   ├── design.md            # this document
│   └── requirements.md      # functional & non-functional reqs
└── pyproject.toml
```

### 2.1 Layer Model

```
Layer 0  ─  grades · models                     ← no dependencies
Layer 1  ─  strength · endurance                 ← depends on Layer 0
Layer 2  ─  load · protocols                     ← depends on Layer 0 + 1
Layer 3  ─  periodization · diagnostics          ← depends on Layer 0 + 1 + 2
Layer 4  ─  io (import/export, data pipelines)   ← depends on all
```

Upper layers may import from lower layers. Never the reverse.

### 2.2 Module Design Criteria

Each module MUST:

1. Be a single `.py` file (until it exceeds ~500 lines, then split into a sub-package).
2. Contain only pure functions and Pydantic models.
3. Have a corresponding `tests/test_<module>.py`.
4. Cite sources in every public function docstring.
5. Export its public API via `__all__`.

## 3 Data Flow

```
Raw force data (CSV/JSON)
    │
    ▼
  io.read_force_csv()
    │
    ▼
  strength.mvc7() / endurance.critical_force()
    │
    ▼
  diagnostics.classify_level() + diagnostics.identify_weakness()
    │
    ▼
  protocols.select() → periodization.mesocycle()
    │
    ▼
  io.export_report()
```

## 4 Dependencies

| Dependency | Purpose | Required |
|-----------|---------|----------|
| `pydantic>=2.0` | Data models, validation, JSON schema | Yes |
| `matplotlib>=3.8` | Plotting (force curves, periodization charts) | Optional `[plot]` |

## 5 Versioning

- [Semantic Versioning 2.0.0](https://semver.org/)
- `patch`: bug fixes, doc improvements, test additions
- `minor`: new module or significant feature addition
- `major`: breaking API changes
- Managed via `bump-my-version` (config in `pyproject.toml`)
