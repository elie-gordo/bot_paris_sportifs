from betting_analyzer import BettingAnalyzer


def test_generate_specific_combination():
    analyzer = BettingAnalyzer()
    analyses = [
        {"match": "A vs B", "recommendation": "A wins (cote: 1.5)", "confidence": 80},
        {"match": "C vs D", "recommendation": "C wins (cote: 1.8)", "confidence": 75},
        {"match": "E vs F", "recommendation": "E wins (cote: 2.0)", "confidence": 70},
        {"match": "G vs H", "recommendation": "G wins (cote: 1.9)", "confidence": 65},
        {"match": "I vs J", "recommendation": "I wins (cote: 1.7)", "confidence": 50},
    ]

    combo = analyzer.generate_specific_combination(analyses, "MOYEN")
    assert combo is not None
    assert combo["type"] == "Combiné MOYEN ⚖️"
    assert len(combo["matches"]) == 4
    assert {"type", "matches", "total_odds", "avg_confidence", "potential_return"}.issubset(combo)
    for m in combo["matches"]:
        assert {"match", "bet", "confidence"}.issubset(m)
