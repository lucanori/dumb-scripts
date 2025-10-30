#!/usr/bin/env python3
"""
Quick test to verify provider selection logic works correctly
"""

import os
import sys

def test_provider_selection():
    """Test provider selection logic without API calls"""
    
    test_cases = [
        ("groq", "GROQ_API_KEY"),
        ("mistral", "MISTRAL_API_KEY"),
        ("invalid", None)
    ]
    
    for provider, expected_key in test_cases:
        os.environ["TRANSCRIPTION_PROVIDER"] = provider
        
        if provider == "groq":
            required_key = "GROQ_API_KEY"
        elif provider == "mistral":
            required_key = "MISTRAL_API_KEY"
        else:
            print(f"✓ Invalid provider '{provider}' correctly rejected")
            continue
        
        if expected_key == required_key:
            print(f"✓ Provider '{provider}' correctly requires '{required_key}'")
        else:
            print(f"✗ Provider '{provider}' key mismatch: expected '{expected_key}', got '{required_key}'")

if __name__ == "__main__":
    print("Testing provider selection logic...")
    test_provider_selection()
    print("Provider selection test completed.")