"""Pydantic schemas for structured output."""
from typing import Optional, Dict, Any, Literal
from pydantic import BaseModel, Field


class ExtractedInfo(BaseModel):
    """Structured information extracted from user message."""

    intent: Literal["order_query", "refund_request", "invoice_request", "general"] = Field(
        description="The user's intent: order_query, refund_request, invoice_request, or general"
    )
    date_mentioned: Optional[str] = Field(
        None,
        description="Date mentioned in YYYY-MM-DD format, or null if no date mentioned"
    )
    original_date_expression: Optional[str] = Field(
        None,
        description="The original date expression from user (e.g., '昨天', '三天前')"
    )
    entities: Dict[str, Any] = Field(
        default_factory=dict,
        description="Other entities extracted (order_id, etc.)"
    )
    raw_message: str = Field(
        description="The original user message"
    )
