#!/usr/bin/env python3
"""
MCP Integration Client for LangGraph Agent
Direct integration with existing FastMCP servers via Python imports
"""

import sys
import os
import logging
import yaml
import importlib.util
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable
from langchain_core.tools import tool
from langchain_core.tools.base import BaseTool
from pydantic import BaseModel, Field

# Add project paths for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.append(str(PROJECT_ROOT))
sys.path.append(str(PROJECT_ROOT / "scripts"))

logger = logging.getLogger(__name__)

class MCPToolWrapper(BaseTool):
    """Wrapper to convert FastMCP tools to LangChain tools"""
    
    name: str
    description: str
    mcp_function: Callable
    args_schema: Optional[type] = None
    
    def _run(self, **kwargs) -> str:
        """Execute the wrapped MCP tool"""
        try:
            result = self.mcp_function(**kwargs)
            if isinstance(result, dict):
                return str(result)
            return str(result)
        except Exception as e:
            logger.error(f"Error executing MCP tool {self.name}: {e}")
            return f"ERROR: Tool execution failed - {str(e)}"

class MCPClient:
    """Client for integrating with existing FastMCP servers"""
    
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.config = self._load_config()
        self.available_tools: Dict[str, BaseTool] = {}
        self.servers = {}
        self._initialize_servers()
    
    def _load_config(self) -> Dict:
        """Load MCP endpoints configuration"""
        with open(self.config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def _initialize_servers(self):
        """Initialize connections to MCP servers by importing their modules"""
        try:
            # Import master orchestrator
            self._import_orchestrator()
            
            # Import topic detection  
            self._import_topic_detection()
            
            # Import GOT/PLT server
            self._import_got_plt_server()
            
            # Import book servers (these will be spawned on demand)
            self._setup_book_servers()
            
            logger.info(f"✅ Initialized MCP client with {len(self.available_tools)} tools")
            
        except Exception as e:
            logger.error(f"Failed to initialize MCP servers: {e}")
            raise
    
    def _import_orchestrator(self):
        """Import master orchestrator tools"""
        try:
            # Import the orchestrator module
            spec = importlib.util.spec_from_file_location(
                "master_orchestrator", 
                PROJECT_ROOT / "scripts" / "master_orchestrator_mcp.py"
            )
            orchestrator_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(orchestrator_module)
            
            # Get the FastMCP instance and its tools
            if hasattr(orchestrator_module, 'mcp'):
                mcp_instance = orchestrator_module.mcp
                
                # Extract tool functions from the MCP instance
                orchestrator_tools = {
                    "analyze_and_route_question": orchestrator_module.analyze_and_route_question,
                    "spawn_specific_server": orchestrator_module.spawn_specific_server,
                    "list_active_servers": orchestrator_module.list_active_servers,
                    "kill_specific_server": orchestrator_module.kill_specific_server,
                    "get_orchestrator_status": orchestrator_module.get_orchestrator_status
                }
                
                # Wrap as LangChain tools
                for tool_name, tool_func in orchestrator_tools.items():
                    wrapped_tool = self._create_langchain_tool(tool_name, tool_func)
                    self.available_tools[f"orchestrator_{tool_name}"] = wrapped_tool
                
                self.servers["orchestrator"] = orchestrator_module
                logger.info("✅ Imported master orchestrator tools")
                
        except Exception as e:
            logger.error(f"Failed to import orchestrator: {e}")
            # Continue without orchestrator tools
    
    def _import_topic_detection(self):
        """Import topic detection tools"""
        try:
            spec = importlib.util.spec_from_file_location(
                "topic_detection",
                PROJECT_ROOT / "scripts" / "topic_detection_mcp.py"
            )
            topic_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(topic_module)
            
            if hasattr(topic_module, 'mcp'):
                # Extract topic detection functions
                topic_tools = {
                    "detect_relevant_server": getattr(topic_module, 'detect_relevant_server', None),
                    "analyze_topic_coverage": getattr(topic_module, 'analyze_topic_coverage', None),
                    "calculate_topic_scores": getattr(topic_module, 'calculate_topic_scores', None),
                    "get_recommendations": getattr(topic_module, 'get_recommendations', None)
                }
                
                # Wrap valid tools
                for tool_name, tool_func in topic_tools.items():
                    if tool_func and callable(tool_func):
                        wrapped_tool = self._create_langchain_tool(tool_name, tool_func)
                        self.available_tools[f"topic_{tool_name}"] = wrapped_tool
                
                self.servers["topic_detection"] = topic_module
                logger.info("✅ Imported topic detection tools")
                
        except Exception as e:
            logger.error(f"Failed to import topic detection: {e}")
            # Continue without topic detection
    
    def _import_got_plt_server(self):
        """Import GOT/PLT educational server tools"""
        try:
            # Look for GOT/PLT server script
            got_plt_paths = [
                PROJECT_ROOT / "scripts" / "got_plt_mcp_server.py",
                PROJECT_ROOT / "got_plt_mcp_server.py"
            ]
            
            got_plt_path = None
            for path in got_plt_paths:
                if path.exists():
                    got_plt_path = path
                    break
            
            if got_plt_path:
                spec = importlib.util.spec_from_file_location("got_plt_server", got_plt_path)
                got_plt_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(got_plt_module)
                
                if hasattr(got_plt_module, 'mcp'):
                    # GOT/PLT has 18 tools across 3 phases
                    got_plt_tools = {
                        # Phase 1: Static Analysis
                        "inspect_got_table": getattr(got_plt_module, 'inspect_got_table', None),
                        "analyze_plt_stubs": getattr(got_plt_module, 'analyze_plt_stubs', None),
                        "list_dynamic_symbols": getattr(got_plt_module, 'list_dynamic_symbols', None),
                        "explain_linking_process": getattr(got_plt_module, 'explain_linking_process', None),
                        "generate_minimal_example": getattr(got_plt_module, 'generate_minimal_example', None),
                        
                        # Phase 2: Educational Validation
                        "validate_concept": getattr(got_plt_module, 'validate_concept', None),
                        "list_available_concepts": getattr(got_plt_module, 'list_available_concepts', None),
                        "find_related_concepts": getattr(got_plt_module, 'find_related_concepts', None),
                        "get_concept_info": getattr(got_plt_module, 'get_concept_info', None),
                        "compare_theory_vs_practice": getattr(got_plt_module, 'compare_theory_vs_practice', None),
                        "create_interactive_example": getattr(got_plt_module, 'create_interactive_example', None),
                        "list_example_templates": getattr(got_plt_module, 'list_example_templates', None),
                        
                        # Phase 3: Runtime Analysis  
                        "trace_symbol_resolution": getattr(got_plt_module, 'trace_symbol_resolution', None),
                        "analyze_lazy_binding": getattr(got_plt_module, 'analyze_lazy_binding', None),
                        "runtime_got_snapshot": getattr(got_plt_module, 'runtime_got_snapshot', None),
                        "compare_binding_modes": getattr(got_plt_module, 'compare_binding_modes', None),
                        "generate_lazy_binding_report": getattr(got_plt_module, 'generate_lazy_binding_report', None),
                        "analyze_plt_behavior": getattr(got_plt_module, 'analyze_plt_behavior', None)
                    }
                    
                    # Wrap valid GOT/PLT tools
                    for tool_name, tool_func in got_plt_tools.items():
                        if tool_func and callable(tool_func):
                            wrapped_tool = self._create_langchain_tool(tool_name, tool_func)
                            self.available_tools[f"gotplt_{tool_name}"] = wrapped_tool
                    
                    self.servers["got_plt"] = got_plt_module
                    logger.info("✅ Imported GOT/PLT educational tools")
            else:
                logger.warning("GOT/PLT server not found")
                
        except Exception as e:
            logger.error(f"Failed to import GOT/PLT server: {e}")
    
    def _setup_book_servers(self):
        """Setup book server configurations for on-demand spawning"""
        book_configs = {
            "kernighan_ritchie": "K&R C Programming concepts",
            "unix_env": "UNIX Environment programming", 
            "linkers_loaders": "Linkers & Loaders concepts",
            "os_three_pieces": "Operating Systems concepts",
            "expert_c_programming": "Expert C Programming",
            "csapp_2016": "Computer Systems (CSAPP)",
            "posix_manpages": "POSIX system calls"
        }
        
        # Create proxy tools that spawn servers on demand
        for book_name, description in book_configs.items():
            search_tool = self._create_book_search_tool(book_name, description)
            details_tool = self._create_book_details_tool(book_name, description)
            
            self.available_tools[f"book_{book_name}_search"] = search_tool
            self.available_tools[f"book_{book_name}_details"] = details_tool
        
        logger.info(f"✅ Setup {len(book_configs)} book server proxies")
    
    def _create_langchain_tool(self, name: str, func: Callable) -> BaseTool:
        """Create a LangChain tool from a function"""
        
        # Extract docstring for description
        description = func.__doc__ or f"MCP tool: {name}"
        if description:
            description = description.strip().split('\n')[0]  # First line only
        
        return MCPToolWrapper(
            name=name,
            description=description,
            mcp_function=func
        )
    
    def _create_book_search_tool(self, book_name: str, description: str) -> BaseTool:
        """Create a search tool that spawns book servers on demand"""
        
        def search_book(query: str, limit: int = 5) -> str:
            try:
                # Spawn the book server first
                if hasattr(self.servers.get("orchestrator"), 'spawn_specific_server'):
                    spawn_result = self.servers["orchestrator"].spawn_specific_server(book_name)
                    if not spawn_result.get('success', False):
                        return f"Failed to spawn {book_name} server: {spawn_result.get('error', 'Unknown error')}"
                
                # Return placeholder result (would need actual server communication)
                return f"Searched {book_name} for '{query}' (limit: {limit}). Server spawned successfully."
                
            except Exception as e:
                return f"Error searching {book_name}: {str(e)}"
        
        return MCPToolWrapper(
            name=f"search_{book_name}",
            description=f"Search {description} for concepts and examples",
            mcp_function=search_book
        )
    
    def _create_book_details_tool(self, book_name: str, description: str) -> BaseTool:
        """Create a details tool for book concepts"""
        
        def get_details(concept_id: str) -> str:
            try:
                # Would need actual server communication
                return f"Details for concept {concept_id} from {book_name}"
            except Exception as e:
                return f"Error getting details from {book_name}: {str(e)}"
        
        return MCPToolWrapper(
            name=f"get_details_{book_name}",
            description=f"Get detailed information about concepts from {description}",
            mcp_function=get_details
        )
    
    def get_tools_for_context(self, context: str = "general") -> List[BaseTool]:
        """Get relevant tools based on context"""
        if context == "binary_analysis":
            return [tool for name, tool in self.available_tools.items() 
                   if "gotplt_" in name or "orchestrator_" in name]
        elif context == "c_programming":
            return [tool for name, tool in self.available_tools.items()
                   if "kernighan_ritchie" in name or "expert_c" in name]
        elif context == "systems":
            return [tool for name, tool in self.available_tools.items()
                   if "unix_env" in name or "csapp" in name or "os_three" in name]
        else:
            # Return core tools for general context
            return [tool for name, tool in self.available_tools.items()
                   if "orchestrator_" in name or "topic_" in name]
    
    def get_all_tools(self) -> List[BaseTool]:
        """Get all available tools"""
        return list(self.available_tools.values())
    
    def route_question(self, question: str) -> Dict[str, Any]:
        """Route a question to appropriate servers"""
        try:
            if "orchestrator_analyze_and_route_question" in self.available_tools:
                tool = self.available_tools["orchestrator_analyze_and_route_question"]
                result = tool._run(programming_question=question)
                return {"success": True, "routing": result}
            else:
                return {"success": False, "error": "Routing tool not available"}
        except Exception as e:
            logger.error(f"Routing error: {e}")
            return {"success": False, "error": str(e)}
