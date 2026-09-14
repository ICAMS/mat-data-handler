# mat-data-handler-data

Validated crystal-plasticity material parameter sets: individual YAML entries
under `entries/`, JSON schemas under `schemas/`, and the Abaqus `PROPS`
mapping table `mapping.csv`. This package ships **data only** — no validation
or export logic; see the `mat-data-handler` package for that.

## Adding a material

Copy `entries/template.yaml.example` to `entries/<stable-material-key>.yaml`,
e.g. `entries/austenite_316l_room_temperature.yaml`. Use lowercase letters,
digits, and underscores for stable keys. Each file contains one material
object without an outer database key. Use descriptive keys to distinguish
calibrations of the same alloy. Replace the example values and reference with
measured or calibrated data, including the conditions under which they apply.

Use spaces for indentation, string keys, unquoted numeric values, and quoted
text identifiers. Put machine-readable units and provenance in fields;
comments are for author guidance. Avoid duplicate keys, custom YAML tags, and
aliases. Do not store grain-specific Euler angles in the material database.

## Accessing the data at runtime

```python
from mat_data_handler_data import entries_dir, schemas_dir, mapping_path

with entries_dir() as entries:
    print(sorted(p.name for p in entries.glob("*.yaml")))
```

`entries_dir()`, `schemas_dir()`, and `mapping_path()` return context managers
that yield real filesystem paths, working correctly whether the package was
installed from a wheel, sdist, or conda package.

## Versioning

This package uses CalVer (`YYYY.M.P`) since it tracks a growing dataset rather
than an API. See [CHANGELOG.md](CHANGELOG.md).
