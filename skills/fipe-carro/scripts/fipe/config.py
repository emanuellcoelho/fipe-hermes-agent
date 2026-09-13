"""Agent preferences. Missing keys mean onboarding is unfinished; the sweep
schedule lives here so onboarding registers exactly what the user chose."""

from __future__ import annotations

from typing import Any

from kit.jsonio import load_json, save_json_atomic

REQUIRED_KEYS = ("timezone", "sweep_time", "language")

DEFAULTS: dict[str, Any] = {
    "timezone": "UTC",
    "sweep_time": "09:00",
    "sweep_schedule": "0 9 * * *",
    "sweep_enabled": True,
    "language": "",                  # "" = mirror the user each turn
    "cron_registered": False,
    "default_local": "brasil",
}


def config_path(home: str) -> str:
    return f"{home}/config.json"


def load(home: str) -> dict[str, Any]:
    stored = load_json(config_path(home), {}) or {}
    return {**DEFAULTS, **stored}


def save(home: str, config: dict[str, Any]) -> None:
    save_json_atomic(config_path(home), config)


def missing_keys(home: str) -> list[str]:
    stored = load_json(config_path(home), {}) or {}
    return [key for key in REQUIRED_KEYS if key not in stored]
