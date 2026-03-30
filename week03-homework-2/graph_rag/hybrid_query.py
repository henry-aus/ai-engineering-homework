"""Hybrid query engine combining RAG and Knowledge Graph reasoning."""

import logging
from typing import List, Dict, Optional, Tuple
from llama_index.llms.openai import OpenAI

from graph_rag.graph_store import Neo4jGraphStore
from graph_rag.vector_store import DocumentVectorStore
from graph_rag.config import (
    OPENAI_API_KEY,
    LLM_MODEL,
    TOP_K_DOCS,
    TOP_K_GRAPH,
    MAX_HOP,
    VECTOR_WEIGHT,
    GRAPH_WEIGHT,
    CONFIDENCE_THRESHOLD,
)

logger = logging.getLogger(__name__)


class HybridQueryEngine:
    """
    Hybrid query engine that combines:
    1. Document retrieval (RAG) from vector store
    2. Knowledge graph reasoning (KG) from Neo4j
    3. LLM synthesis for final answer
    """

    def __init__(
        self,
        graph_store: Neo4jGraphStore,
        vector_store: DocumentVectorStore,
    ):
        """
        Initialize hybrid query engine.

        Args:
            graph_store: Neo4j graph store instance
            vector_store: Document vector store instance
        """
        self.graph_store = graph_store
        self.vector_store = vector_store
        self.llm = OpenAI(model=LLM_MODEL, api_key=OPENAI_API_KEY)
        logger.info("Hybrid query engine initialized")

    def extract_entities(self, query: str) -> List[str]:
        """
        Extract company names from query using LLM.

        Args:
            query: User query

        Returns:
            List of extracted company names
        """
        prompt = f"""
从以下查询中提取公司名称。如果有多个公司名称，返回所有公司名称。
只返回公司名称，每行一个，不要其他内容。

查询：{query}

公司名称：
"""
        response = self.llm.complete(prompt)
        entities = [
            line.strip()
            for line in str(response).strip().split("\n")
            if line.strip()
        ]

        logger.info(f"Extracted entities: {entities}")
        return entities

    def classify_query_type(self, query: str) -> str:
        """
        Classify the type of query to determine processing strategy.

        Args:
            query: User query

        Returns:
            Query type: 'ownership', 'relation', 'general', 'multi_hop'
        """
        prompt = f"""
请分析以下问题的类型，从下列选项中选择一个：
- ownership: 关于股权、股东、控股关系的问题
- relation: 关于公司关系、合作、竞争的问题
- general: 关于公司基本信息的问题
- multi_hop: 需要多步推理的复杂问题

只返回类型名称，不要其他内容。

问题：{query}

类型：
"""
        response = self.llm.complete(prompt)
        query_type = str(response).strip().lower()

        if query_type not in ["ownership", "relation", "general", "multi_hop"]:
            query_type = "general"

        logger.info(f"Query type: {query_type}")
        return query_type

    def retrieve_from_vector_store(
        self, query: str, top_k: int = TOP_K_DOCS
    ) -> Tuple[List[Dict], float]:
        """
        Retrieve relevant documents from vector store.

        Args:
            query: User query
            top_k: Number of documents to retrieve

        Returns:
            Tuple of (documents, confidence_score)
        """
        logger.info("Retrieving from vector store...")
        results = self.vector_store.similarity_search(query, top_k=top_k)

        # Calculate confidence based on scores
        if results:
            avg_score = sum(r["score"] for r in results) / len(results)
            confidence = min(avg_score, 1.0)
        else:
            confidence = 0.0

        logger.info(f"Retrieved {len(results)} documents, confidence: {confidence:.3f}")
        return results, confidence

    def retrieve_from_graph(
        self, query: str, query_type: str, entities: List[str]
    ) -> Tuple[List[Dict], float]:
        """
        Retrieve information from knowledge graph.

        Args:
            query: User query
            query_type: Type of query
            entities: Extracted entities

        Returns:
            Tuple of (graph_results, confidence_score)
        """
        logger.info(f"Retrieving from graph (type: {query_type})...")

        graph_results = []
        confidence = 0.0

        if not entities:
            return graph_results, confidence

        try:
            if query_type == "ownership":
                # Find shareholders and ownership chains
                for entity in entities:
                    shareholders = self.graph_store.find_major_shareholders(
                        entity, max_hops=MAX_HOP
                    )
                    ownership_chain = self.graph_store.find_ownership_chain(entity)

                    graph_results.extend([
                        {
                            "type": "shareholder",
                            "entity": entity,
                            "data": shareholders,
                        },
                        {
                            "type": "ownership_chain",
                            "entity": entity,
                            "data": ownership_chain,
                        },
                    ])

                confidence = 0.9 if graph_results else 0.0

            elif query_type == "relation":
                # Find related companies
                for entity in entities:
                    related = self.graph_store.find_related_companies(entity)
                    graph_results.append({
                        "type": "related_companies",
                        "entity": entity,
                        "data": related,
                    })

                confidence = 0.85 if graph_results else 0.0

            elif query_type == "multi_hop":
                # Multi-hop reasoning between entities
                if len(entities) >= 2:
                    paths = self.graph_store.multi_hop_query(
                        entities[0], entities[1], max_hops=MAX_HOP
                    )
                    graph_results.append({
                        "type": "multi_hop_path",
                        "entities": entities[:2],
                        "data": paths,
                    })
                    confidence = 0.8 if paths else 0.0
                else:
                    # Single entity multi-hop
                    for entity in entities:
                        related = self.graph_store.find_related_companies(entity)
                        graph_results.append({
                            "type": "related_companies",
                            "entity": entity,
                            "data": related,
                        })
                    confidence = 0.75 if graph_results else 0.0

            else:  # general
                # Get company info and basic relationships
                for entity in entities:
                    company_info = self.graph_store.get_company_info(entity)
                    subsidiaries = self.graph_store.find_subsidiaries(entity)

                    if company_info:
                        graph_results.append({
                            "type": "company_info",
                            "entity": entity,
                            "data": company_info,
                        })

                    if subsidiaries:
                        graph_results.append({
                            "type": "subsidiaries",
                            "entity": entity,
                            "data": subsidiaries,
                        })

                confidence = 0.7 if graph_results else 0.0

        except Exception as e:
            logger.error(f"Error retrieving from graph: {e}")
            confidence = 0.0

        logger.info(
            f"Retrieved {len(graph_results)} graph results, confidence: {confidence:.3f}"
        )
        return graph_results, confidence

    def combine_results(
        self,
        vector_results: List[Dict],
        vector_confidence: float,
        graph_results: List[Dict],
        graph_confidence: float,
    ) -> Dict:
        """
        Combine results from vector store and graph with weighted scoring.

        Args:
            vector_results: Results from vector store
            vector_confidence: Confidence of vector results
            graph_results: Results from knowledge graph
            graph_confidence: Confidence of graph results

        Returns:
            Combined results with hybrid score
        """
        # Calculate hybrid confidence score
        hybrid_score = (
            VECTOR_WEIGHT * vector_confidence + GRAPH_WEIGHT * graph_confidence
        )

        # Determine primary source based on confidence
        if graph_confidence > vector_confidence:
            primary_source = "knowledge_graph"
        elif vector_confidence > graph_confidence:
            primary_source = "vector_store"
        else:
            primary_source = "hybrid"

        return {
            "vector_results": vector_results,
            "vector_confidence": vector_confidence,
            "graph_results": graph_results,
            "graph_confidence": graph_confidence,
            "hybrid_score": hybrid_score,
            "primary_source": primary_source,
            "sufficient_confidence": hybrid_score >= CONFIDENCE_THRESHOLD,
        }

    def validate_graph_results(self, graph_results: List[Dict]) -> Tuple[bool, str]:
        """
        Validate graph results to detect potential errors.

        Args:
            graph_results: Results from knowledge graph

        Returns:
            Tuple of (is_valid, validation_message)
        """
        if not graph_results:
            return False, "No graph results found"

        # Check for empty data
        empty_count = sum(
            1 for result in graph_results if not result.get("data")
        )

        if empty_count == len(graph_results):
            return False, "All graph queries returned empty results"

        # Check for consistency
        # (Simple validation - can be enhanced)
        return True, "Graph results validated"

    def generate_answer(
        self, query: str, combined_results: Dict, reasoning_path: List[str]
    ) -> str:
        """
        Generate final answer using LLM with all retrieved information.

        Args:
            query: User query
            combined_results: Combined results from both sources
            reasoning_path: List of reasoning steps

        Returns:
            Generated answer
        """
        logger.info("Generating final answer with LLM...")

        # Prepare context from vector results
        vector_context = "\n\n".join([
            f"[文档 {i+1}] {doc['text']}"
            for i, doc in enumerate(combined_results["vector_results"])
        ])

        # Prepare context from graph results
        graph_context_parts = []
        for result in combined_results["graph_results"]:
            result_type = result["type"]
            data = result["data"]

            if result_type == "shareholder" and data:
                for item in data:
                    rel_desc = " -> ".join([
                        f"{r['type']} ({r['properties'].get('stake', 'N/A')})"
                        for r in item.get("relationships", [])
                    ])
                    graph_context_parts.append(
                        f"股东关系：{item['shareholder_name']} -> {item['target_name']}\n"
                        f"关系链：{rel_desc}"
                    )

            elif result_type == "ownership_chain" and data:
                for item in data:
                    graph_context_parts.append(
                        f"股权链：{item['owner_name']} -> {item['target_name']}\n"
                        f"链条长度：{item['chain_length']}"
                    )

            elif result_type == "subsidiaries" and data:
                subs = ", ".join([s["subsidiary_name"] for s in data])
                graph_context_parts.append(f"子公司：{subs}")

        graph_context = "\n\n".join(graph_context_parts)

        # Prepare reasoning path
        reasoning_text = "\n".join([f"{i+1}. {step}" for i, step in enumerate(reasoning_path)])

        # Create prompt
        prompt = f"""
请基于以下信息回答问题。请综合文档信息和知识图谱信息，给出准确、全面的答案。

【问题】
{query}

【推理过程】
{reasoning_text}

【文档信息】（来源：向量检索）
{vector_context if vector_context else "无相关文档"}

【图谱信息】（来源：知识图谱）
{graph_context if graph_context else "无相关图谱信息"}

【可信度分析】
- 文档检索可信度：{combined_results['vector_confidence']:.2%}
- 图谱推理可信度：{combined_results['graph_confidence']:.2%}
- 综合可信度：{combined_results['hybrid_score']:.2%}
- 主要信息来源：{combined_results['primary_source']}

请生成答案，要求：
1. 优先使用知识图谱信息（如果存在且可信）
2. 结合文档信息进行补充说明
3. 如果两个来源信息冲突，请说明并解释
4. 给出答案的可信度评估
5. 如果信息不足，请明确指出

【答案】
"""

        response = self.llm.complete(prompt)
        return str(response).strip()

    def query(self, query: str) -> Dict:
        """
        Process a hybrid query combining RAG and KG reasoning.

        Args:
            query: User query

        Returns:
            Complete query results with answer and reasoning path
        """
        logger.info(f"Processing hybrid query: {query}")

        # Initialize reasoning path for explainability
        reasoning_path = []

        # Step 1: Classify query type
        query_type = self.classify_query_type(query)
        reasoning_path.append(f"识别查询类型：{query_type}")

        # Step 2: Extract entities
        entities = self.extract_entities(query)
        reasoning_path.append(f"提取实体：{', '.join(entities) if entities else '无'}")

        # Step 3: Retrieve from vector store (RAG)
        vector_results, vector_confidence = self.retrieve_from_vector_store(query)
        reasoning_path.append(
            f"文档检索：找到 {len(vector_results)} 个相关文档 "
            f"(可信度: {vector_confidence:.2%})"
        )

        # Step 4: Retrieve from knowledge graph (KG)
        graph_results, graph_confidence = self.retrieve_from_graph(
            query, query_type, entities
        )
        reasoning_path.append(
            f"图谱查询：获得 {len(graph_results)} 组图谱信息 "
            f"(可信度: {graph_confidence:.2%})"
        )

        # Step 5: Validate graph results
        is_valid, validation_msg = self.validate_graph_results(graph_results)
        reasoning_path.append(f"结果验证：{validation_msg}")

        if not is_valid:
            logger.warning(f"Graph validation failed: {validation_msg}")

        # Step 6: Combine results
        combined_results = self.combine_results(
            vector_results, vector_confidence, graph_results, graph_confidence
        )
        reasoning_path.append(
            f"融合评分：向量权重={VECTOR_WEIGHT}, 图谱权重={GRAPH_WEIGHT}, "
            f"综合得分={combined_results['hybrid_score']:.2%}"
        )

        # Step 7: Generate final answer
        answer = self.generate_answer(query, combined_results, reasoning_path)
        reasoning_path.append("生成最终答案")

        return {
            "query": query,
            "query_type": query_type,
            "entities": entities,
            "answer": answer,
            "reasoning_path": reasoning_path,
            "vector_results": vector_results,
            "graph_results": graph_results,
            "confidence_scores": {
                "vector": vector_confidence,
                "graph": graph_confidence,
                "hybrid": combined_results["hybrid_score"],
            },
            "primary_source": combined_results["primary_source"],
            "validation": {
                "is_valid": is_valid,
                "message": validation_msg,
            },
        }
