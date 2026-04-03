# Copilot Instructions — climbing-science

## Commit Rules

- **No AI markers**: Never add `Co-authored-by: Copilot` or any AI-related trailers to commits.
- All commits must appear as authored by the repository owner only.
- Commit messages: concise, conventional-commit style (`feat:`, `fix:`, `docs:`, `test:`, `chore:`).

## Code Rules

- Every public function MUST have a Google-style docstring citing its source paper (BibTeX key from `docs/references.bib`).
- Every module MUST have unit tests against published benchmarks.
- Small modules, one responsibility each.
- Pure functions preferred — deterministic, no side effects.

## Versioning

- Use `make bump-patch` / `make bump-minor` for releases.
- Always update `CHANGELOG.md` when bumping versions.

## Documentation

- Docs auto-generate from docstrings via mkdocstrings.
- Update `docs/references.bib` when adding new paper references.
