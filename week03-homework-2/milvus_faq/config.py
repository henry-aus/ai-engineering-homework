"""Configuration settings for Milvus FAQ system."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
FAQ_DATA_PATH = Path(__file__).parent / "faq_data.json"

# OpenAI Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
EMBEDDING_MODEL = "text-embedding-3-small"
LLM_MODEL = "gpt-4o-mini"

# Milvus Configuration
MILVUS_HOST = os.getenv("MILVUS_HOST", "localhost")
MILVUS_PORT = int(os.getenv("MILVUS_PORT", "19530"))
MILVUS_COLLECTION_NAME = "faq_collection"
MILVUS_DIMENSION = 1536  # text-embedding-3-small dimension

# Chunking Configuration
CHUNK_SIZE = 512
CHUNK_OVERLAP = 50

# Retrieval Configuration
TOP_K = 3
SIMILARITY_THRESHOLD = 0.7

# API Configuration
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))
