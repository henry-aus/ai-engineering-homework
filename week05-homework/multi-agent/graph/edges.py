"""Conditional edge routing logic for the workflow."""

from typing import Literal

from .state import ArticleState


def route_after_research_hitl(
    state: ArticleState
) -> Literal["writing", "retry_handler"]:
    """Route after research HITL checkpoint.

    Args:
        state: Current state

    Returns:
        Next node name
    """
    if state.get("hitl_approval"):
        return "writing"
    else:
        return "retry_handler"


def route_after_writing_hitl(
    state: ArticleState
) -> Literal["review", "retry_handler"]:
    """Route after writing HITL checkpoint.

    Args:
        state: Current state

    Returns:
        Next node name
    """
    if state.get("hitl_approval"):
        return "review"
    else:
        return "retry_handler"


def route_after_review_hitl(
    state: ArticleState
) -> Literal["polishing", "retry_handler"]:
    """Route after review HITL checkpoint.

    Args:
        state: Current state

    Returns:
        Next node name
    """
    if state.get("hitl_approval"):
        return "polishing"
    else:
        return "retry_handler"


def route_after_retry(
    state: ArticleState
) -> Literal["research", "writing", "review", "polishing", "finalize"]:
    """Route after retry handler based on which agent was retried.

    Args:
        state: Current state

    Returns:
        Next node name (back to the failed agent)
    """
    current_agent = state.get("current_agent", "")
    retry_level = state.get("retry_level", 0)

    # Map agent names to node names
    agent_to_node = {
        "Research Agent": "research",
        "Deep Research Agent (Backup)": "research",
        "Writing Agent": "writing",
        "Structured Writing Agent (Backup)": "writing",
        "Review Agent": "review",
        "Strict Review Agent (Backup)": "review",
        "Polishing Agent": "polishing",
        "Professional Polishing Agent (Backup)": "polishing",
    }

    # Check if max retries exceeded (completed flag set)
    if state.get("completed"):
        return "finalize"

    # Route back to the appropriate agent node
    next_node = agent_to_node.get(current_agent, "finalize")
    return next_node
