"""Vector store for document retrieval in Graph RAG system."""

import logging
from typing import List, Dict, Optional
from llama_index.core import VectorStoreIndex, Document, StorageContext
from llama_index.core.vector_stores import SimpleVectorStore
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI
from llama_index.core import Settings
import json
from pathlib import Path

from graph_rag.config import (
    OPENAI_API_KEY,
    EMBEDDING_MODEL,
    LLM_MODEL,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    DATA_DIR,
    TOP_K_DOCS,
)

logger = logging.getLogger(__name__)


class DocumentVectorStore:
    """Vector store for company document retrieval."""

    def __init__(self):
        """Initialize vector store and embeddings."""
        # Configure global settings
        Settings.llm = OpenAI(model=LLM_MODEL, api_key=OPENAI_API_KEY)
        Settings.embed_model = OpenAIEmbedding(
            model=EMBEDDING_MODEL, api_key=OPENAI_API_KEY
        )
        Settings.chunk_size = CHUNK_SIZE
        Settings.chunk_overlap = CHUNK_OVERLAP

        # Initialize simple vector store
        self.vector_store = SimpleVectorStore()
        self.storage_context = StorageContext.from_defaults(
            vector_store=self.vector_store
        )

        self.index: Optional[VectorStoreIndex] = None
        logger.info("Document vector store initialized")

    def load_documents_from_companies(
        self, companies_file: Path = DATA_DIR / "companies.json"
    ) -> List[Document]:
        """
        Load company data as documents.

        Args:
            companies_file: Path to companies JSON file

        Returns:
            List of LlamaIndex Document objects
        """
        logger.info(f"Loading documents from: {companies_file}")

        with open(companies_file, "r", encoding="utf-8") as f:
            companies = json.load(f)

        documents = []
        for company in companies:
            # Create rich text representation
            text_parts = [
                f"公司名称：{company['name']}",
                f"公司类型：{company['type']}",
                f"所属行业：{company['industry']}",
                f"成立时间：{company['founded']}",
                f"公司简介：{company['description']}",
            ]

            # Add optional fields
            if "revenue" in company:
                text_parts.append(f"营业收入：{company['revenue']}")
            if "employees" in company:
                text_parts.append(f"员工人数：{company['employees']}")
            if "valuation" in company:
                text_parts.append(f"公司估值：{company['valuation']}")
            if "assets" in company:
                text_parts.append(f"管理资产：{company['assets']}")

            text = "\n".join(text_parts)

            doc = Document(
                text=text,
                metadata={
                    "company_id": company["id"],
                    "company_name": company["name"],
                    "type": company["type"],
                    "industry": company["industry"],
                },
                id_=company["id"],
            )
            documents.append(doc)

        logger.info(f"Loaded {len(documents)} company documents")
        return documents

    def build_index(self, documents: List[Document]) -> VectorStoreIndex:
        """
        Build vector index from documents.

        Args:
            documents: List of Document objects

        Returns:
            Built VectorStoreIndex
        """
        logger.info(f"Building index with {len(documents)} documents...")

        self.index = VectorStoreIndex.from_documents(
            documents,
            storage_context=self.storage_context,
            show_progress=True,
        )

        logger.info("Index built successfully")
        return self.index

    def query(self, query_text: str, top_k: int = TOP_K_DOCS) -> Dict:
        """
        Query the vector store.

        Args:
            query_text: Query text
            top_k: Number of results to return

        Returns:
            Query results with documents and scores
        """
        if self.index is None:
            raise ValueError("Index not built. Call build_index first.")

        logger.info(f"Querying: {query_text}")

        query_engine = self.index.as_query_engine(
            similarity_top_k=top_k,
            response_mode="tree_summarize",
        )

        response = query_engine.query(query_text)

        # Extract source nodes
        results = []
        for node in response.source_nodes:
            results.append({
                "text": node.node.text,
                "score": node.score,
                "metadata": node.node.metadata,
                "company_id": node.node.metadata.get("company_id"),
                "company_name": node.node.metadata.get("company_name"),
            })

        return {
            "answer": str(response),
            "documents": results,
            "query": query_text,
        }

    def similarity_search(
        self, query_text: str, top_k: int = TOP_K_DOCS
    ) -> List[Dict]:
        """
        Perform similarity search without LLM synthesis.

        Args:
            query_text: Query text
            top_k: Number of results to return

        Returns:
            List of similar documents with scores
        """
        if self.index is None:
            raise ValueError("Index not built. Call build_index first.")

        logger.info(f"Similarity search: {query_text}")

        retriever = self.index.as_retriever(similarity_top_k=top_k)
        nodes = retriever.retrieve(query_text)

        results = []
        for node in nodes:
            results.append({
                "text": node.node.text,
                "score": node.score,
                "metadata": node.node.metadata,
                "company_id": node.node.metadata.get("company_id"),
                "company_name": node.node.metadata.get("company_name"),
            })

        return results

    def get_document_by_company(self, company_name: str) -> Optional[Dict]:
        """
        Get document for a specific company.

        Args:
            company_name: Name of the company

        Returns:
            Document information if found
        """
        if self.index is None:
            raise ValueError("Index not built. Call build_index first.")

        # Search for the company
        results = self.similarity_search(company_name, top_k=1)

        if results and results[0]["company_name"] == company_name:
            return results[0]

        return None


def initialize_vector_store(rebuild: bool = False) -> DocumentVectorStore:
    """
    Initialize document vector store with company data.

    Args:
        rebuild: Whether to rebuild the index

    Returns:
        Initialized DocumentVectorStore instance
    """
    store = DocumentVectorStore()

    if rebuild or store.index is None:
        documents = store.load_documents_from_companies()
        store.build_index(documents)

    logger.info("Vector store initialized")
    return store
