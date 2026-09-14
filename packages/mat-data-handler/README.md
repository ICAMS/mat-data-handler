# mat-data-handler

Validate, combine, and export crystal-plasticity material parameter sets for
Abaqus UMATs. This package contains the stable Python API and CLI; the
underlying validated material data lives in the separate
[`mat-data-handler-data`](../mat-data-handler-data) package (a runtime
dependency, installed automatically).

## API

- `mat_data_handler.database.build_database(entries, schemas, output_format="yaml")`
  — validate all entries and return the combined database as text.
- `mat_data_handler.database.validate_only(entries, schemas)` — validate only,
  returns the number of valid materials.
- `mat_data_handler.extract.export_entry(entry, mapping, schemas)` — export
  one loaded material entry to Abaqus `PROPS` records.
- `mat_data_handler.extract.load_document(path)` / `parse_mapping(path)` —
  helpers to load a YAML/JSON entry or the `mapping.csv` table.

## CLI

```bash
mat-build-database --output build/materials.yaml --check
mat-extract-params copper --outdir build/includes
mat-extract-params all --outdir build/includes
```

Both commands default to the data bundled in `mat-data-handler-data`; pass
`--entries`/`--schemas`/`--mapping-file` to point at a different data source.

## Development

```bash
pip install -e ../mat-data-handler-data
pip install -e ".[test]"
pytest
```
