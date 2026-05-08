"""Game state definitions for Werewolf game."""

from typing import TypedDict, Literal, Annotated
from operator import add
from langchain_core.messages import BaseMessage


class Player(TypedDict):
    """Player information."""
    id: str
    name: str
    role: Literal["werewolf", "villager"]
    personality: str
    is_alive: bool


class GameState(TypedDict):
    """Game state that is passed between nodes."""
    messages: Annotated[list[BaseMessage], add]
    round_number: int
    phase: Literal["night", "day_announcement", "speech", "voting", "game_over"]
    players: list[Player]
    dead_players: list[str]
    night_kill_target: str | None
    votes: dict[str, str]  # voter_id -> target_id
    game_log: list[dict]
    winner: Literal["werewolves", "villagers"] | None
