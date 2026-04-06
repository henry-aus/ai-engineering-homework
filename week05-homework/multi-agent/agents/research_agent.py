"""Research Agent implementation."""

import json
from typing import Dict, Any
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

from .base import BaseAgent
from ..tools.tavily_search import get_search_tool
from ..prompts.research_prompts import (
    RESEARCH_SYSTEM_PROMPT,
    RESEARCH_USER_PROMPT_TEMPLATE,
    RESEARCH_RETRY_PROMPT_TEMPLATE
)
from ..utils.terminal import ui


class ResearchAgent(BaseAgent):
    """Agent responsible for researching the article topic."""

    def __init__(self, temperature: float = 0.7):
        super().__init__(name="Research Agent", temperature=temperature)

        # Bind search tool
        search_tool = get_search_tool()
        self.llm_with_tools = self.llm.bind_tools([search_tool.as_langchain_tool()])

    def get_system_prompt(self, state: Dict[str, Any]) -> str:
        """Get system prompt for research agent."""
        return RESEARCH_SYSTEM_PROMPT

    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute research on the topic.

        Args:
            state: Current article state

        Returns:
            State updates with research_data
        """
        topic = state["topic"]
        requirements = state.get("user_requirements", {})
        retry_level = state.get("retry_level", 0)

        # Check if this is a retry
        if retry_level > 0:
            errors = state.get("errors", [])
            rejection_reason = state.get("hitl_feedback", "Quality insufficient")

            user_prompt = RESEARCH_RETRY_PROMPT_TEMPLATE.format(
                topic=topic,
                rejection_reason=rejection_reason,
                previous_errors="\n".join([e.get("error", "") for e in errors[-3:]])
            )
        else:
            # Format requirements
            req_text = "\n".join([f"- {k}: {v}" for k, v in requirements.items()])
            if not req_text:
                req_text = "- No specific requirements"

            user_prompt = RESEARCH_USER_PROMPT_TEMPLATE.format(
                topic=topic,
                requirements=req_text
            )

        ui.show_agent_thinking("Preparing research queries...")

        # Invoke LLM with tools
        messages = [
            SystemMessage(content=RESEARCH_SYSTEM_PROMPT),
            HumanMessage(content=user_prompt)
        ]

        # Perform research with tool calling
        research_results = self._research_with_tools(messages, topic)

        # Display results
        if research_results:
            ui.show_research_results(research_results)

        return {
            "research_data": research_results
        }

    def _research_with_tools(self, messages: list, topic: str) -> Dict[str, Any]:
        """Perform research using tools.

        Args:
            messages: Conversation messages
            topic: Research topic

        Returns:
            Structured research data
        """
        search_tool = get_search_tool()
        max_iterations = 5
        iteration = 0

        while iteration < max_iterations:
            iteration += 1

            ui.show_agent_thinking(f"Research iteration {iteration}/{max_iterations}...")

            # Invoke LLM
            response = self.llm_with_tools.invoke(messages)

            # Check if we have tool calls
            if hasattr(response, 'tool_calls') and response.tool_calls:
                # Execute tool calls
                for tool_call in response.tool_calls:
                    if tool_call['name'] == 'tavily_search':
                        query = tool_call['args'].get('query', topic)
                        max_results = tool_call['args'].get('max_results', 5)

                        ui.show_agent_thinking(f"Searching: '{query}'...")

                        # Perform search
                        results = search_tool.search(query, max_results)

                        # Add tool result to messages
                        messages.append(response)
                        messages.append(HumanMessage(
                            content=f"Search results for '{query}':\n{json.dumps(results, indent=2)}"
                        ))

            else:
                # No more tool calls, extract final response
                content = response.content

                # Try to parse JSON from the response
                research_data = self._extract_research_data(content)
                if research_data:
                    return research_data
                else:
                    # If parsing fails, create structured data from the response
                    return self._create_fallback_research_data(topic, content)

        # Max iterations reached, return what we have
        return self._create_fallback_research_data(topic, "Research completed")

    def _extract_research_data(self, content: str) -> Dict[str, Any]:
        """Extract JSON research data from LLM response.

        Args:
            content: LLM response content

        Returns:
            Parsed research data or None if parsing fails
        """
        try:
            # Try to find JSON in the content
            start = content.find('{')
            end = content.rfind('}') + 1

            if start >= 0 and end > start:
                json_str = content[start:end]
                data = json.loads(json_str)

                # Validate structure
                if 'sources' in data and 'key_points' in data:
                    return data

        except (json.JSONDecodeError, ValueError):
            pass

        return None

    def _create_fallback_research_data(self, topic: str, content: str) -> Dict[str, Any]:
        """Create fallback research data if JSON parsing fails.

        Args:
            topic: Research topic
            content: LLM response content

        Returns:
            Basic structured research data
        """
        # Perform a direct search
        search_tool = get_search_tool()
        results = search_tool.search(topic, max_results=7)

        return {
            "sources": results,
            "key_points": [
                f"Research on {topic}",
                "Multiple sources consulted",
                "Information gathered"
            ],
            "statistics": [],
            "perspectives": {
                "mainstream": ["General information found"],
                "alternative": []
            },
            "research_quality": "medium"
        }

    def _get_result_summary(self, result: Dict[str, Any]) -> str:
        """Generate result summary."""
        research_data = result.get("research_data", {})
        num_sources = len(research_data.get("sources", []))
        num_points = len(research_data.get("key_points", []))

        return f"Found {num_sources} sources, extracted {num_points} key points"
