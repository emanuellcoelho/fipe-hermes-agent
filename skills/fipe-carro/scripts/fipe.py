#!/usr/bin/env python3
"""fipe.py -- FIPE, ficha técnica and market price. One JSON object, 0/1/2.

    fipe marcas|modelos <marca>|anos <marca> <modelo>|valor <marca> <modelo> <ano>
    ficha <marca> <modelo> <ano>          the full spec sheet per version
    mercado <marca> <modelo> [--ano] [--local]   real listings + price stats
    avaliar <marca> <modelo> <ano>        FIPE + 0km + market, one verdict
    acompanhar add <marca> <modelo> [--ano] [--local] [--abaixo|--acima N]
    acompanhar list|remove <id>
    sweep [--dry-run]                     the cron entry; quiet = no alerts
    config get [key] | set <k> <v>

`--tipo carros|motos` selects the vehicle family (default carros). Names are
resolved against the live catalogs, so 'toyota' and 'corolla' work as typed."""

from __future__ import annotations

import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from kit import clock, http  # noqa: E402

from fipe import config as config_module  # noqa: E402
from fipe import store as store_module  # noqa: E402
from fipe.engine import market, watch as watch_engine  # noqa: E402
from fipe.models import VehicleKind  # noqa: E402
from fipe.sources import fipe as fipe_src  # noqa: E402
from fipe.sources import mobiauto  # noqa: E402
from fipe.store import FipeStore  # noqa: E402


def emit(payload: object, code: int = 0) -> int:
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return code


def fail(message: str, code: int = 2) -> int:
    return emit({"error": message}, code)


def home() -> str:
    return os.environ.get("FIPE_HOME") or "/var/lib/hermes/fipe"


def kind_of(args: argparse.Namespace) -> VehicleKind:
    return VehicleKind(args.tipo)


def slug_marca(args: argparse.Namespace) -> str:
    return mobiauto.resolve_marca(kind_of(args), args.marca)["name"]


def _mobiauto_slugs(args: argparse.Namespace) -> tuple[str, str]:
    marca = mobiauto.resolve_marca(kind_of(args), args.marca)
    marca_slug = mobiauto.slugify(marca["name"])
    modelo = mobiauto.resolve_modelo(kind_of(args), marca_slug, args.modelo)
    return marca_slug, modelo["nameUrlSeo"]


# --- FIPE (canonical table) -------------------------------------------------

def cmd_fipe(args: argparse.Namespace) -> int:
    kind = kind_of(args)
    if args.action == "marcas":
        return emit({"marcas": fipe_src.marcas(kind)})
    if args.action == "modelos":
        marca = fipe_src.resolve_marca(kind, args.marca)
        return emit({"marca": marca, "modelos": fipe_src.modelos(kind, marca["codigo"])})
    if args.action == "anos":
        marca = fipe_src.resolve_marca(kind, args.marca)
        modelo = fipe_src.resolve_modelo(kind, marca["codigo"], args.modelo)
        return emit({"marca": marca, "modelo": modelo,
                     "anos": fipe_src.anos(kind, marca["codigo"], modelo["codigo"])})
    if args.action == "valor":
        marca = fipe_src.resolve_marca(kind, args.marca)
        modelo = fipe_src.resolve_modelo(kind, marca["codigo"], args.modelo)
        anos = fipe_src.anos(kind, marca["codigo"], modelo["codigo"])
        if not anos:
            return fail("sem anos para esse modelo")
        wanted = str(args.ano)
        match = next((a for a in anos if a["codigo"].startswith(wanted + "-")), None)
        if match is None:
            return fail(f"não há referência {wanted}; anos disponíveis: "
                        f"{', '.join(a['codigo'] for a in anos[:8])}")
        return emit({"valor": fipe_src.valor(kind, marca["codigo"], modelo["codigo"], match["codigo"]).as_dict()})
    return fail("unknown action", 1)


# --- Mobiauto catalog + market ---------------------------------------------

def cmd_ficha(args: argparse.Namespace) -> int:
    marca_slug, modelo_slug = _mobiauto_slugs(args)
    trims = mobiauto.catalog(kind_of(args), marca_slug, modelo_slug, args.ano)
    if not trims:
        return fail(f"sem ficha para {args.marca} {args.modelo} {args.ano}")
    return emit({"marca": args.marca, "modelo": args.modelo, "ano": args.ano,
                 "versoes": [t.as_dict() for t in trims]})


def cmd_mercado(args: argparse.Namespace) -> int:
    marca_slug, modelo_slug = _mobiauto_slugs(args)
    data = mobiauto.deals(kind_of(args), marca_slug, modelo_slug, args.ano, args.local)
    listings = data["listings"]
    prices = [l.price for l in listings]
    return emit({"marca": args.marca, "modelo": args.modelo, "ano": args.ano,
                 "local": args.local, "num_results": data["num_results"],
                 "amostra": len(listings), "stats": market.stats(prices),
                 "listings": [l.as_dict() for l in listings]})


def cmd_avaliar(args: argparse.Namespace) -> int:
    marca_slug, modelo_slug = _mobiauto_slugs(args)
    kind = kind_of(args)
    trims = mobiauto.catalog(kind, marca_slug, modelo_slug, args.ano)
    data = mobiauto.deals(kind, marca_slug, modelo_slug, args.ano, args.local)
    listings = data["listings"]
    prices = [l.price for l in listings]
    fipe_price = min((t.fipe_price for t in trims if t.fipe_price), default=None)
    zero_km = min((t.price0km for t in trims if t.price0km), default=None)
    stats = market.stats(prices)
    stats.update(market.below_fipe_share(prices, fipe_price))
    stats["spread_vs_fipe"] = market.spread(stats["median"], fipe_price)
    return emit({"marca": args.marca, "modelo": args.modelo, "ano": args.ano,
                 "local": args.local, "fipe": fipe_price, "zero_km": zero_km,
                 "num_results": data["num_results"], "amostra": len(listings),
                 "stats": stats, "versoes": len(trims)})


# --- Watch ------------------------------------------------------------------

def cmd_acompanhar(args: argparse.Namespace) -> int:
    store = FipeStore(home())
    if args.action == "list":
        return emit({"watches": [store.compact_view(w) for w in store.all()]})
    if args.action == "remove":
        try:
            watch = store.get(args.id)
        except KeyError as error:
            return fail(str(error))
        store.remove(watch.id)
        store.save()
        return emit({"removed": store.compact_view(watch)})
    if args.action == "add":
        marca_slug, modelo_slug = _mobiauto_slugs(args)
        marca_name = mobiauto.resolve_marca(kind_of(args), args.marca)["name"]
        watch_id = store_module.watch_id_for(kind_of(args), marca_slug, modelo_slug,
                                             args.ano, args.local)
        existing = store.watches.get(watch_id)
        watch = existing or store_module.WatchItem(
            id=watch_id, kind=kind_of(args), marca=marca_slug, modelo=modelo_slug,
            ano=args.ano, local=args.local, abaixo=args.abaixo, acima=args.acima,
            created_at=clock.iso(),
        )
        if existing is not None:
            if args.abaixo is not None:
                existing.abaixo = args.abaixo
            if args.acima is not None:
                existing.acima = args.acima
            watch = existing
        store.add(watch)
        store.save()
        return emit({"added": store.compact_view(watch)})
    return fail("unknown action", 1)


def cmd_sweep(args: argparse.Namespace) -> int:
    store = FipeStore(home())
    cfg = config_module.load(store.home)
    alerts = []
    for watch in store.all():
        kind = watch.kind
        try:
            trims = mobiauto.catalog(kind, watch.marca, watch.modelo, watch.ano) if watch.ano else []
            data = mobiauto.deals(kind, watch.marca, watch.modelo, watch.ano, watch.local)
        except (http.HttpError, LookupError) as error:
            alerts.append({"watch": watch.id, "error": str(error)})
            continue
        listings = data["listings"]
        fresh = watch_engine.new_listings(watch, listings)
        reached = watch_engine.hits(watch, fresh)
        prices = [l.price for l in listings]
        median = market.stats(prices)["median"]
        fipe_price = min((t.fipe_price for t in trims if t.fipe_price), default=None)
        mes = None
        alert = watch_engine.build_alert(watch, fresh, reached, mes, fipe_price, median, fipe_price)
        watch.seen_ids = watch_engine.merge_seen(watch, listings)
        watch.last_fipe_valor = fipe_price
        watch.last_checked_at = clock.iso()
        if alert:
            alerts.append(alert)
    store.save()
    return emit({"swept": len(store.all()), "alerts": alerts, "dry_run": bool(args.dry_run)})


def cmd_config(args: argparse.Namespace) -> int:
    store_home = home()
    if args.action == "get":
        cfg = config_module.load(store_home)
        return emit(cfg if not args.key else {args.key: cfg.get(args.key)})
    if args.action == "set":
        if not args.key or args.value is None:
            return fail("usage: config set <key> <value>")
        cfg = config_module.load(store_home)
        raw = args.value
        parsed: object = raw
        if raw.lower() in ("true", "false"):
            parsed = raw.lower() == "true"
        elif raw.lstrip("-").isdigit():
            parsed = int(raw)
        cfg[args.key] = parsed
        config_module.save(store_home, cfg)
        return emit({"set": {args.key: parsed}})
    return fail("unknown action", 1)


def main() -> int:
    parser = argparse.ArgumentParser(prog="fipe.py", description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)

    def add_common(p, with_modelo=True):
        p.add_argument("--tipo", choices=["carros", "motos"], default="carros")

    fipe_p = sub.add_parser("fipe")
    fipe_sub = fipe_p.add_subparsers(dest="action", required=True)
    m = fipe_sub.add_parser("marcas"); add_common(m)
    m = fipe_sub.add_parser("modelos"); m.add_argument("marca"); add_common(m)
    m = fipe_sub.add_parser("anos"); m.add_argument("marca"); m.add_argument("modelo"); add_common(m)
    m = fipe_sub.add_parser("valor"); m.add_argument("marca"); m.add_argument("modelo"); m.add_argument("ano"); add_common(m)

    f = sub.add_parser("ficha"); add_common(f)
    f.add_argument("marca"); f.add_argument("modelo"); f.add_argument("ano", type=int)

    mk = sub.add_parser("mercado"); add_common(mk)
    mk.add_argument("marca"); mk.add_argument("modelo")
    mk.add_argument("--ano", type=int); mk.add_argument("--local", default="brasil")

    av = sub.add_parser("avaliar"); add_common(av)
    av.add_argument("marca"); av.add_argument("modelo"); av.add_argument("ano", type=int)
    av.add_argument("--local", default="brasil")

    ac = sub.add_parser("acompanhar")
    ac_sub = ac.add_subparsers(dest="action", required=True)
    ac_list = ac_sub.add_parser("list"); add_common(ac_list)
    ac_rm = ac_sub.add_parser("remove"); ac_rm.add_argument("id")
    ac_add = ac_sub.add_parser("add"); add_common(ac_add)
    ac_add.add_argument("marca"); ac_add.add_argument("modelo")
    ac_add.add_argument("--ano", type=int); ac_add.add_argument("--local", default="brasil")
    ac_add.add_argument("--abaixo", type=float); ac_add.add_argument("--acima", type=float)

    sw = sub.add_parser("sweep"); sw.add_argument("--dry-run", action="store_true")

    cf = sub.add_parser("config")
    cf_sub = cf.add_subparsers(dest="action", required=True)
    g = cf_sub.add_parser("get"); g.add_argument("key", nargs="?")
    s = cf_sub.add_parser("set"); s.add_argument("key"); s.add_argument("value")

    handlers = {"fipe": cmd_fipe, "ficha": cmd_ficha, "mercado": cmd_mercado,
                "avaliar": cmd_avaliar, "acompanhar": cmd_acompanhar,
                "sweep": cmd_sweep, "config": cmd_config}
    args = parser.parse_args()
    try:
        return handlers[args.command](args)
    except (KeyError, LookupError) as error:
        return fail(str(error))
    except http.HttpError as error:
        return fail(str(error), 2)
    except Exception as error:
        return emit({"error": f"{type(error).__name__}: {error}"}, 1)


if __name__ == "__main__":
    sys.exit(main())
