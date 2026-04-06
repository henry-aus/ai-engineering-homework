"""Rich terminal UI for displaying agent collaboration."""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.markdown import Markdown
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.layout import Layout
from rich.text import Text
from typing import Optional, List, Dict


console = Console()


class AgentUI:
    """Rich UI for showing agent collaboration in real-time."""

    def __init__(self):
        self.console = console
        self.current_stage = 0
        self.stages = ["Research", "Writing", "Review", "Polishing"]

    def show_welcome(self, topic: str):
        """Display welcome message."""
        self.console.print()
        self.console.print(
            Panel.fit(
                f"[bold cyan]Multi-Agent Article Writing System[/bold cyan]\n\n"
                f"Topic: [yellow]{topic}[/yellow]",
                border_style="cyan",
                padding=(1, 2)
            )
        )
        self.console.print()

    def show_pipeline_progress(self, current_stage: str):
        """Show overall pipeline progress."""
        table = Table(title="Article Generation Pipeline", show_header=False)
        table.add_column("Stage", style="cyan", width=20)
        table.add_column("Status", justify="center", width=10)

        for stage in self.stages:
            if stage.lower() == current_stage.lower():
                status = "🔄 [yellow]In Progress[/yellow]"
                self.current_stage = self.stages.index(stage)
            elif self.stages.index(stage) < self.current_stage:
                status = "✅ [green]Complete[/green]"
            else:
                status = "⏳ [dim]Pending[/dim]"

            table.add_row(stage, status)

        self.console.print(table)
        self.console.print()

    def show_agent_start(self, agent_name: str, task: str):
        """Show agent starting work."""
        self.console.print(
            Panel(
                f"[bold cyan]{agent_name}[/bold cyan]\n{task}",
                title="🤖 Agent Starting",
                border_style="cyan",
                padding=(1, 2)
            )
        )

    def show_agent_thinking(self, thought: str):
        """Show agent's current thought process."""
        self.console.print(f"  [dim]💭 {thought}[/dim]")

    def show_agent_complete(self, agent_name: str, summary: str, duration: float):
        """Show agent completion."""
        self.console.print(
            Panel(
                f"[bold green]{agent_name}[/bold green]\n"
                f"{summary}\n\n"
                f"[dim]Duration: {duration:.2f}s[/dim]",
                title="✅ Agent Complete",
                border_style="green",
                padding=(1, 2)
            )
        )
        self.console.print()

    def show_agent_error(self, agent_name: str, error: str):
        """Show agent error."""
        self.console.print(
            Panel(
                f"[bold red]{agent_name}[/bold red]\n"
                f"[red]Error: {error}[/red]",
                title="❌ Agent Error",
                border_style="red",
                padding=(1, 2)
            )
        )
        self.console.print()

    def show_retry_attempt(self, agent_name: str, level: int, attempt: int):
        """Show retry attempt."""
        level_names = ["", "Same Agent", "Backup Agent", "User Input"]
        self.console.print(
            Panel(
                f"[bold yellow]Retry Level {level}[/bold yellow]: {level_names[level]}\n"
                f"Attempt #{attempt} for {agent_name}",
                title="🔄 Retry",
                border_style="yellow",
                padding=(1, 2)
            )
        )

    def show_research_results(self, research_data: Dict):
        """Display research results summary."""
        sources = research_data.get('sources', [])
        key_points = research_data.get('key_points', [])

        self.console.print("[bold]Research Results:[/bold]")
        self.console.print(f"  📚 Sources found: {len(sources)}")
        self.console.print(f"  💡 Key points: {len(key_points)}")

        if sources:
            self.console.print("\n[bold]Top Sources:[/bold]")
            for i, source in enumerate(sources[:3], 1):
                title = source.get('title', 'Unknown')
                url = source.get('url', '')
                self.console.print(f"  {i}. {title}")
                self.console.print(f"     [dim]{url}[/dim]")

        self.console.print()

    def show_draft_preview(self, draft: str, max_lines: int = 10):
        """Show preview of article draft."""
        lines = draft.split('\n')
        preview = '\n'.join(lines[:max_lines])

        if len(lines) > max_lines:
            preview += f"\n\n[dim]... ({len(lines) - max_lines} more lines)[/dim]"

        self.console.print(
            Panel(
                Markdown(preview),
                title="📝 Draft Preview",
                border_style="blue",
                padding=(1, 2)
            )
        )
        self.console.print()

    def show_review_summary(self, review_feedback: Dict):
        """Display review feedback summary."""
        score = review_feedback.get('overall_score', 0)
        issues = review_feedback.get('issues', [])
        strengths = review_feedback.get('strengths', [])

        # Score with color
        score_color = "green" if score >= 80 else "yellow" if score >= 60 else "red"

        self.console.print(
            Panel(
                f"[bold]Overall Score:[/bold] [{score_color}]{score}/100[/{score_color}]\n\n"
                f"[bold]Issues Found:[/bold] {len(issues)}\n"
                f"[bold]Strengths:[/bold] {len(strengths)}",
                title="📋 Review Summary",
                border_style="blue",
                padding=(1, 2)
            )
        )
        self.console.print()

    def show_final_success(self, duration: float, retry_count: int):
        """Show final success message."""
        self.console.print()
        self.console.print(
            Panel.fit(
                f"[bold green]✅ Article Generation Complete![/bold green]\n\n"
                f"Total Duration: {duration:.2f}s\n"
                f"Total Retries: {retry_count}\n\n"
                f"📄 Check [cyan]report.md[/cyan] for the full article and execution log",
                border_style="green",
                padding=(1, 2)
            )
        )
        self.console.print()

    def show_error(self, message: str):
        """Show error message."""
        self.console.print(
            Panel(
                f"[bold red]Error:[/bold red]\n{message}",
                title="❌ System Error",
                border_style="red",
                padding=(1, 2)
            )
        )


# Global UI instance
ui = AgentUI()
