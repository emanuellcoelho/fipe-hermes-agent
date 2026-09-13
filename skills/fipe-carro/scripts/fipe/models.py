"""The data model: vehicles, FIPE valuations, spec sheets, market listings
and the watch list. Serialization is explicit -- store files are contracts,
not dict dumps. Every number carries the month and source it came from, so a
price is never presented as fresher than its reference."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class VehicleKind(StrEnum):
    CARROS = "carros"
    MOTOS = "motos"


def slugify(name: str) -> str:
    """The Mobiauto URL slug: ASCII, lowercase, non-alnum -> hyphen.
    'Citroën' -> 'citroen', 'Mercedes-Benz' -> 'mercedes-benz'."""
    text = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def parse_brl(text: str) -> float:
    """'R$ 141.745,00' -> 141745.0. Tolerates spaces and the R$ prefix."""
    digits = re.sub(r"[^\d,]", "", text)
    return float(digits.replace(",", "."))


@dataclass
class FipeValue:
    """One row of the canonical FIPE table, from the parallelum mirror."""

    valor: float
    marca: str
    modelo: str
    ano_modelo: int
    combustivel: str
    codigo_fipe: str
    mes_referencia: str
    sigla_combustivel: str

    def as_dict(self) -> dict[str, Any]:
        return {"valor": self.valor, "marca": self.marca, "modelo": self.modelo,
                "ano_modelo": self.ano_modelo, "combustivel": self.combustivel,
                "codigo_fipe": self.codigo_fipe, "mes_referencia": self.mes_referencia,
                "sigla_combustivel": self.sigla_combustivel}


@dataclass
class Trim:
    """One version's full spec sheet, from the Mobiauto catalog. A version is
    the honest unit: 'Corolla XEi 2.0' has its own FIPE price, not 'Corolla'."""

    name: str
    full_name: str
    engine: str
    power_cv: int | None
    torque: float | None
    engine_size: int | None
    transmission: str
    fuel: str
    fuel2: str | None
    tank: float | None
    seats: int | None
    length_mm: int | None
    width_mm: int | None
    height_mm: int | None
    wheelbase_mm: int | None
    weight_kg: int | None
    trunk_l: int | None
    city_consumption: float | None
    road_consumption: float | None
    traction: str | None
    fipe_id: str | None
    fipe_price: float | None
    price0km: float | None
    initial_year: int | None
    final_year: int | None
    in_production: bool
    features: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {"name": self.name, "full_name": self.full_name, "engine": self.engine,
                "power_cv": self.power_cv, "torque": self.torque, "engine_size": self.engine_size,
                "transmission": self.transmission, "fuel": self.fuel, "fuel2": self.fuel2,
                "tank": self.tank, "seats": self.seats, "length_mm": self.length_mm,
                "width_mm": self.width_mm, "height_mm": self.height_mm,
                "wheelbase_mm": self.wheelbase_mm, "weight_kg": self.weight_kg,
                "trunk_l": self.trunk_l, "city_consumption": self.city_consumption,
                "road_consumption": self.road_consumption, "traction": self.traction,
                "fipe_id": self.fipe_id, "fipe_price": self.fipe_price,
                "price0km": self.price0km, "initial_year": self.initial_year,
                "final_year": self.final_year, "in_production": self.in_production,
                "features": self.features}


@dataclass
class Listing:
    """One real used-market offer, from the Mobiauto deals page."""

    id: int
    price: float
    km: int | None
    trim: str
    production_year: int | None
    model_year: int | None
    make: str
    model: str
    fuel: str | None
    transmission: str | None
    city: str | None
    state: str | None
    url: str | None

    def as_dict(self) -> dict[str, Any]:
        return {"id": self.id, "price": self.price, "km": self.km, "trim": self.trim,
                "production_year": self.production_year, "model_year": self.model_year,
                "make": self.make, "model": self.model, "fuel": self.fuel,
                "transmission": self.transmission, "city": self.city, "state": self.state,
                "url": self.url}


@dataclass
class WatchItem:
    """A vehicle the user tracks. Two asks, mutually exclusive: alert me when
    a listing lands at/below `abaixo`, or when the market median reaches
    `acima` (a seller's exit price). FIPE month change is always watched."""

    id: str
    kind: VehicleKind
    marca: str
    modelo: str
    ano: int | None = None
    local: str = "brasil"           # slug: brasil | sp | sp-sorocaba
    abaixo: float | None = None
    acima: float | None = None
    seen_ids: list[int] = field(default_factory=list)
    last_fipe_mes: str | None = None
    last_fipe_valor: float | None = None
    created_at: str = ""
    last_checked_at: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {"id": self.id, "kind": str(self.kind), "marca": self.marca,
                "modelo": self.modelo, "ano": self.ano, "local": self.local,
                "abaixo": self.abaixo, "acima": self.acima, "seen_ids": self.seen_ids,
                "last_fipe_mes": self.last_fipe_mes, "last_fipe_valor": self.last_fipe_valor,
                "created_at": self.created_at, "last_checked_at": self.last_checked_at}

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "WatchItem":
        return cls(id=raw["id"], kind=VehicleKind(raw.get("kind", "carros")),
                   marca=raw["marca"], modelo=raw["modelo"], ano=raw.get("ano"),
                   local=raw.get("local", "brasil"), abaixo=raw.get("abaixo"),
                   acima=raw.get("acima"), seen_ids=list(raw.get("seen_ids", [])),
                   last_fipe_mes=raw.get("last_fipe_mes"), last_fipe_valor=raw.get("last_fipe_valor"),
                   created_at=raw.get("created_at", ""), last_checked_at=raw.get("last_checked_at"))
