"""Reverse-sandhi candidates and Chanda.identify_with_sandhi."""

from backend.core.sandhi_rules import gen_candidates

GITA_2_47 = "कर्मण्येवाधिकारस्ते मा फलेषु कदाचन"


def test_identity_candidate_ranks_first():
    candidates = gen_candidates("कर्मण्येवाधिकारस्ते", k=3)
    assert candidates[0]["cand"] == "कर्मण्येवाधिकारस्ते"
    assert candidates[0]["rules"] == ["identity"]
    assert [c["score"] for c in candidates] == sorted((c["score"] for c in candidates), reverse=True)


def test_long_vowel_split_is_offered():
    rules = [rule for c in gen_candidates("कर्मण्येवाधिकारस्ते", k=5) for rule in c["rules"]]
    assert "savarṇa-dīrgha (ā split)" in rules


def test_identify_with_sandhi_uses_the_rules(chanda):
    result = chanda.identify_with_sandhi(GITA_2_47)

    assert result["sandhi_available"] is True
    assert result["sandhi_original"] == GITA_2_47
    assert result["sandhi_best"]["meter_confidence"] == 10.0
    assert "अनुष्टुभ्" in result["display_chanda_primary"]


def test_identify_text_route_passes_enable_sandhi(client):
    resp = client.post("/api/identify/text", json={"text": GITA_2_47, "enable_sandhi": True})
    line = resp.get_json()["result"]["line"][0]["result"]
    assert line["sandhi_available"] is True
