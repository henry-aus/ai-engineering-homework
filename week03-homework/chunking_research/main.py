import os
from llama_index.core import Settings, VectorStoreIndex, Document
from llama_index.llms.openai_like import OpenAILike
from llama_index.embeddings.dashscope import DashScopeEmbedding, DashScopeTextEmbeddingModels
from llama_index.core.node_parser import (
    SentenceSplitter,
    TokenTextSplitter,
    SentenceWindowNodeParser,
)
from llama_index.core.postprocessor import MetadataReplacementPostProcessor
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv()

# Configure LlamaIndex with Qwen models
Settings.llm = OpenAILike(
    model="qwen-plus",
    api_base="https://dashscope.aliyuncs.com/compatible-mode/v1",
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    is_chat_model=True
)

Settings.embed_model = DashScopeEmbedding(
    model_name=DashScopeTextEmbeddingModels.TEXT_EMBEDDING_V3,
    embed_batch_size=6,
    embed_input_length=8192
)


def create_sample_documents():
    """Create sample documents for testing different chunking strategies."""

    doc1_text = """
    量子计算是一种遵循量子力学规律调控量子信息单元进行计算的新型计算模式。量子计算机利用量子叠加和量子纠缠等量子力学特性来进行信息处理。
    与经典计算机使用的比特不同，量子计算机使用量子比特作为信息的基本单元。量子比特可以同时处于0和1的叠加态，这使得量子计算机能够并行处理大量数据。

    量子计算的发展历史可以追溯到1980年代初期。1981年，物理学家理查德·费曼提出了量子计算的概念。他认为经典计算机在模拟量子系统时会遇到困难，
    而量子计算机则能够更有效地模拟量子系统。1985年，大卫·多伊奇提出了量子图灵机的概念，为量子计算的理论基础奠定了基础。

    量子算法是量子计算的核心。1994年，彼得·秀尔提出了著名的秀尔算法，该算法可以在多项式时间内分解大整数，这对现有的RSA加密系统构成了潜在威胁。
    1996年，洛夫·格罗弗提出了格罗弗算法，用于在无序数据库中进行搜索，其搜索速度比经典算法快平方根倍。

    量子纠缠是量子计算中的关键现象。当两个或多个量子比特处于纠缠态时，它们之间存在着强相关性，即使相隔很远，对其中一个量子比特的测量也会立即影响其他量子比特的状态。
    这种特性使得量子计算机能够实现经典计算机难以达到的计算能力。量子纠缠也是量子通信和量子密码学的基础。

    量子退相干是量子计算面临的主要挑战之一。量子比特非常脆弱，容易受到环境噪声的干扰而失去量子特性。为了克服这个问题，科学家们开发了量子纠错码，
    用于保护量子信息免受错误的影响。然而，量子纠错需要大量的辅助量子比特，这增加了量子计算机的复杂性。

    目前，多种物理系统被用于实现量子比特，包括超导电路、离子阱、光子、拓扑量子比特等。每种系统都有其优缺点。超导量子比特具有可扩展性强的优势，
    但需要极低的温度（接近绝对零度）才能工作。离子阱量子比特具有很长的相干时间，但难以扩展到大规模系统。

    量子计算的应用前景广阔。在密码学领域，量子计算机可以破解现有的公钥加密系统，同时也能实现更安全的量子密钥分发。在药物研发领域，
    量子计算机可以模拟复杂的分子结构和化学反应，加速新药的发现。在优化问题、机器学习、金融建模等领域，量子计算也显示出巨大的潜力。

    2019年，谷歌宣布实现了量子优越性，其53量子比特的量子处理器在200秒内完成了经典超级计算机需要1万年才能完成的任务。
    这一里程碑标志着量子计算进入了一个新的阶段。然而，实现通用量子计算机仍然面临许多挑战，需要在量子比特质量、纠错能力、系统扩展性等方面取得突破。
    """

    doc2_text = """
    气候变化是指地球气候系统长期的统计学变化，包括温度、降水、风和其他气候要素的变化。当前的气候变化主要是指由人类活动导致的全球变暖现象。

    工业革命以来，人类大量燃烧化石燃料（煤炭、石油、天然气），导致大气中二氧化碳等温室气体浓度急剧上升。温室气体能够吸收地球表面辐射的红外线，
    使大气层保持温暖，这种现象被称为温室效应。适度的温室效应对维持地球适宜的温度至关重要，但过度的温室效应则导致全球变暖。

    根据政府间气候变化专门委员会（IPCC）的报告，全球平均温度在过去一个世纪中上升了约1.1摄氏度。这种升温趋势在最近几十年加速，
    2016年和2020年是有记录以来最热的年份之一。如果不采取有效的减排措施，预计到本世纪末，全球平均温度将上升2到4摄氏度甚至更高。

    全球变暖带来了一系列严重后果。首先是海平面上升，由于极地冰盖和冰川融化，以及海水受热膨胀，全球海平面正在以每年3.3毫米的速度上升。
    这对沿海地区和岛国构成了严重威胁。其次，极端天气事件（如热浪、干旱、洪水、飓风）的频率和强度都在增加，给人类社会和生态系统带来巨大损失。

    气候变化对生物多样性也产生了深远影响。许多物种的栖息地正在消失或发生变化，导致物种灭绝速度加快。珊瑚礁由于海水温度上升和酸化而大量白化死亡。
    北极海冰的减少威胁着北极熊等依赖冰层生存的物种。一些物种被迫向高纬度或高海拔地区迁移以寻找适宜的生存环境。

    农业生产也受到气候变化的严重影响。温度上升、降水模式改变、极端天气增多都会影响作物产量。一些地区可能会经历更频繁的干旱，
    而另一些地区则可能面临洪水和水土流失。气候变化还会影响病虫害的分布和活动，增加农业生产的风险。

    为应对气候变化，国际社会达成了一系列协议。1997年的《京都议定书》首次为发达国家设定了具有法律约束力的减排目标。
    2015年的《巴黎协定》更进一步，要求所有缔约方努力将全球平均温度升幅控制在工业化前水平以上2摄氏度以内，并争取限制在1.5摄氏度以内。

    减缓气候变化需要从多个方面入手。首先要大幅减少温室气体排放，这需要能源系统的深刻转型，从化石燃料转向可再生能源（太阳能、风能、水能等）。
    其次要提高能源效率，减少能源浪费。第三要保护和恢复森林等自然碳汇。第四要发展碳捕获和储存技术。

    适应气候变化同样重要。这包括建设更强大的基础设施以应对极端天气，开发抗旱抗洪的作物品种，改善水资源管理，
    建立预警系统，以及帮助脆弱社区提高适应能力。气候变化是全人类面临的共同挑战，需要各国政府、企业、民间组织和个人共同努力。
    """

    doc3_text = """
    人工智能（AI）是计算机科学的一个分支，致力于创建能够执行通常需要人类智能的任务的系统。这些任务包括视觉感知、语音识别、决策制定、
    语言翻译等。人工智能的历史可以追溯到20世纪50年代，当时计算机科学家们开始探索机器是否能够思考。

    1956年，在达特茅斯会议上，约翰·麦卡锡等人正式提出了"人工智能"这个术语，标志着人工智能作为一个独立学科的诞生。
    早期的人工智能研究主要集中在符号推理和问题求解上，研究者们开发了一些能够下棋、证明定理的程序。

    人工智能的发展经历了几次起伏。20世纪60年代到70年代初是第一次繁荣期，研究者们对人工智能的前景充满乐观。
    然而，由于当时技术的局限性和对问题复杂度的低估，许多承诺未能实现，导致了第一次"AI冬天"。80年代，专家系统的成功带来了第二次繁荣，
    但随后又因为维护成本高、应用范围有限等问题而陷入低谷。

    21世纪以来，得益于计算能力的大幅提升、大数据的可用性和机器学习算法的进步，人工智能迎来了新的黄金时代。
    特别是深度学习技术的突破，使得人工智能在图像识别、语音识别、自然语言处理等领域取得了令人瞩目的成果。

    机器学习是人工智能的核心方法之一。它使计算机能够从数据中学习，而不需要明确编程。机器学习可以分为监督学习、无监督学习和强化学习三大类。
    监督学习使用标注的数据进行训练，如垃圾邮件分类。无监督学习从未标注的数据中发现模式，如客户分群。强化学习通过与环境交互并获得奖励来学习，
    如训练游戏AI。

    深度学习是机器学习的一个子领域，使用多层神经网络来学习数据的层次化表示。卷积神经网络（CNN）在图像识别任务中表现出色，
    循环神经网络（RNN）和Transformer架构则在自然语言处理领域大放异彩。2012年，AlexNet在ImageNet竞赛中的胜利标志着深度学习时代的到来。

    自然语言处理（NLP）是人工智能的重要应用领域。近年来，基于Transformer架构的大规模预训练语言模型（如GPT、BERT）取得了突破性进展。
    这些模型在海量文本数据上进行预训练，然后可以针对特定任务进行微调。ChatGPT等应用展示了这些模型在对话、写作、翻译等任务上的强大能力。

    计算机视觉是另一个快速发展的领域。从图像分类、目标检测到图像分割、姿态估计，深度学习模型的性能已经接近甚至超越人类水平。
    人脸识别技术被广泛应用于安全系统和移动设备解锁。自动驾驶汽车使用计算机视觉来感知周围环境，识别道路、车辆、行人等。

    人工智能的应用已经渗透到生活的方方面面。在医疗领域，AI辅助诊断系统能够分析医学影像，帮助医生发现疾病。
    在金融领域，AI用于欺诈检测、信用评分、算法交易等。在教育领域，智能导师系统能够提供个性化学习体验。在娱乐领域，
    推荐系统帮助用户发现感兴趣的内容。

    然而，人工智能的发展也带来了一些挑战和担忧。算法偏见可能导致不公平的决策，影响某些群体的利益。隐私问题日益凸显，
    大数据的收集和使用需要更严格的监管。人工智能可能导致某些工作岗位消失，需要社会提前做好准备。更深层的担忧是超级人工智能的风险，
    一些专家警告说，如果人工智能的发展不受控制，可能对人类构成威胁。因此，负责任的AI开发和使用变得越来越重要。
    """

    documents = [
        Document(text=doc1_text, metadata={"title": "量子计算", "topic": "quantum_computing"}),
        Document(text=doc2_text, metadata={"title": "气候变化", "topic": "climate_change"}),
        Document(text=doc3_text, metadata={"title": "人工智能", "topic": "artificial_intelligence"}),
    ]

    return documents


def evaluate_splitter(splitter, documents, question, ground_truth, splitter_name):
    """Evaluate a text splitter with the given documents and question."""

    print(f"\n{'='*60}")
    print(f"Testing {splitter_name} Splitter")
    print(f"{'='*60}")

    # Parse documents into nodes
    nodes = splitter.get_nodes_from_documents(documents)

    print(f"Number of nodes created: {len(nodes)}")

    # Show sample nodes
    print(f"\nFirst 3 nodes:")
    for i, node in enumerate(nodes[:3]):
        print(f"\n--- Node {i+1} ---")
        print(f"Text length: {len(node.text)} characters")
        print(f"Text preview: {node.text[:200]}...")
        print(f"Metadata: {node.metadata}")

    # Create index
    print(f"\nCreating vector store index...")
    start_time = time.time()

    # For sentence window, we need special handling
    if isinstance(splitter, SentenceWindowNodeParser):
        index = VectorStoreIndex(nodes)
        query_engine = index.as_query_engine(
            similarity_top_k=5,
            node_postprocessors=[
                MetadataReplacementPostProcessor(target_metadata_key="window")
            ]
        )
    else:
        index = VectorStoreIndex(nodes)
        query_engine = index.as_query_engine(similarity_top_k=5)

    index_time = time.time() - start_time
    print(f"Index created in {index_time:.2f} seconds")

    # Query the index
    print(f"\nQuestion: {question}")
    print(f"Ground truth: {ground_truth}")

    print(f"\nQuerying the index...")
    start_time = time.time()
    response = query_engine.query(question)
    query_time = time.time() - start_time

    print(f"Query completed in {query_time:.2f} seconds")
    print(f"\nResponse: {response}")

    # Show source nodes
    print(f"\nSource nodes used:")
    for i, node in enumerate(response.source_nodes):
        print(f"\n--- Source Node {i+1} (Score: {node.score:.4f}) ---")
        print(f"Text: {node.text[:300]}...")
        print(f"Metadata: {node.metadata}")

    # Manual evaluation metrics
    print(f"\n--- Evaluation Metrics ---")
    print(f"Indexing time: {index_time:.2f}s")
    print(f"Query time: {query_time:.2f}s")
    print(f"Total nodes: {len(nodes)}")
    print(f"Avg node length: {sum(len(n.text) for n in nodes) / len(nodes):.1f} chars")

    return {
        "splitter_name": splitter_name,
        "num_nodes": len(nodes),
        "index_time": index_time,
        "query_time": query_time,
        "response": str(response),
        "source_nodes": len(response.source_nodes),
    }


def compare_chunking_strategies():
    """Compare different chunking strategies."""

    print("\n" + "="*60)
    print("Chunking Strategy Comparison")
    print("="*60)

    # Create documents
    documents = create_sample_documents()

    # Define test question and ground truth
    question = "量子计算中的量子纠缠有什么作用？"
    ground_truth = "量子纠缠使得量子比特之间存在强相关性，是量子计算实现强大计算能力的关键，也是量子通信和量子密码学的基础。"

    results = []

    # Test 1: Sentence Splitter
    sentence_splitter = SentenceSplitter(
        chunk_size=512,
        chunk_overlap=50
    )
    result1 = evaluate_splitter(sentence_splitter, documents, question, ground_truth, "Sentence")
    results.append(result1)

    # Test 2: Token Splitter
    token_splitter = TokenTextSplitter(
        chunk_size=256,
        chunk_overlap=32,
        separator="\n"
    )
    result2 = evaluate_splitter(token_splitter, documents, question, ground_truth, "Token")
    results.append(result2)

    # Test 3: Sentence Window Splitter
    sentence_window_splitter = SentenceWindowNodeParser.from_defaults(
        window_size=3,
        window_metadata_key="window",
        original_text_metadata_key="original_text"
    )
    result3 = evaluate_splitter(sentence_window_splitter, documents, question, ground_truth, "Sentence Window")
    results.append(result3)

    # Print comparison summary
    print("\n" + "="*60)
    print("COMPARISON SUMMARY")
    print("="*60)
    print(f"\n{'Strategy':<20} {'Nodes':<10} {'Index Time':<15} {'Query Time':<15}")
    print("-" * 60)
    for result in results:
        print(f"{result['splitter_name']:<20} {result['num_nodes']:<10} "
              f"{result['index_time']:<15.2f} {result['query_time']:<15.2f}")

    return results


def test_parameter_variations():
    """Test different parameter combinations for Sentence Splitter."""

    print("\n" + "="*60)
    print("Parameter Variation Testing (Sentence Splitter)")
    print("="*60)

    documents = create_sample_documents()
    question = "人工智能的发展经历了哪些阶段？"
    ground_truth = "AI发展经历了多次起伏，包括早期符号推理时代、第一次AI冬天、专家系统繁荣、第二次低谷，以及21世纪以来的深度学习黄金时代。"

    # Test different chunk sizes
    chunk_sizes = [256, 512, 1024]
    overlap_ratios = [0.1, 0.2, 0.3]

    print("\n--- Testing different chunk sizes ---")
    for chunk_size in chunk_sizes:
        overlap = int(chunk_size * 0.2)
        splitter = SentenceSplitter(chunk_size=chunk_size, chunk_overlap=overlap)
        nodes = splitter.get_nodes_from_documents(documents)
        print(f"Chunk size: {chunk_size}, Overlap: {overlap} -> Nodes: {len(nodes)}")

    print("\n--- Testing different overlap ratios (chunk_size=512) ---")
    for ratio in overlap_ratios:
        overlap = int(512 * ratio)
        splitter = SentenceSplitter(chunk_size=512, chunk_overlap=overlap)
        nodes = splitter.get_nodes_from_documents(documents)
        print(f"Overlap ratio: {ratio:.1%} ({overlap} chars) -> Nodes: {len(nodes)}")


def main():
    """Main entry point for the chunking research assignment."""

    print("Starting Chunking Research Assignment...")
    print(f"API Key configured: {bool(os.getenv('DASHSCOPE_API_KEY'))}")

    # Compare different chunking strategies
    results = compare_chunking_strategies()

    # Test parameter variations
    test_parameter_variations()

    print("\n" + "="*60)
    print("Assignment 1 Complete!")
    print("="*60)
    print("\nPlease review the results and update the report.md file with your analysis.")
    print("Consider the following aspects:")
    print("- Which chunking strategy performed best for your use case?")
    print("- How did chunk_size and chunk_overlap affect the results?")
    print("- What are the trade-offs between precision and context richness?")


if __name__ == "__main__":
    main()
