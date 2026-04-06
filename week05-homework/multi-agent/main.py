"""
Multi-Agent Article Writing System
Main entry point for the article generation workflow.

Usage:
    python -m multi-agent.main --topic "Your Article Topic"
    python -m multi-agent.main --topic "AI Agents" --style professional --word-count 1500
"""

import argparse
import sys
from pathlib import Path
from dotenv import load_dotenv

from .config import get_config
from .graph.state import create_initial_state
from .graph.workflow import get_workflow
from .utils.terminal import console


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Multi-Agent Article Writing System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m multi-agent.main --topic "AI Agents in 2026"
  python -m multi-agent.main --topic "Quantum Computing" --style technical
  python -m multi-agent.main --topic "Climate Change" --word-count 2000
        """
    )

    parser.add_argument(
        "--topic",
        type=str,
        required=True,
        help="Topic for the article"
    )

    parser.add_argument(
        "--style",
        type=str,
        default="professional",
        choices=["professional", "casual", "technical", "academic"],
        help="Writing style (default: professional)"
    )

    parser.add_argument(
        "--word-count",
        type=int,
        default=1500,
        help="Target word count (default: 1500)"
    )

    parser.add_argument(
        "--output",
        type=str,
        default="./report.md",
        help="Output path for report (default: ./report.md)"
    )

    return parser.parse_args()


def main():
    """Main entry point for the multi-agent system."""
    # Load environment variables
    load_dotenv()

    # Parse arguments
    args = parse_args()

    try:
        # Load configuration
        config = get_config()

        # Override output path if specified
        if args.output != "./report.md":
            config.report_path = args.output

        # Create initial state
        initial_state = create_initial_state(
            topic=args.topic,
            style=args.style,
            word_count=args.word_count
        )

        # Get workflow
        workflow = get_workflow()

        # Execute workflow
        console.print("\n[bold cyan]Starting Multi-Agent Article Writing System...[/bold cyan]\n")

        final_state = workflow.invoke(initial_state)

        # Check if completed successfully
        if final_state.get("completed"):
            console.print("\n[bold green]✅ Article generation completed successfully![/bold green]")
            console.print(f"[cyan]Report saved to: {config.report_path}[/cyan]\n")
            return 0
        else:
            console.print("\n[bold red]❌ Article generation failed.[/bold red]")
            errors = final_state.get("errors", [])
            if errors:
                console.print("\n[yellow]Errors:[/yellow]")
                for error in errors[-3:]:
                    console.print(f"  - {error.get('error', 'Unknown error')}")
            console.print()
            return 1

    except KeyboardInterrupt:
        console.print("\n\n[yellow]⚠️  Interrupted by user[/yellow]\n")
        return 130

    except Exception as e:
        console.print(f"\n[bold red]❌ Fatal error: {str(e)}[/bold red]\n")
        import traceback
        console.print("[dim]" + traceback.format_exc() + "[/dim]")
        return 1


if __name__ == "__main__":
    sys.exit(main())