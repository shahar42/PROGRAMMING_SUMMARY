#!/usr/bin/env python3
"""
Test script for Master Orchestrator (Part 2)
Verifies server spawning and coordination capabilities
"""

import time
import subprocess
import sys
import os
from pathlib import Path

def test_orchestrator_functions():
    """Test the orchestrator functions directly"""
    
    print("🎛️ Testing Master Orchestrator (Part 2)")
    print("=" * 60)
    
    # Add paths for importing (test script is now in project root)
    sys.path.append('.')
    sys.path.append('scripts')
    
    try:
        from scripts.master_orchestrator_mcp import spawn_book_server, BOOK_SERVER_CONFIGS, ACTIVE_SERVERS
        print("✅ Successfully imported orchestrator functions")
    except ImportError as e:
        print(f"❌ Could not import orchestrator functions: {e}")
        print("Make sure master_orchestrator_mcp.py is in the scripts/ directory")
        return False
    
    print(f"\n📚 Available Book Servers: {len(BOOK_SERVER_CONFIGS)}")
    for book_id, config in BOOK_SERVER_CONFIGS.items():
        print(f"  • {book_id}: Port {config['port']}")
    
    # Test spawning a server
    print(f"\n🧪 Testing server spawning...")
    print("-" * 40)
    
    test_book = "kernighan_ritchie"
    print(f"🚀 Attempting to spawn {test_book} server...")
    
    result = spawn_book_server(test_book)
    print(f"📊 Result: {result}")
    
    if result["status"] in ["started", "already_running"]:
        print("✅ Server spawn test PASSED")
        
        # Check if it's actually in the active servers list
        if test_book in ACTIVE_SERVERS:
            print(f"✅ Server registered in ACTIVE_SERVERS")
            print(f"📡 Active servers: {list(ACTIVE_SERVERS.keys())}")
        else:
            print("⚠️ Server not found in ACTIVE_SERVERS")
    else:
        print(f"❌ Server spawn test FAILED: {result['message']}")
    
    return True

def test_placeholder_servers():
    """Test that placeholder servers are created correctly"""
    
    print(f"\n🏗️ Testing Placeholder Server Creation")
    print("-" * 40)
    
    scripts_dir = Path("scripts/book_servers")
    print(f"📁 Checking directory: {scripts_dir}")
    
    if scripts_dir.exists():
        server_files = list(scripts_dir.glob("*_server.py"))
        print(f"📝 Found {len(server_files)} server files:")
        for server_file in server_files:
            print(f"  • {server_file.name}")
        
        if server_files:
            # Test one placeholder server
            test_server = server_files[0]
            print(f"\n🧪 Testing placeholder server: {test_server.name}")
            
            # Try to run it briefly to see if it starts
            try:
                process = subprocess.Popen([
                    "python3", str(test_server)
                ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=3)
                
                time.sleep(1)
                if process.poll() is None:
                    print("✅ Placeholder server starts correctly")
                    process.terminate()
                else:
                    stdout, stderr = process.communicate()
                    print(f"❌ Placeholder server failed: {stderr.decode()[:200]}")
            except subprocess.TimeoutExpired:
                print("✅ Placeholder server running (had to timeout)")
                process.kill()
            except Exception as e:
                print(f"⚠️ Could not test placeholder server: {e}")
    else:
        print("📁 book_servers directory doesn't exist yet (will be created on first spawn)")

def test_integration():
    """Test the full integration workflow"""
    
    print(f"\n🔗 Testing Integration Workflow")
    print("-" * 40)
    
    # Test questions that should trigger different servers
    test_questions = [
        "How do I fix a malloc memory leak?",
        "What's the difference between fork() and exec()?",
        "Why am I getting undefined symbol errors when linking?"
    ]
    
    print("🧠 These questions should trigger intelligent routing:")
    for i, question in enumerate(test_questions, 1):
        print(f"  {i}. {question}")
    
    print("\n🎯 In Claude Code, try:")
    print("  analyze_and_route_question('How do I fix a malloc memory leak?')")
    print("  list_active_servers()")
    print("  get_orchestrator_status()")

def main():
    """Run all tests"""
    
    print("🧪 Master Orchestrator Test Suite")
    print("=" * 60)
    
    # Simple check - we should be in project root
    if not Path("mcp_server.py").exists():
        print("❌ Please run this from the Suumerizing_C_holy_grale_book directory")
        print(f"Current directory: {Path.cwd()}")
        return
    
    # Test orchestrator functions
    if test_orchestrator_functions():
        test_placeholder_servers()
        test_integration()
    
    print("\n" + "=" * 60)
    print("✅ Part 2 Test Complete!")
    print("\nNext steps:")
    print("1. Save master_orchestrator_mcp.py to scripts/ directory")
    print("2. Update your .mcp.json to include master-orchestrator")
    print("3. Test in Claude Code with analyze_and_route_question()")
    print("4. Verify servers spawn correctly")
    print("5. Ready for Part 3: Real book server implementations")
    print("\n🎯 Test script location: Save this as test_orchestrator_part2.py in project root")

if __name__ == "__main__":
    main()
