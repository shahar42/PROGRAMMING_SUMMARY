#!/usr/bin/env python3
"""
Educational Binary Analysis Agent - Main Server
FastAPI server that ties together LangGraph agent with MCP ecosystem
"""

import os
import uuid
import logging
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from dotenv import load_dotenv

import uvicorn
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel

# Load environment from existing config
CONFIG_DIR = Path(__file__).parent.parent / "config"
ENV_FILE = CONFIG_DIR / "config.env"
load_dotenv(ENV_FILE)

# Import our components
from agent.graph import EducationalAgent
from mcp_integration.client import MCPClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Educational Binary Analysis Agent",
    description="LangGraph agent for educational systems programming and binary analysis",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global agent instance
educational_agent: Optional[EducationalAgent] = None
config_path = Path(__file__).parent / "config" / "mcp_endpoints.yaml"

# Request/Response models
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    explanation_level: str = "intermediate"  # beginner, intermediate, advanced
    learning_goal: Optional[str] = None
    binary_path: Optional[str] = None
    preferred_model: Optional[str] = None  # gemini, grok, chatgpt

class ChatResponse(BaseModel):
    response: str
    session_id: str
    success: bool
    analysis_phase: str
    learned_concepts: List[str]
    suggested_next_steps: List[str]
    model_used: Optional[str] = None
    error: Optional[str] = None

class StatusResponse(BaseModel):
    status: str
    active_sessions: int
    available_tools: int
    mcp_servers: Dict[str, str]
    uptime: str

class BinaryAnalysisRequest(BaseModel):
    binary_path: str
    analysis_type: str = "full"  # static, validation, runtime, full
    explanation_level: str = "intermediate"

# Session management
active_sessions: Dict[str, Dict] = {}
start_time = datetime.now()

@app.on_event("startup")
async def startup_event():
    """Initialize the educational agent on startup"""
    global educational_agent
    
    try:
        logger.info("🚀 Starting Educational Binary Analysis Agent")
        
        # Check config file exists
        if not config_path.exists():
            logger.error(f"Config file not found: {config_path}")
            raise FileNotFoundError(f"Configuration file missing: {config_path}")
        
        # Initialize the agent
        educational_agent = EducationalAgent(str(config_path))
        
        logger.info("✅ Educational agent initialized successfully")
        logger.info(f"📊 Available tools: {len(educational_agent.mcp_client.get_all_tools())}")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize agent: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("🛑 Shutting down Educational Binary Analysis Agent")
    # Cleanup active sessions, close database connections, etc.
    active_sessions.clear()

@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint with basic info"""
    return {
        "service": "Educational Binary Analysis Agent",
        "version": "1.0.0",
        "status": "running",
        "description": "LangGraph agent for educational systems programming and binary analysis"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    if educational_agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/status", response_model=StatusResponse)
async def get_status():
    """Get detailed system status"""
    if educational_agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    # Get MCP server status
    try:
        orchestrator_status = educational_agent.mcp_client.available_tools.get("orchestrator_get_orchestrator_status")
        if orchestrator_status:
            mcp_status = orchestrator_status._run()
        else:
            mcp_status = "orchestrator_unavailable"
    except Exception as e:
        mcp_status = f"error: {str(e)}"
    
    uptime = datetime.now() - start_time
    
    return StatusResponse(
        status="running",
        active_sessions=len(active_sessions),
        available_tools=len(educational_agent.mcp_client.get_all_tools()),
        mcp_servers={
            "orchestrator": "port 8100",
            "got_plt": "port 8108", 
            "book_servers": "8101-8107"
        },
        uptime=str(uptime)
    )

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Main chat endpoint for educational interactions"""
    if educational_agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        # Generate session ID if not provided
        session_id = request.session_id or str(uuid.uuid4())
        
        # Track session
        if session_id not in active_sessions:
            active_sessions[session_id] = {
                "created": datetime.now(),
                "messages": 0,
                "learning_progress": {}
            }
        
        active_sessions[session_id]["messages"] += 1
        
        # Invoke the educational agent
        result = educational_agent.invoke(
            user_input=request.message,
            session_id=session_id
        )
        
        if result["success"]:
            # Extract educational metadata from state with better error handling
            state = result.get("state", {})
            if state and isinstance(state, dict):
                # Get the last state from workflow
                state_values = list(state.values())
                final_state = state_values[-1] if state_values else {}
            else:
                final_state = {}
            
            response = ChatResponse(
                response=result["response"],
                session_id=session_id,
                success=True,
                analysis_phase=final_state.get("analysis_phase", "static"),
                learned_concepts=final_state.get("learned_concepts", []),
                suggested_next_steps=_generate_next_steps(final_state),
                model_used=final_state.get("selected_model", "unknown")
            )
        else:
            response = ChatResponse(
                response="I encountered an error processing your request. Please try again.",
                session_id=session_id,
                success=False,
                analysis_phase="error",
                learned_concepts=[],
                suggested_next_steps=["Try rephrasing your question", "Check if binary path is valid"],
                error=result.get("error")
            )
        
        return response
        
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=f"Chat processing failed: {str(e)}")

@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """Streaming chat endpoint for real-time responses"""
    if educational_agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    async def generate_stream():
        try:
            session_id = request.session_id or str(uuid.uuid4())
            
            # Stream the agent's workflow
            config = {"configurable": {"thread_id": session_id}}
            
            initial_state = {
                "messages": [{"role": "user", "content": request.message}],
                "explanation_level": request.explanation_level,
                "learning_goal": request.learning_goal,
                "current_binary": request.binary_path
            }
            
            yield f"data: {{'session_id': '{session_id}', 'status': 'started'}}\n\n"
            
            for event in educational_agent.app.stream(initial_state, config=config):
                # Stream workflow progress
                event_data = {
                    "event": list(event.keys())[0] if event else "unknown",
                    "status": "processing"
                }
                yield f"data: {event_data}\n\n"
            
            yield f"data: {{'status': 'completed'}}\n\n"
            
        except Exception as e:
            yield f"data: {{'error': '{str(e)}'}}\n\n"
    
    return StreamingResponse(generate_stream(), media_type="text/plain")

@app.post("/binary/upload")
async def upload_binary(
    file: UploadFile = File(...),
    analysis_type: str = Form("static"),
    explanation_level: str = Form("intermediate")
):
    """Upload binary for analysis"""
    
    if not file.filename.endswith(('.bin', '.elf', '.exe', '.so', '.out', '')):
        # Allow files without extension (common for Linux binaries)
        pass
    
    try:
        # Save uploaded file
        upload_dir = Path("uploads")
        upload_dir.mkdir(exist_ok=True)
        
        file_path = upload_dir / f"{uuid.uuid4()}_{file.filename}"
        
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Make executable (for ELF files)
        os.chmod(file_path, 0o755)
        
        logger.info(f"📁 Binary uploaded: {file_path}")
        
        return {
            "success": True,
            "file_path": str(file_path),
            "message": f"Binary uploaded successfully. Use path '{file_path}' in chat for analysis.",
            "suggested_commands": [
                f"Analyze the GOT table in {file_path}",
                f"Explain the PLT stubs in {file_path}",
                f"Show me the dynamic symbols in {file_path}"
            ]
        }
        
    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.post("/binary/analyze")
async def analyze_binary(request: BinaryAnalysisRequest):
    """Direct binary analysis endpoint"""
    if educational_agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        # Check if binary exists
        binary_path = Path(request.binary_path)
        if not binary_path.exists():
            raise HTTPException(status_code=404, detail="Binary file not found")
        
        # Create analysis prompt based on type
        analysis_prompts = {
            "static": f"Perform static analysis of the binary {request.binary_path}. Show me the GOT and PLT structure.",
            "validation": f"Validate linking concepts using the binary {request.binary_path}. Compare theory with practice.",
            "runtime": f"Perform runtime analysis of {request.binary_path}. Trace symbol resolution and lazy binding.",
            "full": f"Perform comprehensive analysis of {request.binary_path} covering static, validation, and runtime phases."
        }
        
        prompt = analysis_prompts.get(request.analysis_type, analysis_prompts["static"])
        
        # Create chat request
        chat_request = ChatRequest(
            message=prompt,
            explanation_level=request.explanation_level,
            binary_path=request.binary_path
        )
        
        # Use the chat endpoint
        return await chat(chat_request)
        
    except Exception as e:
        logger.error(f"Binary analysis error: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.get("/sessions")
async def list_sessions():
    """List active sessions"""
    sessions = []
    for session_id, data in active_sessions.items():
        sessions.append({
            "session_id": session_id,
            "created": data["created"].isoformat(),
            "messages": data["messages"],
            "active": True
        })
    
    return {"sessions": sessions, "total": len(sessions)}

@app.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """Delete a specific session"""
    if session_id in active_sessions:
        del active_sessions[session_id]
        return {"success": True, "message": f"Session {session_id} deleted"}
    else:
        raise HTTPException(status_code=404, detail="Session not found")

@app.get("/models")
async def list_available_models():
    """List all available AI models"""
    if educational_agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    models = []
    for model_name in educational_agent.model_manager.get_available_models():
        model_config = educational_agent.config.get("models", {}).get(model_name, {})
        models.append({
            "name": model_name,
            "provider": model_config.get("provider", "unknown"),
            "model_id": model_config.get("model_name", "unknown"),
            "use_for": model_config.get("use_for", []),
            "is_default": model_name == educational_agent.model_manager.default_model
        })
    
    return {
        "models": models,
        "total": len(models),
        "default_model": educational_agent.model_manager.default_model
    }

@app.get("/tools")
async def list_available_tools():
    """List all available MCP tools"""
    if educational_agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    tools = []
    for tool in educational_agent.mcp_client.get_all_tools():
        tools.append({
            "name": tool.name,
            "description": tool.description,
            "category": _categorize_tool(tool.name)
        })
    
    return {"tools": tools, "total": len(tools)}

def _generate_next_steps(state: Dict[str, Any]) -> List[str]:
    """Generate suggested next steps based on current state"""
    
    phase = state.get("analysis_phase", "static")
    current_binary = state.get("current_binary")
    
    if phase == "static" and current_binary:
        return [
            "Validate concepts against theory",
            "Move to runtime analysis",
            "Generate interactive examples"
        ]
    elif phase == "validation":
        return [
            "Proceed to runtime tracing",
            "Create practical examples",
            "Compare with other binaries"
        ]
    elif phase == "runtime":
        return [
            "Synthesize learnings",
            "Generate comprehensive report",
            "Try with different binary"
        ]
    else:
        return [
            "Upload a binary for analysis",
            "Ask about specific concepts", 
            "Request explanation at different level"
        ]

def _categorize_tool(tool_name: str) -> str:
    """Categorize tools for better organization"""
    if "orchestrator_" in tool_name:
        return "orchestration"
    elif "gotplt_" in tool_name:
        return "binary_analysis"
    elif "topic_" in tool_name:
        return "routing"
    elif "book_" in tool_name:
        return "concepts"
    else:
        return "general"

if __name__ == "__main__":
    # Development server
    logger.info("🔧 Starting development server")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8200,
        reload=True,
        log_level="info"
    )
