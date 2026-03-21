"""Configuration settings for Graph RAG system."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = Path(__file__).parent / "data"

# OpenAI Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
EMBEDDING_MODEL = "text-embedding-3-small"
LLM_MODEL = "gpt-4o-mini"

# Neo4j Configuration
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password123")
NEO4J_DATABASE = "neo4j"

# Vector Store Configuration (using in-memory for simplicity)
VECTOR_STORE_TYPE = "simple"  # Can be "milvus" or "simple"
EMBEDDING_DIMENSION = 1536

# Chunking Configuration
CHUNK_SIZE = 512
CHUNK_OVERLAP = 50

# Retrieval Configuration
TOP_K_DOCS = 3
TOP_K_GRAPH = 5
MAX_HOP = 3

# Hybrid Scoring Weights
VECTOR_WEIGHT = 0.5
GRAPH_WEIGHT = 0.5
CONFIDENCE_THRESHOLD = 0.6

# API Configuration
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8001"))
