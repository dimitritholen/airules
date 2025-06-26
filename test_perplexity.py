#!/usr/bin/env python3
"""
Test script for Perplexity API connection and model availability
"""
import os
import openai
from openai import OpenAI


def test_perplexity_api():
    api_key = os.environ.get("PERPLEXITY_API_KEY")
    if not api_key:
        print("❌ PERPLEXITY_API_KEY environment variable not set")
        return False

    print(f"✅ API Key found: {api_key[:10]}...")

    client = OpenAI(api_key=api_key, base_url="https://api.perplexity.ai")

    # Test different model names from the example
    models_to_test = [
        "sonar-pro",
        "llama-3.1-sonar-small-128k-online",
        "llama-3.1-sonar-large-128k-online",
        "llama-3.1-sonar-huge-128k-online",
    ]

    for model in models_to_test:
        print(f"\n🧪 Testing model: {model}")
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "What is 2+2? Answer briefly."}
                ],
                max_tokens=50
            )

            print(f"✅ Model {model} works!")
            print(f"Response: {response.choices[0].message.content}")
            return True

        except Exception as e:
            print(f"❌ Model {model} failed: {str(e)}")

    return False


if __name__ == "__main__":
    success = test_perplexity_api()
    if success:
        print("\n🎉 Perplexity API is working!")
    else:
        print("\n💥 All models failed!")
