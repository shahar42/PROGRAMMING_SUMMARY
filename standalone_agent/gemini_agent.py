#!/usr/bin/env python3
"""
Standalone Gemini-Powered Programming Concepts Agent
A parallel system to your existing MCP servers - completely independent

This agent system uses Google's Gemini API to reason and orchestrate
your existing programming concept tools autonomously.
"""

import os
import sys
import json
import asyncio
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from dotenv import load_dotenv
import google.generativeai as genai

# Add your existing paths (reuse without modification)
import os
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
scripts_path = os.path.join(project_root, 'scripts')

# Add both project root AND scripts directory to path
sys.path.append(project_root)  # For mcp_server.py
sys.path.append(scripts_path)  # For specialized servers

print(f"🔍 Looking for mcp_server.py in: {project_root}")
print(f"🔍 Project root files: {[f for f in os.listdir(project_root) if f.endswith('.py')] if os.path.exists(project_root) else 'Directory not found'}")
print(f"🔍 Looking for specialized tools in: {scripts_path}")
print(f"🔍 Scripts files: {os.listdir(scripts_path) if os.path.exists(scripts_path) else 'Directory not found'}")

# Import your existing MCP server functions (reuse as tools)
try:
    from mcp_server import (
        search_concepts, get_concept_details, compare_concepts,
        generate_study_path, explain_my_code, synthesize_concepts,
        generate_custom_tutorial, create_best_practices_guide,
        search_by_book, find_advanced_concepts
    )
    print("✅ Successfully imported main concept tools")
except ImportError as e:
    print(f"❌ Could not import main tools: {e}")
    print("Make sure your existing mcp_server.py is available")

# Import specialized tools if available
try:
    educational_path = os.path.join(scripts_path, 'educational')
    sys.path.append(educational_path)
    from concept_validator import ConceptValidator
    from example_generator import EnhancedExampleGenerator
    print("✅ Successfully imported educational tools")
    EDUCATIONAL_TOOLS_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Educational tools not available: {e}")
    EDUCATIONAL_TOOLS_AVAILABLE = False


@dataclass
class ToolDefinition:
    """Define a tool that the agent can use"""
    name: str
    description: str
    parameters: Dict[str, Any]
    function: callable


class GeminiReasoningAgent:
    """
    The core reasoning agent powered by Gemini
    
    This agent receives queries, analyzes them, and decides which tools to use
    in what order to accomplish the user's goals.
    """
    
    def __init__(self, api_key: str, model_name: str = "gemini-1.5-pro"):
        """Initialize the Gemini reasoning agent"""
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)
        self.tools = self._initialize_tools()
        self.conversation_history = []
        
        print(f"🧠 Gemini Reasoning Agent initialized with {len(self.tools)} tools")
    
    def _initialize_tools(self) -> List[ToolDefinition]:
        """Define all available tools for the agent"""
        tools = [
            ToolDefinition(
                name="search_concepts",
                description="Search across all programming concept books for specific topics",
                parameters={
                    "query": "str - search query for programming concepts",
                    "limit": "int - maximum results to return (default: 10)"
                },
                function=search_concepts
            ),
            ToolDefinition(
                name="get_concept_details", 
                description="Get detailed information about a specific programming concept",
                parameters={
                    "concept_id": "str - the ID of the concept to retrieve"
                },
                function=get_concept_details
            ),
            ToolDefinition(
                name="compare_concepts",
                description="Compare two programming concepts side-by-side",
                parameters={
                    "concept1_id": "str - ID of first concept",
                    "concept2_id": "str - ID of second concept"
                },
                function=compare_concepts
            ),
            ToolDefinition(
                name="generate_study_path",
                description="Create ordered learning sequence for a programming goal",
                parameters={
                    "goal": "str - learning objective (e.g., 'learn C programming')"
                },
                function=generate_study_path
            ),
            ToolDefinition(
                name="explain_my_code",
                description="Analyze user's code using the programming knowledge base",
                parameters={
                    "code_snippet": "str - the code to analyze",
                    "language": "str - programming language (default: 'C')"
                },
                function=explain_my_code
            ),
            ToolDefinition(
                name="synthesize_concepts",
                description="AI-powered synthesis combining insights from multiple books",
                parameters={
                    "topic": "str - topic to synthesize",
                    "max_sources": "int - maximum number of sources to use (default: 5)"
                },
                function=synthesize_concepts
            ),
            ToolDefinition(
                name="generate_custom_tutorial",
                description="Create personalized tutorials merging related concepts",
                parameters={
                    "topic": "str - tutorial topic",
                    "skill_level": "str - 'beginner', 'intermediate', or 'advanced'"
                },
                function=generate_custom_tutorial
            ),
            ToolDefinition(
                name="create_best_practices_guide",
                description="Generate best practices by analyzing patterns across all sources",
                parameters={
                    "topic": "str - topic for best practices guide"
                },
                function=create_best_practices_guide
            ),
            ToolDefinition(
                name="search_by_book",
                description="Search concepts within a specific book",
                parameters={
                    "book_name": "str - name of book (kernighan_ritchie, unix_env, linkers_loaders, os_three_pieces, expert_c_programming, csapp_2016)",
                    "query": "str - search query within the book (optional)"
                },
                function=search_by_book
            ),
            ToolDefinition(
                name="find_advanced_concepts", 
                description="Find advanced concepts related to a specific topic",
                parameters={
                    "topic": "str - general programming topic (e.g., 'memory', 'linking')",
                    "threshold": "int - difficulty threshold (default: 2)"
                },
                function=find_advanced_concepts
            )
        ]
        
        # Add educational tools if available
        if EDUCATIONAL_TOOLS_AVAILABLE:
            validator = ConceptValidator()
            generator = EnhancedExampleGenerator()
            
            tools.extend([
                ToolDefinition(
                    name="validate_concept",
                    description="Test theoretical concept against real binary files",
                    parameters={
                        "concept_name": "str - name of concept to validate",
                        "binary_path": "str - path to binary file (optional)"
                    },
                    function=validator.validate_concept
                ),
                ToolDefinition(
                    name="create_interactive_example",
                    description="Create complete, compilable example project for a concept",
                    parameters={
                        "concept_name": "str - concept to create example for",
                        "output_directory": "str - where to save example (optional)"
                    },
                    function=generator.generate_concept_example
                )
            ])
        
        return tools
    
    def _create_system_prompt(self) -> str:
        """Create the system prompt that defines the agent's behavior"""
        tools_description = "\n".join([
            f"- {tool.name}({', '.join([f'{k}: {v}' for k, v in tool.parameters.items()])}): {tool.description}"
            for tool in self.tools
        ])
        
        return f"""You are an expert Programming Concepts Agent with access to a comprehensive knowledge base from classic computer science books including:
- The C Programming Language (K&R)
- The UNIX Programming Environment  
- Linkers and Loaders
- Operating Systems Concepts
- Expert C Programming
- Computer Systems: A Programmer's Perspective (CSAPP)

Your role is to help users understand programming concepts, debug code, create learning paths, and bridge theory with practice.

AVAILABLE TOOLS:
{tools_description}

CRITICAL TOOL CALLING REQUIREMENTS:
- Use EXACT parameter names as shown above
- For search_concepts: use "query" and "limit" parameters
- For get_concept_details: use "concept_id" parameter  
- For compare_concepts: use "concept1_id" and "concept2_id" parameters
- For generate_study_path: use "goal" parameter
- For explain_my_code: use "code_snippet" and "language" parameters

REASONING APPROACH:
1. Analyze the user's question carefully
2. Determine which tools would be most helpful
3. Plan a sequence of tool calls if needed
4. Execute the plan step by step
5. Synthesize results into a comprehensive answer

TOOL CALLING FORMAT:
When you need to use a tool, respond with:
TOOL_CALL: tool_name
PARAMETERS: {{"param1": "value1", "param2": "value2"}}

EXAMPLE TOOL CALLS:
TOOL_CALL: search_concepts
PARAMETERS: {{"query": "memory management", "limit": 5}}

TOOL_CALL: compare_concepts  
PARAMETERS: {{"concept1_id": "kernighan_ritchie_concept_038", "concept2_id": "kernighan_ritchie_concept_039"}}

You can make multiple tool calls in sequence. After each tool call, you'll receive the results and can decide on next steps.

Always explain your reasoning and provide educational context with your answers."""

    async def process_query(self, user_query: str) -> str:
        """
        Main method to process user queries
        The agent will reason about the query and use tools as needed
        """
        print(f"\n🤔 Processing query: {user_query}")
        
        # Add to conversation history
        self.conversation_history.append({"role": "user", "content": user_query})
        
        # Create the full prompt with system context and conversation history
        full_prompt = self._create_system_prompt()
        full_prompt += "\n\nCONVERSATION HISTORY:\n"
        for msg in self.conversation_history[-5:]:  # Last 5 messages for context
            full_prompt += f"{msg['role'].upper()}: {msg['content']}\n"
        
        full_prompt += f"\nUSER: {user_query}\n\nAGENT:"
        
        # Start the reasoning loop
        max_iterations = 10  # Increased for complex queries
        iteration = 0
        
        while iteration < max_iterations:
            try:
                response = self.model.generate_content(full_prompt)
                response_text = response.text
                
                print(f"🧠 Agent reasoning (iteration {iteration + 1}):")
                print(response_text[:200] + "..." if len(response_text) > 200 else response_text)
                
                # Check if agent wants to use a tool
                if "TOOL_CALL:" in response_text:
                    tool_result = await self._execute_tool_call(response_text)
                    full_prompt += f"\n{response_text}\n\nTOOL_RESULT: {tool_result}\n\nContinue your analysis:"
                    iteration += 1
                else:
                    # Agent is done reasoning, return final answer
                    self.conversation_history.append({"role": "assistant", "content": response_text})
                    return response_text
                    
            except Exception as e:
                error_msg = f"Error in reasoning loop: {e}"
                print(f"❌ {error_msg}")
                return error_msg
        
        return "Maximum reasoning iterations reached. Please try a simpler query."
    
    async def _execute_tool_call(self, response_text: str) -> str:
        """Extract and execute tool calls from agent response"""
        try:
            # Parse tool call from response
            lines = response_text.split('\n')
            tool_name = None
            parameters = {}
            
            for line in lines:
                if line.startswith("TOOL_CALL:"):
                    tool_name = line.replace("TOOL_CALL:", "").strip()
                elif line.startswith("PARAMETERS:"):
                    param_text = line.replace("PARAMETERS:", "").strip()
                    parameters = json.loads(param_text)
            
            if not tool_name:
                return "ERROR: No valid tool call found"
            
            # Find the tool
            tool = next((t for t in self.tools if t.name == tool_name), None)
            if not tool:
                return f"ERROR: Tool '{tool_name}' not found"
            
            print(f"🔧 Executing tool: {tool_name} with params: {parameters}")
            
            # Execute the tool
            if asyncio.iscoroutinefunction(tool.function):
                result = await tool.function(**parameters)
            else:
                result = tool.function(**parameters)
            
            return str(result)
            
        except Exception as e:
            return f"ERROR executing tool: {e}"


class StandaloneProgrammingAgent:
    """
    Main application class - your new standalone agent system
    This completely replaces the need for claude mcp for this functionality
    """
    
    def __init__(self, config_file: str = None):
        if config_file is None:
            # Look for config in project root
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            config_file = os.path.join(project_root, "config", "config.env")
        
        print(f"🔍 Looking for config at: {config_file}")
        if not os.path.exists(config_file):
            print(f"❌ Config file not found at {config_file}")
            # Try alternative locations
            alt_configs = [
                "config/config.env",
                "../config/config.env", 
                "../../config/config.env"
            ]
            for alt_config in alt_configs:
                if os.path.exists(alt_config):
                    config_file = alt_config
                    print(f"✅ Found config at: {config_file}")
                    break
        
        load_dotenv(config_file)
        
        api_key = os.getenv("GEMINI_API_KEY")
        print(f"🔑 API key loaded: {'Yes' if api_key else 'No'}")
        if api_key:
            print(f"🔑 API key length: {len(api_key)} characters")
        
        if not api_key:
            print(f"❌ GEMINI_API_KEY not found in {config_file}")
            print("Available environment variables:")
            for key in os.environ:
                if 'API' in key or 'KEY' in key:
                    print(f"   {key}=...")
            raise ValueError(f"GEMINI_API_KEY not found in {config_file}")
        
        self.agent = GeminiReasoningAgent(api_key)
        self.running = True
        
        print("🚀 Standalone Programming Agent System Initialized")
        print("This system runs completely independently of your MCP setup")
    
    async def interactive_session(self):
        """Run an interactive session with the agent"""
        print("\n" + "="*60)
        print("🤖 GEMINI PROGRAMMING CONCEPTS AGENT")
        print("Ask me anything about programming concepts!")
        print("Type 'quit' to exit, 'help' for examples")
        print("="*60)
        
        while self.running:
            try:
                user_input = input("\n💬 You: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("👋 Goodbye!")
                    break
                elif user_input.lower() == 'help':
                    self._show_help()
                    continue
                elif not user_input:
                    continue
                
                print("\n🤖 Agent: Processing your query...")
                response = await self.agent.process_query(user_input)
                print(f"\n🤖 Agent: {response}")
                
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
    
    def _show_help(self):
        """Show example queries"""
        examples = [
            "Search for concepts about memory management",
            "Compare malloc vs calloc functions", 
            "Generate a study path for learning C programming",
            "Explain this code: int *ptr = malloc(100);",
            "Create a tutorial about pointers for beginners",
            "Validate the concept of lazy binding against a real binary",
            "What are the best practices for error handling in C?"
        ]
        
        print("\n📚 Example queries you can try:")
        for i, example in enumerate(examples, 1):
            print(f"   {i}. {example}")


async def main():
    """Main entry point for the standalone agent system"""
    try:
        # Initialize the standalone agent (parallel to your MCP system)
        agent_system = StandaloneProgrammingAgent()
        
        # Run interactive session
        await agent_system.interactive_session()
        
    except Exception as e:
        print(f"❌ Failed to start agent system: {e}")
        print("Make sure your config/config.env has GEMINI_API_KEY set")


if __name__ == "__main__":
    asyncio.run(main())
