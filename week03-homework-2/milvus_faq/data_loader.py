"""FAQ data loader and converter."""

import json
import logging
from typing import List, Dict
from pathlib import Path
from llama_index.core import Document

from milvus_faq.config import FAQ_DATA_PATH

logger = logging.getLogger(__name__)


class FAQDataLoader:
    """Load and convert FAQ data to LlamaIndex documents."""

    @staticmethod
    def load_faq_data(file_path: Path = FAQ_DATA_PATH) -> List[Dict]:
        """
        Load FAQ data from JSON file.

        Args:
            file_path: Path to FAQ JSON file

        Returns:
            List of FAQ dictionaries
        """
        logger.info(f"Loading FAQ data from: {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            faq_data = json.load(f)

        logger.info(f"Loaded {len(faq_data)} FAQ entries")
        return faq_data

    @staticmethod
    def faq_to_documents(faq_data: List[Dict]) -> List[Document]:
        """
        Convert FAQ data to LlamaIndex Document objects.

        Each FAQ entry becomes a document with question and answer combined.

        Args:
            faq_data: List of FAQ dictionaries

        Returns:
            List of LlamaIndex Document objects
        """
        documents = []

        for faq in faq_data:
            # Combine question and answer for better retrieval
            text = f"问题：{faq['question']}\n\n答案：{faq['answer']}"

            # Create document with metadata
            doc = Document(
                text=text,
                metadata={
                    "faq_id": faq["id"],
                    "question": faq["question"],
                    "answer": faq["answer"],
                },
                id_=faq["id"],
            )

            documents.append(doc)

        logger.info(f"Converted {len(documents)} FAQ entries to documents")
        return documents

    @staticmethod
    def load_and_convert(file_path: Path = FAQ_DATA_PATH) -> List[Document]:
        """
        Load FAQ data and convert to documents in one step.

        Args:
            file_path: Path to FAQ JSON file

        Returns:
            List of LlamaIndex Document objects
        """
        faq_data = FAQDataLoader.load_faq_data(file_path)
        return FAQDataLoader.faq_to_documents(faq_data)

    @staticmethod
    def add_faq_entry(faq_id: str, question: str, answer: str) -> Document:
        """
        Create a new FAQ document from individual fields.

        Args:
            faq_id: Unique FAQ ID
            question: Question text
            answer: Answer text

        Returns:
            LlamaIndex Document object
        """
        text = f"问题：{question}\n\n答案：{answer}"

        return Document(
            text=text,
            metadata={
                "faq_id": faq_id,
                "question": question,
                "answer": answer,
            },
            id_=faq_id,
        )

    @staticmethod
    def save_faq_data(faq_data: List[Dict], file_path: Path = FAQ_DATA_PATH) -> None:
        """
        Save FAQ data to JSON file.

        Args:
            faq_data: List of FAQ dictionaries
            file_path: Path to save JSON file
        """
        logger.info(f"Saving {len(faq_data)} FAQ entries to: {file_path}")

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(faq_data, f, ensure_ascii=False, indent=2)

        logger.info("FAQ data saved successfully")
