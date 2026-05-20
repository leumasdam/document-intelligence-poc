"""Unit tests for the heuristic summarizer (no API key required)."""
from app.samples import SAMPLE_NARRATIVES
from app.summarizer import _split_sentences, summarize_heuristic


def test_split_sentences_drops_thread_separators():
    text = "--- Reply, 6.5.2026 ---\nThis is a real sentence that is long enough."
    sentences = _split_sentences(text)
    assert all("---" not in s for s in sentences)
    assert len(sentences) >= 1


def test_angry_sentiment_on_legal_threat():
    s = summarize_heuristic(
        "Zasadne nesuhlasim s vasim postupom. Obratim sa na ombudsmana "
        "a Narodnu banku Slovenska a zvazujem pravne kroky."
    )
    assert s.sentiment == "angry"


def test_summary_has_all_parts():
    s = summarize_heuristic(SAMPLE_NARRATIVES["property"]["body"])
    assert len(s.executive_summary) > 20
    assert len(s.key_facts) >= 1
    assert len(s.suggested_action) > 10
    assert len(s.customer_response_draft) > 40
    assert s.sentiment in {"satisfied", "neutral", "frustrated", "angry"}


def test_response_draft_language_matches_input():
    sk = summarize_heuristic("Dobry den, prosim vas o pomoc podla zmluvy. Dakujem.")
    assert sk.detected_language == "sk"
    assert "Dobr" in sk.customer_response_draft


def test_all_sample_narratives_summarize_without_error():
    for kind, data in SAMPLE_NARRATIVES.items():
        s = summarize_heuristic(data["body"])
        assert s.executive_summary
        assert s.customer_response_draft
