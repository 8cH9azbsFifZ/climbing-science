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

## Changelog

- **Single source of truth**: `CHANGELOG.md` in repo root.
- `docs/changelog.md` is a **symlink** to `../CHANGELOG.md` — never create a separate file there.
- Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
- Always add entries under `## [Unreleased]` before bumping.

## Packaging (PyPI)

- Build locally: `make build` (sdist + wheel + twine check).
- Release: `make bump-patch` → `git push origin main --tags` → publish.yml handles PyPI upload.
- Never commit `dist/`, `build/`, or `*.egg-info/` directories.
