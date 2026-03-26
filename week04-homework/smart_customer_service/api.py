"""FastAPI server for smart customer service with hot reload support."""
from typing import Dict, Any, Optional, List
from datetime import datetime
import uuid
import traceback

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from contextlib import asynccontextmanager

from .config import Config
from .graph import create_conversation_graph, run_conversation_turn, ConversationState
from .hot_reload import get_hot_reload_manager


# Pydantic models for request/response
class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    session_id: Optional[str] = Field(None, description="Session ID for conversation continuity")
    message: str = Field(..., description="User message")


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""
    session_id: str = Field(..., description="Session ID for this conversation")
    response: str = Field(..., description="Assistant response")
    intent: Optional[str] = Field(None, description="Detected intent")
    waiting_for: Optional[str] = Field(None, description="Parameter waiting for user input")
    completed: bool = Field(False, description="Whether the current task is completed")


class HealthResponse(BaseModel):
    """Response model for health check."""
    status: str = Field(..., description="Service status")
    timestamp: str = Field(..., description="Current timestamp")
    version: str = Field(..., description="Application version")
    hot_reload: Dict[str, Any] = Field(..., description="Hot reload status")
    config: Dict[str, Any] = Field(..., description="Current configuration")


class ReloadRequest(BaseModel):
    """Request model for reload endpoints."""
    model_name: Optional[str] = Field(None, description="New model name")
    api_key: Optional[str] = Field(None, description="New API key")
    temperature: Optional[float] = Field(None, description="New temperature")


class ReloadResponse(BaseModel):
    """Response model for reload endpoints."""
    success: bool
    message: str
    details: Dict[str, Any]


# Session storage
class SessionManager:
    """Manage conversation sessions with version pinning."""

    def __init__(self):
        self.sessions: Dict[str, Dict[str, Any]] = {}

    def create_session(self) -> str:
        """Create a new session with current versions."""
        session_id = str(uuid.uuid4())
        versions = get_hot_reload_manager().get_current_version()

        self.sessions[session_id] = {
            "state": {
                "messages": [],
                "intent": None,
                "parameters": {},
                "tool_result": None,
                "waiting_for_parameter": None,
                "completed": False,
            },
            "graph": create_conversation_graph(),
            "created_at": datetime.now(),
            "model_version": versions["model_version"],
            "plugin_version": versions["plugin_version"],
        }

        return session_id

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session by ID."""
        return self.sessions.get(session_id)

    def update_session_state(self, session_id: str, state: ConversationState):
        """Update session state."""
        if session_id in self.sessions:
            self.sessions[session_id]["state"] = state

    def delete_session(self, session_id: str):
        """Delete a session."""
        if session_id in self.sessions:
            del self.sessions[session_id]

    def list_sessions(self) -> List[Dict[str, Any]]:
        """List all active sessions."""
        return [
            {
                "session_id": sid,
                "created_at": session["created_at"].isoformat(),
                "model_version": session["model_version"],
                "plugin_version": session["plugin_version"],
                "message_count": len(session["state"]["messages"]),
            }
            for sid, session in self.sessions.items()
        ]


# Global session manager
session_manager = SessionManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    print("="*60)
    print("🚀 Starting Smart Customer Service API")
    print("="*60)

    try:
        Config.validate()
        print("✅ Configuration validated")
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        raise

    # Initialize hot reload manager
    hot_reload_mgr = get_hot_reload_manager()
    print(f"✅ Hot reload manager initialized")

    # Start file watcher if enabled
    if Config.PLUGIN_WATCH_ENABLED:
        hot_reload_mgr.start_file_watcher()
        print("✅ Plugin file watcher started")

    print(f"📡 API server ready on http://{Config.API_HOST}:{Config.API_PORT}")
    print("="*60)

    yield

    # Shutdown
    print("\n🛑 Shutting down...")
    hot_reload_mgr.stop_file_watcher()
    print("✅ Cleanup completed")


# Create FastAPI app
app = FastAPI(
    title="Smart Customer Service API",
    description="AI-powered customer service with hot reload support",
    version="3.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse, tags=["Monitoring"])
async def health_check():
    """
    Health check endpoint for monitoring.

    Returns service status, version, and hot reload information.
    """
    hot_reload_mgr = get_hot_reload_manager()

    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        version="3.0.0",
        hot_reload=hot_reload_mgr.get_status(),
        config=Config.get_dict(),
    )


@app.post("/chat", response_model=ChatResponse, tags=["Conversation"])
async def chat(request: ChatRequest):
    """
    Chat endpoint for multi-turn conversations.

    Maintains session state and supports tool calling.
    """
    try:
        # Get or create session
        if request.session_id:
            session = session_manager.get_session(request.session_id)
            if not session:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Session {request.session_id} not found"
                )
            session_id = request.session_id
        else:
            session_id = session_manager.create_session()
            session = session_manager.get_session(session_id)

        # Run conversation turn
        graph = session["graph"]
        state = session["state"]

        new_state = run_conversation_turn(graph, state, request.message)
        session_manager.update_session_state(session_id, new_state)

        # Extract response
        messages = new_state.get("messages", [])
        last_message = messages[-1] if messages else None
        response_text = last_message.content if last_message and hasattr(last_message, 'content') else "No response"

        return ChatResponse(
            session_id=session_id,
            response=response_text,
            intent=new_state.get("intent"),
            waiting_for=new_state.get("waiting_for_parameter"),
            completed=new_state.get("completed", False),
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error in chat endpoint: {e}")
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error: {str(e)}"
        )


@app.post("/admin/reload-model", response_model=ReloadResponse, tags=["Admin"])
async def reload_model(request: ReloadRequest):
    """
    Reload model configuration.

    New sessions will use the updated model. Existing sessions continue with their original model.
    """
    try:
        hot_reload_mgr = get_hot_reload_manager()
        result = hot_reload_mgr.reload_model(
            model_name=request.model_name,
            api_key=request.api_key,
            temperature=request.temperature,
        )

        return ReloadResponse(
            success=True,
            message="Model configuration reloaded successfully",
            details=result,
        )
    except Exception as e:
        print(f"❌ Error reloading model: {e}")
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reload model: {str(e)}"
        )


@app.post("/admin/reload-plugins", response_model=ReloadResponse, tags=["Admin"])
async def reload_plugins():
    """
    Reload plugins (tools).

    New sessions will use the updated plugins. Existing sessions continue with their original plugins.
    """
    try:
        hot_reload_mgr = get_hot_reload_manager()
        result = hot_reload_mgr.reload_plugins()

        return ReloadResponse(
            success=True,
            message="Plugins reloaded successfully",
            details=result,
        )
    except Exception as e:
        print(f"❌ Error reloading plugins: {e}")
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reload plugins: {str(e)}"
        )


@app.get("/admin/sessions", tags=["Admin"])
async def list_sessions():
    """List all active sessions."""
    return {
        "sessions": session_manager.list_sessions(),
        "total": len(session_manager.sessions),
    }


@app.delete("/sessions/{session_id}", tags=["Conversation"])
async def delete_session(session_id: str):
    """Delete a conversation session."""
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found"
        )

    session_manager.delete_session(session_id)
    return {"message": f"Session {session_id} deleted successfully"}


@app.post("/sessions/{session_id}/reset", tags=["Conversation"])
async def reset_session(session_id: str):
    """Reset a conversation session state."""
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found"
        )

    # Reset state
    session["state"] = {
        "messages": [],
        "intent": None,
        "parameters": {},
        "tool_result": None,
        "waiting_for_parameter": None,
        "completed": False,
    }

    return {"message": f"Session {session_id} reset successfully"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "smart_customer_service.api:app",
        host=Config.API_HOST,
        port=Config.API_PORT,
        reload=Config.API_RELOAD,
    )
