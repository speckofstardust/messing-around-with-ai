#!/usr/bin/env python3
"""
System health monitoring agent using Claude API with tool use.
Usage: python agent.py
Requires: ANTHROPIC_API_KEY environment variable
"""

import json
import os
import sys

import anthropic

from prompts import MODEL, MAX_TOKENS, SYSTEM_PROMPT
from tools import TOOLS, TOOL_DISPATCH

MAX_TURNS = 5


def run_agent() -> None:
    client = anthropic.Anthropic()

    messages = [
        {
            "role": "user",
            "content": "Please perform a complete system health check and produce a health report.",
        }
    ]

    for _ in range(MAX_TURNS):
        try:
            response = client.messages.create(
                model=MODEL,
                max_tokens=MAX_TOKENS,
                system=[
                    {
                        "type": "text",
                        "text": SYSTEM_PROMPT,
                        "cache_control": {"type": "ephemeral"},
                    }
                ],
                tools=TOOLS,
                messages=messages,
            )
        except anthropic.AuthenticationError:
            sys.exit("Error: Invalid API key. Check your ANTHROPIC_API_KEY.")
        except anthropic.RateLimitError:
            sys.exit("Error: Rate limit reached. Please retry later.")
        except anthropic.APIConnectionError as e:
            sys.exit(f"Error: Could not connect to the API. {e}")
        except anthropic.APIStatusError as e:
            sys.exit(f"Error: API returned status {e.status_code}: {e.message}")

        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "end_turn":
            for block in response.content:
                if block.type == "text":
                    print(block.text)
            return

        if response.stop_reason != "tool_use":
            print(
                f"[Agent stopped unexpectedly: stop_reason={response.stop_reason}]",
                file=sys.stderr,
            )
            return

        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                fn = TOOL_DISPATCH.get(block.name)
                if fn is None:
                    content = f"Error: unknown tool '{block.name}'"
                    is_error = True
                else:
                    try:
                        data = fn(**block.input)
                        content = json.dumps(data, indent=2)
                        is_error = False
                    except Exception as exc:
                        content = f"Error running {block.name}: {exc}"
                        is_error = True

                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": content,
                        "is_error": is_error,
                    }
                )

        messages.append({"role": "user", "content": tool_results})

    print("[Agent exceeded maximum turns without producing a report.]", file=sys.stderr)


def main() -> None:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("Error: ANTHROPIC_API_KEY environment variable is not set.")
    run_agent()


if __name__ == "__main__":
    main()
