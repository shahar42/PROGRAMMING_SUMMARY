#!/usr/bin/env python3
"""
Educational Agent State Definition
Defines the persistent state structure for LangGraph educational workflows
"""

from typing import TypedDict, List, Dict, Optional, Any, Annotated
from langchain_core.messages import BaseMessage

class EducationalAgentState(TypedDict):
    """
    Persistent state for educational binary analysis agent.
    This state flows between all nodes and persists across sessions.
    """
    
    # Core conversation flow
    messages: Annotated[List[BaseMessage], lambda x, y: x + y]
    
    # Learning session tracking
    learning_goal: Optional[str]  # "understand GOT", "learn PLT mechanics", etc.
    explanation_level: str  # "beginner", "intermediate", "advanced"
    session_id: Optional[str]
    
    # Concept learning progress
    learned_concepts: List[str]  # Concept IDs that have been explained
    validated_concepts: Dict[str, str]  # concept_id -> validation_status
    concept_dependencies: Dict[str, List[str]]  # concept -> prerequisites
    
    # Multi-phase analysis tracking
    analysis_phase: str  # "static", "validation", "runtime", "synthesis"
    current_binary: Optional[str]  # Path to binary being analyzed
    binary_analysis_results: Dict[str, Any]  # Store analysis outputs
    
    # Educational workflow state
    needs_concept_explanation: bool
    needs_theory_validation: bool
    needs_practical_example: bool
    ready_for_next_phase: bool
    
    # MCP tool routing
    preferred_servers: List[str]  # Server names for current context
    last_tool_used: Optional[str]
    tool_call_history: List[Dict[str, Any]]
    
    # Progress and feedback
    learning_progress: Dict[str, float]  # topic -> progress percentage
    user_feedback: List[str]  # Feedback for learning adaptation
    
    # Error handling and recovery
    last_error: Optional[str]
    retry_count: int
    fallback_mode: bool
    selected_model: Optional[str]  # Track which model was used

# State update helpers for common operations
class StateUpdates:
    """Helper functions for common state updates"""
    
    @staticmethod
    def advance_phase(state: EducationalAgentState) -> Dict[str, Any]:
        """Advance to next analysis phase"""
        phase_order = ["static", "validation", "runtime", "synthesis"]
        current_idx = phase_order.index(state["analysis_phase"])
        next_phase = phase_order[min(current_idx + 1, len(phase_order) - 1)]
        
        return {
            "analysis_phase": next_phase,
            "ready_for_next_phase": False,
            "needs_concept_explanation": True
        }
    
    @staticmethod
    def add_learned_concept(state: EducationalAgentState, concept_id: str) -> Dict[str, Any]:
        """Add a concept to learned list"""
        learned = state.get("learned_concepts", [])
        if concept_id not in learned:
            learned.append(concept_id)
        
        return {"learned_concepts": learned}
    
    @staticmethod
    def update_validation_result(state: EducationalAgentState, 
                                concept_id: str, status: str) -> Dict[str, Any]:
        """Update concept validation results"""
        validated = state.get("validated_concepts", {})
        validated[concept_id] = status
        
        return {"validated_concepts": validated}
    
    @staticmethod
    def reset_for_new_binary(state: EducationalAgentState, 
                            binary_path: str) -> Dict[str, Any]:
        """Reset state for new binary analysis"""
        return {
            "current_binary": binary_path,
            "analysis_phase": "static",
            "binary_analysis_results": {},
            "needs_concept_explanation": True,
            "ready_for_next_phase": False
        }
