"""Backup agents for Level 2 retry mechanism."""

from .research_agent import ResearchAgent
from .writing_agent import WritingAgent
from .review_agent import ReviewAgent
from .polishing_agent import PolishingAgent


class DeepResearchAgent(ResearchAgent):
    """Enhanced research agent with more thorough approach."""

    def __init__(self):
        super().__init__(temperature=0.8)
        self.name = "Deep Research Agent (Backup)"

        # Override config for more results
        self.config.max_search_results = 10


class StructuredWritingAgent(WritingAgent):
    """Enhanced writing agent with structured outline-first approach."""

    def __init__(self):
        super().__init__(temperature=0.6)
        self.name = "Structured Writing Agent (Backup)"


class StrictReviewAgent(ReviewAgent):
    """Enhanced review agent with stricter standards."""

    def __init__(self):
        super().__init__(temperature=0.3)
        self.name = "Strict Review Agent (Backup)"


class ProfessionalPolishingAgent(PolishingAgent):
    """Enhanced polishing agent with professional editor standards."""

    def __init__(self):
        super().__init__(temperature=0.4)
        self.name = "Professional Polishing Agent (Backup)"


# Mapping of standard agents to their backups
BACKUP_AGENT_MAP = {
    "Research Agent": DeepResearchAgent,
    "Writing Agent": StructuredWritingAgent,
    "Review Agent": StrictReviewAgent,
    "Polishing Agent": ProfessionalPolishingAgent,
}


def get_backup_agent(agent_name: str):
    """Get backup agent for the given agent name.

    Args:
        agent_name: Name of the standard agent

    Returns:
        Instance of the backup agent, or None if no backup exists
    """
    backup_class = BACKUP_AGENT_MAP.get(agent_name)
    if backup_class:
        return backup_class()
    return None
