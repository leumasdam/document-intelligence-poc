"""Unit tests for the heuristic case classifier (no API key required)."""
from app.classifier import classify_heuristic
from app.samples import SAMPLE_CASES


def test_vehicle_damage_is_routed_to_motor_team():
    c = classify_heuristic("Mal som dopravnu nehodu, naraznik je poskodeny.")
    assert c.category == "vehicle_damage"
    assert c.route_to == "Motor Claims Team"


def test_regulatory_threat_forces_high_priority():
    c = classify_heuristic(
        "Uz druhy mesiac cakam na plnenie. Obratim sa na NBS a obchodnu inspekciu."
    )
    assert c.priority == "high"


def test_address_change_is_document_update_not_vehicle():
    # 'PZP' (a motor-policy code) appears, but the strong phrase wins.
    c = classify_heuristic(
        "Oznamujem zmenu adresy. Tyka sa zmluvy PZP-22 33 44 55."
    )
    assert c.category == "document_update"
    assert c.priority == "low"


def test_policy_question_is_low_priority():
    c = classify_heuristic("Uvazujem o cestovnom poisteni, mam otazku.")
    assert c.category == "policy_question"
    assert c.priority == "low"


def test_unmatched_text_falls_back_to_other():
    c = classify_heuristic("Kedy mate otvorene pobocku?")
    assert c.category in {"other", "policy_question"}
    assert 0.0 <= c.confidence <= 1.0


def test_all_sample_cases_classify_without_error():
    for kind, data in SAMPLE_CASES.items():
        c = classify_heuristic(data["body"])
        assert c.category
        assert c.priority in {"high", "medium", "low"}
        assert c.route_to
        assert len(c.suggested_actions) >= 1
