"""Watch decisions, pure: a listing list and a watch in, the alerts out."""

from __future__ import annotations

from typing import Any

from fipe.models import Listing, WatchItem


def new_listings(watch: WatchItem, listings: list[Listing]) -> list[Listing]:
    """Listings the watch has not seen. First run sees everything."""
    seen = set(watch.seen_ids)
    return [l for l in listings if l.id not in seen]


def merge_seen(watch: WatchItem, listings: list[Listing], cap: int = 200) -> list[int]:
    seen = set(watch.seen_ids)
    seen.update(l.id for l in listings)
    ordered = [i for i in watch.seen_ids if i in seen]
    for l in listings:
        if l.id not in ordered:
            ordered.append(l.id)
    return ordered[-cap:]


def hits(watch: WatchItem, listings: list[Listing]) -> list[Listing]:
    """The offers worth alerting: at/below `abaixo` for a buyer."""
    if watch.abaixo is None:
        return []
    return [l for l in listings if l.price <= watch.abaixo]


def fipe_changed(watch: WatchItem, mes: str | None, valor: float | None) -> bool:
    """The FIPE reference month moved on from what the watch last recorded."""
    return bool(mes and watch.last_fipe_mes and mes != watch.last_fipe_mes)


def build_alert(watch: WatchItem, new: list[Listing], reached: list[Listing],
                mes: str | None, valor: float | None, median: float | None,
                fipe: float | None) -> dict[str, Any] | None:
    """One JSON alert, or None when the sweep stays quiet."""
    parts: dict[str, Any] = {}
    if reached:
        parts["below"] = [l.as_dict() for l in reached]
    if watch.acima is not None and median is not None and median >= watch.acima:
        parts["above"] = {"median": median, "target": watch.acima}
    if fipe_changed(watch, mes, valor):
        parts["fipe"] = {"mes": mes, "valor": valor, "anterior": watch.last_fipe_valor}
    if not parts:
        return None
    parts["watch"] = watch.id
    return parts
