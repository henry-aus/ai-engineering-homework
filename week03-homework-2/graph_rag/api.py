"""FastAPI REST API for Graph RAG system."""

import logging
from typing import Optional, List
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from graph_rag.graph_store import Neo4jGraphStore, initialize_graph
from graph_rag.vector_store import DocumentVectorStore, initialize_vector_store
from graph_rag.hybrid_query import HybridQueryEngine

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Graph RAG System",
    description="Hybrid question answering system combining RAG and Knowledge Graph reasoning",
    version="1.0.0",
)

# Global instances
graph_store: Optional[Neo4jGraphStore] = None
vector_store: Optional[DocumentVectorStore] = None
query_engine: Optional[HybridQueryEngine] = None


# Request/Response models
class QueryRequest(BaseModel):
    """Query request model."""

    question: str = Field(..., description="User's question", min_length=1)
    include_reasoning: bool = Field(
        True, description="Include reasoning path in response"
    )
    include_sources: bool = Field(True, description="Include source information")


class QueryResponse(BaseModel):
    """Query response model."""

    query: str
    query_type: str
    entities: List[str]
    answer: str
    reasoning_path: Optional[List[str]] = None
    confidence_scores: dict
    primary_source: str
    validation: dict
    vector_results_count: int = 0
    graph_results_count: int = 0


class GraphStatsResponse(BaseModel):
    """Graph statistics response."""

    total_companies: int
    total_relationships: int
    relationship_types: List[dict]


class CompanyInfoRequest(BaseModel):
    """Company info request."""

    company_name: str = Field(..., description="Company name")


class StatusResponse(BaseModel):
    """System status response."""

    status: str
    message: str
    graph_connected: bool
    vector_store_ready: bool


# API endpoints
@app.on_event("startup")
async def startup_event():
    """Initialize system on startup."""
    global graph_store, vector_store, query_engine

    logger.info("Starting Graph RAG API...")

    try:
        # Initialize graph store
        logger.info("Initializing knowledge graph...")
        graph_store = initialize_graph(clear_existing=False)

        # Initialize vector store
        logger.info("Initializing vector store...")
        vector_store = initialize_vector_store(rebuild=False)

        # Initialize query engine
        logger.info("Initializing hybrid query engine...")
        query_engine = HybridQueryEngine(graph_store, vector_store)

        logger.info("Graph RAG API started successfully")

    except Exception as e:
        logger.error(f"Failed to start API: {e}", exc_info=True)
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down Graph RAG API...")
    if graph_store:
        graph_store.close()


@app.get("/", response_model=dict)
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Graph RAG System API",
        "version": "1.0.0",
        "description": "Hybrid question answering combining RAG and Knowledge Graph",
        "endpoints": {
            "query": "POST /query - Query the system",
            "graph_stats": "GET /graph/stats - Get graph statistics",
            "company_info": "POST /graph/company - Get company information",
            "status": "GET /status - System status",
            "health": "GET /health - Health check",
        },
    }


@app.post("/query", response_model=QueryResponse)
async def query_system(request: QueryRequest):
    """
    Query the Graph RAG system.

    Combines document retrieval (RAG) and knowledge graph reasoning (KG)
    to provide comprehensive answers.
    """
    if not query_engine:
        raise HTTPException(status_code=500, detail="Query engine not initialized")

    try:
        logger.info(f"Processing query: {request.question}")

        # Process query
        result = query_engine.query(request.question)

        # Prepare response
        response_data = {
            "query": result["query"],
            "query_type": result["query_type"],
            "entities": result["entities"],
            "answer": result["answer"],
            "confidence_scores": result["confidence_scores"],
            "primary_source": result["primary_source"],
            "validation": result["validation"],
            "vector_results_count": len(result["vector_results"]),
            "graph_results_count": len(result["graph_results"]),
        }

        # Include optional fields
        if request.include_reasoning:
            response_data["reasoning_path"] = result["reasoning_path"]

        return QueryResponse(**response_data)

    except Exception as e:
        logger.error(f"Query failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")


@app.get("/graph/stats", response_model=GraphStatsResponse)
async def get_graph_stats():
    """Get knowledge graph statistics."""
    if not graph_store:
        raise HTTPException(status_code=500, detail="Graph store not initialized")

    try:
        stats = graph_store.get_graph_stats()
        return GraphStatsResponse(**stats)

    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get stats: {str(e)}"
        )


@app.post("/graph/company", response_model=dict)
async def get_company_info(request: CompanyInfoRequest):
    """Get detailed information about a company."""
    if not graph_store:
        raise HTTPException(status_code=500, detail="Graph store not initialized")

    try:
        # Get company info from graph
        company_info = graph_store.get_company_info(request.company_name)

        if not company_info:
            raise HTTPException(
                status_code=404,
                detail=f"Company not found: {request.company_name}",
            )

        # Get related information
        shareholders = graph_store.find_major_shareholders(request.company_name)
        subsidiaries = graph_store.find_subsidiaries(request.company_name)
        related = graph_store.find_related_companies(request.company_name)

        return {
            "company": company_info,
            "shareholders": shareholders,
            "subsidiaries": subsidiaries,
            "related_companies": related,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get company info: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get company info: {str(e)}",
        )


@app.post("/graph/shareholders", response_model=dict)
async def find_shareholders(request: CompanyInfoRequest):
    """Find major shareholders of a company."""
    if not graph_store:
        raise HTTPException(status_code=500, detail="Graph store not initialized")

    try:
        shareholders = graph_store.find_major_shareholders(request.company_name)

        return {
            "company": request.company_name,
            "shareholders": shareholders,
            "count": len(shareholders),
        }

    except Exception as e:
        logger.error(f"Failed to find shareholders: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to find shareholders: {str(e)}",
        )


@app.get("/status", response_model=StatusResponse)
async def get_status():
    """Get system status."""
    graph_connected = graph_store is not None
    vector_ready = vector_store is not None and vector_store.index is not None
    query_ready = query_engine is not None

    if graph_connected and vector_ready and query_ready:
        status = "healthy"
        message = "System is running normally"
    else:
        status = "degraded"
        message = "Some components are not ready"

    return StatusResponse(
        status=status,
        message=message,
        graph_connected=graph_connected,
        vector_store_ready=vector_ready,
    )


@app.get("/health")
async def health_check():
    """Simple health check endpoint."""
    return {"status": "healthy", "service": "graph-rag"}


@app.post("/reload", response_model=dict)
async def reload_system():
    """Reload the entire system (graph and vector store)."""
    global graph_store, vector_store, query_engine

    try:
        logger.info("Reloading system...")

        # Close existing connections
        if graph_store:
            graph_store.close()

        # Reinitialize
        graph_store = initialize_graph(clear_existing=True)
        vector_store = initialize_vector_store(rebuild=True)
        query_engine = HybridQueryEngine(graph_store, vector_store)

        return {
            "status": "success",
            "message": "System reloaded successfully",
        }

    except Exception as e:
        logger.error(f"Failed to reload system: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to reload: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    from graph_rag.config import API_HOST, API_PORT

    uvicorn.run(app, host=API_HOST, port=API_PORT)
