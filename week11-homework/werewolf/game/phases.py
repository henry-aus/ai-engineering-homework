"""Game phase logic for Werewolf game."""

from collections import Counter
import random
from langchain_core.messages import AIMessage
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from werewolf.game.state import GameState

console = Console()


def night_phase_node(state: GameState) -> GameState:
    """Execute night phase where werewolves choose their victim.

    Args:
        state: Current game state

    Returns:
        Updated game state
    """
    console.print(f"\n[bold cyan]{'='*60}[/bold cyan]")
    console.print(f"[bold cyan]ROUND {state['round_number']} - NIGHT PHASE[/bold cyan]")
    console.print(f"[bold cyan]{'='*60}[/bold cyan]\n")

    # Get living werewolves
    werewolves = [p for p in state["players"] if p["role"] == "werewolf" and p["is_alive"]]

    if not werewolves:
        # No werewolves left, game should end
        state["night_kill_target"] = None
        return state

    # Each werewolf proposes a target
    console.print("[yellow]Werewolves are discussing their target...[/yellow]\n")
    votes = []
    for werewolf in werewolves:
        agent = werewolf["agent"]
        target = agent.decide_night_kill(state, state["round_number"])
        if target:
            votes.append(target)
            console.print(f"[red]{werewolf['name']}[/red] proposes: {target}")

    # Determine kill target (most voted, random tiebreaker)
    if votes:
        vote_counts = Counter(votes)
        max_votes = max(vote_counts.values())
        top_targets = [target for target, count in vote_counts.items() if count == max_votes]
        kill_target = random.choice(top_targets)
        state["night_kill_target"] = kill_target
        console.print(f"\n[bold red]Werewolves decided to eliminate: {kill_target}[/bold red]\n")
    else:
        state["night_kill_target"] = None

    state["phase"] = "day_announcement"

    # Add to game log
    state["game_log"].append({
        "round": state["round_number"],
        "phase": "night",
        "event": f"Werewolves chose to kill {state['night_kill_target']}" if state["night_kill_target"] else "No kill"
    })

    return state


def day_announcement_node(state: GameState) -> GameState:
    """Announce the night's victim.

    Args:
        state: Current game state

    Returns:
        Updated game state
    """
    console.print(f"\n[bold yellow]{'='*60}[/bold yellow]")
    console.print(f"[bold yellow]DAY {state['round_number']} - DAWN ANNOUNCEMENT[/bold yellow]")
    console.print(f"[bold yellow]{'='*60}[/bold yellow]\n")

    kill_target = state["night_kill_target"]

    if kill_target:
        # Find and mark player as dead
        for player in state["players"]:
            if player["id"] == kill_target:
                player["is_alive"] = False
                state["dead_players"].append(player["name"])
                console.print(Panel(
                    f"[bold red]{player['name']} was found dead![/bold red]",
                    title="Death Announcement",
                    border_style="red"
                ))

                # All players observe this event
                event = f"{player['name']} was killed during the night."
                for p in state["players"]:
                    if p["is_alive"]:
                        p["agent"].observe_event(event, state["round_number"], "day_announcement")
                break
    else:
        console.print("[green]No one died last night.[/green]\n")

    state["phase"] = "speech"
    state["game_log"].append({
        "round": state["round_number"],
        "phase": "day_announcement",
        "event": f"{kill_target} was killed" if kill_target else "No death"
    })

    return state


def speech_phase_node(state: GameState) -> GameState:
    """Execute speech phase where players discuss.

    Args:
        state: Current game state

    Returns:
        Updated game state
    """
    console.print(f"\n[bold green]{'='*60}[/bold green]")
    console.print(f"[bold green]DAY {state['round_number']} - DISCUSSION PHASE[/bold green]")
    console.print(f"[bold green]{'='*60}[/bold green]\n")

    alive_players = [p for p in state["players"] if p["is_alive"]]

    speeches = []
    for player in alive_players:
        agent = player["agent"]
        speech = agent.generate_speech(state, state["round_number"])

        console.print(Panel(
            speech,
            title=f"[bold]{player['name']}[/bold] speaks",
            border_style="green"
        ))

        speeches.append({
            "player": player["name"],
            "speech": speech
        })

        # All other players observe this speech
        event = f"{player['name']} said: {speech}"
        for p in alive_players:
            if p["id"] != player["id"]:
                p["agent"].observe_event(event, state["round_number"], "speech")

        # Add to messages
        state["messages"].append(AIMessage(content=f"{player['name']}: {speech}"))

    state["phase"] = "voting"
    state["game_log"].append({
        "round": state["round_number"],
        "phase": "speech",
        "speeches": speeches
    })

    return state


def voting_phase_node(state: GameState) -> GameState:
    """Execute voting phase where players vote to eliminate someone.

    Args:
        state: Current game state

    Returns:
        Updated game state
    """
    console.print(f"\n[bold magenta]{'='*60}[/bold magenta]")
    console.print(f"[bold magenta]DAY {state['round_number']} - VOTING PHASE[/bold magenta]")
    console.print(f"[bold magenta]{'='*60}[/bold magenta]\n")

    alive_players = [p for p in state["players"] if p["is_alive"]]
    votes = {}

    console.print("[yellow]Players are casting their votes...[/yellow]\n")

    for player in alive_players:
        agent = player["agent"]
        vote = agent.cast_vote(state, state["round_number"])
        if vote:
            votes[player["id"]] = vote
            # Find target name
            target_name = next((p["name"] for p in state["players"] if p["id"] == vote), vote)
            console.print(f"[cyan]{player['name']}[/cyan] votes for: [red]{target_name}[/red]")

    state["votes"] = votes

    # Count votes
    if votes:
        vote_counts = Counter(votes.values())
        max_votes = max(vote_counts.values())
        top_targets = [target for target, count in vote_counts.items() if count == max_votes]
        eliminated = random.choice(top_targets)

        # Find and eliminate player
        for player in state["players"]:
            if player["id"] == eliminated:
                player["is_alive"] = False
                state["dead_players"].append(player["name"])
                console.print(f"\n[bold red]{player['name']} has been eliminated by vote![/bold red]")
                console.print(f"[dim]{player['name']} was a {player['role'].upper()}[/dim]\n")

                # All players observe this elimination
                event = f"{player['name']} was eliminated by vote and was revealed to be a {player['role']}."
                for p in state["players"]:
                    if p["is_alive"]:
                        p["agent"].observe_event(event, state["round_number"], "voting")
                break

    state["phase"] = "check_victory"
    state["game_log"].append({
        "round": state["round_number"],
        "phase": "voting",
        "votes": votes,
        "eliminated": eliminated if votes else None
    })

    return state


def check_victory_node(state: GameState) -> GameState:
    """Check victory conditions.

    Args:
        state: Current game state

    Returns:
        Updated game state
    """
    alive_players = [p for p in state["players"] if p["is_alive"]]
    alive_werewolves = [p for p in alive_players if p["role"] == "werewolf"]
    alive_villagers = [p for p in alive_players if p["role"] == "villager"]

    # Display current status
    table = Table(title=f"Round {state['round_number']} Status")
    table.add_column("Status", style="cyan")
    table.add_column("Count", style="magenta")
    table.add_row("Alive Werewolves", str(len(alive_werewolves)))
    table.add_row("Alive Villagers", str(len(alive_villagers)))
    table.add_row("Total Alive", str(len(alive_players)))
    console.print(table)

    # Check victory conditions
    if len(alive_werewolves) == 0:
        state["winner"] = "villagers"
        state["phase"] = "game_over"
        console.print("\n[bold green]🎉 VILLAGERS WIN! All werewolves eliminated! 🎉[/bold green]\n")
    elif len(alive_werewolves) >= len(alive_villagers):
        state["winner"] = "werewolves"
        state["phase"] = "game_over"
        console.print("\n[bold red]🐺 WEREWOLVES WIN! They equal or outnumber the villagers! 🐺[/bold red]\n")
    else:
        # Game continues
        state["round_number"] += 1
        state["phase"] = "night"
        console.print(f"\n[dim]Game continues to Round {state['round_number']}...[/dim]\n")

    return state
