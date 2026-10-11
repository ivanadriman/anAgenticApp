"""
Unit tests for reconstruct_abstract and build_text_fragment_url.
Requires no network or API keys.
"""
import pytest
from dev_pipeline import reconstruct_abstract, build_text_fragment_url, encode_fragment_token


def test_reconstruct_abstract_empty():
    assert reconstruct_abstract(None) == ""
    assert reconstruct_abstract({}) == ""
    assert reconstruct_abstract("not a dict") == ""


def test_reconstruct_abstract_valid():
    inverted_index = {
        "Speech": [0],
        "perception": [1],
        "is": [2],
        "hierarchical": [3],
        "and": [4],
        "multistage": [5]
    }
    reconstructed = reconstruct_abstract(inverted_index)
    assert reconstructed == "Speech perception is hierarchical and multistage"


def test_reconstruct_abstract_multiple_positions():
    inverted_index = {
        "the": [0, 4],
        "brain": [1],
        "processes": [2],
        "sound": [3],
        "signal": [5]
    }
    assert reconstruct_abstract(inverted_index) == "the brain processes sound the signal"


def test_encode_fragment_token():
    assert encode_fragment_token("speech") == "speech"
    assert "%2D" in encode_fragment_token("state-of-the-art")
    assert "%2C" in encode_fragment_token("words, clauses")
    assert "%26" in encode_fragment_token("research & development")


def test_build_text_fragment_url_empty_or_invalid():
    assert build_text_fragment_url("", "some quote") == ""
    assert build_text_fragment_url("#", "some quote") == "#"
    assert build_text_fragment_url("https://example.com", "") == "https://example.com"
    assert build_text_fragment_url("https://example.com", "hi") == "https://example.com"


def test_build_text_fragment_url_short_quote():
    raw_url = "http://example.com/paper"
    quote = "Categorical speech perception"
    frag_url = build_text_fragment_url(raw_url, quote)
    assert frag_url.startswith("https://example.com/paper#:~:text=")
    assert "Categorical%20speech%20perception" in frag_url or "Categorical" in frag_url
    assert "," not in frag_url.split("#:~:text=")[1]


def test_build_text_fragment_url_long_quote():
    raw_url = "https://doi.org/10.1038/nature12345"
    quote = '"The auditory cortex processes phonetic tokens through hierarchical spectral decomposition." [1]'
    frag_url = build_text_fragment_url(raw_url, quote)
    assert frag_url.startswith("https://doi.org/10.1038/nature12345#:~:text=")
    # Must have start,end format
    fragment = frag_url.split("#:~:text=")[1]
    assert "," in fragment
    assert "The%20auditory%20cortex" in fragment
    assert "hierarchical%20spectral%20decomposition" in fragment or "spectral%20decomposition" in fragment


def test_build_text_fragment_url_hyphen_encoding():
    raw_url = "https://example.com/paper"
    quote = "Labor-intensive manual evaluations are conducted across multiple cohorts."
    frag_url = build_text_fragment_url(raw_url, quote)
    # W3C text fragment directive requires '-' in words to be percent-encoded as %2D
    assert "%2D" in frag_url
    assert "Labor%2Dintensive" in frag_url
