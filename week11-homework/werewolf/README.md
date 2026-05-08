# AI Werewolf Game - LangChain + LangGraph Implementation

An intelligent multi-agent Werewolf game system where 5 AI agents (2 werewolves + 3 villagers) play against each other with realistic social deduction, strategy, and personality-driven behaviors.

## Architecture Overview

### Agent Design

- **2 Werewolves**: Coordinate night kills, hide identity, deflect suspicion
  - Alice: Aggressive personality (proactive accusations)
  - Bob: Cautious personality (follows crowd)

- **3 Villagers**: Deduce werewolf identities through logic
  - Charlie: Logical personality (evidence-based reasoning)
  - Diana: Emotional personality (trust-based decisions)
  - Eve: Observant personality (pattern recognition)

- **Moderator**: Orchestrated by LangGraph state machine

### Game Flow

```
Night Phase → Day Announcement → Speech Phase → Voting Phase → Victory Check → [Loop or End]
```

### Memory System

**Two-tier architecture:**

1. **Episodic Memory** (LangGraph Checkpointer)
   - Stores conversation threads and game state across phases
   - Enables game state persistence

2. **Semantic Memory** (FAISS Vector Store + RAG)
   - Stores behavioral observations with embeddings
   - Enables similarity search for relevant past events
   - Retrieves top-5 memories to augment agent decisions

**RAG Flow:**
```
Agent Decision → Retrieve relevant memories → Augment prompt → Generate response → Store observation
```

### Technology Stack

- **LangChain 1.x**: Core agent framework
- **LangGraph 1.x**: State machine workflow
- **FAISS**: Vector store for semantic memory
- **OpenAI**: LLM provider (GPT-4o-mini by default)
- **Rich**: Beautiful console output
- **Structlog**: Structured logging

## Installation

1. Create virtual environment with Python 3.13:
```bash
uv venv --python 3.13 ./venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
uv sync
```

3. Configure API keys:
```bash
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

## Usage

Run the game:
```bash
python -m werewolf.main
```

The game will:
1. Initialize 5 AI players with distinct personalities
2. Execute rounds with night kills and day discussions
3. Display rich console output with color-coded phases
4. Export detailed logs to `game_logs/` folder

## Output Files

After each game:

- `game_logs/game_1_log.json` - Complete game narrative
- `game_logs/game_1_trace.json` - Detailed Thought-Action-Observation traces

## Project Structure

```
werewolf/
├── game/
│   ├── state.py          # GameState TypedDict definition
│   ├── graph.py          # LangGraph workflow construction
│   └── phases.py         # Phase logic (night, day, speech, voting)
├── agents/
│   └── player.py         # PlayerAgent with role-specific behaviors
├── memory/
│   └── semantic.py       # FAISS vector store + RAG
├── prompts/
│   ├── system_prompts.py # Role-based system prompts
│   └── personalities.py  # Personality trait templates
├── tracing/
│   └── tracker.py        # Execution trace logging
├── utils/
│   ├── llm.py           # LLM initialization
│   └── logging.py       # Structured logging setup
└── main.py              # Entry point
```

## Key Features

### 1. Role-Based Prompting
Each player receives role-specific system prompts:
- Werewolves: Coordinate, hide identity, deflect
- Villagers: Analyze, deduce, collaborate

### 2. Personality Injection
Five distinct personalities affect decision-making:
- Aggressive werewolf: Bold accusations
- Cautious werewolf: Observes and follows
- Logical villager: Evidence-based
- Emotional villager: Instinct-driven
- Observant villager: Pattern-seeking

### 3. RAG-Enhanced Reasoning
Every decision retrieves top-5 relevant memories:
- Speech generation references past accusations
- Voting decisions consider historical patterns
- Night kills factor in threat assessment

### 4. Execution Tracing
Full Thought-Action-Observation logging:
- **Thought**: Internal reasoning before decision
- **Action**: Actual decision (speech, vote, kill)
- **Observation**: Event perceived and stored

### 5. Rich Console Output
Beautiful visualization with:
- Color-coded phases (Night=Cyan, Day=Yellow, Speech=Green, Voting=Magenta)
- Bordered panels for announcements
- Tables for player status
- Progress indicators

## Example Game Flow

```
ROUND 1 - NIGHT PHASE
Werewolves discussing target...
Alice proposes: player_3
Bob proposes: player_4
Werewolves decided to eliminate: player_3

DAY 1 - DAWN ANNOUNCEMENT
Charlie was found dead!

DAY 1 - DISCUSSION PHASE
Alice speaks: "I find Diana suspicious. She's been too quiet..."
Bob speaks: "I agree with Alice. Diana seems evasive..."
[... more speeches ...]

DAY 1 - VOTING PHASE
Alice votes for: player_4
Bob votes for: player_4
[... more votes ...]
Diana has been eliminated by vote!
Diana was a VILLAGER

Round 1 Status
┌────────────────────┬───────┐
│ Status             │ Count │
├────────────────────┼───────┤
│ Alive Werewolves   │ 2     │
│ Alive Villagers    │ 1     │
│ Total Alive        │ 3     │
└────────────────────┴───────┘

[Game continues...]
```

## Cost & Performance

### Token Usage
- Per player per round: ~500-1000 tokens input + ~200-400 tokens output
- 5 players × 5 rounds ≈ 20-30K tokens per game
- Estimated cost with GPT-4o-mini: ~$0.10-0.20 per game

### Performance
- Average game completion: 3-5 minutes
- Agent response latency: 2-3 seconds per decision
- Memory retrieval: <100ms per query

## Design Decisions

### Why LangGraph over AutoGen/CrewAI?

1. **Flow Control**: LangGraph provides explicit state machine for game phases
2. **Checkpointing**: Built-in episodic memory with MemorySaver
3. **Flexibility**: Easy to add conditional edges for victory conditions
4. **Scalability**: Can extend with more complex phase logic

### Memory Architecture Rationale

**Episodic (Checkpointer)**:
- Maintains complete conversation history
- Enables state rollback/replay
- Low overhead for sequential access

**Semantic (Vector Store)**:
- Enables similarity-based retrieval
- Surfaces relevant patterns across rounds
- Scales to longer games without context window issues

### RAG Integration

RAG enhances every decision by:
1. Retrieving top-5 most relevant past observations
2. Providing context about suspicious behaviors
3. Enabling references to specific past events
4. Improving argument quality in speeches

## Debugging & Analysis

### View Execution Traces
```bash
cat game_logs/game_1_trace.json | jq '.[] | select(.type=="thought")'
```

### Analyze Game Outcomes
```bash
cat game_logs/game_1_log.json | jq '.winner'
```

### Track Agent Decisions
```bash
cat game_logs/game_1_trace.json | jq '.[] | select(.player_id=="player_1" and .phase=="voting")'
```

## Future Enhancements

- [ ] Add Sheriff/Doctor roles
- [ ] Implement voting defense speeches
- [ ] Add more personality archetypes
- [ ] Web UI with Streamlit
- [ ] Multi-game win rate tracking
- [ ] Advanced RAG with reranking
- [ ] Parallel game execution
- [ ] Historical pattern analysis

## Credits

Developed as final homework for AI Engineering Training Course.
Framework: LangChain 1.x + LangGraph 1.x
