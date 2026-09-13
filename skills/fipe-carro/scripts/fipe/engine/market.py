"""Market stats, pure: numbers in, numbers out. No IO, no clock."""

from __future__ import annotations

import statistics
from typing import Any


def stats(prices: list[float]) -> dict[str, Any]:
    """min/median/max of a sample, with the sample size said out loud."""
    prices = [p for p in prices if p and p > 0]
    if not prices:
        return {"count": 0, "min": None, "median": None, "max": None}
    return {
        "count": len(prices),
        "min": min(prices),
        "median": statistics.median(prices),
        "max": max(prices),
    }


def below_fipe_share(prices: list[float], fipe: float | None) -> dict[str, Any]:
    """How much of the sample sits under the FIPE reference."""
    if not fipe:
        return {"below_fipe": None, "below_fipe_count": None}
    below = [p for p in prices if p < fipe]
    return {"below_fipe": round(100 * len(below) / len(prices), 1) if prices else None,
            "below_fipe_count": len(below)}


def spread(median: float | None, fipe: float | None) -> float | None:
    """Median minus FIPE, as a fraction of FIPE. Positive = market asks more."""
    if median is None or not fipe:
        return None
    return round((median - fipe) / fipe, 3)
