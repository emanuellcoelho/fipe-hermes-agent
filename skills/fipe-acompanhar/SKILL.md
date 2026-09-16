---
name: fipe-acompanhar
description: Track a vehicle deal and alert on price movement. Use when the user asks to track or watch a car/deal, asks about a tracked deal or negotiation, or when the sweep cron fires.
---
# fipe-acompanhar

Track a vehicle and alert on price. The engine diffs listings and watches
the FIPE month; you own the message.

## The command

    python3 scripts/fipe.py acompanhar add <marca> <modelo> [--ano] [--local] [--abaixo N] [--acima N] [--tipo ...]
    python3 scripts/fipe.py acompanhar list
    python3 scripts/fipe.py acompanhar remove <id>
    python3 scripts/fipe.py sweep [--dry-run]

Two asks, one per watch:

- **`--abaixo N`** — a buyer: alert when a listing lands at or below N.
- **`--acima N`** — a seller: alert when the market median reaches N.

## The daily sweep (cron)

The cron turn runs `sweep`, then speaks only when there is an alert. One
alert message per watched vehicle:

    🚗 Corolla 2020 — oferta abaixo do seu alvo (R$ 100.000):
    GLi 2.0, 78.000 km — R$ 99.999 — <link>

    Honda CG 160 — FIPE mudou: setembro/2026, R$ 14.641 (era R$ 14.500).

    Seu mercado subiu: Corolla 2020, mediana R$ 121.000 (alvo R$ 120.000).

A quiet sweep ends with NO_REPLY — nothing found is not a message. The
first sweep after `add` reports everything it sees once; after that only
what is new.

## Rules

- Links come from the sweep output, nowhere else.
- The FIPE month change is an alert, never re-stated as a surprise you
  "noticed" — it is a fact the engine compared.
- `acompanhar list` is the ledger; `remove` stops a watch. No nagging about
  a vehicle the user dropped.
