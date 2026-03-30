"""
Main entry point for Milvus FAQ Retrieval System.

This module provides both CLI and API modes for the FAQ system.
"""

import sys
import logging
import argparse
from pathlib import Path

from milvus_faq.vector_store import MilvusFAQStore
from milvus_faq.data_loader import FAQDataLoader
from milvus_faq.config import FAQ_DATA_PATH, API_HOST, API_PORT

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def test_query_mode():
    """Interactive query mode for testing."""
    logger.info("=== Milvus FAQ Retrieval System - Test Mode ===")

    # Initialize FAQ store
    logger.info("Initializing FAQ store...")
    faq_store = MilvusFAQStore()

    # Try to load existing index, or build new one
    if faq_store.load_index() is None:
        logger.info("Building new index from data file...")
        documents = FAQDataLoader.load_and_convert()
        faq_store.build_index(documents)
    else:
        logger.info("Loaded existing index")

    # Get stats
    stats = faq_store.get_stats()
    logger.info(f"Store stats: {stats}")

    # Interactive query loop
    print("\n" + "=" * 60)
    print("FAQ Query System Ready!")
    print("Enter your question (or 'quit' to exit)")
    print("=" * 60 + "\n")

    while True:
        try:
            question = input("\n❓ Your question: ").strip()

            if question.lower() in ["quit", "exit", "q"]:
                print("\nGoodbye!")
                break

            if not question:
                continue

            # Perform query
            print("\n🔍 Searching...")
            result = faq_store.query(question, top_k=3)

            # Display results
            print("\n" + "=" * 60)
            print("📝 Answer:")
            print("-" * 60)
            print(result["answer"])
            print("\n" + "=" * 60)
            print("📚 Source Documents:")
            print("-" * 60)

            for i, source in enumerate(result["sources"], 1):
                print(f"\n{i}. Score: {source['score']:.4f}")
                print(f"   FAQ ID: {source['metadata'].get('faq_id', 'N/A')}")
                print(f"   Question: {source['metadata'].get('question', 'N/A')}")
                print(f"   Text: {source['text'][:200]}...")

            print("\n" + "=" * 60)

        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            logger.error(f"Error during query: {e}")
            print(f"\n❌ Error: {e}")


def demo_mode():
    """Run predefined demo queries."""
    logger.info("=== Running Demo Mode ===")

    # Initialize FAQ store
    faq_store = MilvusFAQStore()

    # Build index
    if faq_store.load_index() is None:
        logger.info("Building index...")
        documents = FAQDataLoader.load_and_convert()
        faq_store.build_index(documents)

    # Demo queries
    demo_queries = [
        "如何退货？",
        "我想修改收货地址",
        "配送要多久？",
        "支付方式有哪些？",
        "忘记密码了怎么办？",
    ]

    print("\n" + "=" * 60)
    print("🎯 Demo Mode - Testing with Sample Queries")
    print("=" * 60)

    for i, query in enumerate(demo_queries, 1):
        print(f"\n\n{'=' * 60}")
        print(f"Query {i}: {query}")
        print("=" * 60)

        result = faq_store.query(query, top_k=2)

        print(f"\n✅ Answer:\n{result['answer']}\n")
        print(f"📊 Top {len(result['sources'])} Sources:")
        for j, source in enumerate(result["sources"], 1):
            print(
                f"  {j}. [{source['metadata'].get('faq_id')}] "
                f"Score: {source['score']:.4f} - "
                f"{source['metadata'].get('question')}"
            )

    print("\n" + "=" * 60)
    print("✨ Demo completed!")
    print("=" * 60)


def api_mode():
    """Start FastAPI server."""
    logger.info("=== Starting API Server ===")

    try:
        import uvicorn
        from milvus_faq.api import app

        logger.info(f"Starting server at http://{API_HOST}:{API_PORT}")
        logger.info("API documentation: http://localhost:8000/docs")

        uvicorn.run(app, host=API_HOST, port=API_PORT)

    except ImportError:
        logger.error("uvicorn not installed. Install with: pip install uvicorn")
        sys.exit(1)


def build_index_mode():
    """Build or rebuild the index."""
    logger.info("=== Building Index ===")

    faq_store = MilvusFAQStore()
    documents = FAQDataLoader.load_and_convert()

    logger.info(f"Building index with {len(documents)} documents...")
    faq_store.build_index(documents)

    logger.info("✅ Index built successfully!")
    stats = faq_store.get_stats()
    logger.info(f"Stats: {stats}")


def main():
    """Main entry point with command-line interface."""
    parser = argparse.ArgumentParser(
        description="Milvus FAQ Retrieval System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run in interactive query mode (default)
  python -m milvus_faq.main

  # Run demo with sample queries
  python -m milvus_faq.main --mode demo

  # Start REST API server
  python -m milvus_faq.main --mode api

  # Build/rebuild index
  python -m milvus_faq.main --mode build

  # Interactive query mode
  python -m milvus_faq.main --mode query
        """,
    )

    parser.add_argument(
        "--mode",
        choices=["query", "demo", "api", "build"],
        default="query",
        help="Operation mode (default: query)",
    )

    args = parser.parse_args()

    # Check if FAQ data file exists
    if not FAQ_DATA_PATH.exists():
        logger.error(f"FAQ data file not found: {FAQ_DATA_PATH}")
        logger.error("Please ensure faq_data.json exists in the milvus_faq directory")
        sys.exit(1)

    # Route to appropriate mode
    try:
        if args.mode == "query":
            test_query_mode()
        elif args.mode == "demo":
            demo_mode()
        elif args.mode == "api":
            api_mode()
        elif args.mode == "build":
            build_index_mode()
    except KeyboardInterrupt:
        logger.info("\nOperation cancelled by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
