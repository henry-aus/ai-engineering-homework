"""LangGraph workflow construction."""

from langgraph.graph import StateGraph, END
from typing import Optional

from .state import ArticleState
from .nodes import (
    initialize_node,
    research_node,
    research_hitl_node,
    writing_node,
    writing_hitl_node,
    review_node,
    review_hitl_node,
    polishing_node,
    retry_handler_node,
    finalize_node,
)
from .edges import (
    route_after_research_hitl,
    route_after_writing_hitl,
    route_after_review_hitl,
    route_after_retry,
)


def create_workflow() -> StateGraph:
    """Create the article writing workflow.

    Returns:
        Compiled StateGraph
    """
    # Create graph
    workflow = StateGraph(ArticleState)

    # Add nodes
    workflow.add_node("initialize", initialize_node)
    workflow.add_node("research", research_node)
    workflow.add_node("research_hitl", research_hitl_node)
    workflow.add_node("writing", writing_node)
    workflow.add_node("writing_hitl", writing_hitl_node)
    workflow.add_node("review", review_node)
    workflow.add_node("review_hitl", review_hitl_node)
    workflow.add_node("polishing", polishing_node)
    workflow.add_node("retry_handler", retry_handler_node)
    workflow.add_node("finalize", finalize_node)

    # Set entry point
    workflow.set_entry_point("initialize")

    # Add sequential edges
    workflow.add_edge("initialize", "research")
    workflow.add_edge("research", "research_hitl")

    # Conditional edge after research HITL
    workflow.add_conditional_edges(
        "research_hitl",
        route_after_research_hitl,
        {
            "writing": "writing",
            "retry_handler": "retry_handler",
        }
    )

    workflow.add_edge("writing", "writing_hitl")

    # Conditional edge after writing HITL
    workflow.add_conditional_edges(
        "writing_hitl",
        route_after_writing_hitl,
        {
            "review": "review",
            "retry_handler": "retry_handler",
        }
    )

    workflow.add_edge("review", "review_hitl")

    # Conditional edge after review HITL
    workflow.add_conditional_edges(
        "review_hitl",
        route_after_review_hitl,
        {
            "polishing": "polishing",
            "retry_handler": "retry_handler",
        }
    )

    workflow.add_edge("polishing", "finalize")

    # Conditional edge after retry handler
    # Routes back to the appropriate agent
    workflow.add_conditional_edges(
        "retry_handler",
        route_after_retry,
        {
            "research": "research",
            "writing": "writing",
            "review": "review",
            "polishing": "polishing",
            "finalize": "finalize",
        }
    )

    # Finalize ends the workflow
    workflow.add_edge("finalize", END)

    return workflow.compile()


# Global workflow instance
_workflow: Optional[StateGraph] = None


def get_workflow() -> StateGraph:
    """Get or create the compiled workflow.

    Returns:
        Compiled workflow
    """
    global _workflow
    if _workflow is None:
        _workflow = create_workflow()
    return _workflow
