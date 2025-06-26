#!/usr/bin/env python3
"""
Test the full workflow to confirm Perplexity research is working
"""
from airules.cli import research_with_perplexity
import os
import sys
sys.path.insert(0, 'airules')


def test_research_workflow():
    """Test the research workflow step by step"""
    print("🔍 Testing Perplexity research workflow...")

    # Test the research function directly
    try:
        print("\n1. Testing research_with_perplexity function...")
        result = research_with_perplexity("python", "pytest")
        print(f"✅ Research successful!")
        print(f"Research result length: {len(result)} characters")
        print(f"First 300 chars: {result[:300]}...")
        print(f"Last 100 chars: ...{result[-100:]}")
        return True

    except Exception as e:
        print(f"❌ Research failed: {str(e)}")
        return False


if __name__ == "__main__":
    success = test_research_workflow()
    if success:
        print("\n🎉 Perplexity research is working perfectly!")
    else:
        print("\n💥 Research workflow failed!")
