"""Execution tracker for Thought-Action-Observation logging."""

import json
from pathlib import Path
from datetime import datetime


class ExecutionTracker:
    """Tracks agent execution traces for analysis."""

    def __init__(self):
        """Initialize execution tracker."""
        self.traces = []

    def log_thought(self, player_id: str, round_num: int, phase: str, thought: str):
        """Log agent's internal reasoning.

        Args:
            player_id: Player identifier
            round_num: Game round number
            phase: Game phase
            thought: Internal reasoning text
        """
        self.traces.append({
            "timestamp": datetime.now().isoformat(),
            "player_id": player_id,
            "round": round_num,
            "phase": phase,
            "type": "thought",
            "content": thought
        })

    def log_action(self, player_id: str, round_num: int, phase: str, action: dict):
        """Log agent's action.

        Args:
            player_id: Player identifier
            round_num: Game round number
            phase: Game phase
            action: Action dictionary
        """
        self.traces.append({
            "timestamp": datetime.now().isoformat(),
            "player_id": player_id,
            "round": round_num,
            "phase": phase,
            "type": "action",
            "content": action
        })

    def log_observation(self, player_id: str, round_num: int, phase: str, observation: str):
        """Log agent's observation.

        Args:
            player_id: Player identifier
            round_num: Game round number
            phase: Game phase
            observation: Observation text
        """
        self.traces.append({
            "timestamp": datetime.now().isoformat(),
            "player_id": player_id,
            "round": round_num,
            "phase": phase,
            "type": "observation",
            "content": observation
        })

    def export_traces(self, output_path: str):
        """Export traces to JSON file.

        Args:
            output_path: Path to output file
        """
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(self.traces, f, indent=2)

    def get_traces(self) -> list[dict]:
        """Get all traces.

        Returns:
            List of trace dictionaries
        """
        return self.traces
