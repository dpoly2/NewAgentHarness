#!/usr/bin/env python3
"""
Test the conversation search endpoint.

Usage:
    python3 test_search.py "search query"
"""

import requests
import sys
import json

BASE_URL = "http://localhost:8765"

# Test credentials (adjust as needed)
USERNAME = "david"
PASSWORD = "archon2026"


def login():
    """Login and get auth token."""
    print("🔐 Logging in...")
    response = requests.post(
        f"{BASE_URL}/api/login",
        json={"username": USERNAME, "password": PASSWORD}
    )
    if response.status_code != 200:
        print(f"❌ Login failed: {response.status_code}")
        print(response.text)
        sys.exit(1)
    
    data = response.json()
    token = data.get("token")
    if not token:
        print("❌ No token in response")
        sys.exit(1)
    
    print("✅ Logged in successfully")
    return token


def search(token: str, query: str, limit: int = 10):
    """Search conversations."""
    print(f"🔍 Searching for: '{query}'")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(
        f"{BASE_URL}/api/search",
        params={"q": query, "limit": limit},
        headers=headers
    )
    
    if response.status_code != 200:
        print(f"❌ Search failed: {response.status_code}")
        print(response.text)
        return
    
    data = response.json()
    print(f"\n✅ Found {data['count']} results:\n")
    
    for i, result in enumerate(data['results'], 1):
        print(f"[{i}] {result['role'].upper()} in '{result['conversation_title']}'")
        print(f"    {result['excerpt']}")
        print(f"    Conversation ID: {result['conversation_id']}")
        print(f"    Created: {result['created_at']}")
        print()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 test_search.py \"search query\"")
        sys.exit(1)
    
    query = " ".join(sys.argv[1:])
    
    try:
        token = login()
        search(token, query)
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Is it running on port 8765?")
        sys.exit(1)
