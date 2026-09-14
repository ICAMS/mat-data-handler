# mat-data-handler

Validate, combine, and export crystal-plasticity material parameter sets used
by Abaqus UMATs (originally developed for the ICAMS CP-UMAT). Extracted from
[cp-work](https://github.com/<org>/cp-work) so it can be reused standalone,
e.g. as a dependency of [Kanapy](https://github.com/ICAMS/Kanapy).

This repository builds **two independently versioned distributions**:

| Package | PyPI / conda-forge name | What it contains | Release cadence |
|---|---|---|---|
| [packages/mat-data-handler-data](packages/mat-data-handler-data) | `mat-data-handler-data` | Validated YAML material entries, JSON schemas, PROPS mapping | Frequent (CalVer, e.g. `2026.9.0`) |
| [packages/mat-data-handler](packages/mat-data-handler) | `mat-data-handler` | Stable Python API/CLI: `build_database`, `export_material` | Infrequent (SemVer) |

`mat-data-handler` depends on `mat-data-handler-data` with a compatible-release
version bound, so new material entries can ship without a new code release,
and code changes don't force a data re-release.

## Why split code and data?

- **Different change cadence.** Material parameters are added/corrected often
  as new calibrations become available; the validation/export API is meant to
  stay stable. Separate distributions let each evolve at its own pace.
- **Reuse.** Other tools that only need the vetted parameter sets (not the
  export logic) can depend on `mat-data-handler-data` alone.
- **Simple contribution model.** Anyone can propose a new material via a pull
  request that adds a YAML file under
  [packages/mat-data-handler-data/src/mat_data_handler_data/entries](packages/mat-data-handler-data/src/mat_data_handler_data/entries).
  CI validates it against the JSON Schema and rebuilds the combined database
  before merge — no code changes needed.

## Installation

```bash
pip install mat-data-handler        # pulls in mat-data-handler-data automatically
# or, for the data only:
pip install mat-data-handler-data
```

(conda-forge feedstocks are set up after the first PyPI release; see
[CONTRIBUTING.md](CONTRIBUTING.md).)

## Usage

```python
from mat_data_handler_data import entries_dir, schemas_dir, mapping_path
from mat_data_handler.database import build_database
from mat_data_handler.extract import export_entry, load_document, parse_mapping

with entries_dir() as entries, schemas_dir() as schemas:
    yaml_text = build_database(entries, schemas)  # combined, validated database

with entries_dir() as entries, schemas_dir() as schemas, mapping_path() as mapping_file:
    entry = load_document(entries / "copper.yaml")
    mapping = parse_mapping(mapping_file)
    records, notes = export_entry(entry, mapping, schemas)
```

Command-line entry points (installed with `mat-data-handler`):

```bash
mat-build-database --output build/materials.yaml --check
mat-extract-params copper --outdir build/includes
```

## Adding or updating a material

See
[packages/mat-data-handler-data/README.md](packages/mat-data-handler-data/README.md).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT — see [LICENSE](LICENSE).
