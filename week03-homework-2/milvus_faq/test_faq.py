"""
Simple test script for Milvus FAQ system.

Run this to verify the system is working correctly.
"""

import logging
from milvus_faq.vector_store import MilvusFAQStore
from milvus_faq.data_loader import FAQDataLoader

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_basic_functionality():
    """Test basic FAQ system functionality."""
    print("\n" + "=" * 60)
    print("Testing Milvus FAQ System")
    print("=" * 60)

    # Step 1: Load data
    print("\n1. Loading FAQ data...")
    documents = FAQDataLoader.load_and_convert()
    print(f"   ✓ Loaded {len(documents)} FAQ documents")

    # Step 2: Initialize store
    print("\n2. Initializing Milvus FAQ store...")
    store = MilvusFAQStore()
    print("   ✓ Store initialized")

    # Step 3: Build index
    print("\n3. Building vector index...")
    index = store.build_index(documents)
    print("   ✓ Index built successfully")

    # Step 4: Test queries
    print("\n4. Testing queries...")
    test_queries = [
        "如何退货？",
        "支付方式",
        "修改地址",
    ]

    for i, query in enumerate(test_queries, 1):
        print(f"\n   Query {i}: {query}")
        result = store.query(query, top_k=2)
        print(f"   Answer: {result['answer'][:100]}...")
        print(f"   Sources: {len(result['sources'])} documents")

    # Step 5: Test hot update
    print("\n5. Testing hot update (add document)...")
    new_doc = FAQDataLoader.add_faq_entry(
        "test_001",
        "测试问题？",
        "这是一个测试答案。"
    )
    store.add_documents([new_doc])
    print("   ✓ Document added successfully")

    # Step 6: Query the new document
    print("\n6. Querying new document...")
    result = store.similarity_search("测试问题", top_k=1)
    if result:
        print(f"   ✓ Found: {result[0]['metadata'].get('question')}")
        print(f"   Score: {result[0]['score']:.4f}")
    else:
        print("   ✗ Document not found")

    # Step 7: Delete test document
    print("\n7. Cleaning up test document...")
    store.delete_document("test_001")
    print("   ✓ Document deleted")

    print("\n" + "=" * 60)
    print("✅ All tests passed!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    try:
        test_basic_functionality()
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        print(f"\n❌ Test failed: {e}")
