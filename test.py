#!/usr/bin/env python3
"""
Check whether an Anthropic API key is valid.

Usage:
    1. Set the key as an environment variable (recommended):
         export ANTHROPIC_API_KEY="sk-ant-..."        # macOS / Linux
         setx ANTHROPIC_API_KEY "sk-ant-..."           # Windows (new shell after)
       then run:  python check_api_key.py

    2. Or pass it on the command line:
         python check_api_key.py sk-ant-...
"""

import os
import sys
import urllib.request
import urllib.error
import json

API_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"


def check_api_key(api_key: str) -> bool:
    """Make a tiny request to the Anthropic API and report whether the key works."""
    # A minimal, cheap request — 1 token is enough to confirm the key authenticates.
    payload = json.dumps({
        "model": "claude-haiku-4-5-20251001",
        "max_tokens": 1,
        "messages": [{"role": "user", "content": "Hi"}],
    }).encode("utf-8")

    request = urllib.request.Request(
        API_URL,
        data=payload,
        method="POST",
        headers={
            "x-api-key": api_key,
            "anthropic-version": ANTHROPIC_VERSION,
            "content-type": "application/json",
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            # Any 2xx means the key authenticated and the request succeeded.
            if 200 <= response.status < 300:
                print("✅ API key is VALID and working.")
                return True
            print(f"⚠️  Unexpected status: {response.status}")
            return False

    except urllib.error.HTTPError as err:
        body = err.read().decode("utf-8", errors="replace")
        try:
            error_type = json.loads(body).get("error", {}).get("type", "")
        except json.JSONDecodeError:
            error_type = ""

        if err.code == 401:
            print("❌ API key is INVALID (401 authentication_error).")
        elif err.code == 403:
            print("❌ Key authenticated but lacks permission (403 permission_error).")
        elif err.code == 429:
            # The key itself is valid; you've just hit a rate/credit limit.
            print("✅ API key is VALID, but you've hit a rate or credit limit (429).")
            return True
        elif err.code == 400 and error_type == "invalid_request_error":
            # The key was accepted; the request shape was the only problem.
            print("✅ API key is VALID (request was authenticated; 400 was a request issue).")
            return True
        else:
            print(f"❌ Request failed: HTTP {err.code} {error_type}")
            print(f"   Details: {body}")
        return False

    except urllib.error.URLError as err:
        print(f"❌ Could not reach the API (network/SSL issue): {err.reason}")
        return False


def main() -> None:
    # Priority: command-line argument, then environment variable.
    api_key = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("ANTHROPIC_API_KEY")

    if not api_key:
        print("No API key found.")
        print("Set the ANTHROPIC_API_KEY environment variable, or pass the key as an argument:")
        print("    python check_api_key.py sk-ant-...")
        sys.exit(2)

    is_valid = check_api_key(api_key.strip())
    sys.exit(0 if is_valid else 1)


if __name__ == "__main__":
    main()