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
    "What's the difference between static and dynamic linking?",
    "static storage class"  # Your specific problematic query
]

def test_topic_detection():
    """Test the topic detection logic directly"""
    
    # Import the detection functions
    import sys
    import os
    
    # Add the scripts directory to path
    scripts_dir = os.path.dirname(os.path.abspath(__file__))
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    
    # Also add parent directory for outputs access
    parent_dir = os.path.dirname(scripts_dir)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    
    try:
        from topic_detection_mcp import calculate_topic_scores, get_recommendations, BOOK_CONFIGS
    except ImportError as e:
        print(f"❌ Could not import topic detection functions: {e}")
        print("Current working directory:", os.getcwd())
        print("Script directory:", scripts_dir)
        print("Python path:", sys.path[:3])
        return
    
    print("🔍 Testing Topic Detection Engine\n")
    print("=" * 60)
    
    for i, question in enumerate(TEST_QUESTIONS, 1):
        print(f"\n🧪 Test {i}: {question}")
        print("-" * 50)
        
        try:
            # Calculate scores
            scores = calculate_topic_scores(question)
            recommendations = get_recommendations(scores)
            
            # Show top match
            if recommendations["top_match"]:
                book_id, data = recommendations["top_match"]
                print(f"🎯 Top Match: {data['name']} (score: {data['score']:.3f})")
                if data["matches"]:
                    print(f"🔑 Keywords: {', '.join(data['matches'][:3])}")
                
                # Show progressive breakdown if available
                if 'query_breakdown' in data:
                    breakdown = data['query_breakdown']
                    print(f"📊 Query breakdown: {breakdown['individual_words']} words, {breakdown['two_word_phrases']} 2-word phrases, {breakdown['expanded_terms']} expanded terms")
            
            # Show recommendations
            if recommendations["primary"]:
                print(f"✅ Primary: {', '.join(recommendations['primary'])}")
            if recommendations["secondary"]:
                print(f"💡 Secondary: {', '.join(recommendations['secondary'])}")
                
        except Exception as e:
            print(f"❌ Error processing question: {e}")
    
    print("\n" + "=" * 60)
    print("✅ Topic Detection Engine test complete!")
    print("\nProgressive search improvements:")
    print("- Individual words should match first (broad foundation)")
    print("- Then 2-word phrases (medium specificity)")  
    print("- Finally exact phrases (highest specificity)")
    print("- Related terms should expand context")

if __name__ == "__main__":
    test_topic_detection()
