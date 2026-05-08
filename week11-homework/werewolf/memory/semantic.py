"""Semantic memory using vector store for RAG."""

from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document
import os


class SemanticMemory:
    """Manages semantic memory with RAG capabilities."""

    def __init__(self):
        """Initialize semantic memory with embeddings and vector store."""
        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small",
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_API_BASE"),
        )
        # Initialize with a dummy document
        dummy_doc = Document(page_content="Game initialization", metadata={"type": "init"})
        self.vectorstore = FAISS.from_documents([dummy_doc], self.embeddings)
        self.memory_count = 0

    def add_observation(self, game_id: str, player_id: str, observation: str, round_num: int, phase: str):
        """Store an observation in semantic memory.

        Args:
            game_id: Unique game identifier
            player_id: Player who made the observation
            observation: The observation text
            round_num: Game round number
            phase: Game phase when observation was made
        """
        metadata = {
            "game_id": game_id,
            "player_id": player_id,
            "round": round_num,
            "phase": phase,
            "type": "observation"
        }
        doc = Document(page_content=observation, metadata=metadata)
        self.vectorstore.add_documents([doc])
        self.memory_count += 1

    def retrieve_relevant(self, game_id: str, player_id: str, query: str, k: int = 5) -> list[str]:
        """Retrieve relevant memories for a given query.

        Args:
            game_id: Unique game identifier
            player_id: Player making the query
            query: The query text
            k: Number of results to return

        Returns:
            List of relevant observation texts
        """
        if self.memory_count == 0:
            return []

        # Search with filter for this game and player
        filter_dict = {"game_id": game_id, "player_id": player_id}

        try:
            results = self.vectorstore.similarity_search(
                query,
                k=k,
                filter=filter_dict
            )
            return [doc.page_content for doc in results]
        except Exception:
            # Fallback without filter if filtering not supported
            results = self.vectorstore.similarity_search(query, k=k)
            # Manually filter results
            filtered = [
                doc.page_content
                for doc in results
                if doc.metadata.get("game_id") == game_id
                and doc.metadata.get("player_id") == player_id
            ]
            return filtered[:k]
