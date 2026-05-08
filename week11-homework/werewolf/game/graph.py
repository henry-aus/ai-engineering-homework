"""LangGraph workflow for Werewolf game."""

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from werewolf.game.state import GameState
from werewolf.game.phases import (
    night_phase_node,
    day_announcement_node,
    speech_phase_node,
    voting_phase_node,
    check_victory_node
)


def create_game_graph():
    """Create the LangGraph workflow for the Werewolf game.

    Returns:
        Compiled graph with checkpointer
    """
    # Create workflow
    workflow = StateGraph(GameState)

    # Add nodes for each phase
    workflow.add_node("night_phase", night_phase_node)
    workflow.add_node("day_announcement", day_announcement_node)
    workflow.add_node("speech_phase", speech_phase_node)
    workflow.add_node("voting_phase", voting_phase_node)
    workflow.add_node("check_victory", check_victory_node)

    # Set entry point
    workflow.set_entry_point("night_phase")

    # Add edges for phase transitions
    workflow.add_edge("night_phase", "day_announcement")
    workflow.add_edge("day_announcement", "speech_phase")
    workflow.add_edge("speech_phase", "voting_phase")
    workflow.add_edge("voting_phase", "check_victory")

    # Add conditional edge for game continuation
    def should_continue(state: GameState) -> str:
        """Determine if game should continue or end.

        Args:
            state: Current game state

        Returns:
            Next node name
        """
        if state["winner"] is not None:
            return "end"
        return "continue"

    workflow.add_conditional_edges(
        "check_victory",
        should_continue,
        {
            "continue": "night_phase",
            "end": END
        }
    )

    # Add checkpointer for episodic memory
    checkpointer = MemorySaver()

    return workflow.compile(checkpointer=checkpointer)
