#!/usr/bin/env python3
"""
Master Programming Orchestrator MCP Server
Part 2: Spawns and coordinates book-specific micro servers based on intelligent routing
UPDATED: Now includes CSAPP (Computer Systems) server support
"""

import json
import logging
import subprocess
import sys
import time
import os
import signal
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Add current directory to Python path
sys.path.append('.')
sys.path.append('scripts')

from mcp.server.fastmcp import FastMCP

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("master-orchestrator-mcp")

# Initialize FastMCP server
mcp = FastMCP("master-orchestrator")

# Import topic detection from Part 1, with robust error handling
try:
    from topic_detection_mcp import calculate_topic_scores, get_recommendations, BOOK_CONFIGS, classify_query_intent
    logger.info("✅ Successfully imported topic detection from Part 1")
except (ImportError, SyntaxError) as e:
    logger.error(f"❌ Could not import from 'topic_detection_mcp.py': {e}")
    logger.warning("⚠️ Using fallback topic detection and intent classification.")
    
    # Fallback basic detection for BOOK_CONFIGS
    BOOK_CONFIGS = {
        "kernighan_ritchie": {"name": "K&R C Programming"},
        "unix_env": {"name": "UNIX Environment"},
        "linkers_loaders": {"name": "Linkers & Loaders"},
        "os_three_pieces": {"name": "Operating Systems"},
        "expert_c_programming": {"name": "Expert C Programming"},
        "csapp_2016": {"name": "Computer Systems (CSAPP)"},
        "posix_manpages": {"name": "POSIX Manpages"}
    }

    # Fallback functions to allow the server to run
    def calculate_topic_scores(question: str) -> Dict:
        """Fallback topic score calculator."""
        logger.warning("Using fallback 'calculate_topic_scores'")
        return {book: 0.0 for book in BOOK_CONFIGS.keys()}

    def get_recommendations(scores: Dict) -> List:
        """Fallback recommendation generator."""
        logger.warning("Using fallback 'get_recommendations'")
        return [{"book": "kernighan_ritchie", "confidence": "low", "reasoning": "Fallback due to import error"}]

    def classify_query_intent(question: str) -> str:
        """Fallback intent classifier."""
        logger.warning("Using fallback 'classify_query_intent'")
        if any(keyword in question.lower() for keyword in ["man", "usage", "parameters", "arguments", "return value"]):
            return "reference"
        return "conceptual"

# Global state for active servers
ACTIVE_SERVERS: Dict[str, Dict] = {}  # {server_name: {"process": subprocess, "port": int, "started_at": timestamp}}
BASE_PORT = 8100  # Starting port for micro servers
PROJECT_ROOT = Path(__file__).resolve().parents[2] # More robust way to find project root

# Book server configurations
BOOK_SERVER_CONFIGS = {
    "kernighan_ritchie": {
        "script_path": "scripts/book_servers/kernighan_ritchie_server.py",
        "port": 8101,
        "description": "K&R C Programming concepts server"
    },
    "unix_env": {
        "script_path": "scripts/book_servers/unix_env_server.py",
        "port": 8102,
        "description": "UNIX Environment programming server"
    },
    "linkers_loaders": {
        "script_path": "scripts/book_servers/linkers_loaders_server.py",
        "port": 8103,
        "description": "Linkers & Loaders concepts server"
    },
    "os_three_pieces": {
        "script_path": "scripts/book_servers/os_three_pieces_server.py",
        "port": 8104,
        "description": "Operating Systems concepts server"
    },
    "expert_c_programming": {
        "script_path": "scripts/book_servers/expert_c_server.py",
        "port": 8105,
        "description": "Expert C Programming techniques server"
    },
    "csapp_2016": {
        "script_path": "scripts/book_servers/csapp_server.py",
        "port": 8106,
        "description": "Computer Systems & Architecture concepts server"
    },
    "posix_manpages": {
    "script_path": "scripts/book_servers/posix_manpages_server.py",
    "port": 8107,
    "description": "POSIX system call reference server"
    }
}

def cleanup_on_exit():
    """Clean up all active servers on exit"""
    global ACTIVE_SERVERS
    
    if ACTIVE_SERVERS:
        logger.info("🧹 Cleaning up active servers...")
        for server_name, server_info in ACTIVE_SERVERS.items():
            try:
                process = server_info["process"]
                if process.poll() is None:  # Still running
                    process.terminate()
                    logger.info(f"🛑 Terminated {server_name}")
            except Exception as e:
                logger.error(f"Error terminating {server_name}: {e}")
        
        ACTIVE_SERVERS.clear()

# Register cleanup function
import atexit
atexit.register(cleanup_on_exit)

@mcp.tool()
def analyze_and_route_question(programming_question: str) -> Dict:
    """
    Analyze a programming question and route to appropriate book servers
    
    Args:
        programming_question: The user's programming or systems question
        
    Returns:
        Dictionary with routing recommendations and spawned servers
    """
    try:
        # Use topic detection from Part 1
        topic_scores = calculate_topic_scores(programming_question)
        recommendations = get_recommendations(topic_scores)
        
        logger.info(f"📊 Question analysis: {programming_question[:50]}...")
        logger.info(f"🎯 Top recommendations: {[r['book'] for r in recommendations[:3]]}")
        
        # Intent-aware routing
        intent = classify_query_intent(programming_question)
        spawned_servers = []
        routing_details = []
        
        # Prioritize POSIX for API reference queries
        if intent == "reference" and any(rec['book'] == 'posix_manpages' for rec in recommendations[:3]):
            spawn_result = spawn_specific_server("posix_manpages")
            if spawn_result['success']:
                spawned_servers.append({
                    "server": "posix_manpages",
                    "port": 8107,
                    "confidence": "high",
                    "description": "POSIX system call reference"
                })
        
        # Add top book recommendations (limit to 2 total servers)
        for rec in recommendations[:2]:
            if len(spawned_servers) >= 2:
                break
            book_name = rec['book']
            confidence = rec['confidence']
            
            if book_name in BOOK_SERVER_CONFIGS and book_name != 'posix_manpages':
                spawn_result = spawn_specific_server(book_name)
                if spawn_result['success']:
                    spawned_servers.append({
                        "server": book_name,
                        "port": BOOK_SERVER_CONFIGS[book_name]["port"],
                        "confidence": confidence,
                        "description": BOOK_SERVER_CONFIGS[book_name]["description"]
                    })
                
                routing_details.append({
                    "book": book_name,
                    "confidence": confidence,
                    "reasoning": rec.get('reasoning', 'Topic match detected'),
                    "server_spawned": spawn_result['success']
                })
        
        return {
            "question": programming_question,
            "analysis": {
                "topic_scores": topic_scores,
                "routing_recommendations": routing_details
            },
            "spawned_servers": spawned_servers,
            "total_active_servers": len(ACTIVE_SERVERS),
            "status": "success",
            "next_steps": f"Query the spawned servers on ports: {[s['port'] for s in spawned_servers]}"
        }
        
    except Exception as e:
        logger.error(f"Error in routing analysis: {e}", exc_info=True)
        return {
            "question": programming_question,
            "error": str(e),
            "status": "error",
            "fallback": "Use main programming concepts server for general queries"
        }

@mcp.tool()
def spawn_specific_server(book_name: str) -> Dict:
    """
    Manually spawn a specific book server
    
    Args:
        book_name: Name of the book server to spawn (e.g., 'csapp_2016', 'kernighan_ritchie')
        
    Returns:
        Dictionary with spawn result and server details
    """
    global ACTIVE_SERVERS
    
    if book_name not in BOOK_SERVER_CONFIGS:
        return {
            "success": False,
            "error": f"Unknown book server: {book_name}",
            "available_servers": list(BOOK_SERVER_CONFIGS.keys())
        }
    
    # Check if already running
    if book_name in ACTIVE_SERVERS:
        server_info = ACTIVE_SERVERS[book_name]
        if server_info["process"].poll() is None:  # Still running
            return {
                "success": True,
                "message": f"{book_name} server already running",
                "port": server_info["port"],
                "started_at": server_info["started_at"],
                "status": "already_active"
            }
        else:
            # Process died, remove from active list
            logger.warning(f"Found dead server process for {book_name}. Cleaning up.")
            del ACTIVE_SERVERS[book_name]
    
    # Spawn new server
    config = BOOK_SERVER_CONFIGS[book_name]
    script_path = os.path.join(PROJECT_ROOT, config["script_path"])
    
    if not os.path.exists(script_path):
        return {
            "success": False,
            "error": f"Server script not found: {script_path}",
            "config": config
        }
    
    try:
        # Start the server process
        process = subprocess.Popen(
            [sys.executable, script_path],
            cwd=PROJECT_ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True, # Decode stdout/stderr as text
            env=os.environ.copy()
        )
        
        # Give it a moment to start
        time.sleep(2)
        
        # Check if it started successfully
        if process.poll() is None:  # Still running
            start_time = time.time()
            ACTIVE_SERVERS[book_name] = {
                "process": process,
                "port": config["port"],
                "started_at": start_time,
                "description": config["description"]
            }
            
            logger.info(f"🚀 Successfully spawned {book_name} server on port {config['port']}")
            
            return {
                "success": True,
                "server": book_name,
                "port": config["port"],
                "description": config["description"],
                "started_at": start_time,
                "status": "newly_spawned"
            }
        else:
            # Process died immediately
            stdout, stderr = process.communicate()
            logger.error(f"Failed to spawn {book_name}. Process died immediately.")
            return {
                "success": False,
                "error": f"Server process for {book_name} died immediately",
                "stdout": stdout,
                "stderr": stderr,
                "config": config
            }
            
    except Exception as e:
        logger.error(f"Error spawning {book_name} server: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "config": config
        }

@mcp.tool()
def list_active_servers() -> Dict:
    """
    List all currently active book servers
    
    Returns:
        Dictionary with active server information
    """
    global ACTIVE_SERVERS
    
    active_list = []
    dead_servers = []
    
    for server_name, server_info in list(ACTIVE_SERVERS.items()):
        process = server_info["process"]
        
        if process.poll() is None:  # Still running
            uptime = time.time() - server_info["started_at"]
            active_list.append({
                "server": server_name,
                "port": server_info["port"],
                "description": server_info["description"],
                "uptime_seconds": round(uptime, 2),
                "status": "running"
            })
        else:
            # Process died
            dead_servers.append(server_name)
            del ACTIVE_SERVERS[server_name]
    
    return {
        "active_servers": active_list,
        "total_active": len(active_list),
        "dead_servers_cleaned": dead_servers,
        "available_servers": list(BOOK_SERVER_CONFIGS.keys()),
        "server_descriptions": {name: config["description"] for name, config in BOOK_SERVER_CONFIGS.items()}
    }

@mcp.tool()
def kill_specific_server(book_name: str) -> Dict:
    """
    Stop a specific book server
    
    Args:
        book_name: Name of the server to stop
        
    Returns:
        Dictionary with termination result
    """
    global ACTIVE_SERVERS
    
    if book_name not in ACTIVE_SERVERS:
        return {
            "success": False,
            "message": f"Server {book_name} is not currently active",
            "active_servers": list(ACTIVE_SERVERS.keys())
        }
    
    try:
        server_info = ACTIVE_SERVERS[book_name]
        process = server_info["process"]
        
        if process.poll() is None:  # Still running
            process.terminate()
            time.sleep(1)  # Give it time to terminate gracefully
            
            if process.poll() is None:  # Still running, force kill
                process.kill()
                time.sleep(0.5)
        
        del ACTIVE_SERVERS[book_name]
        
        logger.info(f"🛑 Terminated {book_name} server")
        
        return {
            "success": True,
            "message": f"Successfully terminated {book_name} server",
            "port_freed": server_info["port"],
            "remaining_active": len(ACTIVE_SERVERS)
        }
        
    except Exception as e:
        logger.error(f"Error killing {book_name}: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "server": book_name
        }

@mcp.tool()
def cleanup_unused_servers() -> Dict:
    """
    Clean up all active servers (useful for resource management)
    
    Returns:
        Dictionary with cleanup results
    """
    global ACTIVE_SERVERS
    
    if not ACTIVE_SERVERS:
        return {
            "message": "No active servers to clean up",
            "servers_terminated": 0
        }
    
    terminated_servers = []
    errors = []
    
    for server_name in list(ACTIVE_SERVERS.keys()):
        result = kill_specific_server(server_name)
        if result["success"]:
            terminated_servers.append(server_name)
        else:
            errors.append(f"{server_name}: {result.get('error', 'Unknown error')}")
    
    return {
        "servers_terminated": terminated_servers,
        "total_terminated": len(terminated_servers),
        "errors": errors,
        "remaining_active": len(ACTIVE_SERVERS),
        "message": f"Cleanup complete. Terminated {len(terminated_servers)} servers."
    }

@mcp.tool()
def get_orchestrator_status() -> Dict:
    """
    Get comprehensive status of the orchestrator and all managed servers
    
    Returns:
        Complete system status information
    """
    global ACTIVE_SERVERS
    
    # Clean up dead processes by calling list_active_servers
    status_report = list_active_servers()
    
    # Calculate total available ports
    all_ports = [config["port"] for config in BOOK_SERVER_CONFIGS.values()]
    used_ports = [server["port"] for server in status_report["active_servers"]]
    free_ports = [port for port in all_ports if port not in used_ports]
    
    return {
        "orchestrator_status": "running",
        "total_managed_books": len(BOOK_SERVER_CONFIGS),
        "active_servers": len(status_report["active_servers"]),
        "dead_servers_cleaned_now": status_report["dead_servers_cleaned"],
        "port_management": {
            "base_port": BASE_PORT,
            "total_ports": len(all_ports),
            "used_ports": used_ports,
            "free_ports": free_ports
        },
        "book_servers": {
            name: {
                "description": config["description"],
                "port": config["port"],
                "status": "active" if config["port"] in used_ports else "inactive"
            }
            for name, config in BOOK_SERVER_CONFIGS.items()
        },
        "project_root": str(PROJECT_ROOT),
        "supported_books": list(BOOK_SERVER_CONFIGS.keys())
    }

if __name__ == "__main__":
    logger.info("🎭 Starting Master Programming Orchestrator")
    logger.info(f"📚 Managing {len(BOOK_SERVER_CONFIGS)} book servers")
    logger.info(f"🌐 Port range: {BASE_PORT+1}-{BASE_PORT+len(BOOK_SERVER_CONFIGS)}")
    
    # Log available servers including CSAPP
    for book, config in BOOK_SERVER_CONFIGS.items():
        logger.info(f"  📖 {book}: {config['description']} (port {config['port']})")
    
    mcp.run()
