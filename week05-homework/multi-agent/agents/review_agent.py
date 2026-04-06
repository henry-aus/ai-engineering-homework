"""Review Agent implementation."""

import json
from typing import Dict, Any

from .base import BaseAgent
from ..prompts.review_prompts import (
    REVIEW_SYSTEM_PROMPT,
    REVIEW_USER_PROMPT_TEMPLATE,
    REVIEW_RETRY_PROMPT_TEMPLATE
)
from ..utils.terminal import ui


class ReviewAgent(BaseAgent):
    """Agent responsible for reviewing the article draft."""

    def __init__(self, temperature: float = 0.5):
        super().__init__(name="Review Agent", temperature=temperature)

    def get_system_prompt(self, state: Dict[str, Any]) -> str:
        """Get system prompt for review agent."""
        return REVIEW_SYSTEM_PROMPT

    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Review the article draft.

        Args:
            state: Current article state with draft_article

        Returns:
            State updates with review_feedback
        """
        topic = state["topic"]
        article = state.get("draft_article", "")
        retry_level = state.get("retry_level", 0)

        # Check if this is a retry
        if retry_level > 0:
            rejection_reason = state.get("hitl_feedback", "Review not thorough enough")

            user_prompt = REVIEW_RETRY_PROMPT_TEMPLATE.format(
                rejection_reason=rejection_reason,
                article=article
            )
        else:
            user_prompt = REVIEW_USER_PROMPT_TEMPLATE.format(
                topic=topic,
                article=article
            )

        ui.show_agent_thinking("Analyzing article quality...")

        # Generate review
        review_text = self.invoke_llm(user_prompt, REVIEW_SYSTEM_PROMPT)

        # Parse review feedback
        review_feedback = self._parse_review(review_text)

        # Show summary
        ui.show_review_summary(review_feedback)

        return {
            "review_feedback": review_feedback
        }

    def _parse_review(self, review_text: str) -> Dict[str, Any]:
        """Parse review feedback from LLM response.

        Args:
            review_text: Raw review text

        Returns:
            Structured review feedback
        """
        # Try to extract JSON
        try:
            start = review_text.find('{')
            end = review_text.rfind('}') + 1

            if start >= 0 and end > start:
                json_str = review_text[start:end]
                data = json.loads(json_str)

                # Validate structure
                if 'overall_score' in data:
                    return self._normalize_review(data)

        except (json.JSONDecodeError, ValueError):
            pass

        # Fallback: create structured review from text
        return self._create_fallback_review(review_text)

    def _normalize_review(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize review data structure.

        Args:
            data: Parsed review data

        Returns:
            Normalized review feedback
        """
        return {
            "overall_score": data.get("overall_score", 75),
            "dimension_scores": data.get("dimension_scores", {}),
            "issues": data.get("issues", []),
            "strengths": data.get("strengths", []),
            "recommendation": data.get("recommendation", "minor_revisions")
        }

    def _create_fallback_review(self, review_text: str) -> Dict[str, Any]:
        """Create fallback review if JSON parsing fails.

        Args:
            review_text: Raw review text

        Returns:
            Basic review feedback
        """
        # Analyze text for positive/negative indicators
        positive_words = ["good", "well", "excellent", "strong", "clear"]
        negative_words = ["weak", "unclear", "poor", "missing", "needs"]

        pos_count = sum(1 for word in positive_words if word in review_text.lower())
        neg_count = sum(1 for word in negative_words if word in review_text.lower())

        # Calculate rough score
        score = 75 + (pos_count * 5) - (neg_count * 5)
        score = max(60, min(95, score))

        return {
            "overall_score": score,
            "dimension_scores": {
                "content_quality": score,
                "structure_logic": score - 5,
                "writing_quality": score + 5,
                "citations": score,
                "engagement": score
            },
            "issues": [
                {
                    "type": "general",
                    "severity": "medium",
                    "location": "Overall",
                    "description": "Review generated as text analysis",
                    "suggestion": review_text[:200]
                }
            ],
            "strengths": ["Article reviewed"],
            "recommendation": "minor_revisions" if score >= 70 else "major_revisions"
        }

    def _get_result_summary(self, result: Dict[str, Any]) -> str:
        """Generate result summary."""
        feedback = result.get("review_feedback", {})
        score = feedback.get("overall_score", 0)
        num_issues = len(feedback.get("issues", []))
        recommendation = feedback.get("recommendation", "unknown")

        return f"Score: {score}/100, Issues: {num_issues}, Recommendation: {recommendation}"
