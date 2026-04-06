"""State schema for the article writing workflow."""

from typing import TypedDict, Optional, List, Dict, Any, Annotated
from operator import add


class ArticleState(TypedDict):
    """Complete state for the article writing workflow.

    This state is passed through the LangGraph workflow and updated
    by each node (agent) as the article progresses from research to
    final polished output.
    """

    # ============= User Input =============
    topic: str
    """The main topic for the article"""

    user_requirements: Dict[str, Any]
    """Additional requirements like style, length, target audience"""

    # ============= Agent Outputs =============
    research_data: Optional[Dict[str, Any]]
    """Structured research results from Research Agent
    Format: {
        'sources': List[Dict],
        'key_points': List[str],
        'statistics': List[Dict],
        'perspectives': Dict
    }
    """

    draft_article: Optional[str]
    """Initial article draft from Writing Agent"""

    review_feedback: Optional[Dict[str, Any]]
    """Review feedback from Review Agent
    Format: {
        'overall_score': int,
        'issues': List[Dict],
        'strengths': List[str],
        'recommendation': str
    }
    """

    final_article: Optional[str]
    """Final polished article from Polishing Agent"""

    # ============= Execution Tracking =============
    current_agent: str
    """Name of the currently executing agent"""

    execution_log: Annotated[List[Dict[str, Any]], add]
    """Log of all agent executions
    Each entry: {
        'agent': str,
        'timestamp': str,
        'status': str,
        'result_summary': str,
        'duration': float
    }
    """

    retry_count: Dict[str, int]
    """Retry count per agent name"""

    retry_level: int
    """Current retry level (0=no retry, 1=same agent, 2=backup, 3=user)"""

    # ============= HITL State =============
    hitl_approval: Optional[bool]
    """Whether user approved at the last HITL checkpoint"""

    hitl_feedback: Optional[str]
    """User feedback provided at HITL checkpoint"""

    # ============= Error Handling =============
    errors: Annotated[List[Dict[str, Any]], add]
    """List of errors encountered during execution
    Each entry: {
        'agent': str,
        'error': str,
        'timestamp': str,
        'retry_level': int
    }
    """

    completed: bool
    """Whether the workflow has completed successfully"""

    # ============= Metadata =============
    start_time: Optional[str]
    """ISO format timestamp of workflow start"""

    end_time: Optional[str]
    """ISO format timestamp of workflow completion"""


def create_initial_state(topic: str, **kwargs) -> ArticleState:
    """Create an initial state for the workflow.

    Args:
        topic: The article topic
        **kwargs: Additional user requirements

    Returns:
        Initialized ArticleState
    """
    from datetime import datetime

    return ArticleState(
        # User input
        topic=topic,
        user_requirements=kwargs,

        # Agent outputs (all None initially)
        research_data=None,
        draft_article=None,
        review_feedback=None,
        final_article=None,

        # Execution tracking
        current_agent="initialize",
        execution_log=[],
        retry_count={},
        retry_level=0,

        # HITL state
        hitl_approval=None,
        hitl_feedback=None,

        # Error handling
        errors=[],
        completed=False,

        # Metadata
        start_time=datetime.now().isoformat(),
        end_time=None,
    )
