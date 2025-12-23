#!/usr/bin/env python3
"""
User prompt hook for ensue-auto-memory.
Detects preference patterns and discovers relevant memories.
"""

import json
import os
import re
import sys
import urllib.request
import urllib.error

# Configuration
RELEVANCY_THRESHOLD = float(os.environ.get("ENSUE_RELEVANCY_THRESHOLD", "0.7"))
DISCOVER_LIMIT = int(os.environ.get("ENSUE_DISCOVER_LIMIT", "10"))

ENSUE_API_URL = "https://api.ensue-network.ai/"

# Patterns that indicate user preferences or corrections
PREFERENCE_PATTERNS = [
    r"\bi\s+(?:always|usually|prefer|like|want|need)\b",
    r"\b(?:don't|do not|never|stop)\s+(?:use|add|include|do)\b",
    r"\bmy\s+(?:preferred|favorite|default)\b",
    r"\b(?:please\s+)?(?:always|never)\b",
]

CORRECTION_PATTERNS = [
    r"\bno,?\s+(?:don't|do not|stop|actually)\b",
    r"\bthat's\s+(?:not|wrong)\b",
    r"\bi\s+(?:said|meant|wanted)\b",
    r"\b(?:instead|rather)\b.*\bnot\b",
]

IDENTITY_PATTERNS = [
    r"\bmy\s+name\s+is\b",
    r"\bi\s+(?:am|work|live)\b",
    r"\bi'm\s+(?:a|an|the)\s+\w+\b",
]


def get_env(var_name: str) -> str:
    """Get environment variable or return None."""
    return os.environ.get(var_name)


def call_ensue_api(api_key: str, method: str, arguments: dict) -> dict:
    """Call the Ensue API with JSON-RPC."""
    payload = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {"name": method, "arguments": arguments},
        "id": 1,
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    try:
        req = urllib.request.Request(
            ENSUE_API_URL,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            result = json.loads(response.read().decode("utf-8"))
            if isinstance(result, str) and result.startswith("data: "):
                result = json.loads(result[6:])

            if "result" in result:
                content = result["result"]
                if "structuredContent" in content:
                    return content["structuredContent"]
                elif "content" in content and len(content["content"]) > 0:
                    text = content["content"][0].get("text", "{}")
                    return json.loads(text)
            return {}
    except (urllib.error.URLError, json.JSONDecodeError, KeyError) as e:
        return {"error": str(e)}


def decode_value(value) -> str:
    """Decode value from API response (handles byte arrays)."""
    if isinstance(value, list):
        return "".join(chr(c) for c in value)
    return str(value)


def detect_patterns(text: str) -> dict:
    """Detect preference, correction, and identity patterns in text."""
    text_lower = text.lower()

    detected = {
        "has_preference": False,
        "has_correction": False,
        "has_identity": False,
    }

    for pattern in PREFERENCE_PATTERNS:
        if re.search(pattern, text_lower):
            detected["has_preference"] = True
            break

    for pattern in CORRECTION_PATTERNS:
        if re.search(pattern, text_lower):
            detected["has_correction"] = True
            break

    for pattern in IDENTITY_PATTERNS:
        if re.search(pattern, text_lower):
            detected["has_identity"] = True
            break

    return detected


def main():
    # Read input from stdin
    try:
        input_data = json.loads(sys.stdin.read())
    except json.JSONDecodeError:
        sys.exit(0)

    user_prompt = input_data.get("user_prompt", "")
    if not user_prompt:
        sys.exit(0)

    # Get environment variables
    api_key = get_env("ENSUE_API_KEY")
    username = get_env("ENSUE_USERNAME")

    # If not configured, exit silently
    if not api_key or not username:
        sys.exit(0)

    user_prefix = f"@{username}/"
    messages = []

    # Step 1: Detect patterns that might need saving
    patterns = detect_patterns(user_prompt)

    if patterns["has_preference"]:
        messages.append(
            "Detected preference statement. Consider saving to Ensue: "
            f"@{username}/preferences/..."
        )

    if patterns["has_correction"]:
        messages.append(
            "Detected correction. Consider saving to Ensue: "
            f"@{username}/corrections/..."
        )

    if patterns["has_identity"]:
        messages.append(
            "Detected identity information. Consider saving to Ensue: "
            f"@{username}/identity/..."
        )

    # Step 2: Discover relevant memories based on the prompt
    # Only do this for substantive prompts (not greetings, etc.)
    if len(user_prompt) > 20:
        discover_result = call_ensue_api(
            api_key,
            "discover_memories",
            {"query": user_prompt, "limit": DISCOVER_LIMIT},
        )

        if "results" in discover_result:
            # Filter by username and relevancy threshold
            relevant_keys = []
            for item in discover_result["results"]:
                key = item.get("key_name", "")
                score = item.get("score", 0)

                # Only include keys for this user and above threshold
                if key.startswith(user_prefix) and score >= RELEVANCY_THRESHOLD:
                    relevant_keys.append(key)

            # Fetch values for relevant keys
            if relevant_keys:
                get_result = call_ensue_api(
                    api_key, "get_memory", {"key_names": relevant_keys[:5]}
                )

                if "results" in get_result:
                    memory_context = []
                    for item in get_result["results"]:
                        if item.get("success"):
                            key = item.get("key_name", "").replace(user_prefix, "")
                            value = decode_value(item.get("value", ""))
                            memory_context.append(f"- {key}: {value}")

                    if memory_context:
                        messages.append(
                            "Relevant memories from Ensue:\n" + "\n".join(memory_context)
                        )

    # Output result
    if messages:
        output = {"systemMessage": "\n\n".join(messages)}
        print(json.dumps(output))


if __name__ == "__main__":
    main()
