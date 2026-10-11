"""
Unit tests for dev_pipeline Pydantic data models.
Does not require any network calls or Gemini API key.
"""
import pytest
from pydantic import ValidationError
from dev_pipeline import CritiqueResult, SourceAuditItem, SourceAuditResult


def test_critique_result_valid():
    critique = CritiqueResult(
        score=9.0,
        status="APPROVED",
        strengths=["Clear synthesis", "Good citations"],
        weaknesses=[],
        actionable_revisions=[]
    )
    assert critique.score == 9.0
    assert critique.status == "APPROVED"
    assert len(critique.strengths) == 2


def test_critique_result_serialization():
    data = {
        "score": 7.2,
        "status": "NEEDS_REVISION",
        "strengths": ["Strong opening"],
        "weaknesses": ["Missing data points"],
        "actionable_revisions": ["Expand section 2"]
    }
    critique = CritiqueResult(**data)
    dumped = critique.model_dump()
    assert dumped["score"] == 7.2
    assert dumped["status"] == "NEEDS_REVISION"


def test_critique_result_missing_fields():
    with pytest.raises(ValidationError):
        CritiqueResult(score=8.0)  # Missing status, strengths, etc.


def test_source_audit_item_valid():
    item = SourceAuditItem(
        id="layer1_source_type_appropriate",
        layer=1,
        title="Source Type Ceiling",
        question="Does source type justify claim level?",
        answer="YES",
        reason="Peer-reviewed studies support claims.",
        offending_text=""
    )
    assert item.answer == "YES"
    assert item.layer == 1
    assert item.offending_text == ""


def test_source_audit_result_valid():
    item1 = SourceAuditItem(
        id="layer1_source_type_appropriate",
        layer=1,
        title="Source Type Ceiling",
        question="Does source type justify claim level?",
        answer="YES",
        reason="Peer-reviewed source",
        offending_text=""
    )
    item2 = SourceAuditItem(
        id="layer2_verb_ladder_justified",
        layer=2,
        title="Verb Ladder Compliance",
        question="Does research design justify the verb used?",
        answer="NO",
        reason="Cross-sectional data used with causal verb",
        offending_text="directly causes performance gain"
    )

    result = SourceAuditResult(
        all_yes=False,
        overall_verdict="DISCREPANCIES_DETECTED",
        score_percentage=50.0,
        failure_patterns_detected=["Correlation-to-causation drift"],
        discrepancies=["Downgrade causal verb in item 2"],
        items=[item1, item2]
    )
    assert not result.all_yes
    assert result.overall_verdict == "DISCREPANCIES_DETECTED"
    assert result.score_percentage == 50.0
    assert len(result.items) == 2
    assert result.items[1].offending_text == "directly causes performance gain"
