# mat-data-handler

Validate, combine, and export crystal-plasticity material parameter sets used
by Abaqus UMATs (originally developed for the ICAMS CP-UMAT). Extracted from
[cp-work](https://github.com/ICAMS/cp-work) so it can be reused standalone,
e.g. as a dependency of [Kanapy](https://github.com/ICAMS/Kanapy).

This is a plain, single Python package. The material data itself (YAML
entries, JSON schemas, PROPS mapping table) is **not** bundled or pip/conda
installed — it lives in the separate, code-free
[mat-data](https://github.com/ICAMS/mat-data) repository and is fetched over
the network (and cached locally) at runtime. See
[`src/mat_data_handler/data_source.py`](src/mat_data_handler/data_source.py).

## Why fetch data over the network instead of packaging it?

- **Different change cadence.** Material parameters are added/corrected often;
  the validation/export API is meant to stay stable. Decoupling them means new
  entries don't require a new `mat-data-handler` release, and vice versa.
- **No packaging overhead for pure data.** `mat-data` doesn't need a
  `pyproject.toml`, a Python package layout, or a PyPI/conda-forge release
  process at all — it's just YAML/JSON/CSV files and documentation, versioned
  with plain git tags.
- **Simple contribution model.** Anyone can propose a new material via a pull
  request to `mat-data` alone; no code repo involvement needed.

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
mat-build-database --output build/materials.yaml --check
mat-extract-params copper --outdir build/includes
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
