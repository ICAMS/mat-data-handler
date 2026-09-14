"""Validate individual materials offline and atomically build a collection.

Ported from the ``cp-work`` proof of concept (materials/build_database.py),
adapted to load default data from the installable ``mat-data-handler-data``
package instead of a fixed repo-relative ``ROOT``.
"""

from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
import re
import sys
import tempfile

import yaml
from jsonschema import Draft201909Validator
from referencing import Registry, Resource

PLASTIC_MODELS = ("ICAMS CP-UMAT", "DAMASK phenopowerlaw")


class EntryLoader(yaml.SafeLoader):
    def compose_node(self, parent, index):
        if self.check_event(yaml.AliasEvent):
            raise ValueError("YAML aliases are not allowed")
        return super().compose_node(parent, index)

    def construct_mapping(self, node, deep=False):
        result = {}
        for key_node, value_node in node.value:
            key = self.construct_object(key_node, deep=deep)
            if not isinstance(key, str):
                raise ValueError(f"line {key_node.start_mark.line + 1}: mapping keys must be strings")
            if key in result:
                raise ValueError(f"line {key_node.start_mark.line + 1}: duplicate key {key!r}")
            result[key] = self.construct_object(value_node, deep=deep)
        return result


def json_errors(value, path="$"):
    """Reject YAML-only values and non-finite numbers before schema validation."""
    if isinstance(value, dict):
        for key, child in value.items():
            yield from json_errors(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from json_errors(child, f"{path}[{index}]")
    elif isinstance(value, float) and not math.isfinite(value):
        yield f"{path}: number must be finite"
    elif value is not None and type(value) not in (str, int, float, bool):
        yield f"{path}: unsupported YAML value ({type(value).__name__}); quote text identifiers"


def validator(schema_dir: Path) -> Draft201909Validator:
    resources = []
    for path in sorted(Path(schema_dir).glob("*.json")):
        schema = json.loads(path.read_text(encoding="utf-8"))
        Draft201909Validator.check_schema(schema)
        resources.append((path.resolve().as_uri(), Resource.from_contents(schema)))
    # Registry has no retrieval callback: unresolved references cannot use the network.
    registry = Registry().with_resources(resources)
    uri = (Path(schema_dir) / "material.schema.json").resolve().as_uri()
    return Draft201909Validator({"$ref": uri}, registry=registry)


def schema_messages(error):
    if error.validator == "oneOf" and error.context:
        # Select only diagnostics from the named model's branch. Validation
        # still runs against the complete schema, including shared constraints.
        if isinstance(error.instance, dict):
            model = error.instance.get("plastic_model_name")
            matching = [
                index for index, branch in enumerate(error.validator_value)
                if branch.get("properties", {}).get("plastic_model_name", {}).get("const") == model
                and model in PLASTIC_MODELS
            ]
            if len(matching) == 1:
                for child in error.context:
                    if child.schema_path and child.schema_path[0] == matching[0]:
                        yield from schema_messages(child)
                return
        yield f"{error.json_path}: does not match an allowed schema alternative"
        for child in error.context:
            yield from schema_messages(child)
    else:
        yield f"{error.json_path}: {error.message}"


def collect(entries: Path, schemas: Path):
    """Validate every YAML entry in ``entries`` against ``schemas``.

    Returns ``(database, errors)``. ``database`` maps material key (filename
    stem) to the parsed entry; ``errors`` lists human-readable problems.
    """
    entries, schemas = Path(entries), Path(schemas)
    check = validator(schemas)
    files = sorted(p for p in entries.iterdir() if p.is_file() and p.suffix in (".yaml", ".yml"))
    if not files:
        raise ValueError(f"{entries}: no YAML entries found")
    database, errors = {}, []
    for path in files:
        if not re.fullmatch(r"[a-z0-9_]+", path.stem):
            errors.append(f"{path}: filename stem must contain lowercase letters, digits, or underscores")
            continue
        if path.stem in database:
            errors.append(f"{path}: duplicate material key {path.stem!r}")
            continue
        try:
            entry = yaml.load(path.read_text(encoding="utf-8"), Loader=EntryLoader)
            problems = list(json_errors(entry))
            if not problems and isinstance(entry, dict):
                model_object = entry.get("constitutive_model", {})
                if isinstance(model_object, dict):
                    model = model_object.get("plastic_model_name")
                    if model not in PLASTIC_MODELS:
                        problems = [
                            "$.constitutive_model.plastic_model_name: "
                            f"missing or unsupported plastic model name {model!r}; "
                            f"expected one of {PLASTIC_MODELS!r}"
                        ]
            if not problems:
                problems = [
                    message
                    for error in check.iter_errors(entry)
                    for message in schema_messages(error)
                ]
            errors.extend(f"{path}: {problem}" for problem in problems)
            database[path.stem] = entry
        except (ValueError, yaml.YAMLError) as error:
            errors.append(f"{path}: {error}")
    return database, errors


def validate_only(entries: Path, schemas: Path) -> int:
    """Validate entries and return the count of valid materials, raising on error."""
    database, errors = collect(entries, schemas)
    if errors:
        raise ValueError("\n".join(errors))
    return len(database)


def build_database(entries: Path, schemas: Path, output_format: str = "yaml") -> str:
    """Validate entries and return the serialized combined database as text."""
    database, errors = collect(entries, schemas)
    if errors:
        raise ValueError("\n".join(errors))
    if output_format == "json":
        return json.dumps(database, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n"
    return yaml.safe_dump(database, sort_keys=True, allow_unicode=True)


def _default_data_paths():
    from mat_data_handler_data import entries_dir, schemas_dir

    return entries_dir(), schemas_dir()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--entries", type=Path, help="Defaults to the bundled mat-data-handler-data entries/")
    parser.add_argument("--schemas", type=Path, help="Defaults to the bundled mat-data-handler-data schemas/")
    parser.add_argument("--output", "-o", type=Path, required=True, help="Destination (.yaml/.yml or .json)")
    parser.add_argument("--format", choices=("yaml", "json"), help="Defaults to output extension, or YAML")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="Fail if the output is missing or stale; write nothing")
    mode.add_argument("--validate-only", action="store_true", help="Validate entries without building")
    args = parser.parse_args(argv)
    try:
        from contextlib import ExitStack

        with ExitStack() as stack:
            if args.entries is None or args.schemas is None:
                default_entries_cm, default_schemas_cm = _default_data_paths()
                entries = args.entries or stack.enter_context(default_entries_cm)
                schemas = args.schemas or stack.enter_context(default_schemas_cm)
            else:
                entries, schemas = args.entries, args.schemas

            output = args.output
            output_format = args.format or ("json" if output.suffix == ".json" else "yaml")
            if output.resolve().parent in (Path(entries).resolve(), Path(schemas).resolve()):
                raise ValueError("Output must be outside the entries and schemas directories")

            if args.validate_only:
                count = validate_only(entries, schemas)
                print(f"Validated {count} materials")
                return 0

            content = build_database(entries, schemas, output_format)
            data = content.encode("utf-8")
            if args.check:
                if not output.is_file() or output.read_bytes() != data:
                    print(f"{output}: missing or stale; rebuild without --check", file=sys.stderr)
                    return 1
                print(f"{output}: up to date")
                return 0
            output.parent.mkdir(parents=True, exist_ok=True)
            temporary = None
            try:
                with tempfile.NamedTemporaryFile(dir=output.parent, delete=False) as stream:
                    temporary = Path(stream.name)
                    stream.write(data)
                    stream.flush()
                    os.fsync(stream.fileno())
                temporary.replace(output)
            finally:
                if temporary is not None:
                    temporary.unlink(missing_ok=True)
            print(f"Wrote database to {output}")
            return 0
    except Exception as error:
        print(f"Build failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
