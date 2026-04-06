"""Three-level retry strategy implementation."""

from typing import Dict, Any, Tuple, Optional
from rich.prompt import Prompt

from ..graph.state import ArticleState
from ..agents.backup_agents import get_backup_agent
from ..config import get_config
from ..utils.terminal import ui, console


class RetryStrategy:
    """Three-level retry strategy for agent failures."""

    def __init__(self):
        self.config = get_config()
        self.max_level_1 = self.config.max_retries_level_1
        self.max_level_2 = self.config.max_retries_level_2

    def should_retry(self, state: ArticleState) -> Tuple[int, bool]:
        """Determine if should retry and at what level.

        Args:
            state: Current article state

        Returns:
            Tuple of (retry_level: int, should_retry: bool)
            retry_level: 0=no retry, 1=same agent, 2=backup, 3=user input
        """
        current_agent = state.get("current_agent", "")
        retry_count = state.get("retry_count", {}).get(current_agent, 0)

        if retry_count == 0:
            # First failure - try same agent
            return 1, True
        elif retry_count < self.max_level_1:
            # Still within level 1 retries
            return 1, True
        elif retry_count < (self.max_level_1 + self.max_level_2):
            # Move to level 2 - backup agent
            return 2, True
        else:
            # Move to level 3 - ask user
            return 3, True

    def execute_retry(
        self,
        state: ArticleState,
        agent_name: str,
        level: int
    ) -> Dict[str, Any]:
        """Execute retry at the specified level.

        Args:
            state: Current article state
            agent_name: Name of the agent to retry
            level: Retry level (1, 2, or 3)

        Returns:
            State updates from retry attempt
        """
        if level == 1:
            return self._retry_level_1(state, agent_name)
        elif level == 2:
            return self._retry_level_2(state, agent_name)
        else:
            return self._retry_level_3(state, agent_name)

    def _retry_level_1(self, state: ArticleState, agent_name: str) -> Dict[str, Any]:
        """Level 1: Retry with same agent.

        Args:
            state: Current article state
            agent_name: Agent to retry

        Returns:
            State updates indicating retry setup
        """
        retry_count = state.get("retry_count", {}).get(agent_name, 0)

        console.print()
        ui.show_retry_attempt(agent_name, level=1, attempt=retry_count + 1)
        console.print("[yellow]Retrying with same agent with enhanced context...[/yellow]")
        console.print()

        # Update state for retry
        updated_retry_count = state.get("retry_count", {}).copy()
        updated_retry_count[agent_name] = retry_count + 1

        return {
            "retry_level": 1,
            "retry_count": updated_retry_count,
            "hitl_approval": None,  # Reset approval
        }

    def _retry_level_2(self, state: ArticleState, agent_name: str) -> Dict[str, Any]:
        """Level 2: Retry with backup agent.

        Args:
            state: Current article state
            agent_name: Original agent name

        Returns:
            State updates indicating backup agent will be used
        """
        retry_count = state.get("retry_count", {}).get(agent_name, 0)

        console.print()
        ui.show_retry_attempt(agent_name, level=2, attempt=retry_count + 1)

        backup_agent = get_backup_agent(agent_name)
        if backup_agent:
            console.print(f"[cyan]Switching to backup agent: {backup_agent.name}[/cyan]")
        else:
            console.print(f"[yellow]No backup agent available, using original with higher temperature[/yellow]")

        console.print()

        # Update state for retry
        updated_retry_count = state.get("retry_count", {}).copy()
        updated_retry_count[agent_name] = retry_count + 1

        return {
            "retry_level": 2,
            "retry_count": updated_retry_count,
            "current_agent": backup_agent.name if backup_agent else agent_name,
            "hitl_approval": None,
        }

    def _retry_level_3(self, state: ArticleState, agent_name: str) -> Dict[str, Any]:
        """Level 3: Ask user for guidance.

        Args:
            state: Current article state
            agent_name: Agent that failed

        Returns:
            State updates with user guidance
        """
        retry_count = state.get("retry_count", {}).get(agent_name, 0)

        console.print()
        ui.show_retry_attempt(agent_name, level=3, attempt=retry_count + 1)

        console.print(f"[red]Agent '{agent_name}' has failed multiple times.[/red]\n")

        # Show previous errors
        errors = state.get("errors", [])
        if errors:
            console.print("[yellow]Previous errors:[/yellow]")
            for i, error in enumerate(errors[-3:], 1):
                console.print(f"  {i}. {error.get('error', 'Unknown error')}")
            console.print()

        # Ask user for guidance
        console.print("[cyan]Please provide additional guidance or information to help the agent:[/cyan]")
        user_guidance = Prompt.ask("Your guidance").strip()

        if not user_guidance:
            user_guidance = "Please try again with more attention to detail."

        console.print(f"\n[green]Guidance received: {user_guidance}[/green]")
        console.print("[yellow]Retrying with user guidance...[/yellow]\n")

        # Update state
        updated_retry_count = state.get("retry_count", {}).copy()
        updated_retry_count[agent_name] = retry_count + 1

        # Add user guidance to requirements
        updated_requirements = state.get("user_requirements", {}).copy()
        updated_requirements["user_guidance"] = user_guidance

        return {
            "retry_level": 3,
            "retry_count": updated_retry_count,
            "user_requirements": updated_requirements,
            "hitl_approval": None,
        }

    def log_retry_attempt(
        self,
        state: ArticleState,
        agent_name: str,
        level: int,
        reason: str
    ) -> Dict[str, Any]:
        """Log a retry attempt.

        Args:
            state: Current state
            agent_name: Agent being retried
            level: Retry level
            reason: Reason for retry

        Returns:
            Log entry dictionary
        """
        from datetime import datetime

        log_entry = {
            "event": "retry_attempt",
            "agent": agent_name,
            "level": level,
            "retry_count": state.get("retry_count", {}).get(agent_name, 0),
            "reason": reason,
            "timestamp": datetime.now().isoformat()
        }

        return log_entry


# Global retry strategy instance
_retry_strategy: Optional[RetryStrategy] = None


def get_retry_strategy() -> RetryStrategy:
    """Get or create the global retry strategy instance.

    Returns:
        RetryStrategy instance
    """
    global _retry_strategy
    if _retry_strategy is None:
        _retry_strategy = RetryStrategy()
    return _retry_strategy
