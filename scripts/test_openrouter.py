#!/usr/bin/env python3
"""Test OpenRouter API directly."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import settings
import requests

def test_openrouter():
    """Test OpenRouter API."""
    print(f"Testing OpenRouter API...")
    print(f"API Key: {settings.LLM_KEY[:20]}...")
    print(f"Model: {settings.OPENROUTER_MODEL}")
    print()
    
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.LLM_KEY}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "model": settings.OPENROUTER_MODEL,
        "messages": [
            {
                "role": "user",
                "content": "Say 'Hello, the API is working!' and nothing else."
            }
        ],
        "max_tokens": 50,
    }
    
    try:
        print("Making request to OpenRouter...")
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print()
        
        if response.status_code != 200:
            print(f"Error Response: {response.text}")
            return
        
        result = response.json()
        print("Success!")
        print(f"Response: {result}")
        
        if "choices" in result and len(result["choices"]) > 0:
            message = result["choices"][0].get("message", {}).get("content", "")
            print(f"\nGenerated text: {message}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_openrouter()

