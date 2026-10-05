"""Unit tests for AIAdvisor."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from src.ai_advisor import AIAdvisor


def test_ai_advisor_availability():
    advisor_no_key = AIAdvisor(api_key="")
    assert advisor_no_key.is_available is False
    assert advisor_no_key.generate("test") is None

    advisor_with_key = AIAdvisor(api_key="mock-key")
    assert advisor_with_key.is_available is True


def test_ai_advisor_generate_mock():
    advisor = AIAdvisor(api_key="mock-key")

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "candidates": [
            {
                "content": {
                    "parts": [{"text": "Actionable feedback analysis."}]
                }
            }
        ]
    }

    with patch("httpx.Client.post", return_value=mock_resp):
        res = advisor.generate("Explain review")
        assert res == "Actionable feedback analysis."


def test_ai_advisor_analyze_review():
    advisor = AIAdvisor(api_key="mock-key")

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "candidates": [
            {
                "content": {
                    "parts": [{"text": "1. Remove redundant test fixture."}]
                }
            }
        ]
    }

    with patch("httpx.Client.post", return_value=mock_resp):
        analysis = advisor.analyze_review_feedback(
            repo="org/repo",
            pr_number=123,
            title="Fix bug",
            review_decision="CHANGES_REQUESTED",
            review_comments=["Please remove this extra test file."],
        )
        assert analysis is not None
        assert "Remove redundant test fixture" in analysis
