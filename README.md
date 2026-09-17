# Fipe

> **FIPE, ficha técnica e preço de mercado de carros e motos — para quem vende e quem compra.**
> **What it's worth, what it's made of, what the market asks.**

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

## Install

One Plow line per agent. From your machine:

```sh
git clone https://github.com/plow-pbc/plow-agents.git
export PATH="$PWD/plow-agents/bin:$PATH"

git clone https://github.com/emanuellcoelho/fipe-hermes-agent.git
cd fipe-hermes-agent

plow-agents login             # once per account; text the activation phrase
plow-agents lines             # pick a free line
plow-agents mint ln_xxx       # writes ./plow-credentials
docker compose up --build -d
```

`mint` must run **before** `up`: the compose file mounts `./plow-credentials`,
and Docker silently creates it as a *directory* if the file is not there yet.
If that happened, `docker compose down -v && rmdir plow-credentials`, then
mint the line and start over.

Watch `docker compose logs -f agent` until
`plow-init: configured ... as cht_` appears, then text your line. The
container joins Plow with that credential (never tracked) and registers
itself on the [Agent Index](https://aiworthusing.com) as `fipe`.

If the build fails pulling the base image from `public.ecr.aws` with a 403,
the cause is a stale credential: `docker logout public.ecr.aws`, then build
again.

Retire it when you are done:

```sh
plow-agents revoke
docker compose down -v        # `down` alone keeps the agent's memory
```

## Tests

```
python3 -m pytest tests/ -q
```

Fixture-fed: real FIPE and Mobiauto responses saved under `tests/fixtures/`;
no network, no sleeps.

MIT licensed; Apache attributions in `NOTICE`.
