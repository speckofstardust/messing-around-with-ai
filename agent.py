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
import psutil

MODEL = "claude-sonnet-4-6"
MAX_TOKENS = 1024
MAX_TURNS = 5

SYSTEM_PROMPT = """\
You are a system health monitoring agent running on a Linux machine.

Your job:
1. Call ALL THREE tools — check_cpu, check_memory, and check_disk — to collect current metrics.
2. After you have results from all three tools, write a concise plain-text health report.

Report format (strictly plain text, no markdown, no # headers):
- First line: overall health verdict (HEALTHY / WARNING / CRITICAL)
- Blank line
- CPU section: utilization %, core count, clock speed
- Memory section: RAM usage GB and %, swap usage GB and %
- Disk section: used/total GB and % for /
- Blank line
- One paragraph of plain-language interpretation: what the numbers mean, which resources
  (if any) are under pressure, and any recommended actions.

Rules:
- Never fabricate metrics. Only report numbers returned by the tools.
- Use WARNING if any metric is above 70%. Use CRITICAL if any is above 90%.
- Keep the report under 300 words.
- Output only the report — no preamble, no "here is your report", no sign-off.\
"""

TOOLS = [
    {
        "name": "check_cpu",
        "description": (
            "Returns current CPU utilization percentage, logical and physical core count, "
            "and clock frequency in MHz. Call this to assess CPU load."
        ),
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "check_memory",
        "description": (
            "Returns RAM and swap usage: total, used, available in GB and percent used. "
            "Call this to assess memory pressure."
        ),
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "check_disk",
        "description": (
            "Returns disk usage for the root filesystem (/): total, used, free in GB "
            "and percent used. Call this to assess disk capacity."
        ),
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
]


def check_cpu(**kwargs) -> dict:
    freq = psutil.cpu_freq()
    return {
        "cpu_percent": psutil.cpu_percent(interval=1),
        "logical_cores": psutil.cpu_count(logical=True),
        "physical_cores": psutil.cpu_count(logical=False),
        "frequency_mhz": round(freq.current, 1) if freq else None,
        "frequency_max_mhz": round(freq.max, 1) if freq else None,
    }


def check_memory(**kwargs) -> dict:
    vm = psutil.virtual_memory()
    sw = psutil.swap_memory()
    gb = 1024 ** 3
    return {
        "ram_total_gb": round(vm.total / gb, 2),
        "ram_used_gb": round(vm.used / gb, 2),
        "ram_available_gb": round(vm.available / gb, 2),
        "ram_percent": vm.percent,
        "swap_total_gb": round(sw.total / gb, 2),
        "swap_used_gb": round(sw.used / gb, 2),
        "swap_percent": sw.percent,
    }


def check_disk(**kwargs) -> dict:
    du = psutil.disk_usage("/")
    gb = 1024 ** 3
    return {
        "mount": "/",
        "total_gb": round(du.total / gb, 2),
        "used_gb": round(du.used / gb, 2),
        "free_gb": round(du.free / gb, 2),
        "percent_used": du.percent,
    }


TOOL_DISPATCH = {
    "check_cpu": check_cpu,
    "check_memory": check_memory,
    "check_disk": check_disk,
}


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
