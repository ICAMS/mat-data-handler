"""Export schema-valid material entries to shared Abaqus PROPS(9:) include files.

Ported from ``cp-work``'s ``materials/extract_params.py``. Business logic for
which parameters are active and how they map to Abaqus PROPS positions is
unchanged; only default data locations moved to the ``mat-data-handler-data``
package.
"""

from __future__ import annotations

import argparse
import ast
import csv
import io
import json
import math
from pathlib import Path
import re
import sys

import yaml

from .database import EntryLoader, json_errors, schema_messages, validator

FLAG_LAYOUT = dict(zip((
    "flag_isotropic_hardening", "flag_back_stress", "flag_gradient_plasticity",
    "flag_int", "flag_super_alloy", "flag_trip", "flag_thermal",
), range(7)))
BASE = ["C11", "C12", "C44", "number_slip_systems", "reference_shear_rate",
        "stress_exponent", "initial_critical_resolved_shear_stress"]
ISO = ["saturated_slip_resistance", "reference_hardening_rate", "self_hardening",
       "cross_hardening", "hardening_exponent"]
KIN = ["nslip_kinematic_hardening", "kinematic_hardening_a1", "kinematic_hardening_b1",
       "ohno_wang_exponent", "chaboche_parameter_a2", "chaboche_parameter_b2",
       "chaboche_parameter_a3", "chaboche_parameter_b3"]
GRAD = ["flag_octree", "C_taui", "L_size", "I_gnd_iso", "I_gnd_kin", "C_unit", "B_lattice"]
THERM = ["activation_energy", "c11_tcoeff", "c12_tcoeff", "c44_tcoeff",
         "kinematic_hardening_a1_tcoeff", "crss0_coef_tcoeff"]


def load_document(path: Path):
    def unique_object(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate key: {key}")
            result[key] = value
        return result

    path = Path(path)
    text = path.read_text(encoding="utf-8")
    # JSON's exponent syntax (e.g. 1e-06) differs from PyYAML's resolver.
    value = (json.loads(text, object_pairs_hook=unique_object) if path.suffix.lower() == ".json"
             else yaml.load(text, Loader=EntryLoader))
    errors = list(json_errors(value))
    if errors:
        raise ValueError("; ".join(errors))
    return value


def parse_mapping(path: Path):
    with Path(path).open(encoding="utf-8-sig", newline="") as stream:
        rows = [{k.strip(): v.strip() for k, v in row.items()} for row in csv.DictReader(stream, delimiter=";")]
    result = {}
    for row in rows:
        key = row[next(k for k in row if k.startswith("json_key"))]
        if key in result:
            raise ValueError(f"duplicate mapping key: {key}")
        result[key] = row
    return result


def condition(expression, env, provided=False):
    expression = expression.strip()
    if expression in ("always", ""):
        return True
    if expression == "never":
        return False
    if expression == "provided":
        return provided
    node = ast.parse(expression, mode="eval")
    allowed = (ast.Expression, ast.Compare, ast.Name, ast.Load, ast.Constant,
               ast.Eq, ast.NotEq, ast.Gt, ast.GtE, ast.Lt, ast.LtE,
               ast.BoolOp, ast.And, ast.Or, ast.UnaryOp, ast.Not)
    if any(not isinstance(n, allowed) for n in ast.walk(node)):
        raise ValueError(f"unsupported mapping condition: {expression}")
    return bool(eval(compile(node, "<mapping condition>", "eval"), {"__builtins__": {}}, env))


def scalar(value, key):
    while isinstance(value, list):
        if len(value) != 1:
            raise ValueError(f"{key}: current Fortran reader supports only one family / coefficient")
        value = value[0]
    if isinstance(value, bool) or not isinstance(value, (float, int)) or not math.isfinite(value):
        raise ValueError(f"{key}: expected a finite number")
    return value


def export_entry(entry, mapping, schemas: Path):
    model = entry.get("constitutive_model", {}) if isinstance(entry, dict) else {}
    if not isinstance(model, dict) or model.get("plastic_model_name") != "ICAMS CP-UMAT":
        raise ValueError("CP-UMAT export requires plastic_model_name: ICAMS CP-UMAT")
    errors = [m for e in validator(schemas).iter_errors(entry) for m in schema_messages(e)]
    if errors:
        raise ValueError("\n".join(errors))
    plastic = model["plastic_parameters"]
    elastic = model["elastic_parameters"]
    units = model["units"]
    records, notes = [], []

    def raw(key):
        if key == "space_group_number":
            if key in plastic and plastic[key] != entry[key]:
                raise ValueError("conflicting space_group_number values")
            return entry[key]
        return elastic.get(key) if key in elastic else plastic.get(key)

    flags = {}
    packed = plastic.get("super_flag")
    if packed is not None and not 0 <= packed <= 0x7FFFFFFF:
        raise ValueError("super_flag exceeds signed 32-bit range")
    for key, pos in FLAG_LAYOUT.items():
        if key in plastic:
            flags[key] = plastic[key]
            if packed is not None and ((packed >> (4 * pos)) & 15) != flags[key]:
                raise ValueError(f"super_flag mismatch for {key}")
        elif packed is not None:
            flags[key] = (packed >> (4 * pos)) & 15
            notes.append(f"{key}: decoded from super_flag = {flags[key]}")
        else:
            flags[key] = int(mapping[key]["default_value"])
            notes.append(f"{key}: mapping default = {flags[key]}")
        maximum = 3 if key == "flag_back_stress" else 1
        if not 0 <= flags[key] <= maximum:
            raise ValueError(f"{key}: unsupported mode {flags[key]}")
    super_flag = sum(value << (4 * FLAG_LAYOUT[key]) for key, value in flags.items())
    if packed is not None and packed != super_flag:
        raise ValueError("super_flag contains unsupported spare bits")
    env = dict(zip(("iso_mode", "kin_mode", "grad_mode", "int_mode", "super_mode", "trip_mode", "thermal_mode"), flags.values()))
    if env["super_mode"]:
        raise ValueError("superalloy export unavailable: the schema/mapping do not represent all 12 values read by the UMAT")
    if env["trip_mode"] or env["int_mode"]:
        raise ValueError("TRIP/internal-stress export requires additional constitutive compatibility checks; currently unsupported")
    if scalar(plastic.get("number_slip_families", 1), "number_slip_families") != 1:
        raise ValueError("current Fortran reader supports one slip family only")
    if any(key in elastic for key in ("C33", "C66", "C13")):
        raise ValueError("current Fortran reader consumes only C11, C12, C44; additional elastic constants cannot be exported")
    for key, value in plastic.items():
        if isinstance(value, list):
            scalar(value, key)
    if env["thermal_mode"]:
        if plastic.get("temperature_polynomial_degree", 1) != 1:
            raise ValueError("current Fortran reader supports linear thermal slopes only")
        extra = [k for k in plastic if k.endswith("_tcoeff") and k not in THERM]
        if extra:
            raise ValueError(f"thermal coefficients not read by CP-UMAT: {extra}")

    def append(key, value, source, unit="-"):
        records.append(dict(props_position=9 + len(records), key=key, value=value, source=source, unit=unit))

    def mapped(key):
        row = mapping[key]
        value = raw(key)
        provided = value is not None
        if not condition(row["active_if"], env, provided):
            raise ValueError(f"mapping disables {key}, but the Fortran reader requires its slot")
        source = "entry"
        if not provided:
            if condition(row["required_if"], env, provided):
                raise ValueError(f"missing required active parameter: {key}")
            value = float(row["default_value"].replace(",", "."))
            source = "mapping default"
        value = scalar(value, key)
        if row["fortran_type"].startswith("integer"):
            if value != int(value):
                raise ValueError(f"{key}: expected integer")
            value = int(value)
        elif not row["fortran_type"].startswith("real"):
            raise ValueError(f"{key}: unsupported mapping type")
        if key in ("number_slip_systems", "nslip_kinematic_hardening") and not 1 <= value <= 60:
            raise ValueError(f"{key}: must be within current Nslp_mx=60")
        if key in ("I_gnd_iso", "I_gnd_kin") and value not in (0, 1):
            raise ValueError(f"{key}: expected 0 or 1")
        unit = row["unit"]
        if provided and unit.startswith("MPa"):
            category = "Stiffness" if key in elastic or key in ("c11_tcoeff", "c12_tcoeff", "c44_tcoeff") else "Stress"
            if units[category] == "Pa":
                value *= 1e-6
                source += " (Pa converted to MPa)"
        if source == "mapping default":
            notes.append(f"{key}: mapping default = {value} {unit}")
        append(key, value, source, unit)

    mapped("space_group_number")
    append("super_flag", super_flag, "packed flags")
    for key in BASE:
        mapped(key)
    if env["iso_mode"]:
        for key in ISO:
            mapped(key)
    if env["kin_mode"]:
        for key in KIN:
            mapped(key)
    if env["grad_mode"]:
        for key in GRAD:
            mapped(key)
        # Not yet in mapping/schema; retain the explicit reader initialization.
        append("CD_smooth", 3e-15, "src/mod_material.f default")
        notes.append("CD_smooth: reader default = 3e-15 (not configurable in current schema/mapping)")
    if env["thermal_mode"]:
        for key in THERM:
            mapped(key)
    return records, notes


def render_outputs(name, entry, records, notes, source):
    values = [str(r["value"]) if isinstance(r["value"], int) else format(r["value"], ".17g") for r in records]
    inc_name = f"{name}_inp_{len(values)}p.inc"
    lines = [", ".join(values[i:i + 8]) + ("," if i + 8 < len(values) else "") for i in range(0, len(values), 8)]
    stream = io.StringIO()
    writer = csv.DictWriter(stream, fieldnames=list(records[0]))
    writer.writeheader()
    writer.writerows(records)
    manifest = [f"Source: {source}", f"Include: {inc_name}", f"Include count: {len(values)}",
                f"Total Abaqus constant count: {len(values) + 8}",
                "PROPS(1:8) supplied by caller: material selector, three Euler angles (rad), four spare values.",
                "", "Abaqus usage (replace Euler angles for each grain):",
                f"*User Material, constants={len(values) + 8}",
                f'{entry["material_id"]}, 0., 0., 0., 0., 0., 0., 0.,',
                f"*Include, input={inc_name}", "", "Positions:"]
    manifest += [f'PROPS({r["props_position"]}): {r["key"]} = {r["value"]} [{r["unit"]}] ({r["source"]})' for r in records]
    manifest += ["", "Defaults and notes:", *notes]
    return {inc_name: "\n".join(lines) + "\n", f"{name}_props_flat.csv": stream.getvalue(),
            f"{name}_props_manifest.txt": "\n".join(manifest) + "\n"}


def export_material(name: str, entry, mapping, schemas: Path):
    """Export one already-loaded material entry. Returns ``(records, notes)``."""
    return export_entry(entry, mapping, schemas)


def _default_data_paths():
    from mat_data_handler_data import entries_dir, schemas_dir, mapping_path

    return entries_dir(), schemas_dir(), mapping_path()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("material", help="Material key or 'all'")
    parser.add_argument("--input", "--yaml_file", "--json_file", dest="input", type=Path,
                         help="Entry directory, single entry, or combined YAML/JSON database; "
                              "defaults to the bundled mat-data-handler-data entries/")
    parser.add_argument("--mapping-file", "--mapping_file", dest="mapping_file", type=Path,
                         help="Defaults to the bundled mat-data-handler-data mapping.csv")
    parser.add_argument("--schemas", type=Path, help="Defaults to the bundled mat-data-handler-data schemas/")
    parser.add_argument("--outdir", type=Path, default=Path("."))
    parser.add_argument("--values-per-line", type=int, choices=[8], default=8)
    args = parser.parse_args(argv)
    try:
        from contextlib import ExitStack

        with ExitStack() as stack:
            if args.input is None or args.mapping_file is None or args.schemas is None:
                default_entries_cm, default_schemas_cm, default_mapping_cm = _default_data_paths()
                input_path = args.input or stack.enter_context(default_entries_cm)
                mapping_file = args.mapping_file or stack.enter_context(default_mapping_cm)
                schemas = args.schemas or stack.enter_context(default_schemas_cm)
            else:
                input_path, mapping_file, schemas = args.input, args.mapping_file, args.schemas

            mapping = parse_mapping(mapping_file)
            input_path = Path(input_path)
            if input_path.is_dir():
                files = sorted(p for p in input_path.iterdir() if p.suffix in (".yaml", ".yml") and p.is_file())
                selected = files if args.material == "all" else [p for p in files if p.stem == args.material]
                entries = {}
                for path in selected:
                    if path.stem in entries:
                        raise ValueError(f"duplicate material key: {path.stem}")
                    entries[path.stem] = load_document(path)
            else:
                data = load_document(input_path)
                if not isinstance(data, dict):
                    raise ValueError("input must be a material object or keyed database")
                entries = {input_path.stem: data} if "constitutive_model" in data else data
                if args.material != "all":
                    entries = {k: v for k, v in entries.items() if k == args.material}
            if not entries:
                raise ValueError(f"no matching materials: {args.material}")

            outputs, errors = {}, []
            for name, entry in sorted(entries.items()):
                try:
                    if not isinstance(name, str) or not re.fullmatch("[a-z0-9_]+", name):
                        raise ValueError("invalid material key")
                    records, notes = export_entry(entry, mapping, schemas)
                    outputs.update(render_outputs(name, entry, records, notes, input_path))
                except (ValueError, KeyError) as error:
                    errors.append(f"{name}: {error}")
            if errors:
                raise ValueError("\n".join(errors))

            # Validate the whole selection before touching any output files.
            args.outdir.mkdir(parents=True, exist_ok=True)
            for name, content in outputs.items():
                path = args.outdir / name
                path.write_text(content, encoding="utf-8")
                print(f"Wrote {path}")
            return 0
    except Exception as error:
        print(f"Export failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
