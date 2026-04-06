"""Base agent class for all agents in the system."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime
import time

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage

from ..config import get_config
from ..utils.terminal import ui


class BaseAgent(ABC):
    """Abstract base class for all agents.

    All agents must implement:
    - execute(): Main execution logic
    - get_system_prompt(): Agent-specific instructions
    """

    def __init__(self, name: str, temperature: Optional[float] = None):
        """Initialize the agent.

        Args:
            name: Agent name (e.g., "Research", "Writing")
            temperature: Optional temperature override
        """
        self.name = name
        self.config = get_config()

        # Initialize LLM
        self.llm = ChatAnthropic(
            model=self.config.claude_model,
            anthropic_api_key=self.config.anthropic_api_key,
            temperature=temperature or self.config.temperature,
            max_tokens=self.config.max_tokens,
        )

        self.tools: List = []
        self.start_time: Optional[float] = None

    @abstractmethod
    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the agent's main task.

        Args:
            state: Current article state

        Returns:
            Dictionary with updated state fields
        """
        pass

    @abstractmethod
    def get_system_prompt(self, state: Dict[str, Any]) -> str:
        """Get the system prompt for this agent.

        Args:
            state: Current article state

        Returns:
            System prompt string
        """
        pass

    def invoke_llm(
        self,
        user_prompt: str,
        system_prompt: Optional[str] = None,
        state: Optional[Dict[str, Any]] = None
    ) -> str:
        """Invoke the LLM with given prompts.

        Args:
            user_prompt: User message
            system_prompt: Optional system message (uses get_system_prompt if not provided)
            state: Optional state for system prompt generation

        Returns:
            LLM response text
        """
        if system_prompt is None and state is not None:
            system_prompt = self.get_system_prompt(state)

        messages = []
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        messages.append(HumanMessage(content=user_prompt))

        ui.show_agent_thinking(f"Calling LLM with {self.config.claude_model}...")

        response = self.llm.invoke(messages)
        return response.content

    def log_execution(
        self,
        state: Dict[str, Any],
        status: str,
        result_summary: str,
        duration: float
    ) -> Dict[str, Any]:
        """Log execution to state.

        Args:
            state: Current state
            status: Status (e.g., "success", "error", "retry")
            result_summary: Summary of results
            duration: Execution duration in seconds

        Returns:
            Log entry dictionary
        """
        log_entry = {
            "agent": self.name,
            "timestamp": datetime.now().isoformat(),
            "status": status,
            "result_summary": result_summary,
            "duration": duration,
        }

        return log_entry

    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Run the agent with timing and error handling.

        This is the main entry point that wraps execute() with:
        - Timing
        - UI updates
        - Error handling
        - Logging

        Args:
            state: Current article state

        Returns:
            Updated state fields
        """
        self.start_time = time.time()

        try:
            # Show agent start
            ui.show_agent_start(
                self.name,
                f"Processing {state.get('topic', 'article')}"
            )

            # Execute agent logic
            result = self.execute(state)

            # Calculate duration
            duration = time.time() - self.start_time

            # Create log entry
            log_entry = self.log_execution(
                state=state,
                status="success",
                result_summary=self._get_result_summary(result),
                duration=duration
            )

            # Show completion
            ui.show_agent_complete(
                self.name,
                log_entry["result_summary"],
                duration
            )

            # Update result with log entry
            result["execution_log"] = [log_entry]
            result["current_agent"] = self.name

            return result

        except Exception as e:
            duration = time.time() - self.start_time

            # Log error
            error_entry = {
                "agent": self.name,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "retry_level": state.get("retry_level", 0)
            }

            # Show error
            ui.show_agent_error(self.name, str(e))

            # Return error state
            return {
                "errors": [error_entry],
                "current_agent": self.name,
                "execution_log": [{
                    "agent": self.name,
                    "timestamp": datetime.now().isoformat(),
                    "status": "error",
                    "result_summary": f"Error: {str(e)}",
                    "duration": duration
                }]
            }

    def _get_result_summary(self, result: Dict[str, Any]) -> str:
        """Generate a summary of the agent's results.

        Can be overridden by subclasses for custom summaries.

        Args:
            result: Result dictionary from execute()

        Returns:
            Human-readable summary string
        """
        return f"{self.name} agent completed successfully"

    def bind_tools(self, tools: List):
        """Bind tools to this agent's LLM.

        Args:
            tools: List of LangChain tools
        """
        self.tools = tools
        if tools:
            self.llm = self.llm.bind_tools(tools)
