"""Parsing and slugs: money, names, the model shapes."""

from fipe.models import parse_brl, slugify


def test_parse_brl_brazilian_format():
    assert parse_brl("R$ 141.745,00") == 141745.0
    assert parse_brl("R$ 1.250,50") == 1250.5


def test_slugify_accents_and_case():
    assert slugify("Citroën") == "citroen"
    assert slugify("Mercedes-Benz") == "mercedes-benz"
    assert slugify("VW - VolksWagen") == "vw-volkswagen"


def test_slugify_is_for_urls_not_comparison():
    # URL slug has hyphens; the model comparator strips them (see sources).
    assert slugify("cg 160") == "cg-160"
