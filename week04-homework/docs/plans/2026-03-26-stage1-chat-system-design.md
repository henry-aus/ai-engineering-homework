# Stage 1: Basic Chat System with Time Inference

**Date:** 2026-03-26
**Status:** Approved

## Overview

Build a basic conversational system using LangChain that can understand user queries about orders and parse relative time expressions (e.g., "昨天" → "2026-03-25"). The system extracts structured information and logs it, preparing the foundation for Stage 2's tool calling.

## Architecture

### Core Components

1. **Main Chat Loop** (`main.py`)
   - Simple CLI using `input()`
   - Instantiates chain and handles conversation flow
   - Logs extracted structured data

2. **LangChain Chain Structure:**
   ```
   PromptTemplate → ChatOpenAI → StructuredOutputParser
   ```
   - **PromptTemplate**: Instructs LLM to extract intent + dates
   - **ChatOpenAI**: OpenAI model (GPT-3.5-turbo or GPT-4)
   - **StructuredOutputParser**: Parses output into structured format

3. **Structured Output Schema:**
   ```python
   {
     "intent": "order_query" | "refund_request" | "invoice_request" | "general",
     "date_mentioned": "2026-03-23" | null,
     "original_date_expression": "昨天" | "三天前" | null,
     "entities": {"order_id": null, ...},
     "raw_message": str
   }
   ```

4. **Configuration:**
   - `.env` file for `OPENAI_API_KEY`
   - Settings loaded via `python-dotenv`

## Prompt Engineering & Date Parsing

### Prompt Template Design

The prompt includes:
1. **System context**: Current date injected dynamically
2. **Task instruction**: Extract intent and parse time references
3. **Date parsing examples**: Show relative date conversion
4. **Output format**: JSON schema specification

### Date Parsing Strategy

- Inject current date (2026-03-26) into prompt
- Let LLM convert Chinese expressions ("昨天", "三天前", "上个月15号") to YYYY-MM-DD
- Use `python-dateutil` for any additional validation if needed
- LLM handles the heavy lifting for Chinese → date conversion

### Example Flow

**User:** "我昨天下的单"

**LLM extracts:**
```json
{
  "intent": "order_query",
  "date_mentioned": "2026-03-25",
  "original_date_expression": "昨天",
  "entities": {},
  "raw_message": "我昨天下的单"
}
```

**System logs:** Structured JSON to console/file

**System responds:** "好的，我看到您询问 2026-03-25 (昨天) 的订单信息。[已记录查询意图]"

## Project Structure

```
smart_customer_service/
├── __init__.py
├── main.py                 # CLI entry point
├── chain.py               # LangChain chain setup
├── prompts.py             # Prompt templates
├── schemas.py             # Pydantic models for structured output
├── config.py              # Configuration loading
└── utils/
    └── date_parser.py     # Date parsing helpers (if needed)
```

## Implementation Details

### Pydantic Schema (`schemas.py`)

```python
class ExtractedInfo(BaseModel):
    intent: Literal["order_query", "refund_request", "invoice_request", "general"]
    date_mentioned: Optional[str] = None  # YYYY-MM-DD format
    original_date_expression: Optional[str] = None
    entities: Dict[str, Any] = {}
    raw_message: str
```

### Chain Builder (`chain.py`)

- Factory function creates the chain
- Uses `PydanticOutputParser` for structured output
- Injects current date dynamically
- Returns runnable chain

### Logging Strategy

- Print structured JSON to console for debugging
- Optionally append to `logs/queries.jsonl` file
- Shows "system understanding" without actual tool execution

### Error Handling

- If LLM output parsing fails, fallback to general intent
- Graceful handling of API errors
- User-friendly error messages

### Exit Strategy

- Type "退出", "exit", or "quit" to end conversation
- Ctrl+C handled gracefully

## Success Criteria

- [ ] User can start CLI chat loop
- [ ] System correctly parses "昨天/今天/明天"
- [ ] System handles advanced expressions like "三天前", "上个月15号"
- [ ] Structured data logged to console
- [ ] Clean error handling and exit flow

## Future Stages

**Stage 2:** Add multi-turn conversation and tool calling (order query, refund)
**Stage 3:** Implement hot-reload for models and plugins, add /health endpoint
