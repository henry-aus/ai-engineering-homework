"""Tavily Search API integration."""

from typing import List, Dict, Any, Optional
from tavily import TavilyClient
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from ..config import get_config


class TavilySearchInput(BaseModel):
    """Input schema for Tavily search."""

    query: str = Field(description="The search query")
    max_results: int = Field(default=5, description="Maximum number of results to return")


class TavilySearchTool:
    """Wrapper for Tavily Search API."""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize Tavily client.

        Args:
            api_key: Optional API key (uses config if not provided)
        """
        config = get_config()
        self.client = TavilyClient(api_key=api_key or config.tavily_api_key)
        self.search_depth = config.search_depth

    def search(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Search the web using Tavily.

        Args:
            query: Search query
            max_results: Maximum number of results

        Returns:
            List of search results, each containing:
                - title: Page title
                - url: Page URL
                - content: Relevant content snippet
                - score: Relevance score
        """
        try:
            response = self.client.search(
                query=query,
                max_results=max_results,
                search_depth=self.search_depth,
                include_answer=True,
                include_raw_content=False
            )

            results = []
            for result in response.get("results", []):
                results.append({
                    "title": result.get("title", ""),
                    "url": result.get("url", ""),
                    "content": result.get("content", ""),
                    "score": result.get("score", 0.0),
                })

            # Add AI-generated answer if available
            if "answer" in response:
                results.insert(0, {
                    "title": "AI Summary",
                    "url": "",
                    "content": response["answer"],
                    "score": 1.0,
                })

            return results

        except Exception as e:
            print(f"Tavily search error: {e}")
            return []

    def as_langchain_tool(self) -> StructuredTool:
        """Convert to LangChain StructuredTool.

        Returns:
            StructuredTool for use with LangChain agents
        """
        return StructuredTool.from_function(
            func=self.search,
            name="tavily_search",
            description=(
                "Search the web for information using Tavily. "
                "Returns relevant articles, pages, and an AI-generated summary. "
                "Use this to research topics, find facts, and gather sources."
            ),
            args_schema=TavilySearchInput,
        )


# Global search tool instance
_search_tool: Optional[TavilySearchTool] = None


def get_search_tool() -> TavilySearchTool:
    """Get or create the global search tool instance.

    Returns:
        TavilySearchTool instance
    """
    global _search_tool
    if _search_tool is None:
        _search_tool = TavilySearchTool()
    return _search_tool
