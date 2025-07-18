#!/usr/bin/env python3
"""
Master Programming Orchestrator MCP Server
Part 2: Spawns and coordinates book-specific micro servers based on intelligent routing
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

# Import topic detection from Part 1
try:
    from topic_detection_mcp import calculate_topic_scores, get_recommendations, BOOK_CONFIGS
    logger.info("✅ Successfully imported topic detection from Part 1")
except ImportError as e:
    logger.error(f"❌ Could not import topic detection: {e}")
    # Fallback basic detection
    BOOK_CONFIGS = {
        "kernighan_ritchie": {"name": "K&R C Programming"},
        "unix_env": {"name": "UNIX Environment"},
        "linkers_loaders": {"name": "Linkers & Loaders"},
        "os_three_pieces": {"name": "Operating Systems"},
        "expert_c_programming": {"name": "Expert C Programming"}
    }

# Global state for active servers
ACTIVE_SERVERS = {}  # {server_name: {"process": subprocess, "port": int, "started_at": timestamp}}
BASE_PORT = 8100  # Starting port for micro servers
PROJECT_ROOT = "/home/shahar42/Suumerizing_C_holy_grale_book"

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
        "description": "Expert C Programming server"
    },
        "memory_optimization": {
        "script_path": "memory_optimization_server.py",
        "port": 8106,
        "description": "Memory optimization, cache performance, TLB efficiency"
    }
}

def save_server_state():
    """Save active server state to disk for persistence"""
    try:
        state_file = Path(PROJECT_ROOT) / "scripts" / "orchestrator_state.json"
        
        # Convert process objects to serializable data
        serializable_state = {}
        for name, data in ACTIVE_SERVERS.items():
            if data["process"] and data["process"].poll() is None:  # Still running
                serializable_state[name] = {
                    "pid": data["process"].pid,
                    "port": data["port"],
                    "started_at": data["started_at"],
                    "description": BOOK_SERVER_CONFIGS.get(name, {}).get("description", "")
                }
        
        with open(state_file, 'w') as f:
            json.dump(serializable_state, f, indent=2)
        
        logger.info(f"💾 Saved server state: {len(serializable_state)} active servers")
    except Exception as e:
        logger.warning(f"Could not save server state: {e}")

def load_server_state():
    """Load active server state from disk"""
    try:
        state_file = Path(PROJECT_ROOT) / "scripts" / "orchestrator_state.json"
        if not state_file.exists():
            return
        
        with open(state_file, 'r') as f:
            saved_state = json.load(f)
        
        # Verify which servers are still actually running
        for name, data in saved_state.items():
            try:
                # Check if process is still alive
                os.kill(data["pid"], 0)  # Send signal 0 to check if process exists
                logger.info(f"📡 Found running server: {name} (PID: {data['pid']})")
                
                # Recreate the process object (for management, not starting)
                ACTIVE_SERVERS[name] = {
                    "process": None,  # We can't recreate the subprocess object
                    "port": data["port"],
                    "started_at": data["started_at"],
                    "pid": data["pid"]
                }
            except (OSError, ProcessLookupError):
                logger.info(f"🔍 Server {name} no longer running (PID: {data['pid']})")
        
        logger.info(f"📂 Loaded server state: {len(ACTIVE_SERVERS)} active servers")
    except Exception as e:
        logger.warning(f"Could not load server state: {e}")

def spawn_book_server(book_name: str) -> Dict:
    """Spawn a specific book server if not already running"""
    
    if book_name in ACTIVE_SERVERS:
        process = ACTIVE_SERVERS[book_name]["process"]
        if process and process.poll() is None:
            return {
                "status": "already_running",
                "message": f"{BOOK_CONFIGS.get(book_name, {}).get('name', book_name)} server already active",
                "port": ACTIVE_SERVERS[book_name]["port"]
            }
    
    if book_name not in BOOK_SERVER_CONFIGS:
        return {
            "status": "error",
            "message": f"Unknown book server: {book_name}",
            "available": list(BOOK_SERVER_CONFIGS.keys())
        }
    
    config = BOOK_SERVER_CONFIGS[book_name]
    script_path = Path(PROJECT_ROOT) / config["script_path"]
    
    # Create the script if it doesn't exist (will be created in Part 3)
    if not script_path.exists():
        script_path.parent.mkdir(parents=True, exist_ok=True)
        create_placeholder_server(script_path, book_name, config["port"])
    
    try:
        # Spawn the server process
        process = subprocess.Popen([
            "python3", str(script_path)
        ], 
        cwd=PROJECT_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        preexec_fn=os.setsid  # Create new process group for easier cleanup
        )
        
        # Wait a moment and check if it started successfully
        time.sleep(1)
        if process.poll() is not None:
            stdout, stderr = process.communicate()
            return {
                "status": "error",
                "message": f"Server failed to start: {stderr.decode()[:200]}",
                "stdout": stdout.decode()[:200]
            }
        
        # Register the active server
        ACTIVE_SERVERS[book_name] = {
            "process": process,
            "port": config["port"],
            "started_at": time.time(),
            "pid": process.pid
        }
        
        save_server_state()
        
        logger.info(f"🚀 Spawned {book_name} server (PID: {process.pid}, Port: {config['port']})")
        
        return {
            "status": "started",
            "message": f"Successfully started {BOOK_CONFIGS.get(book_name, {}).get('name', book_name)} server",
            "port": config["port"],
            "pid": process.pid
        }
        
    except Exception as e:
        return {
            "status": "error", 
            "message": f"Failed to spawn {book_name} server: {str(e)}"
        }

def create_placeholder_server(script_path: Path, book_name: str, port: int):
    """Create a placeholder book server (will be replaced in Part 3)"""
    
    server_template = f'''#!/usr/bin/env python3
"""
{BOOK_CONFIGS.get(book_name, {}).get("name", book_name)} MCP Server
Placeholder server - will be enhanced in Part 3
"""

import sys
import time
sys.path.append('/home/shahar42/Suumerizing_C_holy_grale_book')

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("{book_name}")

@mcp.tool()
def search_concepts(query: str) -> str:
    """Search for programming concepts in {BOOK_CONFIGS.get(book_name, {}).get("name", book_name)}"""
    
    # Placeholder - will load actual book concepts in Part 3
    return f"📚 {{BOOK_CONFIGS.get(book_name, {{}}).get('name', book_name)}} Server Response:\\n\\nSearching for: '{{query}}'\\n\\n[Placeholder - This will be connected to actual book concepts in Part 3]\\n\\nTopics related to {{query}} from {{BOOK_CONFIGS.get(book_name, {{}}).get('name', book_name)}} book would appear here."

@mcp.tool()
def get_book_info() -> str:
    """Get information about this book server"""
    
    return f"""📖 **{{BOOK_CONFIGS.get(book_name, {{}}).get('name', book_name)}} Server**
    
🔧 Status: Active (Placeholder)
🎯 Focus: {{BOOK_SERVER_CONFIGS.get(book_name, {{}}).get('description', 'Programming concepts')}}
📊 Port: {port}
🏗️  Version: Part 2 Placeholder (will be enhanced in Part 3)

This server is currently a placeholder and will be connected to actual extracted concepts in Part 3."""

if __name__ == "__main__":
    print(f"🚀 Starting {{BOOK_CONFIGS.get(book_name, {{}}).get('name', book_name)}} server on port {port}")
    mcp.run()
'''
    
    with open(script_path, 'w') as f:
        f.write(server_template)
    
    script_path.chmod(0o755)  # Make executable
    logger.info(f"📝 Created placeholder server: {script_path}")

def kill_book_server(book_name: str) -> Dict:
    """Kill a specific book server"""
    
    if book_name not in ACTIVE_SERVERS:
        return {
            "status": "not_running",
            "message": f"{book_name} server is not active"
        }
    
    try:
        server_data = ACTIVE_SERVERS[book_name]
        
        if "pid" in server_data:
            # Kill by PID if we have it
            try:
                os.killpg(server_data["pid"], signal.SIGTERM)  # Kill process group
                time.sleep(1)
                os.killpg(server_data["pid"], signal.SIGKILL)  # Force kill if needed
            except (OSError, ProcessLookupError):
                pass  # Process already dead
        
        if server_data["process"]:
            # Kill via subprocess object if available
            server_data["process"].terminate()
            time.sleep(1)
            if server_data["process"].poll() is None:
                server_data["process"].kill()
        
        del ACTIVE_SERVERS[book_name]
        save_server_state()
        
        logger.info(f"🛑 Killed {book_name} server")
        
        return {
            "status": "killed",
            "message": f"Successfully stopped {BOOK_CONFIGS.get(book_name, {}).get('name', book_name)} server"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to kill {book_name} server: {str(e)}"
        }

# Initialize server state on startup
load_server_state()

@mcp.tool()
def analyze_and_route_question(programming_question: str) -> str:
    """
    Analyze a programming question and spawn appropriate book servers to answer it.
    
    Args:
        programming_question: The programming question to analyze and route
        
    Returns:
        Coordinated response from spawned servers
    """
    
    if not programming_question.strip():
        return "Please provide a programming question to analyze."
    
    # Step 1: Use Part 1 topic detection
    try:
        book_scores = calculate_topic_scores(programming_question)
        recommendations = get_recommendations(book_scores)
    except Exception as e:
        logger.error(f"Topic detection failed: {e}")
        return f"❌ Topic detection error: {e}"
    
    if not recommendations["primary"]:
        return "❌ Unable to determine appropriate servers for this question."
    
    # Step 2: Spawn recommended servers
    spawned_servers = []
    spawn_results = []
    
    for server_rec in recommendations["primary"][:2]:  # Max 2 primary servers
        # Convert "K&R C Programming-server" → "kernighan_ritchie"
        book_name = None
        for book_id, config in BOOK_CONFIGS.items():
            if config["name"] in server_rec:
                book_name = book_id
                break
        
        if book_name:
            result = spawn_book_server(book_name)
            spawn_results.append(f"• {server_rec}: {result['status']}")
            if result["status"] in ["started", "already_running"]:
                spawned_servers.append(book_name)
    
    # Step 3: Generate coordinated response
    response_parts = [
        f"🎯 **Question Analysis:** \"{programming_question}\"",
        "",
        f"🧠 **Intelligent Routing Results:**"
    ]
    
    if recommendations["top_match"]:
        book_id, data = recommendations["top_match"]
        confidence = "high" if data["score"] >= 0.3 else "moderate" if data["score"] >= 0.15 else "low"
        response_parts.append(f"• **Top Match:** {data['name']} (confidence: {confidence})")
        if data["matches"]:
            response_parts.append(f"• **Keywords Detected:** {', '.join(data['matches'][:3])}")
    
    response_parts.extend([
        "",
        "🚀 **Server Spawning Results:**"
    ])
    response_parts.extend(spawn_results)
    
    if spawned_servers:
        response_parts.extend([
            "",
            f"✅ **Active Servers:** {len(spawned_servers)} book servers ready",
            f"📡 **Next Step:** Query specific servers using their search_concepts tools",
            "",
            "🔧 **Available Commands:**",
            "• `list_active_servers()` - See all running servers",
            "• Use individual book server tools to get detailed answers"
        ])
    else:
        response_parts.append("❌ **No servers spawned successfully**")
    
    return "\n".join(response_parts)

@mcp.tool()
def list_active_servers() -> str:
    """List all currently active book servers"""
    
    if not ACTIVE_SERVERS:
        return "📭 **No active book servers**\n\nUse `analyze_and_route_question()` to spawn servers based on your question."
    
    response_parts = [f"📡 **Active Book Servers:** {len(ACTIVE_SERVERS)}", ""]
    
    for book_name, data in ACTIVE_SERVERS.items():
        book_config = BOOK_CONFIGS.get(book_name, {})
        server_config = BOOK_SERVER_CONFIGS.get(book_name, {})
        
        status = "🟢 Running"
        if data["process"] and data["process"].poll() is not None:
            status = "🔴 Stopped"
        
        uptime = int(time.time() - data["started_at"]) if "started_at" in data else 0
        
        response_parts.append(
            f"• **{book_config.get('name', book_name)}** {status}\n"
            f"  Port: {data['port']} | Uptime: {uptime}s | PID: {data.get('pid', 'unknown')}\n"
            f"  Focus: {server_config.get('description', 'Programming concepts')}\n"
        )
    
    response_parts.extend([
        "🔧 **Management Commands:**",
        "• `kill_book_server('book_name')` - Stop specific server",
        "• `cleanup_unused_servers()` - Stop all idle servers"
    ])
    
    return "\n".join(response_parts)

@mcp.tool()
def spawn_specific_server(book_name: str) -> str:
    """
    Manually spawn a specific book server.
    
    Args:
        book_name: Name of the book server to spawn (kernighan_ritchie, unix_env, etc.)
    """
    
    result = spawn_book_server(book_name)
    
    if result["status"] == "started":
        return f"✅ **{BOOK_CONFIGS.get(book_name, {}).get('name', book_name)} Server Started**\n\n🚀 Port: {result['port']}\n📊 PID: {result['pid']}\n\n🔧 You can now use this server's tools to search for concepts!"
    elif result["status"] == "already_running":
        return f"ℹ️ **{BOOK_CONFIGS.get(book_name, {}).get('name', book_name)} Server Already Running**\n\n📡 Port: {result['port']}\n\n✅ Ready to use!"
    else:
        return f"❌ **Failed to start {book_name} server**\n\n🔍 Error: {result['message']}\n\n💡 Available servers: {', '.join(BOOK_SERVER_CONFIGS.keys())}"

@mcp.tool()
def kill_specific_server(book_name: str) -> str:
    """
    Kill a specific book server.
    
    Args:
        book_name: Name of the book server to kill
    """
    
    result = kill_book_server(book_name)
    
    if result["status"] == "killed":
        return f"🛑 **{BOOK_CONFIGS.get(book_name, {}).get('name', book_name)} Server Stopped**\n\n✅ Successfully terminated server"
    elif result["status"] == "not_running":
        return f"ℹ️ **{book_name} server was not running**"
    else:
        return f"❌ **Failed to stop {book_name} server**\n\n🔍 Error: {result['message']}"

@mcp.tool()
def cleanup_unused_servers() -> str:
    """Clean up all active servers (useful for testing or resource management)"""
    
    if not ACTIVE_SERVERS:
        return "📭 **No active servers to clean up**"
    
    cleanup_results = []
    servers_to_kill = list(ACTIVE_SERVERS.keys())
    
    for book_name in servers_to_kill:
        result = kill_book_server(book_name)
        cleanup_results.append(f"• {BOOK_CONFIGS.get(book_name, {}).get('name', book_name)}: {result['status']}")
    
    return f"🧹 **Cleanup Complete**\n\n" + "\n".join(cleanup_results)

@mcp.tool()
def get_orchestrator_status() -> str:
    """Get detailed status of the master orchestrator system"""
    
    # Check topic detection
    topic_detection_status = "✅ Working" if 'calculate_topic_scores' in globals() else "❌ Failed"
    
    # Count available vs active servers
    available_servers = len(BOOK_SERVER_CONFIGS)
    active_servers = len(ACTIVE_SERVERS)
    
    # System info
    status_parts = [
        "🎛️ **Master Orchestrator Status**",
        "",
        f"🧠 **Topic Detection (Part 1):** {topic_detection_status}",
        f"📊 **Available Book Servers:** {available_servers}",
        f"📡 **Active Servers:** {active_servers}",
        f"🏗️ **Project Root:** {PROJECT_ROOT}",
        "",
        "📚 **Book Server Registry:**"
    ]
    
    for book_id, config in BOOK_SERVER_CONFIGS.items():
        status = "🟢 Active" if book_id in ACTIVE_SERVERS else "⚪ Inactive"
        book_name = BOOK_CONFIGS.get(book_id, {}).get('name', book_id)
        status_parts.append(f"• **{book_name}:** {status} (Port {config['port']})")
    
    status_parts.extend([
        "",
        "🎯 **Core Capabilities:**",
        "• ✅ Intelligent question analysis and routing",
        "• ✅ Dynamic server spawning and lifecycle management", 
        "• ✅ Multi-server coordination and response synthesis",
        "• 🔄 Book-specific concept servers (Part 3 - in development)"
    ])
    
    return "\n".join(status_parts)

if __name__ == "__main__":
    # Run the MCP server
    logger.info("🎛️ Starting Master Programming Orchestrator...")
    mcp.run()
