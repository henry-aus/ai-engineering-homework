"""Node functions for the LangGraph workflow."""

from typing import Dict, Any
from datetime import datetime

from .state import ArticleState
from ..agents.research_agent import ResearchAgent
from ..agents.writing_agent import WritingAgent
from ..agents.review_agent import ReviewAgent
from ..agents.polishing_agent import PolishingAgent
from ..agents.backup_agents import get_backup_agent
from ..hitl.checkpoints import research_hitl, writing_hitl, review_hitl
from ..retry.strategy import get_retry_strategy
from ..utils.terminal import ui


def initialize_node(state: ArticleState) -> Dict[str, Any]:
    """Initialize the workflow.

    Args:
        state: Initial state

    Returns:
        State updates
    """
    ui.show_welcome(state["topic"])
    ui.show_pipeline_progress("Research")

    return {
        "current_agent": "initialize",
        "start_time": datetime.now().isoformat()
    }


def research_node(state: ArticleState) -> Dict[str, Any]:
    """Execute research agent.

    Args:
        state: Current state

    Returns:
        State updates with research data
    """
    agent = ResearchAgent()
    result = agent.run(state)
    return result


def research_hitl_node(state: ArticleState) -> Dict[str, Any]:
    """HITL checkpoint for research.

    Args:
        state: Current state

    Returns:
        State updates with HITL approval
    """
    return research_hitl(state)


def writing_node(state: ArticleState) -> Dict[str, Any]:
    """Execute writing agent.

    Args:
        state: Current state

    Returns:
        State updates with draft article
    """
    ui.show_pipeline_progress("Writing")
    agent = WritingAgent()
    result = agent.run(state)
    return result


def writing_hitl_node(state: ArticleState) -> Dict[str, Any]:
    """HITL checkpoint for writing.

    Args:
        state: Current state

    Returns:
        State updates with HITL approval
    """
    return writing_hitl(state)


def review_node(state: ArticleState) -> Dict[str, Any]:
    """Execute review agent.

    Args:
        state: Current state

    Returns:
        State updates with review feedback
    """
    ui.show_pipeline_progress("Review")
    agent = ReviewAgent()
    result = agent.run(state)
    return result


def review_hitl_node(state: ArticleState) -> Dict[str, Any]:
    """HITL checkpoint for review.

    Args:
        state: Current state

    Returns:
        State updates with HITL approval
    """
    return review_hitl(state)


def polishing_node(state: ArticleState) -> Dict[str, Any]:
    """Execute polishing agent.

    Args:
        state: Current state

    Returns:
        State updates with final article
    """
    ui.show_pipeline_progress("Polishing")
    agent = PolishingAgent()
    result = agent.run(state)
    return result


def retry_handler_node(state: ArticleState) -> Dict[str, Any]:
    """Handle retry logic based on rejection.

    Args:
        state: Current state

    Returns:
        State updates for retry
    """
    current_agent = state.get("current_agent", "")
    retry_strategy = get_retry_strategy()

    # Determine retry level
    retry_level, should_retry = retry_strategy.should_retry(state)

    if not should_retry:
        # Max retries exceeded, fail gracefully
        return {
            "completed": True,
            "errors": [{
                "agent": current_agent,
                "error": "Max retries exceeded",
                "timestamp": datetime.now().isoformat()
            }]
        }

    # Execute retry
    rejection_reason = state.get("hitl_feedback", "Quality insufficient")
    retry_result = retry_strategy.execute_retry(state, current_agent, retry_level)

    # Log retry attempt
    log_entry = retry_strategy.log_retry_attempt(
        state, current_agent, retry_level, rejection_reason
    )

    # Merge results
    retry_result["execution_log"] = [log_entry]

    return retry_result


def finalize_node(state: ArticleState) -> Dict[str, Any]:
    """Finalize the workflow and generate report.

    Args:
        state: Current state

    Returns:
        Final state updates
    """
    from ..utils.report_generator import generate_report

    # Calculate total duration
    start_time = datetime.fromisoformat(state["start_time"])
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    # Calculate total retries
    retry_count = sum(state.get("retry_count", {}).values())

    # Generate report
    report_path = generate_report(state)

    # Show success
    ui.show_final_success(duration, retry_count)

    return {
        "completed": True,
        "end_time": end_time.isoformat()
    }
