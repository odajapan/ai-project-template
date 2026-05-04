---
paths:
  - "src/**/data/**"
  - "notebooks/**"
---

# Data Pipeline Rules

## Directory Convention

| Path | Purpose |
|------|---------|
| `data/raw/` | Original files — never modified, never committed |
| `data/interim/` | Intermediate results from transformation steps |
| `data/processed/` | Final datasets ready for modelling |
| `data/external/` | Third-party data; sanitize before committing results |

All `data/` subdirectories are gitignored. Document dataset provenance in
`references/` instead.

## Code Style

- Entry point for each pipeline stage: a Click command in `data/make_dataset.py`
- Each transformation step is a pure function: `(input: Path, output: Path) -> None`
- Log progress with the standard `logging` module — no bare `print()`

## Notebooks

- Naming: `<order>-<initials>-<description>.ipynb`
  (e.g. `01-ho-initial-exploration.ipynb`)
- Strip outputs before committing (`nbstripout` pre-commit hook handles this)
- Notebooks are for exploration only — production logic belongs in `src/`
