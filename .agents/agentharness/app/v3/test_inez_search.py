#!/usr/bin/env python3
"""
Test script for Inez web search integration.

This script tests the web search functionality without needing a full server setup.
It directly calls the think() function with a search-worthy query.

Usage:
    # Set your Brave API key first
    export BRAVE_API_KEY="your_key_here"
    
    # Run the test
    python3 test_inez_search.py
"""

import os
import sys
from datetime import datetime

# Ensure BRAVE_API_KEY is set
if not os.environ.get("BRAVE_API_KEY"):
    print("❌ BRAVE_API_KEY not set!")
    print("\nTo test web search, you need a Brave Search API key:")
    print("1. Sign up at: https://brave.com/search/api/")
    print("2. Copy your API key")
    print("3. Export it: export BRAVE_API_KEY='your_key_here'")
    print("\nOr run without search (will skip web search):")
    print("  python3 test_inez_search.py --no-search")
    if "--no-search" not in sys.argv:
        sys.exit(1)

# Test queries
SEARCH_QUERIES = [
    "What's the latest news about Tesla stock?",
    "Current weather in Austin Texas",
    "How much does ChatGPT cost today?",
]

NON_SEARCH_QUERIES = [
    "What is 2 + 2?",
    "Explain Python decorators",
    "What's a good name for my app?",
]

def test_search_analyzer():
    """Test that SearchAnalyzer correctly identifies search-worthy queries."""
    print("\n" + "="*70)
    print("🧪 Testing SearchAnalyzer")
    print("="*70)
    
    from web_search import SearchAnalyzer
    
    print("\n✅ Should trigger search:")
    for query in SEARCH_QUERIES:
        should_search = SearchAnalyzer.should_search(query)
        status = "✓" if should_search else "✗"
        print(f"  {status} '{query}' -> {should_search}")
    
    print("\n❌ Should NOT trigger search:")
    for query in NON_SEARCH_QUERIES:
        should_search = SearchAnalyzer.should_search(query)
        status = "✓" if not should_search else "✗"
        print(f"  {status} '{query}' -> {should_search}")

def test_inez_search():
    """Test Inez integration with web search."""
    print("\n" + "="*70)
    print("🤖 Testing Inez with Web Search")
    print("="*70)
    
    from inez_agent import think
    
    # Test with a search-worthy query
    query = "What's Tesla stock price today?"
    print(f"\n📝 Query: {query}")
    print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\n" + "-"*70)
    
    # Track thinking steps
    def emit_handler(event_type, **kwargs):
        if event_type == "inez_thinking":
            print(f"💭 {kwargs.get('message', kwargs.get('text', ''))}")
        elif event_type == "inez_response":
            print(f"\n✅ Response ready")
    
    try:
        result = think(query, history=[], emit=emit_handler)
        
        print("\n" + "-"*70)
        print("📊 RESULT:")
        print("-"*70)
        
        inez_message = result.get("inez_message", "")
        print(f"\n{inez_message}")
        
        if result.get("has_citations"):
            print(f"\n🌐 Web search was used!")
            print(f"   Search query: {result.get('search_query')}")
            citations = result.get("citations", [])
            print(f"   Found {len(citations)} sources:")
            for cite in citations:
                print(f"      [{cite['id']}] {cite['title']}")
                print(f"          {cite['url']}")
        else:
            print("\n💡 No web search used (LLM answered from knowledge)")
        
        if result.get("error"):
            print(f"\n⚠️  Error: {result['error']}")
        
        print("\n" + "="*70)
        print("✅ Test complete!")
        print("="*70)
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Run all tests."""
    print("\n🚀 Inez Web Search Integration Test")
    print("="*70)
    
    # Test 1: SearchAnalyzer logic
    try:
        test_search_analyzer()
    except Exception as e:
        print(f"\n❌ SearchAnalyzer test failed: {e}")
    
    # Test 2: Full Inez integration (only if API key is set)
    if os.environ.get("BRAVE_API_KEY") and "--no-search" not in sys.argv:
        try:
            test_inez_search()
        except Exception as e:
            print(f"\n❌ Inez integration test failed: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("\n⚠️  Skipping Inez integration test (no BRAVE_API_KEY)")
        print("   Set BRAVE_API_KEY to test full integration")
    
    print("\n" + "="*70)
    print("🎯 Next Steps:")
    print("="*70)
    print("1. If you haven't already, get your Brave API key:")
    print("   https://brave.com/search/api/")
    print("\n2. Set the environment variable:")
    print("   export BRAVE_API_KEY='your_key_here'")
    print("\n3. Start the ArchonHub server:")
    print("   cd /Users/polysqa/Documents/GitHub/NewAgentHarness/.agents/agentharness/app/v3")
    print("   python3 hub_server.py")
    print("\n4. Test from iOS app:")
    print("   - Open ArchonHub app")
    print("   - Ask Inez: 'What's Tesla stock price today?'")
    print("   - Look for 🌐 indicator and [1][2] citations")
    print("\n5. Check database for citation data:")
    print("   sqlite3 ../../../memory/runs_v3.db")
    print("   SELECT content, has_citations, citations FROM messages WHERE has_citations = 1 LIMIT 1;")
    print("="*70 + "\n")

if __name__ == "__main__":
    main()
