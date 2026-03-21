"""Neo4j graph store for company knowledge graph."""

import logging
from typing import List, Dict, Optional, Any
from neo4j import GraphDatabase
import json
from pathlib import Path

from graph_rag.config import (
    NEO4J_URI,
    NEO4J_USER,
    NEO4J_PASSWORD,
    NEO4J_DATABASE,
    DATA_DIR,
)

logger = logging.getLogger(__name__)


class Neo4jGraphStore:
    """Neo4j-based knowledge graph store."""

    def __init__(self):
        """Initialize Neo4j connection."""
        self.driver = GraphDatabase.driver(
            NEO4J_URI,
            auth=(NEO4J_USER, NEO4J_PASSWORD),
        )
        logger.info(f"Connected to Neo4j at {NEO4J_URI}")

    def close(self):
        """Close Neo4j connection."""
        if self.driver:
            self.driver.close()
            logger.info("Neo4j connection closed")

    def clear_graph(self):
        """Clear all nodes and relationships."""
        with self.driver.session(database=NEO4J_DATABASE) as session:
            session.run("MATCH (n) DETACH DELETE n")
        logger.info("Graph cleared")

    def create_company_node(self, company: Dict) -> None:
        """
        Create a company node in the graph.

        Args:
            company: Company data dictionary
        """
        query = """
        MERGE (c:Company {id: $id})
        SET c.name = $name,
            c.type = $type,
            c.industry = $industry,
            c.founded = $founded,
            c.description = $description
        """

        with self.driver.session(database=NEO4J_DATABASE) as session:
            session.run(
                query,
                id=company["id"],
                name=company["name"],
                type=company["type"],
                industry=company["industry"],
                founded=company["founded"],
                description=company["description"],
            )

    def create_relationship(self, rel: Dict) -> None:
        """
        Create a relationship between two companies.

        Args:
            rel: Relationship data dictionary
        """
        query = f"""
        MATCH (from:Company {{id: $from_id}})
        MATCH (to:Company {{id: $to_id}})
        MERGE (from)-[r:{rel['type']}]->(to)
        SET r += $properties
        """

        with self.driver.session(database=NEO4J_DATABASE) as session:
            session.run(
                query,
                from_id=rel["from"],
                to_id=rel["to"],
                properties=rel["properties"],
            )

    def load_graph_from_files(
        self,
        companies_file: Path = DATA_DIR / "companies.json",
        relationships_file: Path = DATA_DIR / "relationships.json",
    ) -> None:
        """
        Load graph data from JSON files.

        Args:
            companies_file: Path to companies JSON file
            relationships_file: Path to relationships JSON file
        """
        logger.info("Loading graph data from files...")

        # Load companies
        with open(companies_file, "r", encoding="utf-8") as f:
            companies = json.load(f)

        logger.info(f"Creating {len(companies)} company nodes...")
        for company in companies:
            self.create_company_node(company)

        # Load relationships
        with open(relationships_file, "r", encoding="utf-8") as f:
            relationships = json.load(f)

        logger.info(f"Creating {len(relationships)} relationships...")
        for rel in relationships:
            self.create_relationship(rel)

        logger.info("Graph data loaded successfully")

    def find_major_shareholders(self, company_name: str, max_hops: int = 2) -> List[Dict]:
        """
        Find major shareholders of a company.

        Args:
            company_name: Name of the company
            max_hops: Maximum relationship hops to traverse

        Returns:
            List of shareholder information with paths
        """
        query = f"""
        MATCH path = (shareholder:Company)-[r:MAJOR_SHAREHOLDER|CONTROLS*1..{max_hops}]->(target:Company)
        WHERE target.name CONTAINS $name
        WITH shareholder, target, path, relationships(path) as rels
        RETURN shareholder.name as shareholder_name,
               shareholder.id as shareholder_id,
               target.name as target_name,
               target.id as target_id,
               [rel in rels | {{type: type(rel), properties: properties(rel)}}] as relationships,
               length(path) as hops
        ORDER BY hops, shareholder.name
        """

        with self.driver.session(database=NEO4J_DATABASE) as session:
            result = session.run(query, name=company_name)
            records = list(result)

        shareholders = []
        for record in records:
            shareholders.append({
                "shareholder_name": record["shareholder_name"],
                "shareholder_id": record["shareholder_id"],
                "target_name": record["target_name"],
                "target_id": record["target_id"],
                "relationships": record["relationships"],
                "hops": record["hops"],
            })

        return shareholders

    def find_ownership_chain(self, company_name: str) -> List[Dict]:
        """
        Find complete ownership chain for a company.

        Args:
            company_name: Name of the company

        Returns:
            List of ownership chain information
        """
        query = """
        MATCH path = (owner:Company)-[r:MAJOR_SHAREHOLDER|CONTROLS|WHOLLY_OWNS*]->(target:Company)
        WHERE target.name CONTAINS $name
        WITH owner, target, path,
             [rel in relationships(path) | type(rel)] as rel_types,
             [rel in relationships(path) | properties(rel)] as rel_props
        RETURN owner.name as owner_name,
               owner.id as owner_id,
               owner.type as owner_type,
               target.name as target_name,
               rel_types,
               rel_props,
               length(path) as chain_length
        ORDER BY chain_length
        """

        with self.driver.session(database=NEO4J_DATABASE) as session:
            result = session.run(query, name=company_name)
            return [dict(record) for record in result]

    def find_subsidiaries(self, company_name: str) -> List[Dict]:
        """
        Find all subsidiaries of a company.

        Args:
            company_name: Name of the parent company

        Returns:
            List of subsidiary information
        """
        query = """
        MATCH (parent:Company)-[r:WHOLLY_OWNS|CONTROLS]->(sub:Company)
        WHERE parent.name CONTAINS $name
        RETURN sub.name as subsidiary_name,
               sub.id as subsidiary_id,
               sub.type as subsidiary_type,
               sub.industry as subsidiary_industry,
               type(r) as relationship_type,
               properties(r) as relationship_properties
        """

        with self.driver.session(database=NEO4J_DATABASE) as session:
            result = session.run(query, name=company_name)
            return [dict(record) for record in result]

    def find_related_companies(
        self, company_name: str, relationship_types: Optional[List[str]] = None
    ) -> List[Dict]:
        """
        Find companies related to the given company.

        Args:
            company_name: Name of the company
            relationship_types: Optional list of relationship types to filter

        Returns:
            List of related company information
        """
        if relationship_types:
            rel_filter = "|".join(relationship_types)
            rel_clause = f"[r:{rel_filter}]"
        else:
            rel_clause = "[r]"

        query = f"""
        MATCH (c:Company)-{rel_clause}-(related:Company)
        WHERE c.name CONTAINS $name
        RETURN related.name as company_name,
               related.id as company_id,
               related.type as company_type,
               related.industry as industry,
               type(r) as relationship_type,
               properties(r) as relationship_properties
        """

        with self.driver.session(database=NEO4J_DATABASE) as session:
            result = session.run(query, name=company_name)
            return [dict(record) for record in result]

    def multi_hop_query(self, start_company: str, end_company: str, max_hops: int = 3) -> List[Dict]:
        """
        Find paths between two companies.

        Args:
            start_company: Starting company name
            end_company: Ending company name
            max_hops: Maximum number of hops

        Returns:
            List of paths with detailed information
        """
        query = f"""
        MATCH path = (start:Company)-[*1..{max_hops}]-(end:Company)
        WHERE start.name CONTAINS $start_name
          AND end.name CONTAINS $end_name
        WITH path,
             [node in nodes(path) | {{name: node.name, id: node.id}}] as node_info,
             [rel in relationships(path) | {{type: type(rel), properties: properties(rel)}}] as rel_info
        RETURN node_info, rel_info, length(path) as path_length
        ORDER BY path_length
        LIMIT 10
        """

        with self.driver.session(database=NEO4J_DATABASE) as session:
            result = session.run(query, start_name=start_company, end_name=end_company)
            return [dict(record) for record in result]

    def execute_cypher(self, query: str, parameters: Optional[Dict] = None) -> List[Dict]:
        """
        Execute a custom Cypher query.

        Args:
            query: Cypher query string
            parameters: Optional query parameters

        Returns:
            List of query results
        """
        with self.driver.session(database=NEO4J_DATABASE) as session:
            result = session.run(query, parameters or {})
            return [dict(record) for record in result]

    def get_company_info(self, company_name: str) -> Optional[Dict]:
        """
        Get detailed information about a company.

        Args:
            company_name: Name of the company

        Returns:
            Company information dictionary
        """
        query = """
        MATCH (c:Company)
        WHERE c.name CONTAINS $name
        RETURN c.name as name,
               c.id as id,
               c.type as type,
               c.industry as industry,
               c.founded as founded,
               c.description as description
        LIMIT 1
        """

        with self.driver.session(database=NEO4J_DATABASE) as session:
            result = session.run(query, name=company_name)
            record = result.single()
            return dict(record) if record else None

    def get_graph_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the knowledge graph.

        Returns:
            Dictionary with graph statistics
        """
        queries = {
            "total_companies": "MATCH (c:Company) RETURN count(c) as count",
            "total_relationships": "MATCH ()-[r]->() RETURN count(r) as count",
            "relationship_types": """
                MATCH ()-[r]->()
                RETURN type(r) as type, count(*) as count
                ORDER BY count DESC
            """,
        }

        stats = {}
        with self.driver.session(database=NEO4J_DATABASE) as session:
            # Total companies
            result = session.run(queries["total_companies"])
            stats["total_companies"] = result.single()["count"]

            # Total relationships
            result = session.run(queries["total_relationships"])
            stats["total_relationships"] = result.single()["count"]

            # Relationship types
            result = session.run(queries["relationship_types"])
            stats["relationship_types"] = [dict(record) for record in result]

        return stats


def initialize_graph(clear_existing: bool = False) -> Neo4jGraphStore:
    """
    Initialize the knowledge graph with sample data.

    Args:
        clear_existing: Whether to clear existing data

    Returns:
        Initialized Neo4jGraphStore instance
    """
    store = Neo4jGraphStore()

    if clear_existing:
        store.clear_graph()

    # Load data from files
    store.load_graph_from_files()

    # Get stats
    stats = store.get_graph_stats()
    logger.info(f"Graph initialized: {stats}")

    return store
