"""Pure engine: market stats and watch decisions."""

from fipe.engine import market, watch
from fipe.models import Listing, WatchItem


def listing(id, price):
    return Listing(id=id, price=price, km=None, trim="x", production_year=2020,
                   model_year=2020, make="Toyota", model="Corolla", fuel=None,
                   transmission=None, city=None, state=None, url=None)


def test_median_of_odd_and_even():
    assert market.stats([10, 20, 30])["median"] == 20
    assert market.stats([10, 20, 30, 40])["median"] == 25


def test_stats_ignore_non_positive():
    s = market.stats([0, None, 100, 200])
    assert s["count"] == 2 and s["min"] == 100


def test_below_fipe_share():
    assert market.below_fipe_share([90, 110, 120], 100)["below_fipe"] == 33.3


def test_spread_positive_when_market_asks_more():
    assert market.spread(110, 100) == 0.1


class TestWatch:
    def test_new_listings_filters_seen(self):
        w = WatchItem(id="w", kind="carros", marca="toyota", modelo="corolla",
                      seen_ids=[1, 2])
        fresh = watch.new_listings(w, [listing(1, 10), listing(3, 30)])
        assert [l.id for l in fresh] == [3]

    def test_merge_seen_caps(self):
        w = WatchItem(id="w", kind="carros", marca="toyota", modelo="corolla")
        merged = watch.merge_seen(w, [listing(i, 10) for i in range(250)], cap=200)
        assert len(merged) == 200

    def test_hits_buyer_below(self):
        w = WatchItem(id="w", kind="carros", marca="toyota", modelo="corolla", abaixo=100)
        assert [l.id for l in watch.hits(w, [listing(1, 99), listing(2, 150)])] == [1]
        assert watch.hits(WatchItem(id="w2", kind="carros", marca="t", modelo="m"), []) == []

    def test_alert_silent_when_nothing(self):
        w = WatchItem(id="w", kind="carros", marca="toyota", modelo="corolla")
        assert watch.build_alert(w, [], [], None, None, 100, 100) is None

    def test_alert_below_and_fipe_change(self):
        w = WatchItem(id="w", kind="carros", marca="toyota", modelo="corolla",
                      abaixo=100, last_fipe_mes="agosto de 2026", last_fipe_valor=105000)
        alert = watch.build_alert(w, [listing(9, 95)], [listing(9, 95)],
                                  "setembro de 2026", 100000, 100000, 100000)
        assert alert["watch"] == "w"
        assert alert["below"][0]["id"] == 9
        assert alert["fipe"]["mes"] == "setembro de 2026"

    def test_seller_above(self):
        w = WatchItem(id="w", kind="carros", marca="toyota", modelo="corolla", acima=150000)
        alert = watch.build_alert(w, [], [], None, None, 160000, 100000)
        assert alert["above"]["median"] == 160000
