import unittest
from sports_api import create_demo_sports_api

class DemoModeOddsTest(unittest.TestCase):
    def test_best_odds_extracted(self):
        api = create_demo_sports_api()
        matches = api.get_odds_for_sport('soccer_epl')
        self.assertTrue(matches, 'No demo matches returned')
        match = matches[0]
        best_odds = api._get_best_odds(
            match['bookmakers'], match['home_team'], match['away_team']
        )
        self.assertIsNotNone(best_odds)
        self.assertGreater(best_odds['home'], 0)
        self.assertGreater(best_odds['away'], 0)

if __name__ == '__main__':
    unittest.main()
