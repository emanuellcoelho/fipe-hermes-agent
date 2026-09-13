"""The watch-list store: one JSON file, written whole, keyed by slug."""

from __future__ import annotations

from typing import Any

from kit.jsonio import load_json, save_json_atomic

from fipe.models import VehicleKind, WatchItem

_WATCHES_FILE = "watches.json"


def watches_path(home: str) -> str:
    return f"{home}/{_WATCHES_FILE}"


def watch_id_for(kind: VehicleKind, marca: str, modelo: str, ano: int | None,
                 local: str) -> str:
    ano_part = str(ano) if ano else "todos"
    return f"{kind}-{marca}-{modelo}-{ano_part}-{local}"


class FipeStore:
    def __init__(self, home: str) -> None:
        self.home = home
        raw = load_json(watches_path(home), {"watches": []}) or {}
        self.watches: dict[str, WatchItem] = {
            data["id"]: WatchItem.from_dict(data) for data in raw.get("watches", [])
        }

    def save(self) -> None:
        save_json_atomic(watches_path(self.home),
                         {"watches": [w.as_dict() for w in self.watches.values()]})

    def add(self, watch: WatchItem) -> WatchItem:
        self.watches[watch.id] = watch
        return watch

    def remove(self, watch_id: str) -> WatchItem:
        return self.watches.pop(watch_id)

    def all(self) -> list[WatchItem]:
        return sorted(self.watches.values(), key=lambda w: w.created_at)

    def get(self, watch_id: str) -> WatchItem:
        if watch_id not in self.watches:
            raise KeyError(f"no watch named {watch_id!r}")
        return self.watches[watch_id]

    def compact_view(self, watch: WatchItem) -> dict[str, Any]:
        return {"id": watch.id, "kind": str(watch.kind), "marca": watch.marca,
                "modelo": watch.modelo, "ano": watch.ano, "local": watch.local,
                "abaixo": watch.abaixo, "acima": watch.acima,
                "last_fipe_valor": watch.last_fipe_valor,
                "last_fipe_mes": watch.last_fipe_mes}
