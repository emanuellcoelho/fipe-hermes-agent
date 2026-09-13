"""The watch store: slug ids, roundtrip, compact view."""

from fipe.models import VehicleKind, WatchItem
from fipe.store import FipeStore, watch_id_for


def test_watch_id_shape():
    assert watch_id_for(VehicleKind.CARROS, "toyota", "corolla", 2020, "brasil") \
        == "carros-toyota-corolla-2020-brasil"
    assert watch_id_for(VehicleKind.MOTOS, "honda", "cg160", None, "sp") \
        == "motos-honda-cg160-todos-sp"


def test_add_roundtrip(home):
    store = FipeStore(home)
    w = WatchItem(id="carros-toyota-corolla-2020-brasil", kind=VehicleKind.CARROS,
                  marca="toyota", modelo="corolla", ano=2020, abaixo=100000,
                  seen_ids=[1, 2, 3], created_at="2026-09-13T00:00:00+00:00")
    store.add(w)
    store.save()
    other = FipeStore(home)
    loaded = other.get(w.id)
    assert loaded.abaixo == 100000
    assert loaded.seen_ids == [1, 2, 3]
    assert loaded.kind == VehicleKind.CARROS


def test_remove(home):
    store = FipeStore(home)
    store.add(WatchItem(id="x", kind=VehicleKind.CARROS, marca="t", modelo="m"))
    store.remove("x")
    assert store.all() == []


def test_compact_view(home):
    store = FipeStore(home)
    w = WatchItem(id="x", kind=VehicleKind.MOTOS, marca="honda", modelo="cg160",
                  abaixo=15000, last_fipe_valor=14641, last_fipe_mes="setembro de 2026")
    store.add(w)
    v = store.compact_view(w)
    assert v["abaixo"] == 15000 and v["kind"] == "motos"
