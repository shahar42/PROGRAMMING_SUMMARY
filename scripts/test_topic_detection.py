#!/usr/bin/env python3
"""
Quick test script for the Topic Detection Engine
Run this to verify Part 1 is working correctly
"""

# Test questions to verify the topic detection
TEST_QUESTIONS = [
    "How do I fix a malloc memory leak in my C program?",
    "What's the difference between fork() and exec() system calls?", 
    "I'm getting undefined symbol errors when linking my program",
    "How does the CPU scheduler decide which process to run next?",
    "What are some common C pointer pitfalls to avoid?",
    "How do I read a file using system calls in Unix?",
    "Why is my shared library not loading properly?",
    "Explain mutex vs semaphore for thread synchronization",
    "How do I properly cast pointers in C without undefined behavior?",
    "What's the difference between static and dynamic linking?"
]

def test_topic_detection():
    """Test the topic detection logic directly"""
    
    # Import the detection functions (assuming the MCP server code is available)
    import sys
    sys.path.append('.')
    try:
        from topic_detection_mcp import calculate_topic_scores, get_recommendations, BOOK_CONFIGS
    except ImportError:
        print("❌ Could not import topic detection functions")
        print("Make sure topic_detection_mcp.py is in the scripts directory")
        return
    
    print("🔍 Testing Topic Detection Engine\n")
    print("=" * 60)
    
    for i, question in enumerate(TEST_QUESTIONS, 1):
        print(f"\n🧪 Test {i}: {question}")
        print("-" * 50)
        
        # Calculate scores
        scores = calculate_topic_scores(question)
        recommendations = get_recommendations(scores)
        
        # Show top match
        if recommendations["top_match"]:
            book_id, data = recommendations["top_match"]
            print(f"🎯 Top Match: {data['name']} (score: {data['score']:.3f})")
            if data["matches"]:
                print(f"🔑 Keywords: {', '.join(data['matches'][:3])}")
        
        # Show recommendations
        if recommendations["primary"]:
            print(f"✅ Primary: {', '.join(recommendations['primary'])}")
        if recommendations["secondary"]:
            print(f"💡 Secondary: {', '.join(recommendations['secondary'])}")
    
    print("\n" + "=" * 60)
    print("✅ Topic Detection Engine test complete!")
    print("\nNext steps:")
    print("1. Save topic_detection_mcp.py to your scripts directory (already there)")
    print("2. Update .mcp.json in your watch_dog directory to include the topic-detection server")
    print("3. Test with Claude Code using the detect_programming_topics tool")

if __name__ == "__main__":
    test_topic_detection()
