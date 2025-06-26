#!/usr/bin/env python3
"""
Test script for the research_with_perplexity function
"""
import os
import openai


def test_research_function():
    """Test the exact research function logic"""
    api_key = os.environ.get("PERPLEXITY_API_KEY")
    if not api_key:
        print("❌ PERPLEXITY_API_KEY environment variable not set")
        return False

    print(f"✅ API Key found: {api_key[:10]}...")

    client = openai.OpenAI(api_key=api_key, base_url="https://api.perplexity.ai")

    # Test the exact function logic
    lang = "python"
    tag = "pytest"

    prompt = f"Provide a detailed, up-to-date summary of best practices for '{tag}' in a '{lang}' project. Focus on actionable rules and configurations."

    print(f"\n🔍 Testing research for: {lang} / {tag}")
    print(f"Prompt: {prompt}")

    try:
        response = client.chat.completions.create(
            model="sonar-pro",
            messages=[
                {
                    "role": "system",
                    "content": "You are an AI assistant that provides concise, expert-level summaries for software development best practices.",
                },
                {"role": "user", "content": prompt},
            ],
        )

        result = response.choices[0].message.content or ""
        print(f"\n✅ Research successful!")
        print(f"Response length: {len(result)} characters")
        print(f"First 200 chars: {result[:200]}...")
        return True

    except Exception as e:
        print(f"❌ Research failed: {str(e)}")
        return False


if __name__ == "__main__":
    success = test_research_function()
    if success:
        print("\n🎉 Research function is working!")
    else:
        print("\n💥 Research function failed!")
