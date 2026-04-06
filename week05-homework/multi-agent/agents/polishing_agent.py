"""Polishing Agent implementation."""

from typing import Dict, Any

from .base import BaseAgent
from ..prompts.polishing_prompts import (
    POLISHING_SYSTEM_PROMPT,
    POLISHING_USER_PROMPT_TEMPLATE,
    POLISHING_RETRY_PROMPT_TEMPLATE
)
from ..utils.terminal import ui


class PolishingAgent(BaseAgent):
    """Agent responsible for final article polishing."""

    def __init__(self, temperature: float = 0.5):
        super().__init__(name="Polishing Agent", temperature=temperature)

    def get_system_prompt(self, state: Dict[str, Any]) -> str:
        """Get system prompt for polishing agent."""
        return POLISHING_SYSTEM_PROMPT

    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Polish the article based on review feedback.

        Args:
            state: Current article state with draft_article and review_feedback

        Returns:
            State updates with final_article
        """
        article = state.get("draft_article", "")
        review_feedback = state.get("review_feedback", {})
        retry_level = state.get("retry_level", 0)

        # Extract review information
        overall_score = review_feedback.get("overall_score", 75)
        issues = review_feedback.get("issues", [])
        strengths = review_feedback.get("strengths", [])

        # Format issues for prompt
        issues_summary = self._format_issues(issues)
        strengths_text = "\n".join([f"- {s}" for s in strengths])

        # Check if this is a retry
        if retry_level > 0:
            rejection_reason = state.get("hitl_feedback", "Polishing insufficient")
            review_summary = f"Score: {overall_score}/100\n{issues_summary}"

            user_prompt = POLISHING_RETRY_PROMPT_TEMPLATE.format(
                rejection_reason=rejection_reason,
                article=article,
                review_summary=review_summary
            )
        else:
            user_prompt = POLISHING_USER_PROMPT_TEMPLATE.format(
                article=article,
                overall_score=overall_score,
                num_issues=len(issues),
                issues_summary=issues_summary,
                strengths=strengths_text
            )

        ui.show_agent_thinking("Polishing article...")
        ui.show_agent_thinking("Addressing review feedback...")

        # Generate polished article
        polished_article = self.invoke_llm(user_prompt, POLISHING_SYSTEM_PROMPT)

        # Clean up the polished article
        polished_article = self._clean_article(polished_article)

        ui.show_agent_thinking(f"Final article: {len(polished_article.split())} words")

        return {
            "final_article": polished_article,
            "completed": True
        }

    def _format_issues(self, issues: list) -> str:
        """Format issues for the prompt.

        Args:
            issues: List of issue dictionaries

        Returns:
            Formatted issues string
        """
        if not issues:
            return "No major issues identified."

        formatted = []
        for i, issue in enumerate(issues[:15], 1):  # Limit to top 15
            formatted.append(
                f"{i}. [{issue.get('severity', 'medium').upper()}] "
                f"{issue.get('type', 'unknown')}: "
                f"{issue.get('description', 'N/A')}\n"
                f"   Location: {issue.get('location', 'N/A')}\n"
                f"   Suggestion: {issue.get('suggestion', 'N/A')}"
            )

        return "\n\n".join(formatted)

    def _clean_article(self, article: str) -> str:
        """Clean up the polished article.

        Args:
            article: Raw article text

        Returns:
            Cleaned article
        """
        # Remove code block markers
        article = article.replace('```markdown', '').replace('```', '')

        # Remove any JSON artifacts
        if article.strip().startswith('{'):
            # This shouldn't happen for polishing, but just in case
            lines = article.split('\n')
            # Find the first non-JSON line
            for i, line in enumerate(lines):
                if line.strip() and line.strip()[0] == '#':
                    article = '\n'.join(lines[i:])
                    break

        # Ensure proper spacing
        lines = article.split('\n')
        cleaned_lines = []
        prev_empty = False

        for line in lines:
            stripped = line.strip()

            # Remove excessive empty lines
            if not stripped:
                if not prev_empty:
                    cleaned_lines.append('')
                    prev_empty = True
            else:
                cleaned_lines.append(line)
                prev_empty = False

        # Ensure article starts with a title
        cleaned = '\n'.join(cleaned_lines).strip()

        # If doesn't start with #, add a simple title
        if not cleaned.startswith('#'):
            cleaned = "# Article\n\n" + cleaned

        return cleaned

    def _get_result_summary(self, result: Dict[str, Any]) -> str:
        """Generate result summary."""
        article = result.get("final_article", "")
        word_count = len(article.split())

        return f"Final polished article ({word_count} words)"
