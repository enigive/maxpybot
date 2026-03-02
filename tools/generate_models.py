#!/usr/bin/env python3
from __future__ import annotations

import argparse
import keyword
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import yaml


DEFAULT_SCHEMA_PATH = Path("vendor/max_bot_api/schema.yaml")
DEFAULT_MODELS_OUTPUT = Path("maxpybot/types/generated/models.py")
DEFAULT_META_OUTPUT = Path("maxpybot/types/generated/openapi_meta.py")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate pydantic models from MAX OpenAPI schema")
    parser.add_argument("--schema", default=str(DEFAULT_SCHEMA_PATH))
    parser.add_argument("--models-output", default=str(DEFAULT_MODELS_OUTPUT))
    parser.add_argument("--meta-output", default=str(DEFAULT_META_OUTPUT))
    return parser.parse_args()


def load_schema(path: Path) -> Dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def ref_name(ref: str) -> str:
    return ref.rsplit("/", 1)[-1]


def sanitize_identifier(name: str, fallback_prefix: str = "field") -> str:
    normalized = re.sub(r"[^a-zA-Z0-9_]", "_", name)
    if not normalized:
        normalized = fallback_prefix
    if normalized[0].isdigit():
        normalized = "{0}_{1}".format(fallback_prefix, normalized)
    if keyword.iskeyword(normalized):
        normalized = normalized + "_"
    return normalized


def sanitize_enum_member(value: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9_]", "_", value).upper()
    normalized = re.sub(r"_+", "_", normalized).strip("_")
    if not normalized:
        normalized = "VALUE"
    if normalized[0].isdigit():
        normalized = "VALUE_{0}".format(normalized)
    if keyword.iskeyword(normalized.lower()):
        normalized = normalized + "_VALUE"
    return normalized


def infer_type(schema: Dict[str, Any]) -> str:
    if "$ref" in schema:
        return ref_name(str(schema["$ref"]))
    if "enum" in schema:
        return "str"
    schema_type = schema.get("type")
    if schema_type == "integer":
        return "int"
    if schema_type == "number":
        return "float"
    if schema_type == "boolean":
        return "bool"
    if schema_type == "string":
        return "str"
    if schema_type == "array":
        items = schema.get("items", {})
        return "List[{0}]".format(infer_type(items if isinstance(items, dict) else {}))
    if schema_type == "object":
        return "Dict[str, Any]"
    if "oneOf" in schema or "anyOf" in schema or "allOf" in schema:
        return "Any"
    return "Any"


def collect_object_definition(
    schema_name: str,
    schema: Dict[str, Any],
    all_schemas: Dict[str, Dict[str, Any]],
    seen: Optional[Set[str]] = None,
) -> Tuple[Dict[str, Dict[str, Any]], Set[str]]:
    if seen is None:
        seen = set()
    if schema_name in seen:
        return {}, set()
    seen.add(schema_name)

    properties: Dict[str, Dict[str, Any]] = {}
    required: Set[str] = set()

    own_properties = schema.get("properties", {})
    if isinstance(own_properties, dict):
        for prop_name, prop_schema in own_properties.items():
            if isinstance(prop_schema, dict):
                properties[prop_name] = prop_schema

    own_required = schema.get("required", [])
    if isinstance(own_required, list):
        required.update([str(name) for name in own_required])

    all_of = schema.get("allOf", [])
    if isinstance(all_of, list):
        for sub_schema in all_of:
            if not isinstance(sub_schema, dict):
                continue
            if "$ref" in sub_schema:
                name = ref_name(str(sub_schema["$ref"]))
                ref_schema = all_schemas.get(name, {})
                nested_properties, nested_required = collect_object_definition(
                    name,
                    ref_schema,
                    all_schemas,
                    seen=seen,
                )
                properties.update(nested_properties)
                required.update(nested_required)
                continue

            sub_properties = sub_schema.get("properties", {})
            if isinstance(sub_properties, dict):
                for prop_name, prop_schema in sub_properties.items():
                    if isinstance(prop_schema, dict):
                        properties[prop_name] = prop_schema
            sub_required = sub_schema.get("required", [])
            if isinstance(sub_required, list):
                required.update([str(name) for name in sub_required])

    return properties, required


def generate_model_file(schema: Dict[str, Any], output_path: Path) -> None:
    schemas = schema.get("components", {}).get("schemas", {})
    if not isinstance(schemas, dict):
        raise RuntimeError("components.schemas is missing in schema")

    lines: List[str] = []
    lines.append("from __future__ import annotations")
    lines.append("")
    lines.append("from enum import Enum")
    lines.append("from typing import Any, Dict, List, Optional")
    lines.append("")
    lines.append("from pydantic import Field")
    lines.append("")
    lines.append("from ..base import MaxBaseModel")
    lines.append("")
    lines.append("")
    lines.append("# This file is auto-generated by tools/generate_models.py.")
    lines.append("# Do not edit manually.")
    lines.append("")

    for schema_name in sorted(schemas.keys()):
        raw_schema = schemas[schema_name]
        if not isinstance(raw_schema, dict):
            continue

        if "enum" in raw_schema and isinstance(raw_schema["enum"], list):
            lines.extend(_emit_enum_model(schema_name, raw_schema["enum"]))
            lines.append("")
            continue

        lines.extend(_emit_object_model(schema_name, raw_schema, schemas))
        lines.append("")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def _emit_enum_model(schema_name: str, enum_values: List[Any]) -> List[str]:
    lines: List[str] = []
    lines.append("class {0}(str, Enum):".format(schema_name))
    used_names: Set[str] = set()
    if not enum_values:
        lines.append('    EMPTY = ""')
        return lines

    for value in enum_values:
        raw_value = str(value)
        member_name = sanitize_enum_member(raw_value)
        if member_name in used_names:
            suffix = 2
            candidate = "{0}_{1}".format(member_name, suffix)
            while candidate in used_names:
                suffix += 1
                candidate = "{0}_{1}".format(member_name, suffix)
            member_name = candidate
        used_names.add(member_name)
        lines.append("    {0} = {1!r}".format(member_name, raw_value))
    return lines


def _emit_object_model(
    schema_name: str,
    schema: Dict[str, Any],
    all_schemas: Dict[str, Dict[str, Any]],
) -> List[str]:
    lines: List[str] = []
    lines.append("class {0}(MaxBaseModel):".format(schema_name))

    properties, required = collect_object_definition(schema_name, schema, all_schemas)
    if not properties:
        lines.append("    pass")
        return lines

    used_field_names: Set[str] = set()
    for prop_name in sorted(properties.keys()):
        prop_schema = properties[prop_name]
        field_name = sanitize_identifier(prop_name)
        if field_name in used_field_names:
            suffix = 2
            candidate = "{0}_{1}".format(field_name, suffix)
            while candidate in used_field_names:
                suffix += 1
                candidate = "{0}_{1}".format(field_name, suffix)
            field_name = candidate
        used_field_names.add(field_name)

        type_hint = infer_type(prop_schema)
        is_required = prop_name in required
        annotation = type_hint if is_required else "Optional[{0}]".format(type_hint)
        default_value = "..." if is_required else "None"

        if field_name != prop_name:
            lines.append(
                "    {0}: {1} = Field({2}, alias={3!r})".format(
                    field_name,
                    annotation,
                    default_value,
                    prop_name,
                )
            )
        else:
            lines.append("    {0}: {1} = {2}".format(field_name, annotation, default_value))
    return lines


def generate_openapi_meta(schema: Dict[str, Any], output_path: Path) -> None:
    paths = schema.get("paths", {})
    if not isinstance(paths, dict):
        raise RuntimeError("paths is missing in schema")

    operations: List[Tuple[str, str, str]] = []
    for raw_path, path_item in paths.items():
        if not isinstance(path_item, dict):
            continue
        for method in ("get", "post", "put", "patch", "delete"):
            operation = path_item.get(method)
            if not isinstance(operation, dict):
                continue
            operation_id = operation.get("operationId")
            if not operation_id:
                continue
            operations.append((str(operation_id), method.upper(), str(raw_path)))

    operations.sort(key=lambda item: item[0])

    lines: List[str] = []
    lines.append("from __future__ import annotations")
    lines.append("")
    lines.append("from typing import Dict, List")
    lines.append("")
    lines.append("")
    lines.append("# This file is auto-generated by tools/generate_models.py.")
    lines.append("# Do not edit manually.")
    lines.append("")
    lines.append("OPERATION_IDS: List[str] = [")
    for operation_id, _, _ in operations:
        lines.append("    {0!r},".format(operation_id))
    lines.append("]")
    lines.append("")
    lines.append("OPERATION_DEFINITIONS: Dict[str, Dict[str, str]] = {")
    for operation_id, method, path in operations:
        lines.append(
            "    {0!r}: {{'method': {1!r}, 'path': {2!r}}},".format(
                operation_id,
                method,
                path,
            )
        )
    lines.append("}")
    lines.append("")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    schema_path = Path(args.schema)
    models_output = Path(args.models_output)
    meta_output = Path(args.meta_output)

    schema = load_schema(schema_path)
    generate_model_file(schema, models_output)
    generate_openapi_meta(schema, meta_output)
    print("Generated models: {0}".format(models_output))
    print("Generated meta: {0}".format(meta_output))


if __name__ == "__main__":
    main()
