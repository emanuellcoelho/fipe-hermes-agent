"""Wall-clock access, injectable so decisions can be tested deterministically."""

from __future__ import annotations

from datetime import datetime, timezone

_clock: callable | None = None


def now(tz: str | None = None) -> datetime:
    """The current time, aware, in `tz` (IANA name) or UTC."""
    zone = timezone.utc if tz in (None, "UTC") else __import__("zoneinfo").ZoneInfo(tz)
    source = _clock() if _clock is not None else datetime.now(timezone.utc)
    return source.astimezone(zone)


def use_clock(provider: callable) -> None:
    """Swap the clock (tests only). Pass None to restore real time."""
    global _clock
    _clock = provider


def iso(at: datetime | None = None) -> str:
    """ISO-8601 UTC instant, the one format the store speaks."""
    moment = at if at is not None else now()
    return moment.astimezone(timezone.utc).isoformat(timespec="seconds")
