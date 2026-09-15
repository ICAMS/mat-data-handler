# mat-data-handler – Organizing Material Data for Crystal Plasticity

Plain Python package to validate, combine, and export crystal-plasticity material parameter sets. The material data itself (YAML
entries, JSON schemas, PROPS mapping table) is retrieved from the
[mat-data](https://github.com/ICAMS/mat-data) repository and fetched over
the network (and cached locally) at runtime.  
Currently only support for the crystal plasticity model [ICAMS CP-UMAT](https://github.com/ICAMS/Crystal_Plasticity_UMAT.git) is provided. Use the `mat_extract_params` command to extract the require .inc files that contains the values for PROPS[9:] read by the ICAMS CP-UMAT.


## Installation

```bash
pip install mat-data-handler
```

First use of the CLI/API fetches the pinned `mat-data` ref (default: `main`)
and caches it under `~/.cache/mat-data-handler`. For offline use or local
development against a sibling checkout, set:

```bash
export MAT_DATA_LOCAL_PATH=/path/to/mat-data   # skips network access entirely
```

Other environment variables: `MAT_DATA_REPO` (default `ICAMS/mat-data`),
`MAT_DATA_REF` (default `main`; pin to a release tag for reproducibility),
`MAT_DATA_FETCH_METHOD` (`http` default, stdlib-only tarball download; or
`git`, which shells out to the `git` binary), `MAT_DATA_CACHE_DIR`.

## API

- `mat_data_handler.data_source.{entries_dir, schemas_dir, mapping_path}()` —
  resolve (fetching/caching as needed) local paths to the `mat-data` content.
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
mat-build-database --output build/materials.yaml  # generate combined database
mat-extract-params copper_generic --outdir build/includes
mat-extract-params all --outdir build/includes
```

Both commands default to fetching data from `mat-data`; pass
`--entries`/`--schemas`/`--mapping-file` to point at a different data source
(e.g. a local checkout) directly.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). For adding/updating material data,
see [mat-data](https://github.com/ICAMS/mat-data) instead — this repo has no
data to edit.

## Development

```bash
pip install -e ".[test]"
export MAT_DATA_LOCAL_PATH=../mat-data   # or wherever your mat-data checkout lives
pytest
```

## License

MIT — see [LICENSE](LICENSE). (Material data in `mat-data` is licensed
separately, under CC-BY-4.0.)
