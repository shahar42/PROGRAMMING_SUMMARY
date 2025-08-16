#!/usr/bin/env python3
"""
Educational Binary Analysis Agent - FastAPI Server
=================================================

SURGICAL FIX APPLIED:
- Fixed core workflow failure by using simplified graph
- Replaced deprecated FastAPI event handlers with modern lifespan
- Added comprehensive error handling to prevent 500 errors
- Maintains all existing API interfaces and functionality

FastAPI server providing REST API for educational binary analysis
using LangGraph agent with MCP ecosystem integration.
"""

import logging
import os
import sys
import traceback
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Dict, List, Optional, Any

import uvicorn
from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Load environment variables
from dotenv import load_dotenv
CONFIG_DIR = Path(__file__).parent.parent / "config"
ENV_FILE = CONFIG_DIR / "config.env"
load_dotenv(ENV_FILE)
print("--- DEBUGGING API KEYS ---")
print(f"Loaded OPENAI_API_KEY: ...{os.getenv('OPENAI_API_KEY')[-4:] if os.getenv('OPENAI_API_KEY') else 'None'}")
print(f"Loaded GROK_API_KEY: ...{os.getenv('GROK_API_KEY')[-4:] if os.getenv('GROK_API_KEY') else 'None'}")
print("--------------------------")

# SURGICAL FIX: Use simplified graph instead of complex one
from agent.basic_graph import SimplifiedEducationalAgent as EducationalAgent
# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global agent instance
agent = None

# Request/Response Models
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    model_preference: Optional[str] = None
    temperature: Optional[float] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str
    status: str = "success"
    model_used: Optional[str] = None
    tools_used: List[str] = []
    thinking_steps: Optional[List[Dict]] = None

class StreamChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    model_preference: Optional[str] = None

class UploadResponse(BaseModel):
    filename: str
    file_id: str
    size: int
    status: str = "uploaded"
    analysis_available: bool = False

class BinaryAnalysisRequest(BaseModel):
    file_id: str
    analysis_type: str = "full"  # "got", "plt", "symbols", "full"
    detail_level: str = "intermediate"  # "beginner", "intermediate", "advanced"

class BinaryAnalysisResponse(BaseModel):
    file_id: str
    analysis_type: str
    result: str
    status: str = "completed"
    tools_used: List[str] = []

class HealthResponse(BaseModel):
    status: str
    version: str = "1.0.0"
    agent_status: str
    models_available: List[str] = []
    tools_count: int = 0

class ModelInfo(BaseModel):
    name: str
    status: str
    capabilities: List[str] = []

class SessionInfo(BaseModel):
    session_id: str
    messages_count: int
    created_at: str
    last_activity: str
    status: str = "active"

# SURGICAL FIX: Modern FastAPI lifespan handler
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Modern FastAPI lifespan handler to replace deprecated @app.on_event"""
    # Startup
    logger.info("🚀 Starting Educational Binary Analysis Agent")
    
    try:
        global agent
        agent = EducationalAgent(config_path="config/mcp_endpoints.yaml")
        logger.info("✅ Educational agent initialized successfully")
        logger.info(f"📊 Available tools: {len(agent.tools) if hasattr(agent, 'tools') else 0}")
        
        yield  # App runs here
        
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise
    finally:
        # Shutdown  
        logger.info("👋 Shutting down Educational Binary Analysis Agent")
        if agent and hasattr(agent, 'mcp_client') and agent.mcp_client:
            try:
                agent.mcp_client.cleanup()
                logger.info("✅ MCP client cleaned up")
            except Exception as e:
                logger.warning(f"⚠️ MCP cleanup warning: {e}")

# Create FastAPI app with modern lifespan
app = FastAPI(
    title="Educational Binary Analysis Agent",
    description="LangGraph agent for educational binary analysis and systems programming",
    version="1.0.0",
    lifespan=lifespan  # SURGICAL FIX: Use modern lifespan instead of @app.on_event
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# File storage for uploads
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# In-memory storage for sessions and files
sessions: Dict[str, Dict] = {}
uploaded_files: Dict[str, Dict] = {}

# === CORE ENDPOINTS ===

@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint with basic info"""
    return {
        "message": "Educational Binary Analysis Agent",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check endpoint"""
    try:
        if not agent:
            return HealthResponse(
                status="unhealthy",
                agent_status="not_initialized",
                models_available=[],
                tools_count=0
            )
        
        models_available = list(agent.models.keys()) if hasattr(agent, 'models') else []
        tools_count = len(agent.tools) if hasattr(agent, 'tools') else 0
        
        return HealthResponse(
            status="healthy",
            agent_status="ready",
            models_available=models_available,
            tools_count=tools_count
        )
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return HealthResponse(
            status="unhealthy", 
            agent_status="error",
            models_available=[],
            tools_count=0
        )

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Main chat endpoint with SURGICAL FIX applied
    
    FIXES:
    - Ensures agent never returns None
    - Comprehensive error handling and fallbacks
    - Proper state extraction from agent responses
    """
    try:
        logger.info(f"📨 Chat request: {request.message[:100]}...")
        
        if not agent:
            raise HTTPException(status_code=503, detail="Agent not initialized")
        
        # Generate session ID if not provided
        session_id = request.session_id or str(uuid.uuid4())
        
        # SURGICAL FIX: Use simplified agent with guaranteed non-None response
        result = agent.invoke(request.message, session_id)
        
        # SURGICAL FIX: Ensure result is never None
        if result is None:
            logger.error("❌ Agent returned None - creating fallback response")
            result = {
                "messages": [
                    {"role": "user", "content": request.message},
                    {"role": "assistant", "content": "I'm having trouble processing your request. Please try again."}
                ],
                "status": "error",
                "error": "Agent returned None"
            }
        
        # SURGICAL FIX: Extract response safely with multiple fallbacks
        messages = result.get("messages", [])
        response_content = "I received your message but couldn't generate a response. Please try again."
        
        if messages:
            last_message = messages[-1]
            if hasattr(last_message, 'content'):
                response_content = last_message.content
            elif isinstance(last_message, dict) and 'content' in last_message:
                response_content = last_message['content']
            elif isinstance(last_message, str):
                response_content = last_message
            else:
                response_content = str(last_message)
        
        # Update session tracking
        if session_id not in sessions:
            sessions[session_id] = {
                "created_at": str(uuid.uuid4()),
                "messages": [],
                "last_activity": str(uuid.uuid4())
            }
        
        sessions[session_id]["messages"].append({
            "user": request.message,
            "assistant": response_content
        })
        sessions[session_id]["last_activity"] = str(uuid.uuid4())
        
        return ChatResponse(
            response=response_content,
            session_id=session_id,
            status=result.get("status", "success"),
            model_used=result.get("current_model", "unknown"),
            tools_used=result.get("tools_used", [])
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat error: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        # SURGICAL FIX: Always return a valid response, never raise unhandled exceptions
        return ChatResponse(
            response=f"I encountered an error: {str(e)}. Please try again.",
            session_id=request.session_id or "error_session",
            status="error",
            model_used="none",
            tools_used=[]
        )

@app.post("/stream")
async def stream_chat(request: StreamChatRequest):
    """Streaming chat endpoint"""
    try:
        if not agent:
            raise HTTPException(status_code=503, detail="Agent not initialized")
        
        session_id = request.session_id or str(uuid.uuid4())
        
        async def generate():
            try:
                for event in agent.stream(request.message, session_id):
                    yield f"data: {event}\n\n"
            except Exception as e:
                logger.error(f"Streaming error: {e}")
                yield f"data: {{'error': '{str(e)}'}}\n\n"
        
        from fastapi.responses import StreamingResponse
        return StreamingResponse(generate(), media_type="text/plain")
        
    except Exception as e:
        logger.error(f"Stream setup error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# === BINARY ANALYSIS ENDPOINTS ===

@app.post("/upload", response_model=UploadResponse)
async def upload_binary(file: UploadFile = File(...)):
    """Upload binary file for analysis"""
    try:
        file_id = str(uuid.uuid4())
        file_path = UPLOAD_DIR / f"{file_id}_{file.filename}"
        
        # Save file
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
        
        # Store file info
        uploaded_files[file_id] = {
            "filename": file.filename,
            "path": str(file_path),
            "size": len(content),
            "content_type": file.content_type,
            "uploaded_at": str(uuid.uuid4())
        }
        
        logger.info(f"📁 Uploaded file: {file.filename} ({len(content)} bytes)")
        
        return UploadResponse(
            filename=file.filename,
            file_id=file_id,
            size=len(content),
            analysis_available=True
        )
        
    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze", response_model=BinaryAnalysisResponse)
async def analyze_binary(request: BinaryAnalysisRequest):
    """Analyze uploaded binary file"""
    try:
        if not agent:
            raise HTTPException(status_code=503, detail="Agent not initialized")
        
        if request.file_id not in uploaded_files:
            raise HTTPException(status_code=404, detail="File not found")
        
        file_info = uploaded_files[request.file_id]
        file_path = file_info["path"]
        
        # Create analysis prompt based on request
        analysis_prompts = {
            "got": f"Please analyze the Global Offset Table (GOT) in the binary file at {file_path}. Detail level: {request.detail_level}",
            "plt": f"Please analyze the Procedure Linkage Table (PLT) in the binary file at {file_path}. Detail level: {request.detail_level}",
            "symbols": f"Please list and analyze the dynamic symbols in the binary file at {file_path}. Detail level: {request.detail_level}",
            "full": f"Please perform a comprehensive analysis of the binary file at {file_path}, including GOT, PLT, and symbols. Detail level: {request.detail_level}"
        }
        
        prompt = analysis_prompts.get(request.analysis_type, analysis_prompts["full"])
        
        # Use agent to analyze
        result = agent.invoke(prompt, f"analysis_{request.file_id}")
        
        if result is None:
            raise HTTPException(status_code=500, detail="Analysis failed")
        
        # Extract result
        messages = result.get("messages", [])
        analysis_result = "Analysis completed but no detailed results available."
        
        if messages:
            last_message = messages[-1]
            if hasattr(last_message, 'content'):
                analysis_result = last_message.content
        
        return BinaryAnalysisResponse(
            file_id=request.file_id,
            analysis_type=request.analysis_type,
            result=analysis_result,
            tools_used=result.get("tools_used", [])
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# === MANAGEMENT ENDPOINTS ===

@app.get("/models", response_model=List[ModelInfo])
async def get_models():
    """Get available models and their status"""
    try:
        if not agent or not hasattr(agent, 'models'):
            return []
        
        models_info = []
        for name, model in agent.models.items():
            models_info.append(ModelInfo(
                name=name,
                status="available",
                capabilities=["chat", "analysis", "education"]
            ))
        
        return models_info
        
    except Exception as e:
        logger.error(f"Models endpoint error: {e}")
        return []

@app.get("/tools", response_model=Dict[str, Any])
async def get_tools():
    """Get available tools information"""
    try:
        if not agent or not hasattr(agent, 'tools'):
            return {"tools": [], "count": 0}
        
        tools_info = []
        for tool in agent.tools:
            tools_info.append({
                "name": getattr(tool, 'name', 'unknown'),
                "description": getattr(tool, 'description', 'No description'),
                "category": "mcp_tool"
            })
        
        return {
            "tools": tools_info,
            "count": len(tools_info),
            "categories": ["binary_analysis", "educational", "orchestration"]
        }
        
    except Exception as e:
        logger.error(f"Tools endpoint error: {e}")
        return {"tools": [], "count": 0}

@app.get("/sessions", response_model=List[SessionInfo])
async def get_sessions():
    """Get active sessions"""
    try:
        sessions_info = []
        for session_id, session_data in sessions.items():
            sessions_info.append(SessionInfo(
                session_id=session_id,
                messages_count=len(session_data.get("messages", [])),
                created_at=session_data.get("created_at", "unknown"),
                last_activity=session_data.get("last_activity", "unknown")
            ))
        
        return sessions_info
        
    except Exception as e:
        logger.error(f"Sessions endpoint error: {e}")
        return []

@app.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """Delete a session"""
    if session_id in sessions:
        del sessions[session_id]
        return {"message": f"Session {session_id} deleted"}
    else:
        raise HTTPException(status_code=404, detail="Session not found")

@app.get("/files", response_model=List[Dict[str, Any]])
async def get_uploaded_files():
    """Get list of uploaded files"""
    try:
        files_info = []
        for file_id, file_data in uploaded_files.items():
            files_info.append({
                "file_id": file_id,
                "filename": file_data["filename"],
                "size": file_data["size"],
                "uploaded_at": file_data["uploaded_at"]
            })
        
        return files_info
        
    except Exception as e:
        logger.error(f"Files endpoint error: {e}")
        return []

@app.delete("/files/{file_id}")
async def delete_file(file_id: str):
    """Delete an uploaded file"""
    try:
        if file_id not in uploaded_files:
            raise HTTPException(status_code=404, detail="File not found")
        
        file_info = uploaded_files[file_id]
        file_path = Path(file_info["path"])
        
        # Delete physical file
        if file_path.exists():
            file_path.unlink()
        
        # Remove from storage
        del uploaded_files[file_id]
        
        return {"message": f"File {file_id} deleted"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"File deletion error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# === EDUCATIONAL ENDPOINTS ===

@app.get("/concepts")
async def get_concepts(topic: Optional[str] = None):
    """Get educational concepts"""
    try:
        if not agent:
            raise HTTPException(status_code=503, detail="Agent not initialized")
        
        if topic:
            prompt = f"List and explain educational concepts related to {topic} in binary analysis and systems programming."
        else:
            prompt = "List the main educational concepts in binary analysis and systems programming."
        
        result = agent.invoke(prompt, "concepts_session")
        
        if result and result.get("messages"):
            last_message = result["messages"][-1]
            content = getattr(last_message, 'content', str(last_message))
            return {"concepts": content}
        
        return {"concepts": "No concepts available"}
        
    except Exception as e:
        logger.error(f"Concepts endpoint error: {e}")
        return {"concepts": f"Error retrieving concepts: {str(e)}"}

@app.get("/learning-paths")
async def get_learning_paths():
    """Get available learning paths"""
    return {
        "paths": [
            {
                "id": "binary_basics",
                "name": "Binary Analysis Basics",
                "description": "Introduction to binary file formats and analysis",
                "difficulty": "beginner"
            },
            {
                "id": "got_plt_deep_dive",
                "name": "GOT/PLT Deep Dive",
                "description": "Understanding dynamic linking and symbol resolution",
                "difficulty": "intermediate"
            },
            {
                "id": "advanced_analysis",
                "name": "Advanced Binary Analysis",
                "description": "Complex binary analysis techniques and tools",
                "difficulty": "advanced"
            }
        ]
    }

# === MAIN ENTRY POINT ===

if __name__ == "__main__":
    logger.info("🔧 Starting development server")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8200,
        reload=True,
        log_level="info"
    )
