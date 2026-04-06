#!/usr/bin/env python3
"""Export OpenAPI spec as Postman collection v2.1.

Usage:
    python scripts/export_postman.py
    python scripts/export_postman.py --output docs/api/CAMIULA.postman_collection.json

Generates a Postman-importable collection from the FastAPI OpenAPI schema.
"""

import argparse
import json
import os
import sys
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

OUTPUT_DEFAULT = ROOT / "docs" / "api" / "CAMIULA.postman_collection.json"


def openapi_to_postman(spec: dict, base_url: str = "{{base_url}}") -> dict:
    """Convert OpenAPI 3.x spec to Postman Collection v2.1 format."""
    collection = {
        "info": {
            "_postman_id": str(uuid4()),
            "name": spec.get("info", {}).get("title", "API"),
            "description": spec.get("info", {}).get("description", ""),
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
        },
        "auth": {
            "type": "bearer",
            "bearer": [{"key": "token", "value": "{{access_token}}", "type": "string"}],
        },
        "variable": [
            {"key": "base_url", "value": "http://localhost:8000", "type": "string"},
            {"key": "access_token", "value": "", "type": "string"},
        ],
        "item": [],
    }

    # Group endpoints by tag
    folders = {}
    for path, methods in spec.get("paths", {}).items():
        for method, details in methods.items():
            if method in ("parameters", "servers"):
                continue
            tags = details.get("tags", ["Untagged"])
            tag = tags[0]
            if tag not in folders:
                folders[tag] = {"name": tag, "item": []}

            # Build request
            url_parts = path.strip("/").split("/")
            host = [base_url]
            path_segments = []
            for part in url_parts:
                if part.startswith("{") and part.endswith("}"):
                    path_segments.append(f":{part[1:-1]}")
                else:
                    path_segments.append(part)

            # Query params
            query_params = []
            path_vars = []
            for param in details.get("parameters", []):
                if param.get("in") == "query":
                    query_params.append({
                        "key": param["name"],
                        "value": "",
                        "description": param.get("description", ""),
                        "disabled": not param.get("required", False),
                    })
                elif param.get("in") == "path":
                    path_vars.append({
                        "key": param["name"],
                        "value": "",
                        "description": param.get("description", ""),
                    })

            request = {
                "method": method.upper(),
                "header": [],
                "url": {
                    "raw": f"{base_url}/{'/'.join(path_segments)}",
                    "host": [base_url],
                    "path": path_segments,
                    "query": query_params,
                    "variable": path_vars,
                },
            }

            # Request body
            request_body = details.get("requestBody", {})
            if request_body:
                json_content = (
                    request_body
                    .get("content", {})
                    .get("application/json", {})
                )
                if json_content:
                    schema_ref = json_content.get("schema", {})
                    request["header"].append({
                        "key": "Content-Type",
                        "value": "application/json",
                    })
                    request["body"] = {
                        "mode": "raw",
                        "raw": json.dumps(
                            _schema_to_example(schema_ref, spec),
                            indent=2,
                        ),
                        "options": {"raw": {"language": "json"}},
                    }

            item = {
                "name": details.get("summary", f"{method.upper()} {path}"),
                "request": request,
                "response": [],
            }
            folders[tag]["item"].append(item)

    collection["item"] = list(folders.values())
    return collection


def _schema_to_example(schema: dict, spec: dict) -> dict:
    """Generate example JSON from an OpenAPI schema reference."""
    if "$ref" in schema:
        ref_path = schema["$ref"].replace("#/", "").split("/")
        resolved = spec
        for part in ref_path:
            resolved = resolved.get(part, {})
        return _schema_to_example(resolved, spec)

    if schema.get("type") == "object":
        result = {}
        for prop_name, prop_schema in schema.get("properties", {}).items():
            result[prop_name] = _schema_to_example(prop_schema, spec)
        return result

    type_map = {
        "string": "string",
        "integer": 0,
        "number": 0.0,
        "boolean": False,
        "array": [],
    }
    return type_map.get(schema.get("type", "string"), "")


def main():
    parser = argparse.ArgumentParser(description="Export OpenAPI as Postman Collection")
    parser.add_argument("--output", default=str(OUTPUT_DEFAULT), help="Output file path")
    args = parser.parse_args()

    from app.main import app

    spec = app.openapi()
    collection = openapi_to_postman(spec)

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(collection, indent=2, ensure_ascii=False))

    endpoint_count = sum(len(f["item"]) for f in collection["item"])
    print(f"Postman collection exported: {output}")
    print(f"  Folders: {len(collection['item'])}")
    print(f"  Requests: {endpoint_count}")
    print(f"\nImport in Postman: File > Import > {output.name}")


if __name__ == "__main__":
    main()
