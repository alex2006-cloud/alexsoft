"""Contract parity: the implementation must expose what artifacts/api/rag.openapi.yaml promises."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from alexsoft_rag.config import Settings
from alexsoft_rag.main import create_app
from alexsoft_rag.services import build_services

SPEC_PATH = Path(__file__).resolve().parents[3] / "artifacts" / "api" / "rag.openapi.yaml"
HTTP_METHODS = {"get", "post", "put", "patch", "delete"}


@pytest.fixture(scope="module")
def spec() -> dict:
    return yaml.safe_load(SPEC_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def impl() -> dict:
    # openapi() does not run lifespan, so no running services are needed here
    return create_app(build_services(Settings(rag_api_key="x"))).openapi()


def _flatten(schema: dict, components: dict) -> tuple[set[str], set[str]]:
    props: set[str] = set(schema.get("properties", {}))
    required: set[str] = set(schema.get("required", []))
    for part in schema.get("allOf", []):
        if "$ref" in part:
            part = components[part["$ref"].rsplit("/", 1)[-1]]
        p, r = _flatten(part, components)
        props |= p
        required |= r
    return props, required


def test_every_contract_operation_is_implemented(spec, impl):
    missing, wrong_id = [], []
    for path, item in spec["paths"].items():
        for method, op in item.items():
            if method not in HTTP_METHODS:
                continue
            impl_op = impl["paths"].get(path, {}).get(method)
            if impl_op is None:
                missing.append(f"{method.upper()} {path}")
            elif impl_op.get("operationId") != op["operationId"]:
                wrong_id.append(f"{method.upper()} {path}: {impl_op.get('operationId')} != {op['operationId']}")
    assert not missing, f"not implemented: {missing}"
    assert not wrong_id, f"operationId mismatch: {wrong_id}"


def test_implementation_has_no_undocumented_operations(spec, impl):
    documented = {(p, m) for p, item in spec["paths"].items() for m in item if m in HTTP_METHODS}
    extra = [
        f"{m.upper()} {p}"
        for p, item in impl["paths"].items()
        for m in item
        if m in HTTP_METHODS and (p, m) not in documented
    ]
    assert not extra, f"endpoints missing from the contract (contract-first!): {extra}"


@pytest.mark.parametrize(
    "name",
    [
        "Health", "CollectionCreate", "Collection", "CollectionPage", "ChunkingConfig",
        "Document", "DocumentPage", "DocumentIngest", "InlineSource", "MinioSource",
        "Job", "Chunk", "SearchResponse", "QueryRequest", "QueryResponse", "Citation", "Usage", "Timings",
        "SearchRequest", "Locator",
    ],
)
def test_schema_properties_match_contract(name, spec, impl):
    spec_components = spec["components"]["schemas"]
    impl_components = impl["components"]["schemas"]
    spec_props, spec_required = _flatten(spec_components[name], spec_components)
    impl_name = name if name in impl_components else None
    if impl_name is None:  # FastAPI suffixes request/response variants (e.g. Collection-Output)
        impl_name = next(k for k in impl_components if k.startswith(name))
    impl_props, impl_required = _flatten(impl_components[impl_name], impl_components)
    assert spec_props == impl_props, f"{name}: contract {sorted(spec_props)} vs impl {sorted(impl_props)}"
    assert spec_required <= impl_required | impl_props, f"{name}: required fields missing"


def test_security_scheme_is_api_key_header(spec):
    assert spec["components"]["securitySchemes"]["apiKey"] == {
        "type": "apiKey",
        "in": "header",
        "name": "X-API-Key",
        "description": spec["components"]["securitySchemes"]["apiKey"]["description"],
    }
