"""
FastAPI main application with RESTful and WebSocket endpoints.
"""
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import uuid
import time
from datetime import datetime
from typing import Dict

from app.config import settings
from app.models import (
    ChatMessageRequest, ChatMessageResponse, SessionResponse,
    ErrorResponse, HealthResponse, CreateSessionRequest,
    LoanApplicationResponse, RAGQueryRequest, RAGQueryResponse
)
from app.utils.logger import logger

# Import core modules (will create these)
from app.core.session import SessionManager
from app.core.agent import LoanSalesAgent
from app.core.rag import RAGSystem

# Global instances
session_manager: SessionManager = None
agent: LoanSalesAgent = None
rag_system: RAGSystem = None

# Metrics
app_start_time = time.time()
metrics = {
    "total_sessions": 0,
    "active_sessions": 0,
    "total_messages": 0,
    "total_response_time": 0.0,
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager for startup and shutdown.
    """
    # Startup
    global session_manager, agent, rag_system
    
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    
    try:
        # Initialize RAG system
        logger.info("Initializing RAG system...")
        rag_system = RAGSystem()
        await rag_system.initialize()
        
        # Initialize session manager
        logger.info("Initializing session manager...")
        session_manager = SessionManager()
        
        # Initialize agent
        logger.info("Initializing LoanSales agent...")
        agent = LoanSalesAgent(rag_system)
        agent.set_session_manager(session_manager)
        
        logger.info("Application startup complete")
        
    except Exception as e:
        logger.error(f"Failed to initialize application: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down application...")
    if rag_system:
        await rag_system.cleanup()
    logger.info("Shutdown complete")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-powered loan sales assistant with conversational interface",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=exc.detail,
            detail=str(exc)
        ).dict()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal server error",
            detail=str(exc) if settings.DEBUG else None
        ).dict()
    )


# Health check endpoints
@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """
    Health check endpoint for monitoring.
    """
    return HealthResponse(
        status="healthy",
        version=settings.APP_VERSION,
        environment=settings.ENVIRONMENT
    )


@app.get("/ready", response_model=HealthResponse, tags=["Health"])
async def readiness_check():
    """
    Readiness check - verifies all services are initialized.
    """
    if not all([session_manager, agent, rag_system]):
        raise HTTPException(status_code=503, detail="Service not ready")
    
    return HealthResponse(
        status="ready",
        version=settings.APP_VERSION,
        environment=settings.ENVIRONMENT
    )


@app.get("/metrics", tags=["Health"])
async def get_metrics():
    """
    Get application metrics.
    """
    uptime = time.time() - app_start_time
    avg_response_time = (
        metrics["total_response_time"] / metrics["total_messages"]
        if metrics["total_messages"] > 0
        else 0.0
    )
    
    return {
        "total_sessions": metrics["total_sessions"],
        "active_sessions": metrics["active_sessions"],
        "total_messages": metrics["total_messages"],
        "avg_response_time_ms": avg_response_time * 1000,
        "uptime_seconds": uptime,
    }


# Session management endpoints
@app.post("/api/v1/sessions", response_model=SessionResponse, tags=["Sessions"])
async def create_session(request: CreateSessionRequest = None):
    """
    Create a new chat session.
    """
    try:
        session_id = str(uuid.uuid4())
        session_manager.create_session(session_id)
        
        # Get initial greeting
        greeting = agent.get_initial_greeting()
        
        metrics["total_sessions"] += 1
        metrics["active_sessions"] += 1
        
        logger.info(f"Created new session: {session_id}")
        
        return SessionResponse(
            session_id=session_id,
            greeting_message=greeting
        )
    except Exception as e:
        logger.error(f"Failed to create session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/sessions/{session_id}", tags=["Sessions"])
async def get_session(session_id: str):
    """
    Get session details and conversation history.
    """
    try:
        session = session_manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return {
            "session_id": session_id,
            "loan_application": session.get("loan_application"),
            "message_count": len(session.get("messages", []))
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/v1/sessions/{session_id}", tags=["Sessions"])
async def delete_session(session_id: str):
    """
    Delete a session and its associated data.
    """
    try:
        session_manager.delete_session(session_id)
        metrics["active_sessions"] = max(0, metrics["active_sessions"] - 1)
        logger.info(f"Deleted session: {session_id}")
        return {"message": "Session deleted successfully"}
    except Exception as e:
        logger.error(f"Failed to delete session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Chat endpoints
@app.post("/api/v1/chat", response_model=ChatMessageResponse, tags=["Chat"])
async def send_message(request: ChatMessageRequest):
    """
    Send a message and get AI response (synchronous).
    """
    start_time = time.time()
    
    try:
        # Create session if not provided
        if not request.session_id:
            session_id = str(uuid.uuid4())
            session_manager.create_session(session_id)
            metrics["total_sessions"] += 1
            metrics["active_sessions"] += 1
        else:
            session_id = request.session_id
            # Verify session exists
            if not session_manager.get_session(session_id):
                raise HTTPException(status_code=404, detail="Session not found")
        
        # Process message through agent
        result = await agent.process_message(session_id, request.message)
        
        # Update metrics
        metrics["total_messages"] += 1
        response_time = time.time() - start_time
        metrics["total_response_time"] += response_time
        
        logger.info(f"Processed message for session {session_id} in {response_time:.2f}s")
        
        return ChatMessageResponse(
            session_id=session_id,
            message=result["message"],
            loan_application=LoanApplicationResponse(**result["loan_application"])
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to process message: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# WebSocket endpoint for streaming responses
@app.websocket("/api/v1/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for real-time streaming chat.
    """
    await websocket.accept()
    logger.info(f"WebSocket connection established for session: {session_id}")
    
    try:
        # Verify or create session
        if not session_manager.get_session(session_id):
            session_manager.create_session(session_id)
            metrics["total_sessions"] += 1
            metrics["active_sessions"] += 1
            
            # Send greeting
            greeting = agent.get_initial_greeting()
            await websocket.send_json({
                "type": "message",
                "content": greeting,
                "session_id": session_id
            })
        
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            message = data.get("message", "")
            
            if not message.strip():
                continue
            
            # Process and stream response
            async for chunk in agent.stream_response(session_id, message):
                await websocket.send_json(chunk)
                
            metrics["total_messages"] += 1
            
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for session: {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
        try:
            await websocket.send_json({
                "type": "error",
                "content": str(e)
            })
        except:
            pass
    finally:
        try:
            await websocket.close()
        except:
            pass


# RAG query endpoint
@app.post("/api/v1/rag/query", response_model=RAGQueryResponse, tags=["RAG"])
async def query_knowledge_base(request: RAGQueryRequest):
    """
    Query the loan products knowledge base directly.
    """
    try:
        results = await rag_system.query(request.query, top_k=request.top_k)
        
        return RAGQueryResponse(
            query=request.query,
            results=results.get("documents", []),
            sources=results.get("sources", [])
        )
    except Exception as e:
        logger.error(f"RAG query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint with API information.
    """
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "docs": "/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )

