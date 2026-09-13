# Fipe — AGENTS.md

A FIPE and car-market Plow agent, and the fourth agent built on the Vigia
template — the first with a **dual catalog** (the FIPE reference and a live
listings source). Read this before changing anything; it says who owns what
and where a change goes.

## The one test

**Who else would have to change if this fact changed?** That owner is where
the change goes.

| Path | Owns | Never here |
| --- | --- | --- |
| `plow-pbc/plow-hermes-agent` (base) | boot, `plow-init`, gateway config, base persona, plugin pin | anything Fipe-specific |
| `persona.md` | Fipe's voice: numbers first, month/sample honesty, seller vs buyer framing | per-turn plumbing, tool how-tos |
| `skills/fipe-carro/` | the engine: models, store, market stats, the FIPE and Mobiauto readers, the CLI — and its SKILL.md | chat delivery (post_chat.py is its only exception, mechanically) |
| `skills/fipe-acompanhar/` | the watch list and the daily sweep conversation | alert math (engine owns that) |
| `skills/fipe-onboarding/` | first contact, timezone, cron registration | the engine's defaults (config.py owns those) |
| `skills/fipe-carro/scripts/kit/` | generic infrastructure: clock, http, jsonio — domain-free | anything that knows what a car is |
| `image/` | s6 services (agent-index reporter), TZ cont-init | gateway config, plow-init — the base's |
| `vendor/client.pin` | which agent-index-client commit runs inside the agent | a vendored copy that drifts |
| `Dockerfile` / `compose.yml` | how this content ships | base-image behavior |

Sibling repos [`vigia-hermes-agent`](https://github.com/emanuellcoelho/vigia-hermes-agent),
[`fandom-hermes-agent`](https://github.com/emanuellcoelho/fandom-hermes-agent)
and [`your-mother-hermes-agent`](https://github.com/emanuellcoelho/your-mother-hermes-agent)
share this structure; `kit/` stays byte-identical across forks until a
fourth fork confirms the pattern graduates it into a package.

## Conventions

- **Scripts are mechanical.** One JSON object on stdout, exit 0/1/2, no
  human words. The SKILL.md files are the voice. No prompt text in Python.
- **stdlib only.** No new dependencies in scripts or the image.
- **The market math is pure** (`fipe/engine/market.py`, `watch.py`): prices
  in, stats out, no IO, no clock. A listing diff is a function of ids, not
  of what the model felt like saying.
- **Honesty is architectural**: a FIPE value carries its month; a market
  price carries its sample size; a listing carries its source and link.
  Sources are adapters behind `fipe/sources/`; the readers parse the FIPE
  mirror and Mobiauto's `__NEXT_DATA__` — no key, no browser.
- **Writes are atomic** (`kit.jsonio.save_json_atomic`). The store file is
  a contract: `fipe/models.py` owns its shape, explicitly serialized.
- **State lives in `/var/lib/hermes/fipe/`** (override with `FIPE_HOME` for
  tests). Nothing under this tree carries a credential, a chat id, or a
  person's data beyond the vehicles they chose to watch.
- **TZ is fixed at boot** from `fipe/config.json`
  (`image/cont-init.d/10-fipe-timezone`). `hermes cron create` takes no
  per-job zone, so onboarding refuses to register schedules while the
  container's zone and the config disagree — a restart applies the zone
  first.

## Commits

Conventional, scoped by the table above, imperative, one concern per commit:
`feat(sources):`, `feat(engine):`, `feat(skills):`, `fix(...)`, `docs:`,
`chore:`. The body says **why**; the diff says what. Never in a commit:
`plow-credentials`, state files, anything under a `FIPE_HOME`. A pin bump
(`vendor/client.pin`, the base digest) is its own commit naming what moved
and why.

## Tests

    python3 -m pytest tests/ -q

Fixture-fed: real FIPE and Mobiauto responses under `tests/fixtures/` — no
network, no clock sleeps. A change to market stats, listing diff, slug
resolution or store shape starts in `tests/`.

## Schedules (the registered spec)

| name | schedule (container TZ) | deliver |
| --- | --- | --- |
| `fipe-sweep` | `0 9 * * *` (onboarding writes the user's time) | post_chat.py per watched vehicle with a new alert; quiet = NO_REPLY |

Changing this row is an edit to `skills/fipe-onboarding/SKILL.md` and this
table together.

## Forking this into a new agent

The structure is deliberately the template:

1. Copy the tree; change `persona.md` and the skills' domain layer
   (`fipe/` → your domain; `kit/` stays).
2. Swap `sources/` for your domain's readers behind the same seam; keep
   the pure engine pure.
3. New `AGENT_ID`, new registration (`agent_index_client.py --register`),
   new compose `AGENT_ID`.
4. LICENSE stays MIT; NOTICE keeps the Apache attributions.

Four siblings now confirm the pattern — `kit/` graduates into its own
package.
