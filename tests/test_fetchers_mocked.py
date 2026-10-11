"""
Unit tests for all 6 scholarly source fetchers with canned responses and failure modes.
Mocks urllib and request_with_retry to guarantee zero network calls.
"""
import json
import urllib.error
from unittest.mock import MagicMock, patch
import pytest

from dev_pipeline import (
    fetch_arxiv_papers,
    fetch_crossref_papers,
    fetch_semantic_scholar_papers,
    fetch_openalex_works,
    fetch_pubmed_works,
    fetch_wikipedia_summary,
)


def make_mock_response(data_dict: dict) -> MagicMock:
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps(data_dict).encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp
    return mock_resp


# ------------------------------------------------------------------------------
# 1. arXiv Fetcher
# ------------------------------------------------------------------------------

def test_fetch_arxiv_papers_success():
    canned_data = {
        "results": [
            {
                "title": "Categorical Speech Perception in Neural Networks",
                "authorships": [{"author": {"display_name": "Alice Smith"}}],
                "ids": {"arxiv": "2301.00001"},
                "publication_year": 2023,
                "abstract_inverted_index": {"Speech": [0], "perception": [1]}
            }
        ]
    }
    with patch("dev_pipeline.request_with_retry", return_value=make_mock_response(canned_data)):
        results = fetch_arxiv_papers("speech perception")
        assert len(results) == 1
        assert results[0]["title"] == "Categorical Speech Perception in Neural Networks"
        assert "Alice Smith" in results[0]["authors"]
        assert results[0]["abstract"] == "Speech perception"


def test_fetch_arxiv_papers_failure():
    # Both primary and fallback fail
    err = urllib.error.URLError("Connection refused")
    with patch("dev_pipeline.request_with_retry", side_effect=err):
        results = fetch_arxiv_papers("speech perception")
        assert results == []


# ------------------------------------------------------------------------------
# 2. Crossref Fetcher
# ------------------------------------------------------------------------------

def test_fetch_crossref_papers_success():
    canned_data = {
        "message": {
            "items": [
                {
                    "title": ["Acoustic Properties of Vowels"],
                    "author": [{"given": "John", "family": "Peterson"}],
                    "DOI": "10.1121/1.12345",
                    "publisher": "Acoustical Society of America",
                    "created": {"date-parts": [[1952]]}
                }
            ]
        }
    }
    with patch("dev_pipeline.request_with_retry", return_value=make_mock_response(canned_data)):
        results = fetch_crossref_papers("vowels")
        assert len(results) == 1
        assert results[0]["title"] == "Acoustic Properties of Vowels"
        assert "John Peterson" in results[0]["authors"]
        assert "10.1121/1.12345" in results[0]["url"]


def test_fetch_crossref_papers_failure():
    err = urllib.error.HTTPError("https://api.crossref.org", 500, "Internal Server Error", None, None)
    with patch("dev_pipeline.request_with_retry", side_effect=err):
        results = fetch_crossref_papers("vowels")
        assert results == []


# ------------------------------------------------------------------------------
# 3. Semantic Scholar Fetcher
# ------------------------------------------------------------------------------

def test_fetch_semantic_scholar_papers_success():
    canned_data = {
        "data": [
            {
                "title": "Speech Processing in Cortical Hierarchies",
                "authors": [{"name": "David Poeppel"}],
                "year": 2020,
                "citationCount": 450,
                "paperId": "abc12345",
                "abstract": "Cortical oscillations support phonetic encoding."
            }
        ]
    }
    with patch("dev_pipeline.request_with_retry", return_value=make_mock_response(canned_data)):
        results = fetch_semantic_scholar_papers("speech cortical")
        assert len(results) == 1
        assert results[0]["title"] == "Speech Processing in Cortical Hierarchies"
        assert results[0]["citations"] == 450
        assert results[0]["abstract"] == "Cortical oscillations support phonetic encoding."


def test_fetch_semantic_scholar_papers_failure():
    err = TimeoutError("Request timed out")
    with patch("dev_pipeline.request_with_retry", side_effect=err):
        results = fetch_semantic_scholar_papers("speech cortical")
        assert results == []


# ------------------------------------------------------------------------------
# 4. OpenAlex Works Fetcher
# ------------------------------------------------------------------------------

def test_fetch_openalex_works_success():
    canned_data = {
        "results": [
            {
                "title": "Auditory Cortex Receptive Fields",
                "authorships": [{"author": {"display_name": "E. Chang"}}],
                "primary_location": {"source": {"display_name": "Nature Neuroscience"}},
                "publication_year": 2021,
                "doi": "https://doi.org/10.1038/s41593-021",
                "abstract_inverted_index": {"Receptive": [0], "fields": [1]}
            }
        ]
    }
    with patch("dev_pipeline.request_with_retry", return_value=make_mock_response(canned_data)):
        results = fetch_openalex_works("auditory cortex")
        assert len(results) >= 1
        assert results[0]["title"] == "Auditory Cortex Receptive Fields"
        assert results[0]["venue"] == "Nature Neuroscience"


def test_fetch_openalex_works_failure():
    err = urllib.error.URLError("DNS lookup failed")
    with patch("dev_pipeline.request_with_retry", side_effect=err):
        results = fetch_openalex_works("auditory cortex")
        assert results == []


# ------------------------------------------------------------------------------
# 5. PubMed Works Fetcher
# ------------------------------------------------------------------------------

def test_fetch_pubmed_works_success():
    canned_europepmc = {
        "resultList": {
            "result": [
                {
                    "title": "Neural bases of speech sound discrimination",
                    "authorString": "Kraus N, McGee T",
                    "pubYear": "1996",
                    "pmcid": "PMC21456",
                    "abstractText": "Auditory evoked potentials reveal phonetic processing."
                }
            ]
        }
    }
    with patch("dev_pipeline.request_with_retry", return_value=make_mock_response(canned_europepmc)):
        results = fetch_pubmed_works("speech discrimination")
        assert len(results) == 1
        assert results[0]["title"] == "Neural bases of speech sound discrimination"
        assert "PMC21456" in results[0]["url"]


def test_fetch_pubmed_works_failure():
    err = urllib.error.HTTPError("https://eutils.ncbi.nlm.nih.gov", 503, "Service Unavailable", None, None)
    with patch("dev_pipeline.request_with_retry", side_effect=err):
        results = fetch_pubmed_works("speech discrimination")
        assert results == []


# ------------------------------------------------------------------------------
# 6. Wikipedia Summary Fetcher
# ------------------------------------------------------------------------------

def test_fetch_wikipedia_summary_success():
    search_hit = {
        "query": {
            "search": [{"title": "Speech perception"}]
        }
    }
    summary_data = {
        "extract": "Speech perception is the process by which the sounds of language are heard, interpreted, and understood.",
        "content_urls": {
            "desktop": {
                "page": "https://en.wikipedia.org/wiki/Speech_perception"
            }
        }
    }

    mock_resp1 = make_mock_response(search_hit)
    mock_resp2 = make_mock_response(summary_data)

    with patch("dev_pipeline.request_with_retry", side_effect=[mock_resp1, mock_resp2]):
        results = fetch_wikipedia_summary("Speech perception", lang="en")
        assert len(results) == 1
        assert results[0]["title"] == "Speech perception"
        assert "Speech perception is the process" in results[0]["extract"]


def test_fetch_wikipedia_summary_failure():
    err = TimeoutError("Wikipedia API timed out")
    with patch("dev_pipeline.request_with_retry", side_effect=err):
        results = fetch_wikipedia_summary("Speech perception", lang="en")
        assert results == []
