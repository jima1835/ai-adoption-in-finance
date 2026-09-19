#!/usr/bin/env python3
"""Validate every public data file against its schema in schemas/.

Run:  python3 tools/validate_data.py        → exit 0 if everything validates

Why a hand-rolled validator instead of `jsonschema`: this repo ships with two
runtime dependencies on purpose, and the schemas here use a small, deliberate
subset of JSON Schema 2020-12. The subset is enumerated in SUPPORTED below and
anything outside it is a hard ERROR rather than a silent pass — a schema that
quietly validates nothing is worse than no schema at all, because it reads like
a guarantee.

Known: data/institutions.json currently reports one error (an undocumented key
on the GIC row). That is real, is tracked as a strict xfail in
tests/test_schemas.py, and leaves with the next data release. The validator has
no allowlist: exceptions live in the test suite, where they are visible.
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCHEMAS = ROOT / "schemas"
DATA = ROOT / "data"

# The JSON Schema keywords this validator implements. A schema using anything
# else raises rather than passing unchecked.
SUPPORTED = {
    "$schema", "$id", "title", "description",
    "type", "properties", "required", "additionalProperties",
    "items", "enum", "pattern", "minLength", "minItems",
}

TYPES = {
    "object": dict,
    "array": list,
    "string": str,
    "boolean": bool,
    "integer": int,
    "number": (int, float),
    "null": type(None),
}

# path -> (schema file, "json" | "jsonl"). A .jsonl file's schema describes ONE
# record; every line is validated against it.
FILES = [
    ("institutions.json", "institution.schema.json", "json"),
    ("not_classified.json", "not_classified.schema.json", "json"),
    ("roles_expansion.json", "roles_expansion.schema.json", "json"),
    ("excluded.json", "excluded.schema.json", "json"),
    ("roles.jsonl", "role_event.schema.json", "jsonl"),
    ("roles_not_found.jsonl", "roles_not_found.schema.json", "jsonl"),
]


class SchemaUnsupported(Exception):
    """A schema used a keyword this validator does not implement."""


def validate(value, schema, where="$"):
    """Return a list of human-readable error strings. Empty means valid."""
    unknown = set(schema) - SUPPORTED
    if unknown:
        raise SchemaUnsupported(f"{where}: schema uses unimplemented {sorted(unknown)}")

    errors = []
    expected = schema.get("type")
    if expected is not None:
        names = [expected] if isinstance(expected, str) else list(expected)
        # bool is a subclass of int in Python; JSON Schema treats them apart.
        ok = any(
            isinstance(value, TYPES[n]) and not (n != "boolean" and isinstance(value, bool))
            for n in names
        )
        if not ok:
            return [f"{where}: expected {'/'.join(names)}, got {type(value).__name__}"]

    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{where}: {value!r} not in {schema['enum']}")

    if isinstance(value, str):
        if "pattern" in schema and not re.search(schema["pattern"], value):
            errors.append(f"{where}: {value!r} does not match {schema['pattern']}")
        if "minLength" in schema and len(value) < schema["minLength"]:
            errors.append(f"{where}: shorter than minLength {schema['minLength']}")

    if isinstance(value, list):
        if "minItems" in schema and len(value) < schema["minItems"]:
            errors.append(f"{where}: fewer than minItems {schema['minItems']}")
        if "items" in schema:
            for i, item in enumerate(value):
                errors += validate(item, schema["items"], f"{where}[{i}]")

    if isinstance(value, dict):
        props = schema.get("properties", {})
        for key in schema.get("required", []):
            if key not in value:
                errors.append(f"{where}: missing required {key!r}")
        if schema.get("additionalProperties") is False:
            for key in set(value) - set(props):
                errors.append(f"{where}: undocumented key {key!r}")
        for key, sub in props.items():
            if key in value:
                errors += validate(value[key], sub, f"{where}.{key}")

    return errors


def _load_schema(name):
    return json.loads((SCHEMAS / name).read_text(encoding="utf-8"))


def validate_file(data_name, schema_name, kind):
    """Errors for one data file, each prefixed with the file name."""
    path = DATA / data_name
    if not path.exists():
        return [f"{data_name}: missing"]
    schema = _load_schema(schema_name)
    text = path.read_text(encoding="utf-8")

    if kind == "jsonl":
        errors = []
        for lineno, line in enumerate(text.splitlines(), 1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as e:
                errors.append(f"{data_name}:{lineno}: unparseable ({e})")
                continue
            errors += [f"{data_name}:{lineno} {e}" for e in validate(record, schema)]
        return errors

    try:
        value = json.loads(text)
    except json.JSONDecodeError as e:
        return [f"{data_name}: unparseable ({e})"]
    return [f"{data_name} {e}" for e in validate(value, schema)]


def main():
    failures = 0
    for data_name, schema_name, kind in FILES:
        errors = validate_file(data_name, schema_name, kind)
        status = "ok" if not errors else f"{len(errors)} error(s)"
        print(f"{data_name:<24} {status}")
        for e in errors:
            print(f"  - {e}")
        failures += len(errors)
    print("—" * 40)
    print("all files valid" if not failures else f"{failures} error(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
