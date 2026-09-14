# Contributing

This repository contains only code: validation, database-building, and
Abaqus `.inc` export logic for material parameter sets. It has no material
data of its own — that lives in the separate
[mat-data](https://github.com/ICAMS/mat-data) repository.

## Adding or updating a material (data change)

Open a pull request against [mat-data](https://github.com/ICAMS/mat-data),
not here. See its `CONTRIBUTING.md`.

## Changing the API or export logic (code change)

1. Make changes under `src/mat_data_handler/`.
2. Add/update tests under `tests/`.
3. Follow SemVer: patch for bug fixes, minor for backward-compatible
   additions, major for breaking changes to the public API
   (`build_database`, `export_entry`, CLI flags).
4. Update `CHANGELOG.md`.

## Running tests locally

```bash
pip install -e ".[test]"
export MAT_DATA_LOCAL_PATH=../mat-data   # point at a sibling mat-data checkout
pytest
```

## Release process

Tag `vX.Y.Z` to trigger `.github/workflows/release.yml`, which builds and
publishes to PyPI via Trusted Publishing. conda-forge tracks PyPI releases
once `conda-recipe/meta.yaml` has been accepted into
`conda-forge/staged-recipes`.

## Reporting issues

Please include the command run and the full error output. If the issue is
about specific material values, file it against `mat-data` instead.
