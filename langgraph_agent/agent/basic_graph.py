#!/usr/bin/env python3
"""
Simplified Educational Agent Graph - SURGICAL FIX
=====================================================

This is a simplified version of agent/graph.py that bypasses the complex 
educational routing logic and implements a basic agent → tools → end workflow.

ROOT CAUSE FIX: Complex educational routing logic causing workflow to return None
SOLUTION: Simple, reliable agent-tools-end pattern

PRESERVES:
- All existing API naming and interfaces  
- EducationalAgentState compatibility
- Multi-model support (grok, chatgpt)
- All 23 MCP tools integration
- Backward compatibility with main.py

RESTORES:
- Basic chat functionality immediately
- Proper state handling and returns
- Tool calling capabilities
- Error handling
"""

import logging
import os
from typing import Dict, List, Optional, Literal, Any
from pathlib import Path

# LangGraph imports
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import ToolNode

# LangChain imports  
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq

# Local imports
from agent.state import EducationalAgentState, create_initial_state

from mcp_integration.client import MCPClient

logger = logging.getLogger(__name__)

class SimplifiedEducationalAgent:
    """
    Simplified Educational Agent with basic agent → tools → end workflow
    
    DESIGN PRINCIPLES:
    - Start with basic functionality that works
    - Add complexity gradually after basic flow works  
    - Explicit state handling and error recovery
    - Simple conditional routing without over-engineering
    """
    
    def __init__(self, config_path: str = "config/mcp_endpoints.yaml"):
        self.config_path = config_path
        self.models = {}
        self.tools = []
        self.mcp_client = None
        self.graph = None
        self.app = None
        
        # Initialize components
        self._setup_models()
        self._setup_tools()
        self._build_graph()
        
        logger.info(f"✅ Simplified Educational agent initialized with {len(self.tools)} tools")
        logger.info(f"🤖 Available models: {list(self.models.keys())}")
    
    def _setup_models(self):
        """Initialize available models with fallback handling"""
        try:
            # Grok model setup
            grok_api_key = os.getenv("GROK_API_KEY")
            if grok_api_key:
                self.models["grok"] = ChatGroq(
                    model="llama-3.1-8b-instant",
                    api_key=grok_api_key,
                    temperature=0.3
                )
                logger.info("✅ Initialized grok model")
            else:
                logger.warning("⚠️ Grok API key not found")
                
        except Exception as e:
            logger.error(f"❌ Failed to initialize grok: {e}")
        
        try:
            # ChatGPT model setup
            openai_api_key = os.getenv("OPENAI_API_KEY")
            if openai_api_key:
                self.models["chatgpt"] = ChatOpenAI(
                    model="gpt-4o-mini",
                    api_key=openai_api_key,
                    temperature=0.3
                )
                logger.info("✅ Initialized chatgpt model")
            else:
                logger.warning("⚠️ OpenAI API key not found")
                
        except Exception as e:
            logger.error(f"❌ Failed to initialize chatgpt: {e}")
        
        # Ensure we have at least one working model
        if not self.models:
            raise RuntimeError("❌ No working models available. Check API keys.")
    
    def _setup_tools(self):
        """Initialize MCP tools"""
        try:
            self.mcp_client = MCPClient(self.config_path)
            
            self.tools = self.mcp_client.get_all_tools()
            logger.info(f"✅ Loaded {len(self.tools)} MCP tools")
            
        except Exception as e:
            logger.error(f"❌ Failed to setup MCP tools: {e}")
            self.tools = []  # Continue without tools if needed
    
    def _select_model(self, state: EducationalAgentState):
        """
        Simple model selection with fallback
        
        SIMPLIFIED LOGIC:
        - Use grok for technical/reasoning tasks
        - Use chatgpt for quick tasks and fallback
        - Always have a working fallback
        """
        # Get the current message content for context
        messages = state.get("messages", [])
        if messages:
            last_message = messages[-1].content.lower() if hasattr(messages[-1], 'content') else ""
            
            # Simple keyword-based routing
            technical_keywords = ["binary", "assembly", "got", "plt", "analyze", "technical", "explain"]
            if any(keyword in last_message for keyword in technical_keywords) and "grok" in self.models:
                return self.models["grok"]
        
        # Default fallback chain
        if "chatgpt" in self.models:
            return self.models["chatgpt"]
        elif "grok" in self.models:
            return self.models["grok"]
        else:
            raise RuntimeError("No available models")
    
    def _agent_node(self, state: EducationalAgentState) -> Dict[str, Any]:
        """
        Core agent node - simplified and reliable
        
        SURGICAL FIX: This replaces the complex educational routing
        with a simple, working agent that can call tools
        """
        try:
            # Select appropriate model
            model = self._select_model(state)
            
            # Bind tools to model if available
            if self.tools:
                model_with_tools = model.bind_tools(self.tools)
            else:
                model_with_tools = model
            
            # Get messages from state
            messages = state.get("messages", [])
            
            # Add system message for educational context
            system_message = SystemMessage(content="""
You are an educational programming concepts assistant with access to knowledge from 6 classic computer science books:
- K&R C Programming Language (kernighan_ritchie)
- UNIX Environment Programming (unix_env)
- Linkers & Loaders (linkers_loaders)
- Operating Systems: Three Easy Pieces (os_three_pieces)
- Expert C Programming (expert_c_programming)
- Computer Systems: A Programmer's Perspective (csapp_2016)
- POSIX System Calls (posix_manpages)

When users ask about programming concepts, system calls, algorithms, pointers, memory management, or technical topics:
1. Use analyze_and_route_question to determine which books are most relevant
2. Search appropriate book concepts using search_* tools (e.g., search_kernighan_ritchie, search_unix_env)
3. Get detailed explanations using get_details_* tools for specific concept IDs
4. Provide clear, educational explanations adapted to the user's level

Always prioritize using your knowledge base tools to provide accurate, book-backed information rather than generating responses without context.
Focus on educational explanations that help users understand underlying concepts and principles.
""")
            
            # Prepare messages for model
            model_messages = [system_message] + messages
            
            # Get response from model
            response = model_with_tools.invoke(model_messages)
            
            # Update state with new message
            updated_messages = messages + [response]
            
            # Simple state update
            return {
                "messages": updated_messages,
                "status": "active",
                "current_model": model.model_name if hasattr(model, 'model_name') else "unknown"
            }
            
        except Exception as e:
            logger.error(f"❌ Agent node error: {e}")
            
            # Error recovery - return error message
            error_message = AIMessage(content=f"I encountered an error: {str(e)}. Please try again.")
            return {
                "messages": state.get("messages", []) + [error_message],
                "status": "error",
                "error": str(e)
            }
    
    def _router(self, state: EducationalAgentState) -> Literal["tools", "end"]:
        """
        Simple router - only checks if tools need to be called
        
        SURGICAL FIX: This replaces complex conditional routing with simple logic
        """
        try:
            messages = state.get("messages", [])
            if not messages:
                return "end"
            
            last_message = messages[-1]
            
            # Check if the last message has tool calls
            if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
                return "tools"
            
            return "end"
            
        except Exception as e:
            logger.error(f"❌ Router error: {e}")
            return "end"  # Always end on error to prevent loops
    
    def _build_graph(self):
        """
        Build the simplified graph: agent → tools → end
        
        SURGICAL FIX: This replaces the complex educational workflow
        with a proven, simple pattern
        """
        try:
            # Create tool node if we have tools
            if self.tools:
                tool_node = ToolNode(self.tools)
            else:
                # Create a dummy tool node that does nothing
                def dummy_tool_node(state):
                    return {"messages": state.get("messages", [])}
                tool_node = dummy_tool_node
            
            # Build the graph
            workflow = StateGraph(EducationalAgentState)
            
            # Add nodes
            workflow.add_node("agent", self._agent_node)
            workflow.add_node("tools", tool_node)
            
            # Set entry point
            workflow.set_entry_point("agent")
            
            # Add edges
            workflow.add_conditional_edges(
                "agent",
                self._router,
                {
                    "tools": "tools",
                    "end": END
                }
            )
            
            # Tools always go back to agent for follow-up
            workflow.add_edge("tools", "agent")
            
            # Compile with memory
            memory = MemorySaver()
            self.app = workflow.compile(checkpointer=memory)
            
            logger.info("✅ Simplified graph compiled successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to build graph: {e}")
            raise
    
    def invoke(self, message: str, session_id: str = "default") -> Dict[str, Any]:
        """
        Invoke the agent with a message
        
        SURGICAL FIX: This ensures the graph always returns a valid result
        """
        try:
            # Create initial state
            initial_state = create_initial_state()
            initial_state["messages"] = [HumanMessage(content=message)]
            
            # Configure session
            config = {"configurable": {"thread_id": session_id}}
            
            # Invoke the graph
            result = self.app.invoke(initial_state, config=config)
            
            # Ensure we always return a valid result
            if result is None:
                logger.error("❌ Graph returned None - creating fallback response")
                fallback_message = AIMessage(content="I'm having trouble processing your request. Please try again.")
                result = {
                    "messages": initial_state["messages"] + [fallback_message],
                    "status": "error",
                    "error": "Graph returned None"
                }
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Invoke error: {e}")
            
            # Always return a valid response, never None
            fallback_message = AIMessage(content=f"I encountered an error: {str(e)}. Please try again.")
            return {
                "messages": [HumanMessage(content=message), fallback_message],
                "status": "error", 
                "error": str(e)
            }
    
    def stream(self, message: str, session_id: str = "default"):
        """Stream responses from the agent"""
        try:
            initial_state = create_initial_state()
            initial_state["messages"] = [HumanMessage(content=message)]
            
            config = {"configurable": {"thread_id": session_id}}
            
            for event in self.app.stream(initial_state, config=config):
                yield event
                
        except Exception as e:
            logger.error(f"❌ Stream error: {e}")
            yield {"error": str(e)}

# Factory function for backward compatibility
def create_educational_agent(config_path: str = "config/mcp_endpoints.yaml") -> SimplifiedEducationalAgent:
    """
    Factory function to create the simplified educational agent
    
    MAINTAINS: Backward compatibility with existing main.py code
    """
    return SimplifiedEducationalAgent(config_path)

# Alias for existing code compatibility
EducationalAgent = SimplifiedEducationalAgent
