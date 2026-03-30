"""
Milvus FAQ Retrieval System

A production-ready FAQ retrieval system powered by Milvus and LlamaIndex.
"""

__version__ = "1.0.0"
__author__ = "AI Engineer Training"

from milvus_faq.vector_store import MilvusFAQStore
from milvus_faq.data_loader import FAQDataLoader
from milvus_faq.config import (
    MILVUS_HOST,
    MILVUS_PORT,
    MILVUS_COLLECTION_NAME,
    TOP_K,
)

__all__ = [
    "MilvusFAQStore",
    "FAQDataLoader",
    "MILVUS_HOST",
    "MILVUS_PORT",
    "MILVUS_COLLECTION_NAME",
    "TOP_K",
]
