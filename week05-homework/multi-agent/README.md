# Multi-Agent Article Writing System

A sophisticated multi-agent system built with LangGraph and MCP protocol that automates article writing through collaborative agents.

## Overview

This system orchestrates four specialized agents that work sequentially with human-in-the-loop checkpoints:

1. **Research Agent** - Gathers information using Tavily Search API
2. **Writing Agent** - Creates article draft from research
3. **Review Agent** - Evaluates quality and provides feedback
4. **Polishing Agent** - Produces final polished article

## Features

- ✅ **LangGraph State Machine** - Robust workflow orchestration
- ✅ **Human-in-the-Loop (HITL)** - Review and approve at each stage
- ✅ **3-Level Retry Mechanism**:
  - Level 1: Same agent retry (max 2 attempts)
  - Level 2: Backup agent with enhanced capabilities
  - Level 3: User guidance input
- ✅ **Rich Terminal UI** - Real-time collaboration display
- ✅ **Comprehensive Logging** - Full execution trace in report.md
- ✅ **Tavily Search Integration** - High-quality web research

## Installation

### Prerequisites

- Python 3.11 or higher
- `uv` package manager (or `pip`)

### Setup

1. **Install dependencies**:

```bash
cd week05-homework
uv sync
# or: pip install -e .
```

2. **Configure environment**:

```bash
cp .env.example .env
# Edit .env and add your API keys:
# - ANTHROPIC_API_KEY (get from https://console.anthropic.com/)
# - TAVILY_API_KEY (get from https://tavily.com/)
```

## Usage

### Basic Usage

```bash
python -m multi-agent.main --topic "Your Article Topic"
```

### Advanced Options

```bash
python -m multi-agent.main \
  --topic "AI Agents in 2026" \
  --style professional \
  --word-count 1500 \
  --output ./my-article-report.md
```

### Arguments

- `--topic` (required): Article topic
- `--style`: Writing style - `professional`, `casual`, `technical`, `academic` (default: professional)
- `--word-count`: Target word count (default: 1500)
- `--output`: Report output path (default: ./report.md)

## Workflow

The system follows this workflow:

```
Initialize → Research → HITL → Writing → HITL → Review → HITL → Polishing → Finalize
                ↓                ↓                ↓
             Retry Handler (3-level strategy)
```

### HITL Checkpoints

At each checkpoint, you can:
- **Approve (a)**: Continue to next stage
- **Reject (r)**: Trigger retry mechanism with feedback
- **Feedback (f)**: Provide notes but continue

### Retry Mechanism

When you reject an agent's output:

1. **Level 1** (attempts 1-2): Same agent retries with enhanced context
2. **Level 2** (attempts 3-4): Backup agent with higher capabilities
3. **Level 3** (attempt 5+): System requests your guidance

## Architecture

```
multi-agent/
├── agents/          # Agent implementations
│   ├── base.py
│   ├── research_agent.py
│   ├── writing_agent.py
│   ├── review_agent.py
│   ├── polishing_agent.py
│   └── backup_agents.py
├── graph/           # LangGraph workflow
│   ├── state.py     # State schema
│   ├── workflow.py  # StateGraph construction
│   ├── nodes.py     # Node functions
│   └── edges.py     # Conditional routing
├── tools/           # Integrations
│   └── tavily_search.py
├── hitl/            # Human-in-the-loop
│   └── checkpoints.py
├── retry/           # Retry strategy
│   └── strategy.py
├── utils/           # Utilities
│   ├── terminal.py  # Rich UI
│   └── report_generator.py
├── prompts/         # Agent prompts
└── config.py        # Configuration
```

## Output

The system generates `report.md` containing:

- **Execution Summary**: Duration, agent count, retries
- **Agent Details**: Step-by-step execution log
- **Retry Log**: All retry attempts and reasons
- **Final Article**: Complete polished article

## Example Output

See `report.md` after running the system for a complete example showing:
- Research sources found
- Draft article generation
- Review feedback
- Final polished article
- Complete execution timeline

## Configuration

Environment variables in `.env`:

| Variable | Description | Default |
|----------|-------------|---------|
| `ANTHROPIC_API_KEY` | Claude API key | Required |
| `TAVILY_API_KEY` | Tavily Search API key | Required |
| `CLAUDE_MODEL` | Claude model to use | `claude-3-5-sonnet-20241022` |
| `MAX_RETRIES_LEVEL_1` | Same agent retries | `2` |
| `MAX_RETRIES_LEVEL_2` | Backup agent retries | `2` |
| `HITL_ENABLED` | Enable HITL checkpoints | `true` |
| `TARGET_WORD_COUNT` | Default word count | `1500` |
| `ARTICLE_STYLE` | Default style | `professional` |

## Troubleshooting

### API Key Issues

```
ValueError: ANTHROPIC_API_KEY is required
```

Solution: Ensure `.env` file exists with valid API keys.

### Import Errors

```
ModuleNotFoundError: No module named 'langchain'
```

Solution: Run `uv sync` or `pip install -e .`

### Tavily Search Errors

```
Tavily search error: ...
```

Solution: Verify `TAVILY_API_KEY` is valid and you have API credits.

## Development

### Running Tests

```bash
pytest tests/
```

### Code Structure

- Each agent inherits from `BaseAgent`
- Agents use LLM via `invoke_llm()`
- State updates via dictionary returns
- HITL checkpoints return approval status

## License

MIT License - see LICENSE file

## Credits

Built for AI Engineer Training Course (Week 5 Homework)
- LangGraph for workflow orchestration
- Anthropic Claude for LLM
- Tavily for web search
- Rich for terminal UI
