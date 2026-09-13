"""Mobiauto: the spec catalog and the used-market listings. Both are
server-rendered into __NEXT_DATA__, so a plain GET is enough -- no key, no
browser. The catalog gives the full ficha técnica plus the FIPE and 0km
price per version; the deals page gives real offers with km, dealer and a
direct link.

Honesty is built in: the listings return the total count AND the sample the
page renders, so the agent can say '698 ofertas, amostra de 24' instead of
pretending it saw them all."""

from __future__ import annotations

import json
import re
from typing import Any

from kit import http

from fipe.models import Listing, Trim, VehicleKind, slugify

CATALOG = "https://www.mobiauto.com.br/catalogo"
DEALS_KIND = {VehicleKind.CARROS: "carros-usados", VehicleKind.MOTOS: "motos-usadas"}

def _next_data(url: str) -> tuple[dict[str, Any], str]:
    status, body = http.fetch(url, timeout_s=20)
    if status != 200:
        raise http.HttpError(f"Mobiauto respondeu HTTP {status}")
    html = body.decode("utf-8", "replace") if isinstance(body, bytes) else body
    match = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.S)
    if not match:
        raise http.HttpError(f"Mobiauto devolveu página sem dados ({url})")
    return json.loads(match.group(1)), html


def makes(kind: VehicleKind) -> list[dict[str, Any]]:
    data, _ = _next_data(f"{CATALOG}/{kind.value}")
    groups = data["props"]["pageProps"].get("makes", [])
    for group in groups:
        if group.get("vehicleType") == kind.value:
            return group.get("makes", [])
    return []


def models(kind: VehicleKind, marca_slug: str) -> list[dict[str, Any]]:
    data, _ = _next_data(f"{CATALOG}/{kind.value}/{marca_slug}")
    content = data["props"]["pageProps"].get("modelsBySearch", {})
    return content.get("content", [])


def resolve_marca(kind: VehicleKind, query: str) -> dict[str, Any]:
    wanted = slugify(query)
    for marca in makes(kind):
        if slugify(marca["name"]) == wanted:
            return marca
    raise LookupError(f"não achei a marca {query!r} no catálogo Mobiauto")


def _key(name: str) -> str:
    """Comparison key: lowercase alphanumerics only. 'cg 160', 'cg160' and
    'CG 160' are one model; Mobiauto's own slug drops the separator too."""
    return re.sub(r"[^a-z0-9]", "", name.lower())


def resolve_modelo(kind: VehicleKind, marca_slug: str, query: str) -> dict[str, Any]:
    wanted = _key(query)
    all_models = models(kind, marca_slug)
    exact = [m for m in all_models if _key(m.get("nameUrlSeo") or "") == wanted]
    if exact:
        return exact[0]
    matches = [m for m in all_models if wanted in _key(m.get("nameUrlSeo") or "")]
    if not matches:
        raise LookupError(f"não achei o modelo {query!r} da {marca_slug!r} no Mobiauto")
    return matches[0]


def _num(value: Any) -> float | None:
    try:
        return float(value) if value not in (None, "") else None
    except (TypeError, ValueError):
        return None


def _parse_trims(trims: list[dict[str, Any]]) -> list[Trim]:
    result = []
    for t in trims:
        features = [f["name"] for f in t.get("featureMap", []) if f.get("present")]
        result.append(Trim(
            name=t.get("name", ""), full_name=t.get("fullName", ""),
            engine=t.get("engine", ""), power_cv=int(t["power"]) if t.get("power") is not None else None,
            torque=_num(t.get("torque")), engine_size=int(t["engineSize"]) if t.get("engineSize") is not None else None,
            transmission=t.get("transmissionName", ""), fuel=t.get("fuelName", ""),
            fuel2=t.get("fuel2Name"), tank=_num(t.get("tank")), seats=t.get("seats"),
            length_mm=t.get("length"), width_mm=t.get("width"), height_mm=t.get("height"),
            wheelbase_mm=t.get("wheelbases"), weight_kg=t.get("weight"), trunk_l=t.get("trunk"),
            city_consumption=_num(t.get("cityConsumption")), road_consumption=_num(t.get("roadConsumption")),
            traction=t.get("traction"), fipe_id=t.get("fipeId"), fipe_price=_num(t.get("fipePrice")),
            price0km=_num(t.get("price0km")), initial_year=t.get("initialYear"),
            final_year=t.get("finalYear"), in_production=bool(t.get("inProduction")),
            features=features,
        ))
    return result


def _parse_listings(results: list[dict[str, Any]], urls: dict[int, str]) -> list[Listing]:
    listings = []
    for item in results:
        trim = item.get("trim", {}) or {}
        model = trim.get("model", {}) or {}
        make = trim.get("make", {}) or {}
        dealer = item.get("dealer", {}) or {}
        listings.append(Listing(
            id=item["id"], price=float(item.get("price") or 0),
            km=int(item["km"]) if item.get("km") is not None else None,
            trim=trim.get("name", ""), production_year=trim.get("productionYear"),
            model_year=model.get("year"), make=make.get("name", ""),
            model=model.get("name", ""),
            fuel=(trim.get("fuel") or {}).get("name") if isinstance(trim.get("fuel"), dict) else None,
            transmission=(trim.get("transmission") or {}).get("name") if isinstance(trim.get("transmission"), dict) else None,
            city=dealer.get("city"), state=dealer.get("state"), url=urls.get(item["id"]),
        ))
    return listings


def catalog(kind: VehicleKind, marca_slug: str, modelo_slug: str, ano: int) -> list[Trim]:
    data, _ = _next_data(f"{CATALOG}/{kind.value}/{marca_slug}/{modelo_slug}/{ano}")
    return _parse_trims(data["props"]["pageProps"].get("trims", []))


def deals(kind: VehicleKind, marca_slug: str, modelo_slug: str,
          ano: int | None = None, local: str = "brasil") -> dict[str, Any]:
    deals_kind = DEALS_KIND[kind]
    path = f"/comprar/{deals_kind}/{local}/{marca_slug}/{modelo_slug}"
    if ano is not None:
        path += f"/ano-{ano}"
    data, html = _next_data(f"https://www.mobiauto.com.br{path}")
    d = data["props"]["pageProps"].get("deals", {})
    results = d.get("results", [])
    # The detail URLs live in the page's anchors, keyed by listing id.
    urls: dict[int, str] = {}
    for m in re.finditer(r'href="(https://www\.mobiauto\.com\.br/comprar/[^"]*?/detalhes/(\d+))', html):
        urls[int(m.group(2))] = m.group(1)
    return {"num_results": d.get("numResults"), "listings": _parse_listings(results, urls)}
