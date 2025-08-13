import pytest
from sports_api import SportsAPI


def test_generate_demo_matches_structure():
    api = SportsAPI(api_key="demo", demo_mode=True)
    matches = api._generate_demo_matches("soccer_epl", "Premier League")

    assert 3 <= len(matches) <= 6
    required_match_keys = {"id", "sport_key", "sport_title", "commence_time", "home_team", "away_team", "bookmakers"}

    for match in matches:
        # basic fields
        assert required_match_keys.issubset(match)
        assert match["sport_key"] == "soccer_epl"
        assert match["sport_title"] == "Premier League"
        # bookmakers structure
        assert isinstance(match["bookmakers"], list) and match["bookmakers"]
        bookmaker = match["bookmakers"][0]
        assert {"key", "title", "markets"}.issubset(bookmaker)
        assert isinstance(bookmaker["markets"], list) and bookmaker["markets"]
        market = bookmaker["markets"][0]
        assert {"key", "outcomes"}.issubset(market)
        assert isinstance(market["outcomes"], list) and len(market["outcomes"]) >= 2
        outcome = market["outcomes"][0]
        assert {"name", "price"}.issubset(outcome)
