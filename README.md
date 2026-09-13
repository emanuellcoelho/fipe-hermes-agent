# Fipe

> **FIPE, ficha técnica e preço de mercado — para quem vende e quem compra.**
> **FIPE, the spec sheet and the market price — for sellers and for buyers.**

A Brazilian car-and-motorcycle market [Plow](https://plow.co) agent. Send it
a make and model — "toyota corolla 2020" — and it answers three ways: the
canonical **FIPE** reference (with its month), the **ficha técnica** (power,
torque, consumption, dimensions, per version), and the **real market** from
live listings (price range, median, how much sits under FIPE). It tracks a
vehicle with a target price and alerts when a deal appears or the FIPE
month turns.

A Hermes agent built on the
[`plow-hermes-agent`](https://github.com/plow-pbc/plow-hermes-agent) base
image for the AI Worth Using Hackathon, September 2026. Sibling of
[`vigia-hermes-agent`](https://github.com/emanuellcoelho/vigia-hermes-agent),
[`fandom-hermes-agent`](https://github.com/emanuellcoelho/fandom-hermes-agent)
and [`your-mother-hermes-agent`](https://github.com/emanuellcoelho/your-mother-hermes-agent)
— same template, new domain.

## What it does

- **FIPE** — `fipe valor <marca> <modelo> <ano>` on the public FIPE table
  mirror, with the reference month always named.
- **Ficha técnica** — `ficha <marca> <modelo> <ano>` for the full spec sheet
  per version: power, torque, engine, transmission, consumption, dimensions,
  weight, trunk, plus the FIPE and 0km price for each version.
- **Mercado** — `mercado <marca> <modelo> [--ano] [--local]` over real
  listings: total offers, a 24-offer sample, min/median/max, and how much
  sits below FIPE. `avaliar` adds the verdict for the seller or the buyer.
- **Acompanhar** — `acompanhar add ... --abaixo N` (buyer) or `--acima N`
  (seller), checked daily: new deals under target, the market median
  reaching your number, or the FIPE month changing.
- **Carros e motos** — `--tipo carros|motos` switches the whole pipeline.

## The stack

- `skills/fipe-carro/` — the CLI (`fipe.py`), the engine and the three
  answers
- `skills/fipe-acompanhar/` — the watch list and the daily sweep
- `skills/fipe-onboarding/` — first contact, timezone, cron registration
- `kit/` — clock, http, jsonio: the generic plumbing shared with the
  sibling agents
- Sources: the public FIPE mirror (`parallelum.com.br`) and Mobiauto's
  server-rendered catalog and listings. No third-party dependencies;
  stdlib only, like the base image.

## Run it

```
docker compose up -d
```

The container joins Plow with the credential at `plow-credentials` (never
tracked), registers itself on the [Agent Index](https://aiworthusing.com)
as `fipe`, and answers.

## Tests

```
python3 -m pytest tests/ -q
```

Fixture-fed: real FIPE and Mobiauto responses saved under `tests/fixtures/`;
no network, no sleeps.

MIT licensed; Apache attributions in `NOTICE`.
