# Contributing

## Adding or updating a material (data-only change)

1. Copy `packages/mat-data-handler-data/src/mat_data_handler_data/entries/template.yaml.example`
   to `entries/<stable-material-key>.yaml` (lowercase letters, digits, underscores).
2. Fill in measured/calibrated values, following
   `packages/mat-data-handler-data/src/mat_data_handler_data/schemas/material.schema.json`.
3. Open a pull request. CI will:
   - validate the entry against the JSON Schema,
   - rebuild the combined database and confirm it is reproducible,
   - run the export tests against the new entry if it targets `ICAMS CP-UMAT`.
4. A maintainer reviews the physical plausibility of the values (schema
   validity alone does not guarantee a physically correct material) and
   merges.

Data-only PRs are released independently as a new `mat-data-handler-data`
version (CalVer, e.g. `2026.10.0`) without requiring a `mat-data-handler` code
release.

## Changing the API or export logic (code change)

1. Make changes under `packages/mat-data-handler/src/mat_data_handler/`.
2. Add/update tests under `packages/mat-data-handler/tests/`.
3. Follow SemVer for `mat-data-handler`: patch for bug fixes, minor for
   backward-compatible additions, major for breaking changes to the public
   API (`build_database`, `export_material`, CLI flags).
4. Update `CHANGELOG.md`.

## Running tests locally

```bash
cd packages/mat-data-handler-data && pip install -e .
cd ../mat-data-handler && pip install -e ".[test]"
pytest
```

## Release process

- Tag `data-vYYYY.M.P` triggers `.github/workflows/release-data.yml`, building
  and publishing `mat-data-handler-data` to PyPI via Trusted Publishing.
- Tag `core-vX.Y.Z` triggers `.github/workflows/release-core.yml` for
  `mat-data-handler`.
- conda-forge feedstocks track the PyPI releases automatically once
  `staged-recipes` submissions (see `conda-recipes/*/meta.yaml` as a starting
  point) have been accepted for both packages.

## Reporting issues

Please include the material key (if applicable), the command run, and the
full error output.
