#!/usr/bin/env python3
"""
Robust Multi-LLM Programming Concepts Agent - Rewritten from Scratch
Never abandons tools, systematically self-corrects, learns from mistakes

Key improvements:
- Robust tool calling with automatic parameter validation
- Systematic error recovery (never abandons tools)
- Built-in self-diagnostic capabilities
- Integrated long-term memory
- Tool-first mentality (tools always preferred over general knowledge)
"""

import os
import sys
import json
import asyncio
import readline
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from collections import defaultdict, Counter
from dotenv import load_dotenv
from abc import ABC, abstractmethod

# Enable command history
readline.set_startup_hook(lambda: readline.insert_text(''))

# LLM imports
import google.generativeai as genai
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# Setup paths
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
scripts_path = os.path.join(project_root, 'scripts')
sys.path.extend([project_root, scripts_path])

# Import tools
try:
    from mcp_server import (
        search_concepts, get_concept_details, compare_concepts,
        generate_study_path, explain_my_code, synthesize_concepts,
        generate_custom_tutorial, create_best_practices_guide,
        search_by_book, find_advanced_concepts
    )
    MAIN_TOOLS_AVAILABLE = True
    print("✅ Main concept tools imported")
except ImportError as e:
    MAIN_TOOLS_AVAILABLE = False
    print(f"❌ Main tools failed: {e}")

try:
    sys.path.append(os.path.join(scripts_path, 'educational'))
    from concept_validator import ConceptValidator
    from example_generator import EnhancedExampleGenerator
    EDUCATIONAL_TOOLS_AVAILABLE = True
    print("✅ Educational tools imported")
except ImportError as e:
    EDUCATIONAL_TOOLS_AVAILABLE = False
    print(f"⚠️  Educational tools unavailable: {e}")


@dataclass
class ToolSpec:
    """Complete tool specification with validation"""
    name: str
    description: str
    parameters: Dict[str, str]  # param_name -> type_description
    required_params: List[str]
    function: callable
    examples: List[str]


class ToolRegistry:
    """Centralized tool registry with built-in parameter validation"""
    
    def __init__(self):
        self.tools = {}
        self._register_all_tools()
    
    def _register_all_tools(self):
        """Register all available tools with exact specifications"""
        
        if MAIN_TOOLS_AVAILABLE:
            self._register_main_tools()
        
        if EDUCATIONAL_TOOLS_AVAILABLE:
            self._register_educational_tools()
        
        # Always register meta-tools
        self._register_meta_tools()
        
        print(f"🛠️  Registered {len(self.tools)} tools")
    
    def _register_main_tools(self):
        """Register main concept tools"""
        self.tools.update({
            "search_concepts": ToolSpec(
                name="search_concepts",
                description="Search across all programming concept books",
                parameters={
                    "query": "str - search query for programming concepts",
                    "limit": "int - maximum results to return (default: 10)"
                },
                required_params=["query"],
                function=search_concepts,
                examples=[
                    'search_concepts(query="memory management", limit=5)',
                    'search_concepts(query="cache miss")'
                ]
            ),
            
            "get_concept_details": ToolSpec(
                name="get_concept_details",
                description="Get detailed information about a specific concept",
                parameters={
                    "concept_id": "str - the exact ID of the concept to retrieve"
                },
                required_params=["concept_id"],
                function=get_concept_details,
                examples=[
                    'get_concept_details(concept_id="csapp_2016_concept_175")',
                    'get_concept_details(concept_id="kernighan_ritchie_concept_038")'
                ]
            ),
            
            "compare_concepts": ToolSpec(
                name="compare_concepts", 
                description="Compare two programming concepts side-by-side",
                parameters={
                    "concept1_id": "str - ID of first concept to compare",
                    "concept2_id": "str - ID of second concept to compare"
                },
                required_params=["concept1_id", "concept2_id"],
                function=compare_concepts,
                examples=[
                    'compare_concepts(concept1_id="csapp_2016_concept_175", concept2_id="csapp_2016_concept_126")'
                ]
            ),
            
            "search_by_book": ToolSpec(
                name="search_by_book",
                description="Search concepts within a specific book",
                parameters={
                    "book_name": "str - book name (kernighan_ritchie, unix_env, linkers_loaders, os_three_pieces, expert_c_programming, csapp_2016)",
                    "query": "str - search query within the book (optional, empty shows all concepts)"
                },
                required_params=["book_name"],
                function=search_by_book,
                examples=[
                    'search_by_book(book_name="csapp_2016", query="cache")',
                    'search_by_book(book_name="kernighan_ritchie", query="malloc")'
                ]
            ),
            
            "generate_study_path": ToolSpec(
                name="generate_study_path",
                description="Create ordered learning sequence for a programming goal",
                parameters={
                    "goal": "str - learning objective description"
                },
                required_params=["goal"],
                function=generate_study_path,
                examples=[
                    'generate_study_path(goal="learn systems programming")',
                    'generate_study_path(goal="master C memory management")'
                ]
            ),
            
            "explain_my_code": ToolSpec(
                name="explain_my_code",
                description="Analyze user's code using the programming knowledge base",
                parameters={
                    "code_snippet": "str - the code to analyze",
                    "language": "str - programming language (default: 'C')"
                },
                required_params=["code_snippet"],
                function=explain_my_code,
                examples=[
                    'explain_my_code(code_snippet="int *ptr = malloc(100);", language="C")'
                ]
            )
        })
    
    def _register_educational_tools(self):
        """Register educational validation tools"""
        validator = ConceptValidator()
        generator = EnhancedExampleGenerator()
        
        self.tools.update({
            "validate_concept": ToolSpec(
                name="validate_concept",
                description="Test theoretical concept against real binary files",
                parameters={
                    "concept_name": "str - name of concept to validate",
                    "binary_path": "str - path to binary file (optional)"
                },
                required_params=["concept_name"],
                function=validator.validate_concept,
                examples=[
                    'validate_concept(concept_name="Global Offset Table", binary_path="/bin/ls")'
                ]
            ),
            
            "create_interactive_example": ToolSpec(
                name="create_interactive_example",
                description="Create complete, compilable example project",
                parameters={
                    "concept_name": "str - concept to create example for",
                    "output_directory": "str - where to save example (optional)"
                },
                required_params=["concept_name"],
                function=generator.generate_concept_example,
                examples=[
                    'create_interactive_example(concept_name="lazy binding")'
                ]
            )
        })
    
    def _register_meta_tools(self):
        """Register meta-tools for self-diagnosis"""
        self.tools.update({
            "describe_tools": ToolSpec(
                name="describe_tools",
                description="Get exact parameter specifications for any tool",
                parameters={
                    "tool_name": "str - name of tool to describe (empty shows all tools)"
                },
                required_params=[],
                function=self._describe_tools,
                examples=[
                    'describe_tools(tool_name="search_concepts")',
                    'describe_tools()'
                ]
            ),
            
            "diagnose_last_error": ToolSpec(
                name="diagnose_last_error",
                description="Diagnose the last tool execution error and suggest fixes",
                parameters={},
                required_params=[],
                function=self._diagnose_last_error,
                examples=['diagnose_last_error()']
            )
        })
    
    def _describe_tools(self, tool_name: str = "") -> str:
        """Describe tool specifications"""
        if tool_name:
            if tool_name in self.tools:
                tool = self.tools[tool_name]
                result = f"🔧 **{tool.name}**\n\n"
                result += f"**Description:** {tool.description}\n\n"
                result += f"**Parameters:**\n"
                for param, desc in tool.parameters.items():
                    required = " (REQUIRED)" if param in tool.required_params else " (optional)"
                    result += f"  - `{param}`: {desc}{required}\n"
                result += f"\n**Examples:**\n"
                for example in tool.examples:
                    result += f"  - `{example}`\n"
                return result
            else:
                return f"❌ Tool '{tool_name}' not found. Available: {list(self.tools.keys())}"
        else:
            result = "🛠️ **Available Tools:**\n\n"
            for name, tool in self.tools.items():
                params = ", ".join([f"{p}: {self.tools[name].parameters[p].split(' - ')[0]}" for p in tool.required_params])
                result += f"**{name}**({params}) - {tool.description}\n"
            return result
    
    def _diagnose_last_error(self) -> str:
        """Diagnose and suggest fixes for the last error"""
        return "🔍 **Error Diagnosis:** Use describe_tools() to get correct parameters. Never abandon tools - they contain authoritative data."
    
    def get_tool(self, name: str) -> Optional[ToolSpec]:
        """Get tool specification"""
        return self.tools.get(name)
    
    def validate_parameters(self, tool_name: str, parameters: Dict) -> Tuple[bool, str]:
        """Validate parameters for a tool call"""
        if tool_name not in self.tools:
            return False, f"Tool '{tool_name}' not found"
        
        tool = self.tools[tool_name]
        
        # Check required parameters
        missing = [p for p in tool.required_params if p not in parameters]
        if missing:
            return False, f"Missing required parameters: {missing}. Use describe_tools('{tool_name}') for help."
        
        # Check for unknown parameters
        unknown = [p for p in parameters if p not in tool.parameters]
        if unknown:
            return False, f"Unknown parameters: {unknown}. Valid parameters: {list(tool.parameters.keys())}"
        
        return True, "Parameters valid"


class AgentMemory:
    """Enhanced memory system with better learning"""
    
    def __init__(self, memory_file: str = "agent_memory.json"):
        self.memory_file = memory_file
        self.memory = self._load_memory()
        self.successful_calls = self.memory.get("successful_calls", {})
        self.failed_calls = self.memory.get("failed_calls", [])
        self.user_patterns = self.memory.get("user_patterns", {})
        
        print(f"💾 Memory loaded: {len(self.successful_calls)} successful patterns learned")
    
    def _load_memory(self) -> Dict:
        """Load memory from disk"""
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, 'r') as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}
    
    def save_memory(self):
        """Save memory to disk"""
        try:
            self.memory = {
                "successful_calls": self.successful_calls,
                "failed_calls": self.failed_calls[-100:],  # Keep last 100 failures
                "user_patterns": self.user_patterns,
                "last_updated": datetime.now().isoformat()
            }
            with open(self.memory_file, 'w') as f:
                json.dump(self.memory, f, indent=2)
        except Exception as e:
            print(f"⚠️  Memory save failed: {e}")
    
    def remember_success(self, query: str, tool_name: str, parameters: Dict, result_snippet: str):
        """Remember a successful tool call"""
        pattern_key = f"{tool_name}_{hash(query) % 10000}"
        
        self.successful_calls[pattern_key] = {
            "query": query,
            "tool": tool_name,
            "parameters": parameters,
            "result_snippet": result_snippet[:200],
            "timestamp": datetime.now().isoformat(),
            "success_count": self.successful_calls.get(pattern_key, {}).get("success_count", 0) + 1
        }
        
        self.save_memory()
        print(f"💾 Learned: {query} → {tool_name} SUCCESS")
    
    def remember_failure(self, query: str, tool_name: str, parameters: Dict, error: str):
        """Remember a failed tool call"""
        failure = {
            "query": query,
            "tool": tool_name,
            "parameters": parameters,
            "error": error,
            "timestamp": datetime.now().isoformat()
        }
        
        self.failed_calls.append(failure)
        print(f"💾 Learned: {query} → {tool_name} FAILED ({error[:50]})")
    
    def suggest_parameters(self, query: str, tool_name: str) -> Optional[Dict]:
        """Suggest parameters based on successful patterns"""
        # Find similar successful calls
        for pattern_key, call in self.successful_calls.items():
            if (call["tool"] == tool_name and 
                any(word in call["query"].lower() for word in query.lower().split())):
                print(f"💡 Memory suggests parameters from similar query: {call['parameters']}")
                return call["parameters"].copy()
        
        return None


class RobustLLMAgent(ABC):
    """Base class for robust LLM agents that never abandon tools"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.tool_registry = ToolRegistry()
        self.memory = AgentMemory()
        self.conversation_history = []
        self.last_error = None
        self.current_query = ""
        
        print(f"🤖 {self.__class__.__name__} initialized with {len(self.tool_registry.tools)} tools")
    
    def _create_system_prompt(self) -> str:
    
        # Get available tools from registry
        available_tools = []
        for name, tool in self.tool_registry.tools.items():
            params = ", ".join([f"{p}: {tool.parameters[p].split(' - ')[0]}" for p in tool.required_params])
            available_tools.append(f"- {name}({params}) - {tool.description}")
        
        tools_list = "\n".join(available_tools)
        
        return f"""You are a Programming Concepts Expert with access to 693 concepts from 6 classic CS books.
    Your knowledge base contains extracted concepts from: K&R C, UNIX Environment, Linkers & Loaders, Operating Systems, Expert C Programming, CSAPP.

    AVAILABLE TOOLS:
    {tools_list}

    CRITICAL TOOL USAGE RULES:
    1. ALWAYS prefer tool results over your general knowledge
    2. NEVER abandon tools - they contain your authoritative data
    3. If a tool fails, FIRST call describe_tools(tool_name) to get correct parameters
    4. If still failing after getting help, call diagnose_last_error() for guidance
    5. Keep trying tools with correct parameters - never give up on tools
    6. Your extracted concepts are ALWAYS more accurate than general knowledge

    TOOL CALLING FORMAT:
    TOOL_CALL: tool_name
    PARAMETERS: {{"param": "value"}}

    RECOVERY PROCESS when tools fail:
    1. Call describe_tools(failed_tool_name) to get correct parameters
    2. Retry with exact parameters shown
    3. If still failing, try related tools (e.g., search_by_book instead of search_concepts)
    4. NEVER resort to general knowledge when tools are available

    Be systematic, educational, and persistent with tool usage."""

    @abstractmethod
    async def generate_response(self, prompt: str) -> str:
        """Generate response from LLM"""
        pass
    
    async def process_query(self, user_query: str) -> str:
        """Process query with robust error recovery"""
        print(f"\n🤔 [{self.__class__.__name__}] Processing: {user_query}")
        
        self.current_query = user_query
        self.conversation_history.append({"role": "user", "content": user_query})
        
        # Check memory for suggestions
        suggested_tool = self._suggest_tool_from_memory(user_query)
        
        # Create enhanced prompt with memory insights
        full_prompt = self._create_system_prompt()
        if suggested_tool:
            full_prompt += f"\n\n💡 MEMORY SUGGESTION: Based on similar queries, consider using {suggested_tool}"
        
        full_prompt += "\n\nCONVERSATION HISTORY:\n"
        for msg in self.conversation_history[-3:]:
            full_prompt += f"{msg['role'].upper()}: {msg['content']}\n"
        full_prompt += f"\nUSER: {user_query}\n\nAGENT:"
        
        # Robust reasoning loop with better error recovery
        max_iterations = 15  # More iterations for complex recovery
        iteration = 0
        consecutive_failures = 0
        
        while iteration < max_iterations:
            try:
                response_text = await self.generate_response(full_prompt)
                
                print(f"🧠 [{self.__class__.__name__}] Iteration {iteration + 1}:")
                print(response_text[:100] + "..." if len(response_text) > 100 else response_text)
                
                if "TOOL_CALL:" in response_text:
                    tool_result, success = await self._robust_tool_execution(response_text)
                    
                    if success:
                        consecutive_failures = 0
                        # Check if this looks like a final answer
                        if self._is_comprehensive_answer(tool_result):
                            self.conversation_history.append({"role": "assistant", "content": tool_result})
                            return tool_result
                    else:
                        consecutive_failures += 1
                        if consecutive_failures >= 3:
                            # Inject recovery guidance
                            full_prompt += f"\n{response_text}\n\nTOOL_RESULT: {tool_result}\n\n"
                            full_prompt += "🔧 RECOVERY GUIDANCE: The tool failed. Call describe_tools() to get correct parameters. Never abandon tools - they have your authoritative data.\n\nContinue:"
                        else:
                            full_prompt += f"\n{response_text}\n\nTOOL_RESULT: {tool_result}\n\nContinue:"
                    
                    iteration += 1
                else:
                    # Final answer - make sure it's not tool abandonment
                    if self._detected_tool_abandonment(response_text):
                        full_prompt += f"\n{response_text}\n\n❌ CRITICAL: You abandoned tools! Your extracted concepts are more accurate than general knowledge. Use describe_tools() to get help and retry tools.\n\nUse tools to answer:"
                        iteration += 1
                    else:
                        # Legitimate final answer
                        self.conversation_history.append({"role": "assistant", "content": response_text})
                        return response_text
                
            except Exception as e:
                error_msg = f"[{self.__class__.__name__}] Reasoning error: {e}"
                print(f"❌ {error_msg}")
                return error_msg
        
        return f"[{self.__class__.__name__}] Reached maximum iterations. Consider simplifying your query."
    
    async def _robust_tool_execution(self, response_text: str) -> Tuple[str, bool]:
        """Execute tools with robust error handling and validation"""
        try:
            # Parse tool call
            tool_name, parameters = self._parse_tool_call(response_text)
            
            if not tool_name:
                return "ERROR: No valid tool call found. Use format: TOOL_CALL: tool_name", False
            
            # Get tool specification
            tool_spec = self.tool_registry.get_tool(tool_name)
            if not tool_spec:
                available_tools = list(self.tool_registry.tools.keys())
                return f"ERROR: Tool '{tool_name}' not found. Available tools: {available_tools}", False
            
            # Validate parameters
            valid, validation_msg = self.tool_registry.validate_parameters(tool_name, parameters)
            if not valid:
                self.last_error = validation_msg
                return f"PARAMETER ERROR: {validation_msg}", False
            
            print(f"🔧 [{self.__class__.__name__}] Executing: {tool_name} with {parameters}")
            
            # Execute tool
            if asyncio.iscoroutinefunction(tool_spec.function):
                result = await tool_spec.function(**parameters)
            else:
                result = tool_spec.function(**parameters)
            
            result_str = str(result)
            
            # Check for obvious failures
            if any(fail_indicator in result_str.lower() for fail_indicator in ["not found", "error", "failed", "invalid"]):
                self.memory.remember_failure(self.current_query, tool_name, parameters, result_str[:100])
                return result_str, False
            else:
                # Success!
                self.memory.remember_success(self.current_query, tool_name, parameters, result_str[:200])
                print(f"✅ Tool succeeded: {tool_name}")
                return result_str, True
                
        except json.JSONDecodeError as e:
            error_msg = f"JSON Parse Error: {e}. Use describe_tools('{tool_name}') for correct parameter format."
            self.last_error = error_msg
            return error_msg, False
        except Exception as e:
            error_msg = f"Tool execution error: {e}"
            self.last_error = error_msg
            return error_msg, False
    
    def _parse_tool_call(self, response_text: str) -> Tuple[Optional[str], Dict]:
        """Parse tool call from response with robust JSON extraction"""
        lines = response_text.split('\n')
        tool_name = None
        parameters = {}
        
        for line in lines:
            if line.startswith("TOOL_CALL:"):
                tool_name = line.replace("TOOL_CALL:", "").strip()
            elif line.startswith("PARAMETERS:"):
                param_text = line.replace("PARAMETERS:", "").strip()
                
                # Robust JSON extraction
                start = param_text.find('{')
                end = param_text.rfind('}') + 1
                
                if start != -1 and end > start:
                    json_text = param_text[start:end]
                    try:
                        parameters = json.loads(json_text)
                    except json.JSONDecodeError:
                        # Try to fix common JSON issues
                        json_text = json_text.replace("'", '"')  # Fix single quotes
                        parameters = json.loads(json_text)
        
        return tool_name, parameters
    
    def _suggest_tool_from_memory(self, query: str) -> Optional[str]:
        """Suggest tool based on memory patterns"""
        query_words = query.lower().split()
        
        # Look for successful patterns
        for call in self.memory.successful_calls.values():
            if any(word in call["query"].lower() for word in query_words):
                return call["tool"]
        
        return None
    
    def _is_comprehensive_answer(self, result: str) -> bool:
        """Check if result looks like a comprehensive final answer"""
        indicators = ["**", "##", "Description:", "Details:", "Example:", "Code:", "Source:"]
        return len(result) > 200 and any(indicator in result for indicator in indicators)
    
    def _detected_tool_abandonment(self, response: str) -> bool:
        """Detect if agent is abandoning tools"""
        abandonment_phrases = [
            "cannot access", "tool is not working", "rely on my internal knowledge",
            "based on my knowledge", "without using tools", "tools are unavailable"
        ]
        response_lower = response.lower()
        return any(phrase in response_lower for phrase in abandonment_phrases)


class GeminiAgent(RobustLLMAgent):
    """Robust Gemini agent"""
    
    def __init__(self, api_key: str, model_name: str = "gemini-1.5-pro"):
        super().__init__(api_key)
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)
        print(f"🤖 Gemini Agent ready ({model_name})")
    
    async def generate_response(self, prompt: str) -> str:
        response = self.model.generate_content(prompt)
        return response.text


if OPENAI_AVAILABLE:
    class OpenAIAgent(RobustLLMAgent):
        """Robust OpenAI agent"""
        
        def __init__(self, api_key: str, model_name: str = "gpt-4"):
            super().__init__(api_key)
            self.client = OpenAI(api_key=api_key)
            self.model_name = model_name
            print(f"🤖 OpenAI Agent ready ({model_name})")
        
        async def generate_response(self, prompt: str) -> str:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1500
            )
            return response.choices[0].message.content


class RobustMultiLLMSystem:
    """Main application with robust multi-LLM support"""
    
    def __init__(self, config_file: str = None):
        if config_file is None:
            config_file = os.path.join(project_root, "config", "config.env")
        
        print(f"🔍 Loading config from: {config_file}")
        load_dotenv(config_file)
        
        # Initialize agents
        self.agents = {}
        
        if os.getenv("GEMINI_API_KEY"):
            try:
                self.agents["gemini"] = GeminiAgent(os.getenv("GEMINI_API_KEY"))
                print("✅ Gemini agent ready")
            except Exception as e:
                print(f"❌ Gemini failed: {e}")
        
        if os.getenv("OPENAI_API_KEY") and OPENAI_AVAILABLE:
            try:
                self.agents["openai"] = OpenAIAgent(os.getenv("OPENAI_API_KEY"))
                print("✅ OpenAI agent ready")
            except Exception as e:
                print(f"❌ OpenAI failed: {e}")
        
        if not self.agents:
            raise ValueError("No agents could be initialized")
        
        print(f"\n🚀 Robust Multi-LLM System Ready!")
        print(f"Available: {list(self.agents.keys())}")
    
    async def interactive_session(self):
        """Interactive session with robust agents"""
        print("\n" + "="*70)
        print("🤖 ROBUST MULTI-LLM PROGRAMMING CONCEPTS AGENT")
        print("Agents that never abandon tools and systematically self-correct!")
        print(f"Available: {', '.join(self.agents.keys())}")
        print("Commands: 'switch [llm]', 'compare [query]', 'memory', 'quit'")
        print("="*70)
        
        current_llm = list(self.agents.keys())[0]
        
        while True:
            try:
                user_input = input(f"\n💬 [{current_llm.upper()}] You: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("👋 Goodbye!")
                    break
                
                elif user_input.startswith('switch '):
                    new_llm = user_input.split(' ', 1)[1].lower()
                    if new_llm in self.agents:
                        current_llm = new_llm
                        print(f"🔄 Switched to {new_llm.upper()}")
                    else:
                        print(f"❌ {new_llm} not available. Options: {list(self.agents.keys())}")
                    continue
                
                elif user_input.startswith('compare '):
                    query = user_input.split(' ', 1)[1]
                    await self._compare_llms(query)
                    continue
                
                elif user_input == 'memory':
                    stats = self.agents[current_llm].memory.successful_calls
                    print(f"💾 Memory: {len(stats)} successful patterns learned")
                    continue
                
                elif user_input == 'help':
                    self._show_help()
                    continue
                
                elif not user_input:
                    continue
                
                # Process with current agent
                print(f"\n🤖 [{current_llm.upper()}] Processing with robust error recovery...")
                response = await self.agents[current_llm].process_query(user_input)
                print(f"\n🤖 [{current_llm.upper()}]: {response}")
                
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
    
    async def _compare_llms(self, query: str):
        """Compare LLM responses"""
        print(f"\n🔄 Comparing robust agents on: '{query}'")
        print("="*60)
        
        for llm_name, agent in self.agents.items():
            print(f"\n🤖 {llm_name.upper()} Response:")
            print("-" * 30)
            try:
                response = await agent.process_query(query)
                print(response[:500] + "..." if len(response) > 500 else response)
            except Exception as e:
                print(f"❌ {llm_name} failed: {e}")
            print()
    
    def _show_help(self):
        """Show help"""
        print("\n📚 Commands:")
        print("   switch [llm] - Switch between agents")
        print("   compare [query] - Test same query on all agents")
        print("   memory - Show learned patterns")
        print("   quit - Exit")
        print("\n💡 These agents never abandon tools and learn from every interaction!")


async def main():
    """Main entry point"""
    try:
        system = RobustMultiLLMSystem()
        await system.interactive_session()
    except Exception as e:
        print(f"❌ System failed to start: {e}")


if __name__ == "__main__":
    asyncio.run(main())
