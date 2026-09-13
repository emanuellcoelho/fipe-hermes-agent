import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).parent.parent / "skills" / "fipe-carro" / "scripts"
sys.path.insert(0, str(SCRIPTS))

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture()
def home(tmp_path):
    return str(tmp_path / "fipe")


def load_fixture(name: str):
    import json
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


@pytest.fixture()
def catalogo_data():
    return load_fixture("mobiauto-catalogo.json")


@pytest.fixture()
def deals_data():
    return load_fixture("mobiauto-deals.json")


@pytest.fixture()
def fipe_valor_data():
    return load_fixture("fipe-valor.json")
