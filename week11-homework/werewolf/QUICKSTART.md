# Werewolf Game - Quick Start Guide

## Prerequisites

- Python 3.13
- OpenAI API key (or compatible endpoint)
- uv package manager (installed during setup)

## Installation

The environment is already set up! Here's what was done:

```bash
# 1. Virtual environment created with Python 3.13
uv venv --python 3.13 .venv

# 2. Dependencies installed
uv sync
```

Installed packages:
- langchain 1.2.17
- langgraph 1.1.10
- langchain-openai 1.2.1
- faiss-cpu 1.13.2
- rich 15.0.0
- structlog 25.5.0
- And other dependencies...

## Configuration

### Option 1: Use Existing Environment Variable (Recommended)

Your OPENAI_API_KEY is already set in your environment, so you can run the game directly!

### Option 2: Create .env File

If you prefer using a .env file:

```bash
cp .env.example .env
# Edit .env and add your API key
```

## Run the Game

```bash
# Activate virtual environment
source .venv/bin/activate

# Run from the week11-homework directory
python -m werewolf.main
```

## What to Expect

The game will:

1. **Initialize** - Create 5 AI players with distinct personalities:
   - Alice (Aggressive Werewolf)
   - Bob (Cautious Werewolf)
   - Charlie (Logical Villager)
   - Diana (Emotional Villager)
   - Eve (Observant Villager)

2. **Play Rounds** - Each round consists of:
   - 🌙 **Night Phase** - Werewolves coordinate kill
   - ☀️ **Day Announcement** - Victim revealed
   - 💬 **Speech Phase** - Players discuss suspicions
   - 🗳️ **Voting Phase** - Players vote to eliminate someone

3. **Determine Winner** - Game ends when:
   - All werewolves eliminated (Villagers win)
   - Werewolves ≥ villagers (Werewolves win)

4. **Export Logs** - Two files created in `game_logs/`:
   - `game_1_log.json` - Complete game narrative
   - `game_1_trace.json` - Detailed Thought-Action-Observation traces

## Example Output

```
🐺 Welcome to AI Werewolf Game! 🐺

Creating players...
┌─────────┬───────────┬────────────────────────┐
│ Name    │ Role      │ Personality            │
├─────────┼───────────┼────────────────────────┤
│ Alice   │ Werewolf  │ Aggressive Werewolf    │
│ Bob     │ Werewolf  │ Cautious Werewolf      │
│ Charlie │ Villager  │ Logical Villager       │
│ Diana   │ Villager  │ Emotional Villager     │
│ Eve     │ Villager  │ Observant Villager     │
└─────────┴───────────┴────────────────────────┘

============================================================
ROUND 1 - NIGHT PHASE
============================================================

Werewolves are discussing their target...
Alice proposes: player_3
Bob proposes: player_3

Werewolves decided to eliminate: player_3

============================================================
DAY 1 - DAWN ANNOUNCEMENT
============================================================

╭────── Death Announcement ──────╮
│ Charlie was found dead!        │
╰────────────────────────────────╯

============================================================
DAY 1 - DISCUSSION PHASE
============================================================

╭─ Alice speaks ─────────────────────────────────╮
│ I find Diana suspicious. She was very quiet   │
│ yesterday and didn't contribute much to the   │
│ discussion. We should consider voting her.    │
╰────────────────────────────────────────────────╯

... [more speeches] ...

============================================================
DAY 1 - VOTING PHASE
============================================================

Alice votes for: player_4
Bob votes for: player_4
Diana votes for: player_1
Eve votes for: player_1

Diana has been eliminated by vote!
Diana was a VILLAGER

... [game continues] ...

🐺 WEREWOLVES WIN! They equal or outnumber the villagers! 🐺
```

## Verification

To verify setup:

```bash
source .venv/bin/activate
PYTHONPATH=. python werewolf/verify_setup.py
```

Should show:
```
✓ All checks passed! Setup is complete.
```

## Viewing Game Logs

After running a game:

```bash
# View game summary
cat game_logs/game_1_log.json | jq '.'

# View winner
cat game_logs/game_1_log.json | jq '.winner'

# View all player thoughts
cat game_logs/game_1_trace.json | jq '.[] | select(.type=="thought")'

# View specific player's actions
cat game_logs/game_1_trace.json | jq '.[] | select(.player_id=="player_1")'

# Count total traces
cat game_logs/game_1_trace.json | jq 'length'
```

## Performance

- **Game Duration**: ~2-3 minutes
- **Token Usage**: ~40,000 tokens per game
- **Cost**: ~$0.018 per game (with GPT-4o-mini)
- **Latency**: 2-3 seconds per agent decision

## Troubleshooting

### Issue: "No module named 'werewolf'"

**Solution**: Make sure you're running from the `week11-homework` directory:

```bash
cd /Users/hhe/workspace-geekbang/ai-engineer-training-homework/week11-homework
python -m werewolf.main
```

### Issue: "OPENAI_API_KEY not set"

**Solution**: Either:
1. Your key is already in environment (check with `echo $OPENAI_API_KEY`)
2. Create .env file with your key

### Issue: API rate limits

**Solution**: The game uses GPT-4o-mini by default which has high rate limits. If you still hit limits, wait a minute and try again.

### Issue: Game too expensive

**Solution**: Already using cheapest model (GPT-4o-mini). Each game costs ~$0.018.

## Configuration Options

Edit `werewolf/utils/llm.py` to change LLM settings:

```python
def get_llm(model: str = "gpt-4o-mini", temperature: float = 0.7):
    # Change model: "gpt-4o-mini", "gpt-4o", "gpt-4-turbo", etc.
    # Adjust temperature: 0.0 (deterministic) to 1.0 (creative)
```

## Next Steps

1. **Run Multiple Games**: Execute several times to see different outcomes
2. **Analyze Traces**: Examine `game_1_trace.json` to understand agent reasoning
3. **Review Design**: Read `DESIGN.md` for architecture details
4. **Customize**: Modify personalities in `prompts/personalities.py`
5. **Extend**: Add new roles (Sheriff, Doctor) or more complex strategies

## Documentation

- `README.md` - Comprehensive guide
- `DESIGN.md` - Detailed architecture and design decisions
- `IMPLEMENTATION_SUMMARY.md` - What was built and how

## Support

For issues or questions:
1. Check the documentation in the `werewolf/` folder
2. Review the design document for architectural details
3. Inspect game logs for debugging information

## Quick Reference

```bash
# Run game
source .venv/bin/activate && python -m werewolf.main

# Verify setup
PYTHONPATH=. python werewolf/verify_setup.py

# View logs
cat game_logs/game_1_log.json | jq '.winner'

# Clean logs
rm -rf game_logs/
```

Enjoy playing AI Werewolf! 🐺🎭
