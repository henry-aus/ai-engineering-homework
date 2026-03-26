"""LangChain chain setup."""
import json
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.runnables import RunnablePassthrough

from .config import Config
from .prompts import get_extraction_prompt
from .schemas import ExtractedInfo


def create_extraction_chain():
    """Create a chain that extracts structured information from user input."""

    # Validate configuration
    Config.validate()

    # Initialize LLM
    llm = ChatOpenAI(
        model=Config.OPENAI_MODEL,
        api_key=Config.OPENAI_API_KEY,
        temperature=0,  # Deterministic for extraction
    )

    # Create parser
    parser = JsonOutputParser(pydantic_object=ExtractedInfo)

    # Create prompt
    prompt = get_extraction_prompt()

    # Build chain: Prompt → LLM → Parser
    chain = prompt | llm | parser

    return chain


def extract_info(user_input: str) -> ExtractedInfo:
    """
    Extract structured information from user input.

    Args:
        user_input: The user's message

    Returns:
        ExtractedInfo object with parsed information
    """
    chain = create_extraction_chain()

    try:
        # Run the chain
        result = chain.invoke({"user_input": user_input})

        # Ensure raw_message is included
        if "raw_message" not in result:
            result["raw_message"] = user_input

        # Convert to Pydantic model
        extracted = ExtractedInfo(**result)
        return extracted

    except Exception as e:
        # Fallback to general intent if parsing fails
        print(f"⚠️  解析失败: {e}")
        return ExtractedInfo(
            intent="general",
            date_mentioned=None,
            original_date_expression=None,
            entities={},
            raw_message=user_input
        )
