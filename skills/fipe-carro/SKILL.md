---
name: fipe-carro
description: FIPE value, spec sheet (ficha técnica) and market price for a car. Use when the user asks what a car is worth, asks for the FIPE value or spec sheet, or sends a listing to evaluate.
---
# fipe-carro

FIPE, ficha técnica and market price. The engine owns the numbers; you own
the verdict. Every number you state came out of `fipe.py` this turn.

## The command

    python3 scripts/fipe.py fipe marcas [--tipo carros|motos]
    python3 scripts/fipe.py fipe modelos <marca> [--tipo ...]
    python3 scripts/fipe.py fipe anos <marca> <modelo> [--tipo ...]
    python3 scripts/fipe.py fipe valor <marca> <modelo> <ano> [--tipo ...]
    python3 scripts/fipe.py ficha <marca> <modelo> <ano> [--tipo ...]
    python3 scripts/fipe.py mercado <marca> <modelo> [--ano] [--local] [--tipo ...]
    python3 scripts/fipe.py avaliar <marca> <modelo> <ano> [--local] [--tipo ...]

Names resolve against the live catalogs — "toyota", "corolla", "cg 160" work
as typed. `--local` narrows listings: `brasil` (default), `sp`, `sp-sorocaba`.

## The three answers

**FIPE** (`fipe valor`) — the reference table. Always name the month:
"FIPE (ref. setembro/2026): R$ 120.111". If the version is ambiguous, the
table has several entries for one model — pick the one that matches the
user's car, or list the years and ask which version.

**Ficha** (`ficha`) — the spec sheet, one line per version:

    Corolla 2020 — 5 versões:
    • GLi 2.0 — 154 cv, 2.0, automática, 7,2 km/l cidade · FIPE R$ 106.084 · 0km R$ 112.663
    • 2.0 XEi Multi-Drive S — ...

Keep it to power, engine, transmission, consumption and the FIPE/0km numbers.
The full feature list lives in the JSON; surface it only when asked.

**Mercado** (`mercado` / `avaliar`) — real listings. Say the sample:

    Corolla 2020 — 283 ofertas (amostra de 24):
    pedem entre R$ 99.999 e R$ 138.900, mediana R$ 120.450
    12,5% abaixo da FIPE

`avaliar` adds the verdict. For a buyer: point at the spread under FIPE.
For a seller: "o mercado pede 13,5% acima da FIPE — seu preço está dentro"
or "seu preço está R$ X acima do teto que o mercado aceita".

## Rules

- A price is never stated without its month (FIPE) or its sample size
  (market). Blending 0km, FIPE and used into one number is a lie.
- A listing gets its link when you mention it; the source is Mobiauto.
- Motos work the same (`--tipo motos`): `ficha honda "cg 160" 2022 --tipo motos`.
- When a name resolves to several versions, ask which one before pricing.
