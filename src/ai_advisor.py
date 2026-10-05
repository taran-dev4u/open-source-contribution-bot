"""Cloud AI Advisor leveraging Google Gemini for open-source analysis."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from src.config import config

logger = logging.getLogger(__name__)

DEFAULT_MODELS = [
    "gemini-flash-latest",
    "gemini-2.5-flash-lite",
    "gemini-pro-latest",
]


class AIAdvisor:
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key if api_key is not None else config.gemini_api_key

    @property
    def is_available(self) -> bool:
        return bool(self.api_key)

    def generate(self, prompt: str, system_instruction: str | None = None) -> str | None:
        """Query Gemini API with automatic model fallback."""
        if not self.is_available:
            logger.debug("Gemini API key not configured; skipping AI generation.")
            return None

        payload: dict[str, Any] = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.2,
                "maxOutputTokens": 1024,
            },
        }
        if system_instruction:
            payload["systemInstruction"] = {
                "parts": [{"text": system_instruction}]
            }

        for model in DEFAULT_MODELS:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.api_key}"
            try:
                with httpx.Client(timeout=25.0) as client:
                    resp = client.post(url, json=payload)
                    if resp.status_code == 200:
                        data = resp.json()
                        candidates = data.get("candidates", [])
                        if candidates:
                            parts = candidates[0].get("content", {}).get("parts", [])
                            if parts:
                                return parts[0].get("text", "").strip()
                    elif resp.status_code in (404, 503):
                        logger.warning("Model %s returned HTTP %d, falling back...", model, resp.status_code)
                        continue
                    else:
                        logger.warning("Gemini API error (%s): %s", model, resp.text[:200])
            except Exception as exc:
                logger.warning("Gemini request failed for model %s: %s", model, exc)

        return None

    def analyze_review_feedback(
        self,
        repo: str,
        pr_number: int,
        title: str,
        review_decision: str,
        review_comments: list[str],
    ) -> str | None:
        """Synthesize maintainer feedback into a concise, human-standard remediation action."""
        if not review_comments:
            return None

        joined_comments = "\n---\n".join(review_comments[-5:])
        system_instruction = (
            "You are a principal software engineer advising an open-source contributor. "
            "Write concise, direct, authentic developer notes. Do not use marketing adjectives, "
            "rigid templates, emojis, or corporate filler."
        )
        prompt = (
            f"Repository: {repo}\n"
            f"Pull Request #{pr_number}: {title}\n"
            f"Review Decision: {review_decision}\n"
            f"Maintainer Comments:\n{joined_comments}\n\n"
            "Provide:\n"
            "1. Core issue/request raised by the maintainer (1-2 sentences).\n"
            "2. Minimal code/test modification required.\n"
            "3. Natural 1-2 sentence developer reply draft."
        )
        return self.generate(prompt, system_instruction=system_instruction)

    def evaluate_candidate_issue(
        self,
        repo: str,
        issue_number: int,
        title: str,
        body: str,
    ) -> str | None:
        """Evaluate an uncontested issue for feasibility and recruiter profile value."""
        system_instruction = (
            "You are a staff engineer evaluating open-source issues. Be terse and technical."
        )
        prompt = (
            f"Repository: {repo}\n"
            f"Issue #{issue_number}: {title}\n"
            f"Description:\n{body[:1500]}\n\n"
            "Briefly evaluate:\n"
            "1. Technical substance (low/medium/high) and why.\n"
            "2. Expected files to touch.\n"
            "3. Feasibility of a focused, non-disruptive fix."
        )
        return self.generate(prompt, system_instruction=system_instruction)
