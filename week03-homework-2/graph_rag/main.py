"""
Main entry point for Graph RAG system.

This module provides CLI and API modes for the hybrid query system.
"""

import sys
import logging
import argparse
from pathlib import Path

from graph_rag.graph_store import Neo4jGraphStore, initialize_graph
from graph_rag.vector_store import DocumentVectorStore, initialize_vector_store
from graph_rag.hybrid_query import HybridQueryEngine
from graph_rag.config import DATA_DIR, API_HOST, API_PORT

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def print_query_result(result: dict) -> None:
    """Pretty print query result."""
    print("\n" + "=" * 80)
    print("📊 查询结果")
    print("=" * 80)

    print(f"\n【问题】 {result['query']}")
    print(f"【类型】 {result['query_type']}")
    print(f"【实体】 {', '.join(result['entities']) if result['entities'] else '无'}")

    print(f"\n{'=' * 80}")
    print("🔍 推理路径")
    print("=" * 80)
    for i, step in enumerate(result['reasoning_path'], 1):
        print(f"{i}. {step}")

    print(f"\n{'=' * 80}")
    print("💡 答案")
    print("=" * 80)
    print(result['answer'])

    print(f"\n{'=' * 80}")
    print("📈 可信度评估")
    print("=" * 80)
    scores = result['confidence_scores']
    print(f"- 文档检索可信度: {scores['vector']:.2%}")
    print(f"- 图谱推理可信度: {scores['graph']:.2%}")
    print(f"- 综合可信度: {scores['hybrid']:.2%}")
    print(f"- 主要来源: {result['primary_source']}")

    print(f"\n{'=' * 80}")
    print("✅ 验证结果")
    print("=" * 80)
    print(f"- 有效性: {'通过' if result['validation']['is_valid'] else '失败'}")
    print(f"- 说明: {result['validation']['message']}")

    print(f"\n{'=' * 80}")
    print(f"📚 文档来源: {len(result['vector_results'])} 个文档")
    if result['vector_results']:
        for i, doc in enumerate(result['vector_results'][:3], 1):
            print(f"{i}. [{doc['company_name']}] 相似度: {doc['score']:.3f}")

    print(f"\n{'=' * 80}")
    print(f"🕸️  图谱来源: {len(result['graph_results'])} 组信息")
    if result['graph_results']:
        for i, gr in enumerate(result['graph_results'][:3], 1):
            print(f"{i}. 类型: {gr['type']}, 实体: {gr.get('entity', 'N/A')}")

    print("\n" + "=" * 80 + "\n")


def demo_mode():
    """Run demo with predefined queries."""
    logger.info("=== Running Demo Mode ===")

    # Initialize stores
    logger.info("Initializing knowledge graph...")
    graph_store = initialize_graph(clear_existing=True)

    logger.info("Initializing vector store...")
    vector_store = initialize_vector_store(rebuild=True)

    # Initialize hybrid query engine
    logger.info("Initializing hybrid query engine...")
    engine = HybridQueryEngine(graph_store, vector_store)

    # Demo queries
    demo_queries = [
        "阿里巴巴集团的最大股东是谁？",
        "蚂蚁集团是谁投资的？",
        "阿里巴巴有哪些子公司？",
        "软银集团和阿里巴巴是什么关系？",
        "腾讯和阿里巴巴有什么关系？",
    ]

    print("\n" + "=" * 80)
    print("🎯 Graph RAG 演示模式")
    print("=" * 80)
    print(f"\n将运行 {len(demo_queries)} 个示例查询...\n")

    for i, query in enumerate(demo_queries, 1):
        print(f"\n{'#' * 80}")
        print(f"示例 {i}/{len(demo_queries)}")
        print(f"{'#' * 80}")

        try:
            result = engine.query(query)
            print_query_result(result)
        except Exception as e:
            logger.error(f"Query failed: {e}", exc_info=True)
            print(f"\n❌ 查询失败: {e}\n")

    # Close connections
    graph_store.close()

    print("\n" + "=" * 80)
    print("✨ 演示完成！")
    print("=" * 80)


def interactive_mode():
    """Interactive query mode."""
    logger.info("=== Interactive Query Mode ===")

    # Initialize stores
    logger.info("Initializing knowledge graph...")
    graph_store = initialize_graph(clear_existing=False)

    logger.info("Initializing vector store...")
    vector_store = initialize_vector_store(rebuild=False)

    # Initialize hybrid query engine
    logger.info("Initializing hybrid query engine...")
    engine = HybridQueryEngine(graph_store, vector_store)

    print("\n" + "=" * 80)
    print("💬 Graph RAG 交互式查询")
    print("=" * 80)
    print("\n提示：")
    print("- 输入问题进行查询")
    print("- 输入 'quit' 或 'exit' 退出")
    print("- 输入 'stats' 查看图谱统计")
    print("=" * 80 + "\n")

    try:
        while True:
            try:
                query = input("\n❓ 请输入问题: ").strip()

                if query.lower() in ["quit", "exit", "q"]:
                    print("\n再见！")
                    break

                if not query:
                    continue

                if query.lower() == "stats":
                    stats = graph_store.get_graph_stats()
                    print("\n📊 图谱统计信息:")
                    print(f"- 公司总数: {stats['total_companies']}")
                    print(f"- 关系总数: {stats['total_relationships']}")
                    print("- 关系类型:")
                    for rel in stats['relationship_types']:
                        print(f"  • {rel['type']}: {rel['count']}")
                    continue

                # Process query
                print("\n🔄 处理中...")
                result = engine.query(query)
                print_query_result(result)

            except KeyboardInterrupt:
                print("\n\n再见！")
                break
            except Exception as e:
                logger.error(f"Error during query: {e}", exc_info=True)
                print(f"\n❌ 错误: {e}")

    finally:
        graph_store.close()


def init_mode():
    """Initialize knowledge graph and vector store."""
    logger.info("=== Initialization Mode ===")

    print("\n" + "=" * 80)
    print("🔧 初始化 Graph RAG 系统")
    print("=" * 80)

    # Check if data files exist
    companies_file = DATA_DIR / "companies.json"
    relationships_file = DATA_DIR / "relationships.json"

    if not companies_file.exists():
        logger.error(f"Companies data file not found: {companies_file}")
        print(f"\n❌ 错误: 找不到公司数据文件 {companies_file}")
        return

    if not relationships_file.exists():
        logger.error(f"Relationships data file not found: {relationships_file}")
        print(f"\n❌ 错误: 找不到关系数据文件 {relationships_file}")
        return

    # Initialize knowledge graph
    print("\n1️⃣  初始化知识图谱...")
    try:
        graph_store = initialize_graph(clear_existing=True)
        stats = graph_store.get_graph_stats()
        print(f"   ✓ 成功创建 {stats['total_companies']} 个公司节点")
        print(f"   ✓ 成功创建 {stats['total_relationships']} 个关系")
        graph_store.close()
    except Exception as e:
        logger.error(f"Failed to initialize graph: {e}", exc_info=True)
        print(f"   ❌ 失败: {e}")
        return

    # Initialize vector store
    print("\n2️⃣  初始化向量存储...")
    try:
        vector_store = initialize_vector_store(rebuild=True)
        print(f"   ✓ 成功建立向量索引")
    except Exception as e:
        logger.error(f"Failed to initialize vector store: {e}", exc_info=True)
        print(f"   ❌ 失败: {e}")
        return

    print("\n" + "=" * 80)
    print("✅ 初始化完成！")
    print("=" * 80)
    print("\n现在可以运行查询了：")
    print("  python -m graph_rag.main --mode demo")
    print("  python -m graph_rag.main --mode query")
    print("=" * 80 + "\n")


def api_mode():
    """Start FastAPI server."""
    logger.info("=== Starting API Server ===")

    try:
        import uvicorn
        from graph_rag.api import app

        logger.info(f"Starting server at http://{API_HOST}:{API_PORT}")
        print("\n" + "=" * 80)
        print("🚀 启动 Graph RAG API 服务")
        print("=" * 80)
        print(f"\nAPI 地址: http://{API_HOST}:{API_PORT}")
        print(f"API 文档: http://localhost:{API_PORT}/docs")
        print("\n" + "=" * 80 + "\n")

        uvicorn.run(app, host=API_HOST, port=API_PORT)

    except ImportError:
        logger.error("uvicorn not installed")
        print("\n❌ 错误: uvicorn 未安装")
        print("请运行: pip install uvicorn")
        sys.exit(1)


def main():
    """Main entry point with CLI."""
    parser = argparse.ArgumentParser(
        description="Graph RAG: 融合文档检索和图谱推理的问答系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 初始化系统（首次运行）
  python -m graph_rag.main --mode init

  # 运行演示
  python -m graph_rag.main --mode demo

  # 交互式查询
  python -m graph_rag.main --mode query

  # 启动 API 服务
  python -m graph_rag.main --mode api
        """,
    )

    parser.add_argument(
        "--mode",
        choices=["init", "demo", "query", "api"],
        default="query",
        help="运行模式 (默认: query)",
    )

    args = parser.parse_args()

    # Check if data directory exists
    if not DATA_DIR.exists():
        logger.error(f"Data directory not found: {DATA_DIR}")
        print(f"\n❌ 错误: 数据目录不存在 {DATA_DIR}")
        print("请确保 data/ 目录存在且包含必要的数据文件")
        sys.exit(1)

    # Route to appropriate mode
    try:
        if args.mode == "init":
            init_mode()
        elif args.mode == "demo":
            demo_mode()
        elif args.mode == "query":
            interactive_mode()
        elif args.mode == "api":
            api_mode()
    except KeyboardInterrupt:
        logger.info("\n操作已取消")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        print(f"\n❌ 致命错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
