"""Player agent implementation."""

from langchain_core.messages import SystemMessage, HumanMessage
from werewolf.utils.llm import get_llm
from werewolf.prompts.system_prompts import get_role_prompt
from werewolf.prompts.personalities import get_personality_prompt
from werewolf.memory.semantic import SemanticMemory
from werewolf.tracing.tracker import ExecutionTracker


class PlayerAgent:
    """Represents a player in the Werewolf game."""

    def __init__(
        self,
        player_id: str,
        name: str,
        role: str,
        personality: str,
        semantic_memory: SemanticMemory,
        tracker: ExecutionTracker,
        game_id: str = "game_1"
    ):
        """Initialize player agent.

        Args:
            player_id: Unique player identifier
            name: Player name
            role: Player role (werewolf or villager)
            personality: Personality key
            semantic_memory: Shared semantic memory
            tracker: Shared execution tracker
            game_id: Game identifier
        """
        self.player_id = player_id
        self.name = name
        self.role = role
        self.personality = personality
        self.semantic_memory = semantic_memory
        self.tracker = tracker
        self.game_id = game_id
        self.llm = get_llm()

        # Build system prompt
        role_prompt = get_role_prompt(role)
        personality_prompt = get_personality_prompt(personality)
        self.system_prompt = f"{role_prompt}\n\nPersonality: {personality_prompt}"

    def _retrieve_memories(self, query: str, round_num: int, phase: str) -> str:
        """Retrieve relevant memories from semantic memory.

        Args:
            query: Query string
            round_num: Current round number
            phase: Current game phase

        Returns:
            Formatted memory context string
        """
        memories = self.semantic_memory.retrieve_relevant(
            self.game_id, self.player_id, query, k=5
        )

        if not memories:
            return "No previous memories found."

        memory_text = "Relevant memories from past rounds:\n"
        for i, memory in enumerate(memories, 1):
            memory_text += f"{i}. {memory}\n"

        return memory_text

    def generate_speech(self, game_state: dict, round_num: int) -> str:
        """Generate a speech for the discussion phase.

        Args:
            game_state: Current game state
            round_num: Current round number

        Returns:
            Speech text
        """
        # Prepare context
        alive_players = [p for p in game_state["players"] if p["is_alive"]]
        dead_players = game_state.get("dead_players", [])

        query = f"Round {round_num} discussion: who is suspicious and why?"
        memories = self._retrieve_memories(query, round_num, "speech")

        # Log thought
        thought = f"Generating speech for round {round_num}. I will retrieve memories and form an argument."
        self.tracker.log_thought(self.player_id, round_num, "speech", thought)

        # Construct prompt
        context = f"""Round {round_num} - Discussion Phase

Alive players: {', '.join([p['name'] for p in alive_players])}
Dead players: {', '.join(dead_players) if dead_players else 'None'}

{memories}

Based on your role, personality, and memories, give a speech (2-3 sentences) about who you find suspicious and why. Stay in character."""

        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=context)
        ]

        response = self.llm.invoke(messages)
        speech = response.content

        # Log action
        self.tracker.log_action(
            self.player_id, round_num, "speech",
            {"action": "speak", "speech": speech}
        )

        # Store observation
        observation = f"Round {round_num}: I gave a speech about suspicions."
        self.semantic_memory.add_observation(
            self.game_id, self.player_id, observation, round_num, "speech"
        )
        self.tracker.log_observation(self.player_id, round_num, "speech", observation)

        return speech

    def cast_vote(self, game_state: dict, round_num: int) -> str:
        """Cast a vote to eliminate a player.

        Args:
            game_state: Current game state
            round_num: Current round number

        Returns:
            Player ID to vote for
        """
        alive_players = [p for p in game_state["players"] if p["is_alive"] and p["id"] != self.player_id]

        if not alive_players:
            return None

        query = f"Round {round_num} voting: who should be eliminated?"
        memories = self._retrieve_memories(query, round_num, "voting")

        # Log thought
        thought = f"Deciding who to vote for in round {round_num}."
        self.tracker.log_thought(self.player_id, round_num, "voting", thought)

        # Construct prompt
        player_list = "\n".join([f"- {p['name']} ({p['id']})" for p in alive_players])
        context = f"""Round {round_num} - Voting Phase

You must vote to eliminate one player from this list:
{player_list}

{memories}

Based on your analysis, who should be eliminated? Respond with ONLY the player ID (like player_1, player_2, etc.)."""

        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=context)
        ]

        response = self.llm.invoke(messages)
        vote = response.content.strip()

        # Validate vote
        valid_ids = [p["id"] for p in alive_players]
        if vote not in valid_ids:
            # Fallback: vote for first available player
            vote = valid_ids[0] if valid_ids else None

        # Log action
        self.tracker.log_action(
            self.player_id, round_num, "voting",
            {"action": "vote", "target": vote}
        )

        # Store observation
        observation = f"Round {round_num}: I voted for {vote}."
        self.semantic_memory.add_observation(
            self.game_id, self.player_id, observation, round_num, "voting"
        )
        self.tracker.log_observation(self.player_id, round_num, "voting", observation)

        return vote

    def decide_night_kill(self, game_state: dict, round_num: int) -> str:
        """Decide who to kill during night phase (werewolves only).

        Args:
            game_state: Current game state
            round_num: Current round number

        Returns:
            Player ID to kill
        """
        if self.role != "werewolf":
            return None

        villagers = [
            p for p in game_state["players"]
            if p["is_alive"] and p["role"] == "villager"
        ]

        if not villagers:
            return None

        query = f"Round {round_num} night: who should we eliminate?"
        memories = self._retrieve_memories(query, round_num, "night")

        # Log thought
        thought = f"Deciding night kill target for round {round_num}."
        self.tracker.log_thought(self.player_id, round_num, "night", thought)

        # Construct prompt
        villager_list = "\n".join([f"- {p['name']} ({p['id']})" for p in villagers])
        context = f"""Round {round_num} - Night Phase (Werewolf)

Available targets (villagers):
{villager_list}

{memories}

Who should the werewolves eliminate tonight? Consider who is most dangerous to your team. Respond with ONLY the player ID."""

        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=context)
        ]

        response = self.llm.invoke(messages)
        target = response.content.strip()

        # Validate target
        valid_ids = [p["id"] for p in villagers]
        if target not in valid_ids:
            # Fallback: target first villager
            target = valid_ids[0] if valid_ids else None

        # Log action
        self.tracker.log_action(
            self.player_id, round_num, "night",
            {"action": "kill_vote", "target": target}
        )

        # Store observation
        observation = f"Round {round_num}: I proposed killing {target}."
        self.semantic_memory.add_observation(
            self.game_id, self.player_id, observation, round_num, "night"
        )
        self.tracker.log_observation(self.player_id, round_num, "night", observation)

        return target

    def observe_event(self, event: str, round_num: int, phase: str):
        """Observe and remember an event.

        Args:
            event: Event description
            round_num: Current round number
            phase: Current game phase
        """
        observation = f"Round {round_num} ({phase}): {event}"
        self.semantic_memory.add_observation(
            self.game_id, self.player_id, observation, round_num, phase
        )
        self.tracker.log_observation(self.player_id, round_num, phase, observation)


def create_players(semantic_memory: SemanticMemory, tracker: ExecutionTracker, game_id: str = "game_1") -> list[dict]:
    """Create the 5 player agents (2 werewolves, 3 villagers).

    Args:
        semantic_memory: Shared semantic memory
        tracker: Shared execution tracker
        game_id: Game identifier

    Returns:
        List of player dictionaries
    """
    players_config = [
        {"id": "player_1", "name": "Alice", "role": "werewolf", "personality": "aggressive_werewolf"},
        {"id": "player_2", "name": "Bob", "role": "werewolf", "personality": "cautious_werewolf"},
        {"id": "player_3", "name": "Charlie", "role": "villager", "personality": "logical_villager"},
        {"id": "player_4", "name": "Diana", "role": "villager", "personality": "emotional_villager"},
        {"id": "player_5", "name": "Eve", "role": "villager", "personality": "observant_villager"},
    ]

    players = []
    for config in players_config:
        agent = PlayerAgent(
            player_id=config["id"],
            name=config["name"],
            role=config["role"],
            personality=config["personality"],
            semantic_memory=semantic_memory,
            tracker=tracker,
            game_id=game_id
        )
        players.append({
            "id": config["id"],
            "name": config["name"],
            "role": config["role"],
            "personality": config["personality"],
            "is_alive": True,
            "agent": agent
        })

    return players
