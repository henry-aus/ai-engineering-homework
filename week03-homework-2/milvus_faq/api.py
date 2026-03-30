"""FastAPI REST API for Milvus FAQ system."""

import logging
from typing import Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

from milvus_faq.vector_store import MilvusFAQStore
from milvus_faq.data_loader import FAQDataLoader
from milvus_faq.config import TOP_K

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Milvus FAQ Retrieval System",
    description="A FAQ retrieval system powered by Milvus and LlamaIndex",
    version="1.0.0",
)

# Global FAQ store instance
faq_store: Optional[MilvusFAQStore] = None


# Request/Response models
class QueryRequest(BaseModel):
    """Query request model."""

    question: str = Field(..., description="User's question", min_length=1)
    top_k: int = Field(TOP_K, description="Number of results to return", ge=1, le=10)
    search_only: bool = Field(
        False, description="If True, return only similarity search without LLM answer"
    )


class QueryResponse(BaseModel):
    """Query response model."""

    answer: Optional[str] = Field(None, description="Generated answer from LLM")
    sources: list = Field([], description="Source documents with scores")
    query: str = Field(..., description="Original query")


class AddFAQRequest(BaseModel):
    """Add FAQ request model."""

    faq_id: str = Field(..., description="Unique FAQ ID")
    question: str = Field(..., description="Question text")
    answer: str = Field(..., description="Answer text")


class StatusResponse(BaseModel):
    """System status response."""

    status: str
    message: str
    stats: dict


# API endpoints
@app.on_event("startup")
async def startup_event():
    """Initialize FAQ store on startup."""
    global faq_store
    logger.info("Starting up FAQ API...")

    try:
        faq_store = MilvusFAQStore()

        # Try to load existing index
        if faq_store.load_index() is None:
            # No existing index, build from data file
            logger.info("No existing index found, building new index...")
            documents = FAQDataLoader.load_and_convert()
            faq_store.build_index(documents)

        logger.info("FAQ API started successfully")
    except Exception as e:
        logger.error(f"Failed to start FAQ API: {e}")
        raise


@app.get("/", response_model=dict)
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Milvus FAQ Retrieval System",
        "version": "1.0.0",
        "endpoints": {
            "query": "/query",
            "add_faq": "/faq",
            "update_faq": "/faq/{faq_id}",
            "delete_faq": "/faq/{faq_id}",
            "reload": "/reload",
            "status": "/status",
        },
    }


@app.post("/query", response_model=QueryResponse)
async def query_faq(request: QueryRequest):
    """
    Query the FAQ system.

    Returns the most relevant FAQ entries for the given question.
    """
    if faq_store is None:
        raise HTTPException(status_code=500, detail="FAQ store not initialized")

    try:
        if request.search_only:
            # Similarity search only
            sources = faq_store.similarity_search(request.question, request.top_k)
            return QueryResponse(
                answer=None, sources=sources, query=request.question
            )
        else:
            # Full query with LLM answer
            result = faq_store.query(request.question, request.top_k)
            return QueryResponse(**result)

    except Exception as e:
        logger.error(f"Query failed: {e}")
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")


@app.post("/faq", response_model=dict)
async def add_faq(request: AddFAQRequest):
    """
    Add a new FAQ entry (hot update).

    The new FAQ will be immediately available for queries.
    """
    if faq_store is None:
        raise HTTPException(status_code=500, detail="FAQ store not initialized")

    try:
        # Create document from FAQ
        document = FAQDataLoader.add_faq_entry(
            request.faq_id, request.question, request.answer
        )

        # Add to index
        faq_store.add_documents([document])

        return {
            "status": "success",
            "message": f"FAQ {request.faq_id} added successfully",
            "faq_id": request.faq_id,
        }

    except Exception as e:
        logger.error(f"Failed to add FAQ: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to add FAQ: {str(e)}")


@app.put("/faq/{faq_id}", response_model=dict)
async def update_faq(faq_id: str, request: AddFAQRequest):
    """
    Update an existing FAQ entry (hot update).

    The updated FAQ will be immediately available for queries.
    """
    if faq_store is None:
        raise HTTPException(status_code=500, detail="FAQ store not initialized")

    try:
        # Create updated document
        document = FAQDataLoader.add_faq_entry(
            request.faq_id, request.question, request.answer
        )

        # Update in index
        faq_store.update_document(faq_id, document)

        return {
            "status": "success",
            "message": f"FAQ {faq_id} updated successfully",
            "faq_id": faq_id,
        }

    except Exception as e:
        logger.error(f"Failed to update FAQ: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update FAQ: {str(e)}")


@app.delete("/faq/{faq_id}", response_model=dict)
async def delete_faq(faq_id: str):
    """
    Delete a FAQ entry (hot update).

    The FAQ will be immediately removed from queries.
    """
    if faq_store is None:
        raise HTTPException(status_code=500, detail="FAQ store not initialized")

    try:
        faq_store.delete_document(faq_id)

        return {
            "status": "success",
            "message": f"FAQ {faq_id} deleted successfully",
            "faq_id": faq_id,
        }

    except Exception as e:
        logger.error(f"Failed to delete FAQ: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete FAQ: {str(e)}")


@app.post("/reload", response_model=dict)
async def reload_index(background_tasks: BackgroundTasks):
    """
    Reload the entire index from the FAQ data file.

    This operation runs in the background.
    """
    if faq_store is None:
        raise HTTPException(status_code=500, detail="FAQ store not initialized")

    def reload_task():
        try:
            logger.info("Reloading index from data file...")
            documents = FAQDataLoader.load_and_convert()
            faq_store.build_index(documents)
            logger.info("Index reloaded successfully")
        except Exception as e:
            logger.error(f"Failed to reload index: {e}")

    background_tasks.add_task(reload_task)

    return {
        "status": "success",
        "message": "Index reload started in background",
    }


@app.get("/status", response_model=StatusResponse)
async def get_status():
    """
    Get system status and statistics.
    """
    if faq_store is None:
        return StatusResponse(
            status="error",
            message="FAQ store not initialized",
            stats={},
        )

    try:
        stats = faq_store.get_stats()
        return StatusResponse(
            status="healthy",
            message="System is running",
            stats=stats,
        )
    except Exception as e:
        return StatusResponse(
            status="error",
            message=f"Error getting status: {str(e)}",
            stats={},
        )


@app.get("/health")
async def health_check():
    """Simple health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    from milvus_faq.config import API_HOST, API_PORT

    uvicorn.run(app, host=API_HOST, port=API_PORT)
