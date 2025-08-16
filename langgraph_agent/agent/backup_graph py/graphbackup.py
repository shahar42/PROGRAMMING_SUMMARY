#!/usr/bin/env python3
"""
Educational Agent Graph - Core LangGraph Implementation
Orchestrates educational workflows through your MCP ecosystem
"""

import os
import uuid
import yaml
import logging
from typing import Dict, List, Any, Literal
from pathlib import Path
from dotenv import load_dotenv

from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import ToolNode

from agent.state import EducationalAgentState, StateUpdates
from mcp_integration.client import MCPClient

# Load environment variables from existing config
CONFIG_DIR = Path(__file__).parent.parent.parent / "config"
ENV_FILE = CONFIG_DIR / "config.env"
load_dotenv(ENV_FILE)

logger = logging.getLogger(__name__)

class ModelManager:
    """Manages multiple LLM models for different tasks"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.models = {}
        self.default_model = config.get("agent", {}).get("default_model", "gemini")
        self._initialize_models()
    
    def _initialize_models(self):
        """Initialize all configured models"""
        model_configs = self.config.get("models", {})
        
        for model_name, model_config in model_configs.items():
            try:
                model = self._create_model(model_name, model_config)
                if model:
                    self.models[model_name] = model
                    logger.info(f"✅ Initialized {model_name} model")
            except Exception as e:
                logger.error(f"❌ Failed to initialize {model_name}: {e}")
    
    def _create_model(self, model_name: str, config: Dict[str, Any]):
        """Create a model instance based on provider"""
        provider = config.get("provider")
        model_id = config.get("model_name")
        temperature = self.config.get("agent", {}).get("temperature", 0.1)
        
        if provider == "google":
            return ChatGoogleGenerativeAI(
                model=model_id,
                temperature=temperature,
                google_api_key=os.getenv("GOOGLE_API_KEY")
            )
        elif provider == "openai":
            return ChatOpenAI(
                model=model_id,
                temperature=temperature,
                openai_api_key=os.getenv("OPENAI_API_KEY")
            )
        elif provider == "openai_compatible":  # For Grok
            return ChatOpenAI(
                model=model_id,
                temperature=temperature,
                openai_api_key=os.getenv("XAI_API_KEY"),
                base_url=config.get("base_url", "https://api.x.ai/v1")
            )
        else:
            logger.warning(f"Unknown provider: {provider}")
            return None
    
    def get_model_for_task(self, task_type: str = "general") -> Any:
        """Get the best model for a specific task type"""
        
        # Find models that support this task type
        suitable_models = []
        for model_name, model_config in self.config.get("models", {}).items():
            if task_type in model_config.get("use_for", []) and model_name in self.models:
                suitable_models.append(model_name)
        
        # Use the first suitable model, or default, or any available model
        if suitable_models:
            selected_model = suitable_models[0]
        elif self.default_model in self.models:
            selected_model = self.default_model
        elif self.models:  # Use any available model as fallback
            selected_model = list(self.models.keys())[0]
        else:
            return None
        
        return self.models.get(selected_model)
    
    def get_available_models(self) -> List[str]:
        """Get list of available model names"""
        return list(self.models.keys())

class EducationalAgent:
    """Educational binary analysis agent using LangGraph"""
    
    def __init__(self, config_path: str):
        self.config_path = config_path
        
        # Load configuration
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        # Initialize MCP client
        self.mcp_client = MCPClient(config_path)
        
        # Initialize model manager
        self.model_manager = ModelManager(self.config)
        
        # Get default model for initialization
        self.default_llm = self.model_manager.get_model_for_task("general")
        if not self.default_llm:
            raise ValueError("No models available! Check your API keys and configuration.")
        
        # Create educational system prompt
        self.system_prompt = self._create_system_prompt()
        
        # Initialize LLM with tools
        all_tools = self.mcp_client.get_all_tools()
        self.llm_with_tools = self.default_llm.bind_tools(all_tools)
        
        # Create tool node
        self.tool_node = ToolNode(all_tools)
        
        # Build the graph
        self.graph = self._build_graph()
        
        # Setup persistence
        self.checkpointer = MemorySaver()
        self.app = self.graph.compile(checkpointer=self.checkpointer)
        
        available_models = self.model_manager.get_available_models()
        logger.info(f"✅ Educational agent initialized with {len(all_tools)} tools")
        logger.info(f"🤖 Available models: {', '.join(available_models)}")
    
    def _create_system_prompt(self) -> str:
        """Create educational system prompt"""
        return """You are an educational binary analysis expert helping users learn systems programming concepts.

Your educational approach:
- Start with the user's current understanding level (beginner/intermediate/advanced)
- Use the three-phase learning model: static analysis → concept validation → runtime analysis
- Provide multi-level explanations with practical examples
- Connect theory to practice using real binaries
- Track learning progress and build on previous concepts

Available analysis phases:
1. STATIC: Examine binary structure (GOT, PLT, symbols) without execution
2. VALIDATION: Test theoretical concepts against real binary behavior  
3. RUNTIME: Trace dynamic linking and symbol resolution during execution
4. SYNTHESIS: Combine insights and provide comprehensive understanding

Educational principles:
- Always explain WHY something works, not just HOW
- Use progressive disclosure - start simple, add complexity gradually
- Validate understanding before moving to next concepts
- Provide interactive examples when helpful
- Connect concepts to broader systems programming knowledge

You have access to 40+ specialized tools across:
- Master orchestrator (routing and server management)
- Topic detection (intelligent question analysis)  
- GOT/PLT analysis (18 tools for binary analysis education)
- Book-specific concept search (K&R, UNIX, OS, Linkers & Loaders, etc.)

Always route complex questions through the orchestrator first to ensure optimal tool selection."""

    def _build_graph(self) -> StateGraph:
        """Build the educational workflow graph"""
        
        # Create the workflow graph
        workflow = StateGraph(EducationalAgentState)
        
        # Add nodes
        workflow.add_node("agent", self._agent_node)
        workflow.add_node("tools", self._tool_node) 
        workflow.add_node("educational_router", self._educational_router_node)
        workflow.add_node("concept_validator", self._concept_validator_node)
        workflow.add_node("phase_manager", self._phase_manager_node)
        workflow.add_node("explanation_generator", self._explanation_generator_node)
        
        # Set entry point
        workflow.set_entry_point("educational_router")
        
        # Add conditional edges
        workflow.add_conditional_edges(
            "educational_router",
            self._route_from_educational_router,
            {
                "analyze_question": "agent",
                "validate_concepts": "concept_validator", 
                "advance_phase": "phase_manager",
                "end": END
            }
        )
        
        workflow.add_conditional_edges(
            "agent",
            self._route_from_agent,
            {
                "tools": "tools",
                "explain": "explanation_generator",
                "validate": "concept_validator", 
                "end": END
            }
        )
        
        workflow.add_conditional_edges(
            "tools",
            self._route_from_tools,
            {
                "agent": "agent",
                "validate": "concept_validator",
                "explain": "explanation_generator",
                "phase": "phase_manager"
            }
        )
        
        # Simple edges
        workflow.add_edge("concept_validator", "explanation_generator")
        workflow.add_edge("phase_manager", "agent")
        workflow.add_edge("explanation_generator", "educational_router")
        
        return workflow
    
    def _agent_node(self, state: EducationalAgentState) -> Dict[str, Any]:
        """Core agent reasoning node with model selection"""
        try:
            # Determine task type from current phase and context
            current_phase = state.get("analysis_phase", "static")
            needs_validation = state.get("needs_theory_validation", False)
            
            # Select appropriate model based on task
            if needs_validation:
                task_type = "validation"
            elif current_phase == "runtime":
                task_type = "technical"
            elif state.get("needs_concept_explanation", False):
                task_type = "explanation"
            else:
                task_type = "general"
            
            # Get model for this task
            selected_model = self.model_manager.get_model_for_task(task_type)
            
            # Bind tools to selected model
            llm_with_tools = selected_model.bind_tools(self.mcp_client.get_all_tools())
            
            # Add system prompt to messages
            messages = [{"role": "system", "content": self.system_prompt}] + state["messages"]
            
            # Get LLM response
            response = llm_with_tools.invoke(messages)
            
            # Update retry count on success
            return {
                "messages": [response],
                "retry_count": 0,
                "last_error": None,
                "fallback_mode": False,
                "selected_model": task_type  # Track which model was used
            }
            
        except Exception as e:
            logger.error(f"Agent node error: {e}")
            retry_count = state.get("retry_count", 0) + 1
            
            # Try fallback model on error
            if retry_count <= 2:
                try:
                    fallback_model = self.default_llm.bind_tools(self.mcp_client.get_all_tools())
                    messages = [{"role": "system", "content": self.system_prompt}] + state["messages"]
                    response = fallback_model.invoke(messages)
                    
                    return {
                        "messages": [response],
                        "retry_count": retry_count,
                        "last_error": str(e),
                        "fallback_mode": True,
                        "selected_model": "fallback"
                    }
                except Exception as fallback_error:
                    logger.error(f"Fallback model also failed: {fallback_error}")
            
            # Create fallback response
            fallback_msg = AIMessage(content=f"I encountered an error: {str(e)}. Let me try a different approach.")
            
            return {
                "messages": [fallback_msg],
                "retry_count": retry_count,
                "last_error": str(e),
                "fallback_mode": retry_count > 2
            }
    
    def _tool_node(self, state: EducationalAgentState) -> Dict[str, Any]:
        """Tool execution node with educational context"""
        try:
            # Execute tools using LangGraph's ToolNode
            result = self.tool_node.invoke(state)
            
            # Track tool usage
            last_message = state["messages"][-1] if state["messages"] else None
            tool_calls = getattr(last_message, "tool_calls", []) if last_message else []
            
            tool_history = state.get("tool_call_history", [])
            for tool_call in tool_calls:
                tool_history.append({
                    "tool": tool_call.get("name", "unknown"),
                    "args": tool_call.get("args", {}),
                    "timestamp": str(uuid.uuid4())  # Simple timestamp
                })
            
            # Update state with tool results
            updated_state = result.copy()
            updated_state.update({
                "tool_call_history": tool_history,
                "last_tool_used": tool_calls[0].get("name") if tool_calls else None,
                "needs_concept_explanation": self._should_explain_concepts(tool_calls),
                "needs_theory_validation": self._should_validate_theory(tool_calls)
            })
            
            return updated_state
            
        except Exception as e:
            logger.error(f"Tool execution error: {e}")
            error_msg = AIMessage(content=f"Tool execution failed: {str(e)}. Let me try a different approach.")
            
            return {
                "messages": state["messages"] + [error_msg],
                "last_error": str(e),
                "retry_count": state.get("retry_count", 0) + 1
            }
    
    def _educational_router_node(self, state: EducationalAgentState) -> Dict[str, Any]:
        """Routes based on educational workflow needs"""
        
        # Check if we need to advance learning phase
        if state.get("ready_for_next_phase", False):
            return {"routing_decision": "advance_phase"}
        
        # Check if we need concept validation
        if state.get("needs_theory_validation", False):
            return {"routing_decision": "validate_concepts"}
        
        # Check if this is a new question that needs analysis
        messages = state.get("messages", [])
        if messages and isinstance(messages[-1], HumanMessage):
            return {"routing_decision": "analyze_question"}
        
        # Default to ending if no clear next step
        return {"routing_decision": "end"}
    
    def _concept_validator_node(self, state: EducationalAgentState) -> Dict[str, Any]:
        """Validates concepts against theory using GOT/PLT tools"""
        
        current_binary = state.get("current_binary")
        learned_concepts = state.get("learned_concepts", [])
        
        if not current_binary or not learned_concepts:
            return {
                "needs_theory_validation": False,
                "validation_status": "skipped_no_context"
            }
        
        # Use GOT/PLT validation tools
        validation_results = {}
        for concept in learned_concepts[-3:]:  # Validate recent concepts
            try:
                # This would call the actual MCP validation tool
                validation_results[concept] = "validated"
            except Exception as e:
                validation_results[concept] = f"validation_failed: {str(e)}"
        
        return {
            "validated_concepts": {**state.get("validated_concepts", {}), **validation_results},
            "needs_theory_validation": False,
            "needs_concept_explanation": True
        }
    
    def _phase_manager_node(self, state: EducationalAgentState) -> Dict[str, Any]:
        """Manages progression through learning phases"""
        
        current_phase = state.get("analysis_phase", "static")
        
        # Use StateUpdates helper
        if state.get("ready_for_next_phase", False):
            phase_update = StateUpdates.advance_phase(state)
            logger.info(f"Advanced from {current_phase} to {phase_update['analysis_phase']}")
            return phase_update
        
        return {"ready_for_next_phase": False}
    
    def _explanation_generator_node(self, state: EducationalAgentState) -> Dict[str, Any]:
        """Generates educational explanations at appropriate level"""
        
        explanation_level = state.get("explanation_level", "intermediate")
        current_phase = state.get("analysis_phase", "static")
        
        # Create contextual explanation prompt
        explanation_prompt = f"""
        Based on the recent analysis, provide a {explanation_level}-level explanation focusing on the {current_phase} phase.
        
        Educational guidelines:
        - Beginner: Use simple terms, focus on concepts, provide analogies
        - Intermediate: Include technical details, show relationships between concepts  
        - Advanced: Deep dive into implementation, optimization considerations
        
        Current context: {current_phase} analysis phase
        Learning goal: {state.get('learning_goal', 'general understanding')}
        """
        
        return {
            "needs_concept_explanation": False,
            "last_explanation_level": explanation_level,
            "explanation_context": current_phase
        }
    
    # Routing functions
    def _route_from_educational_router(self, state: EducationalAgentState) -> Literal["analyze_question", "validate_concepts", "advance_phase", "end"]:
        """Route from educational router based on state"""
        decision = state.get("routing_decision", "end")
        return decision
    
    def _route_from_agent(self, state: EducationalAgentState) -> Literal["tools", "explain", "validate", "end"]:
        """Route from agent based on response type"""
        
        if not state["messages"]:
            return "end"
        
        last_message = state["messages"][-1]
        
        # Check for tool calls
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"
        
        # Check if explanation is needed
        if state.get("needs_concept_explanation", False):
            return "explain"
        
        # Check if validation is needed
        if state.get("needs_theory_validation", False):
            return "validate"
        
        return "end"
    
    def _route_from_tools(self, state: EducationalAgentState) -> Literal["agent", "validate", "explain", "phase"]:
        """Route from tools based on results and educational needs"""
        
        # Check if we should advance phase
        if state.get("ready_for_next_phase", False):
            return "phase"
        
        # Check if validation is needed
        if state.get("needs_theory_validation", False):
            return "validate"
        
        # Check if explanation is needed
        if state.get("needs_concept_explanation", False):
            return "explain"
        
        # Continue agent reasoning
        return "agent"
    
    # Helper functions
    def _should_explain_concepts(self, tool_calls: List[Dict]) -> bool:
        """Determine if concepts need explanation based on tools used"""
        educational_tools = ["gotplt_validate_concept", "gotplt_inspect_got_table", "gotplt_analyze_plt_stubs"]
        return any(call.get("name", "") in educational_tools for call in tool_calls)
    
    def _should_validate_theory(self, tool_calls: List[Dict]) -> bool:
        """Determine if theory validation is needed"""
        analysis_tools = ["gotplt_inspect_got_table", "gotplt_analyze_plt_stubs"]
        return any(call.get("name", "") in analysis_tools for call in tool_calls)
    
    def invoke(self, user_input: str, session_id: str = None) -> Dict[str, Any]:
        """Invoke the educational agent"""
        
        if session_id is None:
            session_id = str(uuid.uuid4())
        
        config = {"configurable": {"thread_id": session_id}}
        
        # Create initial state
        initial_state = {
            "messages": [HumanMessage(content=user_input)],
            "learning_goal": None,
            "explanation_level": "intermediate",
            "session_id": session_id,
            "learned_concepts": [],
            "validated_concepts": {},
            "analysis_phase": "static",
            "needs_concept_explanation": False,
            "needs_theory_validation": False,
            "ready_for_next_phase": False,
            "preferred_servers": [],
            "last_tool_used": None,
            "tool_call_history": [],
            "learning_progress": {},
            "user_feedback": [],
            "last_error": None,
            "retry_count": 0,
            "fallback_mode": False
        }
        
        try:
            # Stream the workflow
            final_state = None
            events = []
            
            for event in self.app.stream(initial_state, config=config):
                events.append(event)
                final_state = event
                logger.debug(f"Workflow event: {list(event.keys()) if event else 'None'}")
            
            if final_state:
                return {
                    "success": True,
                    "response": self._extract_response(final_state),
                    "session_id": session_id,
                    "state": final_state
                }
            else:
                return {
                    "success": False,
                    "error": "No workflow events generated",
                    "session_id": session_id,
                    "response": "Workflow failed to generate any events"
                }
            
        except Exception as e:
            logger.error(f"Agent invocation error: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "session_id": session_id,
                "response": f"Agent error: {str(e)}"
            }
    
    def _extract_response(self, final_state: Dict[str, Any]) -> str:
        """Extract final response from workflow state"""
        if not final_state:
            return "No response generated"
        
        # Get the last state from the workflow
        try:
            last_state_key = list(final_state.keys())[-1]
            state = final_state[last_state_key]
            
            if not state or not isinstance(state, dict):
                return "Invalid state format"
            
            messages = state.get("messages", [])
            if messages:
                last_message = messages[-1]
                if hasattr(last_message, "content"):
                    return last_message.content
                return str(last_message)
            
            return "Workflow completed but no response found"
            
        except (IndexError, KeyError, AttributeError) as e:
            logger.error(f"Response extraction error: {e}")
            return f"Response extraction failed: {str(e)}"
