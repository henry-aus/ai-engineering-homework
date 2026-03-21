"""
Test script for Graph RAG system.

Run this to verify the system is working correctly.
"""

import sys
import logging
from graph_rag.graph_store import initialize_graph
from graph_rag.vector_store import initialize_vector_store
from graph_rag.hybrid_query import HybridQueryEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_graph_operations():
    """Test basic graph operations."""
    print("\n" + "=" * 80)
    print("测试 1: Neo4j 图谱操作")
    print("=" * 80)

    try:
        # Initialize graph
        print("\n1. 初始化图谱...")
        graph_store = initialize_graph(clear_existing=True)
        print("   ✓ 图谱初始化成功")

        # Get stats
        print("\n2. 获取图谱统计...")
        stats = graph_store.get_graph_stats()
        print(f"   ✓ 公司数量: {stats['total_companies']}")
        print(f"   ✓ 关系数量: {stats['total_relationships']}")
        print("   ✓ 关系类型:")
        for rel in stats['relationship_types']:
            print(f"      - {rel['type']}: {rel['count']}")

        # Test shareholder query
        print("\n3. 测试股东查询...")
        shareholders = graph_store.find_major_shareholders("阿里巴巴")
        print(f"   ✓ 找到 {len(shareholders)} 个股东")
        if shareholders:
            print(f"      示例: {shareholders[0]['shareholder_name']}")

        # Test subsidiaries
        print("\n4. 测试子公司查询...")
        subsidiaries = graph_store.find_subsidiaries("阿里巴巴")
        print(f"   ✓ 找到 {len(subsidiaries)} 个子公司")
        if subsidiaries:
            print(f"      示例: {subsidiaries[0]['subsidiary_name']}")

        # Close connection
        graph_store.close()
        print("\n✅ 图谱操作测试通过")

    except Exception as e:
        logger.error(f"图谱测试失败: {e}", exc_info=True)
        print(f"\n❌ 测试失败: {e}")
        return False

    return True


def test_vector_operations():
    """Test vector store operations."""
    print("\n" + "=" * 80)
    print("测试 2: 向量存储操作")
    print("=" * 80)

    try:
        # Initialize vector store
        print("\n1. 初始化向量存储...")
        vector_store = initialize_vector_store(rebuild=True)
        print("   ✓ 向量存储初始化成功")

        # Test similarity search
        print("\n2. 测试相似度搜索...")
        results = vector_store.similarity_search("阿里巴巴集团", top_k=3)
        print(f"   ✓ 找到 {len(results)} 个相关文档")
        if results:
            print(f"      最相似: {results[0]['company_name']} (分数: {results[0]['score']:.3f})")

        # Test query
        print("\n3. 测试文档查询...")
        query_result = vector_store.query("互联网公司", top_k=2)
        print(f"   ✓ 查询成功")
        print(f"      答案长度: {len(query_result['answer'])} 字符")
        print(f"      相关文档: {len(query_result['documents'])} 个")

        print("\n✅ 向量操作测试通过")

    except Exception as e:
        logger.error(f"向量测试失败: {e}", exc_info=True)
        print(f"\n❌ 测试失败: {e}")
        return False

    return True


def test_hybrid_query():
    """Test hybrid query engine."""
    print("\n" + "=" * 80)
    print("测试 3: 混合查询引擎")
    print("=" * 80)

    try:
        # Initialize stores
        print("\n1. 初始化系统...")
        graph_store = initialize_graph(clear_existing=False)
        vector_store = initialize_vector_store(rebuild=False)
        engine = HybridQueryEngine(graph_store, vector_store)
        print("   ✓ 混合查询引擎初始化成功")

        # Test query classification
        print("\n2. 测试查询分类...")
        query_type = engine.classify_query_type("阿里巴巴的最大股东是谁？")
        print(f"   ✓ 查询类型: {query_type}")

        # Test entity extraction
        print("\n3. 测试实体提取...")
        entities = engine.extract_entities("软银集团和阿里巴巴的关系")
        print(f"   ✓ 提取实体: {entities}")

        # Test full query
        print("\n4. 测试完整查询...")
        result = engine.query("阿里巴巴集团的最大股东是谁？")
        print(f"   ✓ 查询成功")
        print(f"      查询类型: {result['query_type']}")
        print(f"      提取实体: {result['entities']}")
        print(f"      推理步骤: {len(result['reasoning_path'])} 步")
        print(f"      向量可信度: {result['confidence_scores']['vector']:.2%}")
        print(f"      图谱可信度: {result['confidence_scores']['graph']:.2%}")
        print(f"      综合可信度: {result['confidence_scores']['hybrid']:.2%}")
        print(f"      主要来源: {result['primary_source']}")
        print(f"\n   答案预览:")
        print(f"   {result['answer'][:200]}...")

        # Close connection
        graph_store.close()
        print("\n✅ 混合查询测试通过")

    except Exception as e:
        logger.error(f"混合查询测试失败: {e}", exc_info=True)
        print(f"\n❌ 测试失败: {e}")
        return False

    return True


def test_multi_hop_reasoning():
    """Test multi-hop reasoning."""
    print("\n" + "=" * 80)
    print("测试 4: 多跳推理")
    print("=" * 80)

    try:
        # Initialize
        print("\n1. 初始化系统...")
        graph_store = initialize_graph(clear_existing=False)
        vector_store = initialize_vector_store(rebuild=False)
        engine = HybridQueryEngine(graph_store, vector_store)
        print("   ✓ 系统初始化成功")

        # Test multi-hop query
        print("\n2. 测试多跳查询...")
        queries = [
            "软银集团和蚂蚁集团有什么关系？",
            "高瓴资本投资了哪些公司？",
        ]

        for i, query in enumerate(queries, 1):
            print(f"\n   查询 {i}: {query}")
            result = engine.query(query)
            print(f"      ✓ 查询成功")
            print(f"      - 类型: {result['query_type']}")
            print(f"      - 实体: {result['entities']}")
            print(f"      - 推理步骤: {len(result['reasoning_path'])}")
            print(f"      - 综合可信度: {result['confidence_scores']['hybrid']:.2%}")

        # Close connection
        graph_store.close()
        print("\n✅ 多跳推理测试通过")

    except Exception as e:
        logger.error(f"多跳推理测试失败: {e}", exc_info=True)
        print(f"\n❌ 测试失败: {e}")
        return False

    return True


def main():
    """Run all tests."""
    print("\n" + "=" * 80)
    print("🧪 Graph RAG 系统测试")
    print("=" * 80)

    results = []

    # Run tests
    results.append(("图谱操作", test_graph_operations()))
    results.append(("向量操作", test_vector_operations()))
    results.append(("混合查询", test_hybrid_query()))
    results.append(("多跳推理", test_multi_hop_reasoning()))

    # Summary
    print("\n" + "=" * 80)
    print("📊 测试总结")
    print("=" * 80)

    for name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{status} - {name}")

    all_passed = all(result[1] for result in results)

    print("\n" + "=" * 80)
    if all_passed:
        print("🎉 所有测试通过！")
    else:
        print("⚠️  部分测试失败，请检查日志")
    print("=" * 80 + "\n")

    return 0 if all_passed else 1


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n测试中断")
        sys.exit(1)
    except Exception as e:
        logger.error(f"测试失败: {e}", exc_info=True)
        print(f"\n❌ 测试失败: {e}")
        sys.exit(1)
