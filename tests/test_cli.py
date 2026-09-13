"""The CLI speaks one JSON object per turn. Sources are stubbed; the CLI
wiring (resolve -> parse -> emit) is what is under test."""

import importlib.util
import json
from pathlib import Path

import pytest

_SCRIPTS = Path(__file__).parent.parent / "skills" / "fipe-carro" / "scripts"
_spec = importlib.util.spec_from_file_location("fipe_cli", _SCRIPTS / "fipe.py")
cli = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cli)

from fipe.models import VehicleKind  # noqa: E402


@pytest.fixture()
def stub_sources(monkeypatch, catalogo_data, deals_data):
    from fipe.sources import fipe as fipe_src, mobiauto
    monkeypatch.setattr(fipe_src, "marcas",
                        lambda kind: [{"codigo": "56", "nome": "Toyota"}])
    monkeypatch.setattr(fipe_src, "modelos",
                        lambda kind, c: [{"codigo": "9300", "nome": "Corolla XEi"}])
    monkeypatch.setattr(fipe_src, "anos",
                        lambda kind, c, m: [{"codigo": "2020-5", "nome": "2020"}])
    monkeypatch.setattr(fipe_src, "valor",
                        lambda *a, **k: fipe_src.FipeValue(
                            valor=123253.0, marca="Toyota", modelo="Corolla XEi",
                            ano_modelo=2020, combustivel="Flex", codigo_fipe="002112-1",
                            mes_referencia="setembro de 2026", sigla_combustivel="F"))
    monkeypatch.setattr(mobiauto, "makes",
                        lambda kind: [{"name": "Toyota"}])
    monkeypatch.setattr(mobiauto, "models",
                        lambda kind, slug: [{"nameUrlSeo": "corolla", "name": "Corolla"}])
    monkeypatch.setattr(mobiauto, "catalog",
                        lambda *a, **k: mobiauto._parse_trims(catalogo_data["trims"]))
    monkeypatch.setattr(mobiauto, "deals",
                        lambda *a, **k: {"num_results": 283, "listings": mobiauto._parse_listings(deals_data["results"], {})})
    return {"deals": deals_data}


def run(monkeypatch, home, *argv):
    monkeypatch.setenv("FIPE_HOME", home)
    monkeypatch.setattr("sys.argv", ["fipe.py", *argv])
    return cli.main()


def last(capsys):
    out = capsys.readouterr().out
    decoder, objects, index = json.JSONDecoder(), [], 0
    while index < len(out):
        if not out[index].isspace():
            obj, index = decoder.raw_decode(out, index)
            objects.append(obj)
        else:
            index += 1
    return objects[-1]


def test_fipe_valor(monkeypatch, home, capsys, stub_sources):
    assert run(monkeypatch, home, "fipe", "valor", "toyota", "corolla", "2020") == 0
    assert last(capsys)["valor"]["valor"] == 123253.0


def test_avaliar(monkeypatch, home, capsys, stub_sources):
    assert run(monkeypatch, home, "avaliar", "toyota", "corolla", "2020") == 0
    d = last(capsys)
    assert d["fipe"] == 106084.0
    assert d["stats"]["count"] == 6


def test_acompanhar_flow(monkeypatch, home, capsys, stub_sources):
    assert run(monkeypatch, home, "acompanhar", "add", "toyota", "corolla",
               "--ano", "2020", "--abaixo", "100000") == 0
    assert last(capsys)["added"]["abaixo"] == 100000.0
    assert run(monkeypatch, home, "acompanhar", "list") == 0
    assert len(last(capsys)["watches"]) == 1
    assert run(monkeypatch, home, "acompanhar", "remove",
               "carros-toyota-corolla-2020-brasil") == 0
    assert run(monkeypatch, home, "acompanhar", "list") == 0
    assert last(capsys)["watches"] == []


def test_unknown_marca_fails(monkeypatch, home, capsys, stub_sources):
    from fipe.sources import mobiauto
    monkeypatch.setattr(mobiauto, "makes", lambda kind: [])
    assert run(monkeypatch, home, "ficha", "naoexiste", "corolla", "2020") == 2
    assert "error" in last(capsys)


def test_config_roundtrip(monkeypatch, home, capsys):
    assert run(monkeypatch, home, "config", "set", "timezone", "America/Sao_Paulo") == 0
    assert run(monkeypatch, home, "config", "get", "timezone") == 0
    assert last(capsys)["timezone"] == "America/Sao_Paulo"
