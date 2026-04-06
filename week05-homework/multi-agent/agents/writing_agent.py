"""Writing Agent implementation."""

import json
from typing import Dict, Any

from .base import BaseAgent
from ..prompts.writing_prompts import (
    WRITING_SYSTEM_PROMPT,
    WRITING_USER_PROMPT_TEMPLATE,
    WRITING_RETRY_PROMPT_TEMPLATE
)
from ..utils.terminal import ui


class WritingAgent(BaseAgent):
    """Agent responsible for writing the article draft."""

    def __init__(self, temperature: float = 0.7):
        super().__init__(name="Writing Agent", temperature=temperature)

    def get_system_prompt(self, state: Dict[str, Any]) -> str:
        """Get system prompt for writing agent."""
        return WRITING_SYSTEM_PROMPT

    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Write article draft based on research.

        Args:
            state: Current article state with research_data

        Returns:
            State updates with draft_article
        """
        topic = state["topic"]
        research_data = state.get("research_data", {})
        requirements = state.get("user_requirements", {})
        retry_level = state.get("retry_level", 0)

        # Get style and word count
        style = requirements.get("style", self.config.article_style)
        target_word_count = requirements.get("word_count", self.config.target_word_count)

        # Prepare research summary
        research_summary = self._format_research_summary(research_data)
        key_points = "\n".join([f"- {kp}" for kp in research_data.get("key_points", [])[:10]])

        # Check if this is a retry
        if retry_level > 0:
            rejection_reason = state.get("hitl_feedback", "Draft needs improvement")

            user_prompt = WRITING_RETRY_PROMPT_TEMPLATE.format(
                topic=topic,
                rejection_reason=rejection_reason,
                feedback=state.get("hitl_feedback", ""),
                research_summary=research_summary
            )
        else:
            user_prompt = WRITING_USER_PROMPT_TEMPLATE.format(
                topic=topic,
                style=style,
                target_word_count=target_word_count,
                research_summary=research_summary,
                key_points=key_points
            )

        ui.show_agent_thinking("Drafting article structure...")

        # Generate article
        article = self.invoke_llm(user_prompt, WRITING_SYSTEM_PROMPT)

        # Clean up the article
        article = self._clean_article(article)

        # Show preview
        ui.show_draft_preview(article)

        return {
            "draft_article": article
        }

    def _format_research_summary(self, research_data: Dict[str, Any]) -> str:
        """Format research data for the writing prompt.

        Args:
            research_data: Research results

        Returns:
            Formatted summary string
        """
        sources = research_data.get("sources", [])
        key_points = research_data.get("key_points", [])
        statistics = research_data.get("statistics", [])

        summary = f"Sources ({len(sources)}):\n"
        for i, source in enumerate(sources[:7], 1):
            summary += f"{i}. {source.get('title', 'Unknown')}\n"
            summary += f"   {source.get('content', '')[:200]}...\n\n"

        summary += f"\nKey Points:\n"
        for point in key_points:
            summary += f"- {point}\n"

        if statistics:
            summary += f"\nStatistics:\n"
            for stat in statistics:
                summary += f"- {stat.get('stat', '')}: {stat.get('source', '')}\n"

        return summary

    def _clean_article(self, article: str) -> str:
        """Clean up the article text.

        Args:
            article: Raw article text

        Returns:
            Cleaned article
        """
        # Remove any JSON artifacts
        if article.strip().startswith('{'):
            # Try to extract article from JSON
            try:
                data = json.loads(article)
                if 'article' in data:
                    article = data['article']
            except:
                pass

        # Remove code block markers if present
        article = article.replace('```markdown', '').replace('```', '')

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

        return '\n'.join(cleaned_lines).strip()

    def _get_result_summary(self, result: Dict[str, Any]) -> str:
        """Generate result summary."""
        article = result.get("draft_article", "")
        word_count = len(article.split())

        return f"Generated article draft ({word_count} words)"
