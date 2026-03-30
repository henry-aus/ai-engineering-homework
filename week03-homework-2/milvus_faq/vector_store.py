"""Milvus vector store implementation."""

import logging
from typing import List, Optional
from llama_index.core import VectorStoreIndex, StorageContext, Document
from llama_index.vector_stores.milvus import MilvusVectorStore
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI
from llama_index.core import Settings

from milvus_faq.config import (
    MILVUS_HOST,
    MILVUS_PORT,
    MILVUS_COLLECTION_NAME,
    MILVUS_DIMENSION,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    EMBEDDING_MODEL,
    LLM_MODEL,
    OPENAI_API_KEY,
    TOP_K,
)

logger = logging.getLogger(__name__)


class MilvusFAQStore:
    """Milvus-based FAQ vector store with hot reload support."""

    def __init__(self):
        """Initialize Milvus vector store and LlamaIndex settings."""
        # Configure global settings
        Settings.llm = OpenAI(model=LLM_MODEL, api_key=OPENAI_API_KEY)
        Settings.embed_model = OpenAIEmbedding(
            model=EMBEDDING_MODEL, api_key=OPENAI_API_KEY
        )
        Settings.chunk_size = CHUNK_SIZE
        Settings.chunk_overlap = CHUNK_OVERLAP

        # Initialize vector store
        self.vector_store = MilvusVectorStore(
            host=MILVUS_HOST,
            port=MILVUS_PORT,
            collection_name=MILVUS_COLLECTION_NAME,
            dim=MILVUS_DIMENSION,
            overwrite=False,
        )

        # Initialize storage context
        self.storage_context = StorageContext.from_defaults(
            vector_store=self.vector_store
        )

        # Initialize index (will be None until first build)
        self.index: Optional[VectorStoreIndex] = None

        # Node parser for chunking
        self.node_parser = SentenceSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
        )

        logger.info(
            f"Initialized Milvus FAQ Store: {MILVUS_HOST}:{MILVUS_PORT}/{MILVUS_COLLECTION_NAME}"
        )

    def build_index(self, documents: List[Document]) -> VectorStoreIndex:
        """
        Build or rebuild the vector index from documents.

        Args:
            documents: List of LlamaIndex Document objects

        Returns:
            VectorStoreIndex: The built index
        """
        logger.info(f"Building index with {len(documents)} documents...")

        # Create index from documents
        self.index = VectorStoreIndex.from_documents(
            documents,
            storage_context=self.storage_context,
            show_progress=True,
        )

        logger.info("Index built successfully")
        return self.index

    def load_index(self) -> Optional[VectorStoreIndex]:
        """
        Load existing index from Milvus.

        Returns:
            VectorStoreIndex if exists, None otherwise
        """
        try:
            self.index = VectorStoreIndex.from_vector_store(
                vector_store=self.vector_store,
            )
            logger.info("Loaded existing index from Milvus")
            return self.index
        except Exception as e:
            logger.warning(f"Could not load existing index: {e}")
            return None

    def add_documents(self, documents: List[Document]) -> None:
        """
        Add new documents to existing index (hot update).

        Args:
            documents: List of new Document objects to add
        """
        if self.index is None:
            logger.warning("No index exists, building new index")
            self.build_index(documents)
            return

        logger.info(f"Adding {len(documents)} documents to existing index...")

        # Insert documents into existing index
        for doc in documents:
            self.index.insert(doc)

        logger.info("Documents added successfully")

    def update_document(self, doc_id: str, document: Document) -> None:
        """
        Update an existing document (hot update).

        Args:
            doc_id: ID of document to update
            document: New document content
        """
        if self.index is None:
            raise ValueError("No index exists")

        logger.info(f"Updating document: {doc_id}")

        # Delete old document
        self.index.delete_ref_doc(doc_id, delete_from_docstore=True)

        # Insert new document
        self.index.insert(document)

        logger.info(f"Document {doc_id} updated successfully")

    def delete_document(self, doc_id: str) -> None:
        """
        Delete a document from index (hot update).

        Args:
            doc_id: ID of document to delete
        """
        if self.index is None:
            raise ValueError("No index exists")

        logger.info(f"Deleting document: {doc_id}")
        self.index.delete_ref_doc(doc_id, delete_from_docstore=True)
        logger.info(f"Document {doc_id} deleted successfully")

    def query(self, query_text: str, top_k: int = TOP_K) -> dict:
        """
        Query the FAQ system.

        Args:
            query_text: User's question
            top_k: Number of results to return

        Returns:
            dict with query results and metadata
        """
        if self.index is None:
            raise ValueError("No index exists. Please build index first.")

        logger.info(f"Querying: {query_text}")

        # Create query engine
        query_engine = self.index.as_query_engine(
            similarity_top_k=top_k,
            response_mode="tree_summarize",
        )

        # Execute query
        response = query_engine.query(query_text)

        # Extract source nodes for detailed information
        results = []
        for node in response.source_nodes:
            results.append(
                {
                    "text": node.node.text,
                    "score": node.score,
                    "metadata": node.node.metadata,
                }
            )

        return {
            "answer": str(response),
            "sources": results,
            "query": query_text,
        }

    def similarity_search(self, query_text: str, top_k: int = TOP_K) -> List[dict]:
        """
        Perform similarity search without LLM synthesis.

        Args:
            query_text: User's question
            top_k: Number of results to return

        Returns:
            List of matching documents with scores
        """
        if self.index is None:
            raise ValueError("No index exists. Please build index first.")

        logger.info(f"Similarity search: {query_text}")

        # Create retriever
        retriever = self.index.as_retriever(similarity_top_k=top_k)

        # Retrieve nodes
        nodes = retriever.retrieve(query_text)

        # Format results
        results = []
        for node in nodes:
            results.append(
                {
                    "text": node.node.text,
                    "score": node.score,
                    "metadata": node.node.metadata,
                    "doc_id": node.node.ref_doc_id,
                }
            )

        return results

    def get_stats(self) -> dict:
        """
        Get statistics about the vector store.

        Returns:
            dict with store statistics
        """
        # Note: Actual stats would require direct Milvus client access
        return {
            "collection_name": MILVUS_COLLECTION_NAME,
            "host": MILVUS_HOST,
            "port": MILVUS_PORT,
            "index_exists": self.index is not None,
        }
