#!/usr/bin/env python3
"""
Session start hook for ensue-auto-memory.
Retrieves user's memories from Ensue and injects them as context.
"""

import json
import os
import sys
import urllib.request
import urllib.error

# Configuration (can be overridden via environment variables)
PREFERENCES_LIMIT = int(os.environ.get("ENSUE_PREFERENCES_LIMIT", "10"))
CORRECTIONS_LIMIT = int(os.environ.get("ENSUE_CORRECTIONS_LIMIT", "5"))
PROJECT_MEMORY_LIMIT = int(os.environ.get("ENSUE_PROJECT_LIMIT", "5"))

ENSUE_API_URL = "https://api.ensue-network.ai/"


def get_env_or_exit(var_name: str) -> str:
    """Get environment variable or exit with error."""
    value = os.environ.get(var_name)
    if not value:
        output = {
            "systemMessage": f"Ensue Auto-Memory: {var_name} environment variable is not set. "
            f"Please set it to enable automatic memory. "
            f"Get an API key at https://www.ensue-network.ai/dashboard"
        }
        print(json.dumps(output))
        sys.exit(0)
    return value


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
        with urllib.request.urlopen(req, timeout=15) as response:
            result = json.loads(response.read().decode("utf-8"))
            # Handle streaming response (data: prefix)
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


def get_project_name() -> str:
    """Get the current project name from CLAUDE_PROJECT_DIR or PWD."""
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())
    return os.path.basename(project_dir)


def filter_keys_by_prefix(keys: list, prefix: str, limit: int = None) -> list:
    """Filter keys by prefix and optionally limit results."""
    filtered = [k for k in keys if k["key_name"].startswith(prefix)]
    # Sort by updated_at descending (most recent first)
    filtered.sort(key=lambda x: x.get("updated_at", 0), reverse=True)
    if limit:
        filtered = filtered[:limit]
    return filtered


def decode_value(value) -> str:
    """Decode value from API response (handles byte arrays)."""
    if isinstance(value, list):
        return "".join(chr(c) for c in value)
    return str(value)


def main():
    # Get required environment variables
    api_key = get_env_or_exit("ENSUE_API_KEY")
    username = get_env_or_exit("ENSUE_USERNAME")

    user_prefix = f"@{username}/"
    project_name = get_project_name()

    # Step 1: List all keys
    list_result = call_ensue_api(api_key, "list_keys", {"limit": 200})

    if "error" in list_result:
        output = {"systemMessage": f"Ensue Auto-Memory: Failed to retrieve memories: {list_result['error']}"}
        print(json.dumps(output))
        sys.exit(0)

    all_keys = list_result.get("keys", [])

    # Step 2: Filter keys by category
    identity_keys = filter_keys_by_prefix(all_keys, f"{user_prefix}identity/")
    preferences_keys = filter_keys_by_prefix(all_keys, f"{user_prefix}preferences/", PREFERENCES_LIMIT)
    corrections_keys = filter_keys_by_prefix(all_keys, f"{user_prefix}corrections/", CORRECTIONS_LIMIT)
    project_keys = filter_keys_by_prefix(all_keys, f"{user_prefix}projects/{project_name}/", PROJECT_MEMORY_LIMIT)

    # Combine all keys to fetch
    keys_to_fetch = []
    for key_list in [identity_keys, preferences_keys, corrections_keys, project_keys]:
        keys_to_fetch.extend([k["key_name"] for k in key_list])

    if not keys_to_fetch:
        output = {
            "systemMessage": f"Ensue Auto-Memory: No memories found for @{username}. "
            f"Memories will be automatically saved as you work."
        }
        print(json.dumps(output))
        sys.exit(0)

    # Step 3: Fetch memory values
    get_result = call_ensue_api(api_key, "get_memory", {"key_names": keys_to_fetch})

    if "error" in get_result:
        output = {"systemMessage": f"Ensue Auto-Memory: Failed to retrieve memory values: {get_result['error']}"}
        print(json.dumps(output))
        sys.exit(0)

    # Step 4: Format memories for context
    memories_by_category = {
        "identity": [],
        "preferences": [],
        "corrections": [],
        "project": [],
    }

    results = get_result.get("results", [])
    for item in results:
        if not item.get("success", False):
            continue

        key = item.get("key_name", "")
        value = decode_value(item.get("value", ""))
        description = item.get("description", "")

        # Categorize by key prefix
        if f"{user_prefix}identity/" in key:
            short_key = key.replace(f"{user_prefix}identity/", "")
            memories_by_category["identity"].append(f"- {short_key}: {value}")
        elif f"{user_prefix}preferences/" in key:
            short_key = key.replace(f"{user_prefix}preferences/", "")
            memories_by_category["preferences"].append(f"- {short_key}: {value}")
        elif f"{user_prefix}corrections/" in key:
            short_key = key.replace(f"{user_prefix}corrections/", "")
            memories_by_category["corrections"].append(f"- {short_key}: {value}")
        elif f"{user_prefix}projects/{project_name}/" in key:
            short_key = key.replace(f"{user_prefix}projects/{project_name}/", "")
            memories_by_category["project"].append(f"- {short_key}: {value}")

    # Build context message
    context_parts = []
    context_parts.append(f"## Ensue Auto-Memory Context for @{username}")
    context_parts.append(f"Project: {project_name}")
    context_parts.append("")

    if memories_by_category["identity"]:
        context_parts.append("### Identity")
        context_parts.extend(memories_by_category["identity"])
        context_parts.append("")

    if memories_by_category["preferences"]:
        context_parts.append("### Preferences")
        context_parts.extend(memories_by_category["preferences"])
        context_parts.append("")

    if memories_by_category["corrections"]:
        context_parts.append("### Corrections (DO NOT repeat these mistakes)")
        context_parts.extend(memories_by_category["corrections"])
        context_parts.append("")

    if memories_by_category["project"]:
        context_parts.append(f"### Project Context ({project_name})")
        context_parts.extend(memories_by_category["project"])
        context_parts.append("")

    context_message = "\n".join(context_parts)

    output = {"systemMessage": context_message}
    print(json.dumps(output))


if __name__ == "__main__":
    main()
