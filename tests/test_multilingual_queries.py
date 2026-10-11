"""
Unit tests for resolve_multilingual_queries.
Tests both heuristic dictionary path (no client/key) and mocked Gemini LLM path.
"""
import json
from unittest.mock import MagicMock, patch
import pytest
import dev_pipeline
from dev_pipeline import resolve_multilingual_queries


def test_resolve_multilingual_queries_heuristic_fallback():
    with patch("dev_pipeline.get_client", side_effect=ValueError("No API key configured")):
        # Indonesian topic using known dictionary term
        res = resolve_multilingual_queries("Persepsi wicara dalam komunikasi", lang="id")
        assert "speech perception" in res["global"].lower()
        assert res["regional"] == "Persepsi wicara dalam komunikasi"
        assert res["is_indonesian"] is True

        # English topic
        res_en = resolve_multilingual_queries("quantum computing algorithms", lang="en")
        assert res_en["global"] == "quantum computing algorithms"
        assert res_en["regional"] == "quantum computing algorithms"
        assert res_en["is_indonesian"] is False


def test_resolve_multilingual_queries_mocked_llm():
    mock_client = MagicMock()
    mock_resp = MagicMock()
    mock_resp.text = json.dumps({
        "global_stem": "speech perception phonetic tokens",
        "regional": "Persepsi wicara",
        "is_indonesian": True
    })
    mock_client.models.generate_content.return_value = mock_resp
    dev_pipeline.set_client(mock_client)

    res = resolve_multilingual_queries("Persepsi wicara", lang="id")
    assert res["global"] == "speech perception phonetic tokens"
    assert res["regional"] == "Persepsi wicara"
    assert res["is_indonesian"] is True


def test_resolve_multilingual_queries_mocked_llm_json_error():
    mock_client = MagicMock()
    mock_resp = MagicMock()
    mock_resp.text = "NOT JSON OUTPUT"
    mock_client.models.generate_content.return_value = mock_resp
    dev_pipeline.set_client(mock_client)

    # Should not crash; gracefully fall back to heuristic dictionary
    res = resolve_multilingual_queries("persepsi wicara", lang="id")
    assert "speech perception" in res["global"].lower()
    assert res["is_indonesian"] is True
