"""
Graph RAG System

A hybrid question answering system that combines:
- Document Retrieval (RAG) using vector embeddings
- Knowledge Graph Reasoning (KG) using Neo4j
- Multi-hop inference with explainable reasoning paths
"""

__version__ = "1.0.0"
__author__ = "AI Engineer Training"

from graph_rag.graph_store import Neo4jGraphStore, initialize_graph
from graph_rag.vector_store import DocumentVectorStore, initialize_vector_store
from graph_rag.hybrid_query import HybridQueryEngine
from graph_rag.config import (
    NEO4J_URI,
    NEO4J_USER,
    NEO4J_PASSWORD,
    TOP_K_DOCS,
    TOP_K_GRAPH,
    MAX_HOP,
)

__all__ = [
    "Neo4jGraphStore",
    "initialize_graph",
    "DocumentVectorStore",
    "initialize_vector_store",
    "HybridQueryEngine",
    "NEO4J_URI",
    "NEO4J_USER",
    "NEO4J_PASSWORD",
    "TOP_K_DOCS",
    "TOP_K_GRAPH",
    "MAX_HOP",
]
