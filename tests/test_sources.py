"""The source adapters, fed real saved fixtures. No network."""

import json

import pytest

from fipe.models import VehicleKind
from fipe.sources import fipe as fipe_src
from fipe.sources import mobiauto


@pytest.fixture()
def fake_fipe(monkeypatch, fipe_valor_data):
    def _get(path):
        return fipe_valor_data
    monkeypatch.setattr(fipe_src, "_get", _get)
    return fipe_valor_data


def test_fipe_valor_parse(fake_fipe):
    v = fipe_src.valor(VehicleKind.CARROS, "56", "9300", "2020-5")
    assert v.marca == "Toyota"
    assert v.valor == 123253.0
    assert v.mes_referencia == "setembro de 2026"
    assert v.codigo_fipe


def _fake_next_data(page_props, html=""):
    return ({"props": {"pageProps": page_props}}, html)


class TestCatalog:
    def test_catalog_parses_trims(self, monkeypatch, catalogo_data):
        monkeypatch.setattr(mobiauto, "_next_data",
                            lambda url: _fake_next_data({"trims": catalogo_data["trims"]}))
        trims = mobiauto.catalog(VehicleKind.CARROS, "toyota", "corolla", 2020)
        assert len(trims) == 3
        t = trims[0]
        assert t.name == "GLi 2.0"
        assert t.power_cv == 154
        assert t.torque == 20.7
        assert t.fipe_price == 106084.0
        assert t.price0km == 112663.0
        assert t.engine == "2.0"

    def test_catalog_features_present_only(self, monkeypatch, catalogo_data):
        monkeypatch.setattr(mobiauto, "_next_data",
                            lambda url: _fake_next_data({"trims": catalogo_data["trims"]}))
        trims = mobiauto.catalog(VehicleKind.CARROS, "toyota", "corolla", 2020)
        assert all(isinstance(f, str) for f in trims[0].features)


class TestDeals:
    def test_deals_parse_listings_and_urls(self, monkeypatch, deals_data):
        html = "".join(
            f'<a href="{u}">' for u in deals_data["urls"].values()
        )
        monkeypatch.setattr(mobiauto, "_next_data",
                            lambda url: _fake_next_data(
                                {"deals": {"numResults": deals_data["num_results"],
                                           "results": deals_data["results"]}}, html))
        data = mobiauto.deals(VehicleKind.CARROS, "toyota", "corolla", ano=2020)
        assert data["num_results"] == 283
        assert len(data["listings"]) == 6
        first = data["listings"][0]
        assert first.price > 0 and first.make == "Toyota"
        assert first.url and "detalhes" in first.url


class TestResolve:
    def test_model_key_normalizes(self):
        assert mobiauto._key("CG 160") == mobiauto._key("cg160") == "cg160"

    def test_resolve_modelo_exact(self, monkeypatch):
        monkeypatch.setattr(mobiauto, "models",
                            lambda kind, slug: [{"nameUrlSeo": "cg160", "name": "CG 160"}])
        m = mobiauto.resolve_modelo(VehicleKind.MOTOS, "honda", "cg 160")
        assert m["nameUrlSeo"] == "cg160"
