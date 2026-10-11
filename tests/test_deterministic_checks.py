"""
Unit tests for run_deterministic_checks.
Requires no network or API keys.
"""
import pytest
from dev_pipeline import run_deterministic_checks


def test_deterministic_checks_clean_draft():
    draft = """# Language Processing
According to experimental findings, "the left hemisphere processes phonetic transitions reliably" [1].

## References
[1] Liberman, A. M. (1967). Some results on speech perception. https://doi.org/10.1121/1.1910402
"""
    dossier = "Some results on speech perception: the left hemisphere processes phonetic transitions reliably in lab conditions."
    result = run_deterministic_checks(draft, dossier)
    assert result["passed"] is True
    assert result["has_issues"] is False
    assert result["in_text_count"] == 1
    assert result["ref_count"] == 1
    assert result["quote_count"] == 1
    assert result["verified_quotes_count"] == 1


def test_deterministic_checks_missing_reference_entry():
    draft = """# Speech Findings
Recent work reports that "acoustic cues guide lexical access" [1]. Furthermore, syntax is engaged early [2].

## References
[1] Cutler, A. (2012). Native Listening. MIT Press.
"""
    result = run_deterministic_checks(draft)
    assert result["passed"] is False
    assert result["has_issues"] is True
    assert any("In-text citation numbers missing in references" in issue for issue in result["issues"])
    assert "[2]" in str(result["issues"])


def test_deterministic_checks_no_verbatim_quotes():
    draft = """# Speech Overview
Speech perception is complex and involves multiple brain regions [1].

## References
[1] Hickok & Poeppel (2007). Nature Reviews Neuroscience.
"""
    result = run_deterministic_checks(draft)
    assert result["passed"] is False
    assert any("No verbatim quotes" in issue for issue in result["issues"])


def test_deterministic_checks_causal_verb_flag():
    # English causal verb near citation
    draft_en = """# Speech Model
Empirical data proves [1] that rapid speech causes syntactic failure. "Processing is acoustic" [1].

## References
[1] Smith (2020).
"""
    result_en = run_deterministic_checks(draft_en)
    assert result_en["passed"] is False
    assert any("causal verb" in issue.lower() or "verb ladder" in issue.lower() for issue in result_en["issues"])

    # Indonesian causal verb near citation
    draft_id = """# Model Wicara
Hasil survei membuktikan [1] bahwa kecepatan wicara memicu respons saraf. "Pemrosesan bersifat akustik" [1].

## Referensi
[1] Suryadi (2021).
"""
    result_id = run_deterministic_checks(draft_id)
    assert result_id["passed"] is False
    assert any("causal verb" in issue.lower() or "verb ladder" in issue.lower() for issue in result_id["issues"])
