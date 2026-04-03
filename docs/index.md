# climbing-science

**Open-source Python library for evidence-based climbing training analysis.**

[![CI](https://github.com/8cH9azbsFifZ/climbing-science/actions/workflows/ci.yml/badge.svg)](https://github.com/8cH9azbsFifZ/climbing-science/actions/workflows/ci.yml)
[![Docs](https://github.com/8cH9azbsFifZ/climbing-science/actions/workflows/docs.yml/badge.svg)](https://8cH9azbsFifZ.github.io/climbing-science/)

## Why this project exists

1. **Open Source** — Existing climbing analysis tools hide behind paywalls or proprietary JavaScript. This library is open, peer-reviewable, and citable.
2. **Reproducible** — Every formula traces back to a published reference (BibTeX in `docs/references.bib`), not a black-box implementation.
3. **Validatable** — Unit tests verify results against published benchmarks (Giles et al., Lattice Research, Levernier & Laffaye).
4. **End-to-end** — Raw force-gauge data flows through a complete assessment pipeline: import → clean → analyse → report.
5. **Dual purpose** — A Python library you can `pip install` *and* a mathematically rigorous, auto-generated reference manual.

## Installation

```bash
pip install -e .
```

For development:

```bash
pip install -e ".[dev]"
```

## Usage

```python
import climbing_science
```

## Documentation

Full auto-generated documentation: [User Manual](https://8cH9azbsFifZ.github.io/climbing-science/)

Build locally:

```bash
make docs
```

## Development

```bash
make test        # run tests
make lint        # run linter
make docs        # build documentation
make bump-patch  # bump patch version (0.1.0 → 0.1.1)
make bump-minor  # bump minor version (0.1.0 → 0.2.0)
```

## References

All algorithms and formulas cite peer-reviewed sources. See [`docs/references.bib`](docs/references.bib) for the complete bibliography.

## License

MIT — see [LICENSE](LICENSE).
