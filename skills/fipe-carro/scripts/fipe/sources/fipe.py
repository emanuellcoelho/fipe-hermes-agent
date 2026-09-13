"""The canonical FIPE table, via the public parallelum.com.br mirror.

marcas -> modelos -> anos -> valor. One GET per step; the mirror serves the
reference table with the current month, and the value carries its month so a
stale read is never presented as fresh."""

from __future__ import annotations

import json
from urllib.parse import quote
from typing import Any

from kit import http

from fipe.models import FipeValue, VehicleKind, parse_brl

BASE = "https://parallelum.com.br/fipe/api/v1"


def _get(path: str) -> Any:
    status, body = http.fetch(f"{BASE}/{path}", timeout_s=15)
    if status != 200:
        raise http.HttpError(f"FIPE respondeu HTTP {status}")
    return json.loads(body.decode("utf-8"))


def marcas(kind: VehicleKind) -> list[dict[str, str]]:
    return _get(f"{kind.value}/marcas")


def modelos(kind: VehicleKind, marca_codigo: str) -> list[dict[str, Any]]:
    data = _get(f"{kind.value}/marcas/{marca_codigo}/modelos")
    return data.get("modelos", []) if isinstance(data, dict) else data


def anos(kind: VehicleKind, marca_codigo: str, modelo_codigo: str) -> list[dict[str, str]]:
    return _get(f"{kind.value}/marcas/{marca_codigo}/modelos/{modelo_codigo}/anos")


def valor(kind: VehicleKind, marca_codigo: str, modelo_codigo: str, ano_codigo: str) -> FipeValue:
    data = _get(f"{kind.value}/marcas/{marca_codigo}/modelos/{modelo_codigo}/anos/{quote(ano_codigo)}")
    if "error" in data:
        raise LookupError(data["error"])
    return FipeValue(
        valor=parse_brl(str(data["Valor"])),
        marca=data["Marca"], modelo=data["Modelo"],
        ano_modelo=int(data["AnoModelo"]), combustivel=data["Combustivel"],
        codigo_fipe=data["CodigoFipe"], mes_referencia=data["MesReferencia"],
        sigla_combustivel=data.get("SiglaCombustivel", ""),
    )


def resolve_marca(kind: VehicleKind, query: str) -> dict[str, str]:
    wanted = query.strip().lower()
    for marca in marcas(kind):
        if marca["nome"].lower() == wanted:
            return marca
    matches = [m for m in marcas(kind) if wanted in m["nome"].lower()]
    if not matches:
        raise LookupError(f"não achei a marca {query!r} na tabela FIPE")
    return matches[0]


def resolve_modelo(kind: VehicleKind, marca_codigo: str, query: str) -> dict[str, Any]:
    wanted = query.strip().lower()
    all_models = modelos(kind, marca_codigo)
    exact = [m for m in all_models if m["nome"].lower() == wanted]
    if exact:
        return exact[0]
    matches = [m for m in all_models if wanted in m["nome"].lower()]
    if not matches:
        raise LookupError(f"não achei o modelo {query!r} na tabela FIPE")
    return matches[0]
