#!/usr/bin/env python3
"""
Test script for follow-up question suggestions.

Tests that Inez generates relevant, specific follow-up questions
after answering queries.

Usage:
    python3 test_followups.py
"""

import sys
import os

# Test scenarios
TEST_SCENARIOS = [
    {
        "question": "How's the real estate market in Austin?",
        "expected_themes": ["neighborhoods", "prices", "trends", "comparison", "investment"],
    },
    {
        "question": "What's Tesla stock price?",
        "expected_themes": ["analysis", "forecast", "comparison", "news", "fundamentals"],
    },
    {
        "question": "How do I improve XFTC website SEO?",
        "expected_themes": ["keywords", "content", "backlinks", "technical", "analytics"],
    },
]

def test_followup_generation():
    """Test that follow-up questions are relevant and specific."""
    print("\n" + "="*70)
    print("🧪 Testing Follow-Up Question Generation")
    print("="*70)
    
    from inez_agent import _generate_followups
    
    for i, scenario in enumerate(TEST_SCENARIOS, 1):
        question = scenario["question"]
        
        # Simulate a simple response
        response = f"Based on current data, here's what I found about your question: {question}"
        
        print(f"\n--- Test {i}/{len(TEST_SCENARIOS)} ---")
        print(f"📝 Question: {question}")
        print(f"⏰ Generating follow-ups...")
        
        try:
            followups = _generate_followups(question, response)
            
            if not followups:
                print(f"❌ No follow-ups generated")
                continue
            
            print(f"\n✅ Generated {len(followups)} follow-up questions:")
            for j, followup in enumerate(followups, 1):
                print(f"   {j}. {followup}")
            
            # Check quality
            if len(followups) < 3:
                print(f"⚠️  Only {len(followups)} suggestions (expected 3-5)")
            elif len(followups) > 5:
                print(f"⚠️  Too many suggestions: {len(followups)} (expected 3-5)")
            else:
                print(f"✓ Good count: {len(followups)} questions")
            
            # Check for genericness
            generic_phrases = ["tell me more", "anything else", "what else", "more info"]
            generic_count = sum(
                1 for followup in followups 
                for phrase in generic_phrases 
                if phrase in followup.lower()
            )
            if generic_count > 0:
                print(f"⚠️  {generic_count} generic questions detected")
            else:
                print(f"✓ All questions are specific")
            
            # Check length
            too_long = [f for f in followups if len(f) > 120]
            if too_long:
                print(f"⚠️  {len(too_long)} questions exceed 120 chars")
            else:
                print(f"✓ All questions are concise")
                
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()

def test_full_integration():
    """Test full integration with Inez think() function."""
    print("\n" + "="*70)
    print("🤖 Testing Full Integration with Inez")
    print("="*70)
    
    from inez_agent import think
    
    query = "What's the latest news about Tesla?"
    print(f"\n📝 Query: {query}")
    print(f"⏰ Calling think()...")
    
    def emit_handler(event_type, **kwargs):
        if event_type == "inez_thinking":
            print(f"💭 {kwargs.get('message', kwargs.get('text', ''))}")
    
    try:
        result = think(query, history=[], emit=emit_handler)
        
        print("\n" + "-"*70)
        print("📊 RESULT:")
        print("-"*70)
        
        inez_message = result.get("inez_message", "")
        print(f"\n💬 Inez: {inez_message[:200]}...")
        
        followups = result.get("followup_suggestions", [])
        if followups:
            print(f"\n💡 Follow-up suggestions ({len(followups)}):")
            for i, followup in enumerate(followups, 1):
                print(f"   {i}. {followup}")
        else:
            print("\n⚠️  No follow-up suggestions in result")
        
        if result.get("has_citations"):
            print(f"\n🌐 Web search was used")
        
        print("\n✅ Full integration test complete!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Run all tests."""
    print("\n🚀 Follow-Up Question Suggestions Test Suite")
    print("="*70)
    
    # Check LLM availability
    try:
        from inez_agent import LLM_OK
        if not LLM_OK:
            print("\n❌ LangChain/OpenAI not available")
            print("Install with: pip3 install langchain langchain-openai")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error importing inez_agent: {e}")
        sys.exit(1)
    
    # Check OpenAI API key
    if not os.environ.get("OPENAI_API_KEY"):
        print("\n⚠️  OPENAI_API_KEY not set!")
        print("Export it: export OPENAI_API_KEY='your_key_here'")
        print("\nTests will likely fail without it.")
        response = input("\nContinue anyway? (y/n): ")
        if response.lower() != 'y':
            sys.exit(1)
    
    # Run tests
    test_followup_generation()
    
    # Optional: full integration test
    if "--full" in sys.argv:
        test_full_integration()
    
    print("\n" + "="*70)
    print("🎯 Next Steps:")
    print("="*70)
    print("1. Update iOS app to display follow-up suggestions")
    print("   - Add followupSuggestions: [String]? to InezResponse")
    print("   - Display as tappable chips below message")
    print("   - Tap chip → automatically send that question")
    print("\n2. Test with server:")
    print("   python3 hub_server.py")
    print("\n3. Test from iOS app:")
    print("   - Ask Inez any question")
    print("   - Look for 💡 follow-up question chips")
    print("   - Tap to ask follow-up")
    print("\n4. Optional: Add regenerate button")
    print("   - '🔄 More suggestions' button")
    print("   - Calls /api/inez/regenerate-followups endpoint")
    print("="*70 + "\n")

if __name__ == "__main__":
    main()
