"""Report generation utilities."""

from typing import Dict, Any
from datetime import datetime
from pathlib import Path

from ..graph.state import ArticleState
from ..config import get_config


def generate_report(state: ArticleState) -> str:
    """Generate comprehensive report.md file.

    Args:
        state: Final article state

    Returns:
        Path to generated report file
    """
    config = get_config()
    report_path = Path(config.report_path)

    # Build report sections
    sections = [
        _generate_header(state),
        _generate_execution_summary(state),
        _generate_agent_details(state),
        _generate_retry_log(state),
        _generate_final_article(state),
    ]

    # Write report
    report_content = "\n\n".join(sections)

    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report_content)

    return str(report_path)


def _generate_header(state: ArticleState) -> str:
    """Generate report header."""
    topic = state.get("topic", "Unknown Topic")
    completed = state.get("completed", False)
    end_time = state.get("end_time")

    if end_time:
        timestamp = datetime.fromisoformat(end_time).strftime('%Y-%m-%d %H:%M:%S')
    else:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    status_emoji = "✅" if completed else "❌"
    status_text = "Success" if completed else "Failed"

    return f"""# Article Generation Report

**Topic**: {topic}
**Generated**: {timestamp}
**Status**: {status_emoji} {status_text}
"""


def _generate_execution_summary(state: ArticleState) -> str:
    """Generate execution summary."""
    start_time = state.get("start_time")
    end_time = state.get("end_time")

    if start_time and end_time:
        start_dt = datetime.fromisoformat(start_time)
        end_dt = datetime.fromisoformat(end_time)
        duration = (end_dt - start_dt).total_seconds()
        duration_str = f"{duration:.2f}s ({duration / 60:.1f}m)"
    else:
        duration_str = "N/A"

    execution_log = state.get("execution_log", [])
    unique_agents = len(set(log.get("agent", "") for log in execution_log))

    retry_count = sum(state.get("retry_count", {}).values())

    # Count HITL interventions (approval/rejection events)
    hitl_count = sum(1 for log in execution_log if "hitl" in log.get("agent", "").lower())

    return f"""## Execution Summary

- **Total Duration**: {duration_str}
- **Agents Executed**: {unique_agents}
- **Total Retries**: {retry_count}
- **HITL Interventions**: {hitl_count}
"""


def _generate_agent_details(state: ArticleState) -> str:
    """Generate detailed agent execution log."""
    execution_log = state.get("execution_log", [])

    if not execution_log:
        return "## Agent Execution Details\n\nNo execution log available."

    lines = ["## Agent Execution Details\n"]

    for log in execution_log:
        agent = log.get("agent", "Unknown")
        timestamp = log.get("timestamp", "")
        status = log.get("status", "unknown")
        result_summary = log.get("result_summary", "No summary")
        duration = log.get("duration", 0)

        # Format timestamp
        if timestamp:
            try:
                dt = datetime.fromisoformat(timestamp)
                time_str = dt.strftime('%H:%M:%S')
            except:
                time_str = timestamp
        else:
            time_str = "N/A"

        # Status emoji
        status_emoji = {
            "success": "✅",
            "error": "❌",
            "retry": "🔄"
        }.get(status, "⚪")

        lines.append(f"### {status_emoji} {agent} - {time_str}")
        lines.append(f"**Status**: {status}")
        lines.append(f"**Duration**: {duration:.2f}s")
        lines.append(f"**Result**: {result_summary}")
        lines.append("")

    return "\n".join(lines)


def _generate_retry_log(state: ArticleState) -> str:
    """Generate retry attempts log."""
    retry_count = state.get("retry_count", {})
    errors = state.get("errors", [])

    if not any(retry_count.values()) and not errors:
        return "## Retry Log\n\nNo retries needed. All agents succeeded on first attempt."

    lines = ["## Retry Log\n"]

    # Retry counts per agent
    if any(retry_count.values()):
        lines.append("### Retry Attempts by Agent\n")
        for agent, count in retry_count.items():
            if count > 0:
                lines.append(f"- **{agent}**: {count} retry attempts")
        lines.append("")

    # Error details
    if errors:
        lines.append("### Error Details\n")
        for i, error in enumerate(errors, 1):
            agent = error.get("agent", "Unknown")
            error_msg = error.get("error", "No message")
            timestamp = error.get("timestamp", "N/A")
            retry_level = error.get("retry_level", 0)

            lines.append(f"**Error #{i}**")
            lines.append(f"- Agent: {agent}")
            lines.append(f"- Message: {error_msg}")
            lines.append(f"- Retry Level: {retry_level}")
            lines.append(f"- Time: {timestamp}")
            lines.append("")

    return "\n".join(lines)


def _generate_final_article(state: ArticleState) -> str:
    """Generate final article section."""
    final_article = state.get("final_article", "")

    if not final_article:
        # Fallback to draft if no final article
        final_article = state.get("draft_article", "")

    if not final_article:
        return "## Final Article\n\nNo article was generated."

    return f"""## Final Article

---

{final_article}

---

**End of Article**
"""


def format_duration(seconds: float) -> str:
    """Format duration in human-readable format.

    Args:
        seconds: Duration in seconds

    Returns:
        Formatted string (e.g., "2m 30s")
    """
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}m {secs}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"
