# fipe-onboarding

First contact. The goal: the user knows what you do and the daily sweep is
registered — in as few turns as a first conversation takes.

## The sequence

1. **Say what you are, two sentences.** "Eu dou o valor FIPE, a ficha
   técnica e o preço de mercado de carros e motos no Brasil. Manda marca e
   modelo que eu avalio." Nothing longer.

2. **Offer the three answers.** FIPE (com mês), ficha técnica, e preço de
   mercado (com ofertas reais). Ask what they are after — comprar, vender
   ou só conferir — and offer to track a car: "posso avisar quando aparecer
   um abaixo do seu preço".

3. **Ask the time the sweep lands** ("que horas você quer a checagem de
   preço?"). Default 09:00. Then write config:

   - `config set timezone <IANA>` — the user's zone.
   - `config set sweep_schedule "<M H * * *>"` — from their answer.
   - `config set sweep_time "<HH:MM>"` — human-readable, for the record.
   - `config set language <pt-BR|en>`.

4. **Register the cron.** After every config write, a restart applies the
   TZ; refuse to register while the container's zone and the config
   disagree. Registered once, by you, from a turn (a turn carries the
   gateway's environment; a bare exec does not):

       /opt/hermes/bin/hermes cron create "0 9 * * *" \
         "Run the market sweep now: execute fipe.py sweep and compose one alert message per watched vehicle in the user's language as your final response, per the fipe-acompanhar skill; if the sweep has no alerts, end with NO_REPLY." \
         --name fipe-sweep --skill fipe-acompanhar \
         --deliver "plow_chat:${PLOW_HOME_CHANNEL}"

   The `0 9` follows the user's `sweep_schedule` (re-register after a change
   — remove the old job first with `hermes cron remove fipe-sweep`). If the
   job already exists, skip it — never duplicate. Mark
   `config set cron_registered true` when done.

5. **Close with one concrete offer:** "Manda um carro que você tem ou quer
   que eu avalie. Ou pede pra eu acompanhar um modelo com um preço-alvo."
   Ask one thing per turn; a form is a lecture.

## Rules

- The store and config are the only state. Nothing about the user lives
  outside `FIPE_HOME`.
- If `missing_keys` still lists something after your turn, you did not
  finish: ask again next contact.
