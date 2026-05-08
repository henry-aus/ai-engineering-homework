"""Main entry point for Werewolf game."""

import json
from pathlib import Path
from rich.console import Console
from rich.table import Table

from werewolf.game.graph import create_game_graph
from werewolf.agents.player import create_players
from werewolf.memory.semantic import SemanticMemory
from werewolf.tracing.tracker import ExecutionTracker
from werewolf.utils.logging import setup_logging

console = Console()


def display_final_summary(state: dict, tracker: ExecutionTracker):
    """Display final game summary.

    Args:
        state: Final game state
        tracker: Execution tracker
    """
    console.print("\n" + "="*60)
    console.print("[bold cyan]GAME SUMMARY[/bold cyan]")
    console.print("="*60 + "\n")

    # Winner
    winner = state["winner"]
    if winner == "villagers":
        console.print("[bold green]🎉 VILLAGERS WIN! 🎉[/bold green]\n")
    else:
        console.print("[bold red]🐺 WEREWOLVES WIN! 🐺[/bold red]\n")

    # Final player status
    table = Table(title="Final Player Status")
    table.add_column("Name", style="cyan")
    table.add_column("Role", style="yellow")
    table.add_column("Personality", style="magenta")
    table.add_column("Status", style="white")

    for player in state["players"]:
        status = "✓ Alive" if player["is_alive"] else "✗ Dead"
        status_style = "green" if player["is_alive"] else "red"
        table.add_row(
            player["name"],
            player["role"].capitalize(),
            player["personality"].replace("_", " ").title(),
            f"[{status_style}]{status}[/{status_style}]"
        )

    console.print(table)

    # Game statistics
    console.print(f"\n[bold]Total Rounds:[/bold] {state['round_number'] - 1}")
    console.print(f"[bold]Total Deaths:[/bold] {len(state['dead_players'])}")
    console.print(f"[bold]Execution Traces:[/bold] {len(tracker.get_traces())} events logged\n")


def export_game_log(state: dict, output_path: str):
    """Export game log to JSON file.

    Args:
        state: Final game state
        output_path: Path to output file
    """
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    log_data = {
        "winner": state["winner"],
        "total_rounds": state["round_number"] - 1,
        "players": [
            {
                "name": p["name"],
                "role": p["role"],
                "personality": p["personality"],
                "survived": p["is_alive"]
            }
            for p in state["players"]
        ],
        "game_log": state["game_log"]
    }

    with open(output_path, "w") as f:
        json.dump(log_data, f, indent=2)


def main():
    """Main entry point for Werewolf game."""
    console.print("[bold cyan]🐺 Welcome to AI Werewolf Game! 🐺[/bold cyan]\n")

    # Setup
    setup_logging()
    semantic_memory = SemanticMemory()
    tracker = ExecutionTracker()
    game_id = "game_1"

    # Create players
    console.print("[yellow]Creating players...[/yellow]")
    players = create_players(semantic_memory, tracker, game_id)

    # Display player info
    table = Table(title="Player Setup")
    table.add_column("Name", style="cyan")
    table.add_column("Role", style="yellow")
    table.add_column("Personality", style="magenta")

    for player in players:
        table.add_row(
            player["name"],
            player["role"].capitalize(),
            player["personality"].replace("_", " ").title()
        )

    console.print(table)
    console.print()

    # Create game graph
    console.print("[yellow]Initializing game...[/yellow]\n")
    game_graph = create_game_graph()

    # Initialize state
    initial_state = {
        "round_number": 1,
        "phase": "night",
        "players": players,
        "dead_players": [],
        "night_kill_target": None,
        "votes": {},
        "game_log": [],
        "winner": None,
        "messages": []
    }

    # Run game
    config = {"configurable": {"thread_id": game_id}}

    console.print("[bold green]Starting game...[/bold green]\n")

    try:
        final_state = None
        for event in game_graph.stream(initial_state, config):
            # The event contains the state after each node execution
            if event:
                # Get the latest state from the event
                for node_name, node_state in event.items():
                    final_state = node_state

        # Display final summary
        if final_state:
            display_final_summary(final_state, tracker)

            # Export logs
            console.print("[yellow]Exporting game logs...[/yellow]")
            tracker.export_traces("game_logs/game_1_trace.json")
            export_game_log(final_state, "game_logs/game_1_log.json")

            console.print("[bold green]✓ Game logs exported to game_logs/[/bold green]")
            console.print("[dim]  - game_logs/game_1_log.json (game summary)")
            console.print("[dim]  - game_logs/game_1_trace.json (detailed traces)[/dim]\n")

    except KeyboardInterrupt:
        console.print("\n[yellow]Game interrupted by user.[/yellow]")
    except Exception as e:
        console.print(f"\n[bold red]Error during game: {e}[/bold red]")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()