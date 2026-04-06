"""Human-in-the-loop checkpoint implementation."""

from typing import Tuple, Optional, Dict, Any
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.prompt import Prompt

from ..graph.state import ArticleState


console = Console()


def hitl_checkpoint(
    state: ArticleState,
    checkpoint_name: str,
    content_to_review: str,
    content_type: str = "text"
) -> Tuple[bool, Optional[str]]:
    """Present content to user for review and approval.

    Args:
        state: Current article state
        checkpoint_name: Name of the checkpoint (e.g., "Research Review")
        content_to_review: Content for user to review
        content_type: Type of content ("text", "markdown", "json")

    Returns:
        Tuple of (approved: bool, feedback: Optional[str])
    """
    console.print("\n" + "=" * 80)
    console.print(f"[bold cyan]🔍 HITL Checkpoint: {checkpoint_name}[/bold cyan]")
    console.print("=" * 80 + "\n")

    # Display content based on type
    if content_type == "markdown":
        console.print(Panel(
            Markdown(content_to_review),
            title="Content to Review",
            border_style="blue",
            padding=(1, 2)
        ))
    else:
        console.print(Panel(
            content_to_review,
            title="Content to Review",
            border_style="blue",
            padding=(1, 2)
        ))

    console.print()

    # Get user decision
    while True:
        console.print("[yellow]Options:[/yellow]")
        console.print("  [green]a[/green] - Approve and continue to next stage")
        console.print("  [red]r[/red] - Reject and request retry")
        console.print("  [blue]f[/blue] - Provide feedback and continue")
        console.print()

        choice = Prompt.ask(
            "Your choice",
            choices=["a", "r", "f", "approve", "reject", "feedback"],
            default="a"
        ).lower()

        if choice in ["a", "approve"]:
            console.print("\n[green]✅ Approved! Moving to next stage...[/green]\n")
            return True, None

        elif choice in ["r", "reject"]:
            console.print()
            reason = Prompt.ask(
                "[yellow]Please provide a reason for rejection[/yellow]"
            ).strip()

            if reason:
                console.print(f"\n[red]❌ Rejected: {reason}[/red]")
                console.print("[yellow]Initiating retry mechanism...[/yellow]\n")
                return False, reason
            else:
                console.print("[red]Rejection reason cannot be empty. Please try again.[/red]\n")
                continue

        elif choice in ["f", "feedback"]:
            console.print()
            feedback = Prompt.ask(
                "[yellow]Your feedback (optional, will be noted but won't trigger retry)[/yellow]",
                default=""
            ).strip()

            if feedback:
                console.print(f"\n[blue]📝 Feedback noted: {feedback}[/blue]")
                console.print("[green]Continuing to next stage...[/green]\n")
                return True, feedback
            else:
                console.print("\n[green]✅ Continuing to next stage...[/green]\n")
                return True, None


def research_hitl(state: ArticleState) -> Dict[str, Any]:
    """HITL checkpoint for research results.

    Args:
        state: Current article state

    Returns:
        State updates with HITL approval status
    """
    research_data = state.get("research_data", {})

    # Format research results for review
    sources = research_data.get("sources", [])
    key_points = research_data.get("key_points", [])

    content = f"""# Research Results

## Sources Found: {len(sources)}

"""

    for i, source in enumerate(sources[:5], 1):
        content += f"{i}. **{source.get('title', 'Unknown')}**\n"
        content += f"   - URL: {source.get('url', 'N/A')}\n"
        content += f"   - Relevance: {source.get('score', 0):.2f}\n\n"

    content += f"\n## Key Points Identified: {len(key_points)}\n\n"
    for i, point in enumerate(key_points[:10], 1):
        content += f"{i}. {point}\n"

    # Get user approval
    approved, feedback = hitl_checkpoint(
        state=state,
        checkpoint_name="Research Review",
        content_to_review=content,
        content_type="markdown"
    )

    return {
        "hitl_approval": approved,
        "hitl_feedback": feedback
    }


def writing_hitl(state: ArticleState) -> Dict[str, Any]:
    """HITL checkpoint for article draft.

    Args:
        state: Current article state

    Returns:
        State updates with HITL approval status
    """
    draft = state.get("draft_article", "")

    # Truncate for preview if too long
    lines = draft.split("\n")
    if len(lines) > 50:
        preview = "\n".join(lines[:50])
        preview += f"\n\n... ({len(lines) - 50} more lines) ...\n\n"
        preview += "\n".join(lines[-5:])
    else:
        preview = draft

    # Get user approval
    approved, feedback = hitl_checkpoint(
        state=state,
        checkpoint_name="Draft Review",
        content_to_review=preview,
        content_type="markdown"
    )

    return {
        "hitl_approval": approved,
        "hitl_feedback": feedback
    }


def review_hitl(state: ArticleState) -> Dict[str, Any]:
    """HITL checkpoint for review feedback.

    Args:
        state: Current article state

    Returns:
        State updates with HITL approval status
    """
    review_feedback = state.get("review_feedback", {})

    # Format review feedback
    content = f"""# Review Feedback

## Overall Score: {review_feedback.get('overall_score', 0)}/100

## Issues Found: {len(review_feedback.get('issues', []))}
"""

    issues = review_feedback.get("issues", [])
    for i, issue in enumerate(issues[:10], 1):
        content += f"\n{i}. **[{issue.get('severity', 'medium').upper()}]** {issue.get('type', 'Unknown')}\n"
        content += f"   - Location: {issue.get('location', 'N/A')}\n"
        content += f"   - Suggestion: {issue.get('suggestion', 'N/A')}\n"

    content += f"\n## Strengths: {len(review_feedback.get('strengths', []))}\n\n"
    for strength in review_feedback.get("strengths", []):
        content += f"- {strength}\n"

    content += f"\n## Recommendation: {review_feedback.get('recommendation', 'N/A')}\n"

    # Get user approval
    approved, feedback = hitl_checkpoint(
        state=state,
        checkpoint_name="Review Feedback",
        content_to_review=content,
        content_type="markdown"
    )

    return {
        "hitl_approval": approved,
        "hitl_feedback": feedback
    }
