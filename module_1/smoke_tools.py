"""Behaviour smoke for real tool calling (not prose that describes a call).

Cases students will also run in the lab:
  1. select correct tool + valid args
  2. use the returned tool result
  3. answer without a tool when appropriate
  4. missing information (ask; do not invent a city)
  5. tool error (acknowledge / retry — do not hallucinate weather)

Usage:
  python -m module_1.smoke_tools --endpoint qwen3
  python -m module_1.smoke_tools --endpoint kimi
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from openai import OpenAI

from module_1.config import resolve_stack

WEATHER_TOOLS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get current weather for a city. Requires a city name.",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "City name"},
                },
                "required": ["city"],
            },
        },
    }
]


def _assistant_tool_message(message: Any) -> dict[str, Any]:
    tool_calls = []
    for tc in message.tool_calls or []:
        tool_calls.append(
            {
                "id": tc.id,
                "type": "function",
                "function": {
                    "name": tc.function.name,
                    "arguments": tc.function.arguments,
                },
            }
        )
    return {
        "role": "assistant",
        "content": message.content,
        "tool_calls": tool_calls,
    }


def chat(client: OpenAI, model: str, messages: list[dict[str, Any]], **kw: Any):
    return client.chat.completions.create(
        model=model,
        messages=messages,
        tools=WEATHER_TOOLS,
        tool_choice="auto",
        max_tokens=400,
        **kw,
    )


def require_tool_call(label: str, message: Any) -> Any:
    calls = message.tool_calls or []
    if not calls:
        content = (message.content or "").strip()
        raise AssertionError(
            f"FAIL {label}: expected structured tool_calls, got prose only:\n{content[:300]}"
        )
    return calls[0]


def require_no_tool(label: str, message: Any) -> None:
    if message.tool_calls:
        names = [tc.function.name for tc in message.tool_calls]
        raise AssertionError(f"FAIL {label}: expected no tool, got {names}")


def run_suite(alias: str) -> int:
    stack = resolve_stack(alias)
    print(f"Stack: {stack.label}")
    print(f"  base_url: {stack.base_url}")
    print(f"  model:    {stack.model}")
    client = OpenAI(api_key=stack.api_key, base_url=stack.base_url)
    failures: list[str] = []

    def step(label: str, fn) -> None:
        try:
            fn()
            print(f"PASS  {label}")
        except Exception as exc:  # noqa: BLE001
            print(f"FAIL  {label}: {exc}")
            failures.append(label)

    # 1 — select tool + args
    m1_holder: dict[str, Any] = {}

    def select_args() -> None:
        r = chat(
            client,
            stack.model,
            [{"role": "user", "content": "What is the weather in Tokyo right now?"}],
        )
        m = r.choices[0].message
        tc = require_tool_call("select+args", m)
        if tc.function.name != "get_weather":
            raise AssertionError(f"wrong tool {tc.function.name}")
        args = json.loads(tc.function.arguments or "{}")
        if str(args.get("city") or "").lower() != "tokyo":
            raise AssertionError(f"bad args {args}")
        m1_holder["m"] = m
        m1_holder["tc"] = tc

    step("1 select+args", select_args)

    # 2 — use result
    def use_result() -> None:
        m = m1_holder.get("m")
        tc = m1_holder.get("tc")
        if not m or not tc:
            raise AssertionError("skipped — select+args failed")
        r = chat(
            client,
            stack.model,
            [
                {"role": "user", "content": "What is the weather in Tokyo right now?"},
                _assistant_tool_message(m),
                {
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": json.dumps(
                        {"city": "Tokyo", "temp_c": 18, "condition": "cloudy"}
                    ),
                },
            ],
        )
        msg = r.choices[0].message
        require_no_tool("use_result", msg)
        text = (msg.content or "").lower()
        if "18" not in text and "cloudy" not in text:
            raise AssertionError(f"did not use tool result: {msg.content!r}")

    step("2 use_result", use_result)

    # 3 — no tool
    def no_tool() -> None:
        r = chat(
            client,
            stack.model,
            [{"role": "user", "content": "What is 2+2? Answer briefly with no tools."}],
        )
        msg = r.choices[0].message
        require_no_tool("no_tool", msg)
        if "4" not in (msg.content or ""):
            raise AssertionError(f"unexpected answer: {msg.content!r}")

    step("3 no_tool", no_tool)

    # 4 — missing info
    def missing_info() -> None:
        r = chat(
            client,
            stack.model,
            [{"role": "user", "content": "What is the weather there?"}],
        )
        msg = r.choices[0].message
        # Prefer ask-back with no tool. If it tools with a guessed city, fail.
        if msg.tool_calls:
            args = json.loads(msg.tool_calls[0].function.arguments or "{}")
            raise AssertionError(f"guessed a city instead of asking: {args}")
        text = (msg.content or "").lower()
        if "city" not in text and "where" not in text and "which" not in text:
            raise AssertionError(f"did not ask for city: {msg.content!r}")

    step("4 missing_info", missing_info)

    # 5 — tool error
    def tool_error() -> None:
        m = m1_holder.get("m")
        tc = m1_holder.get("tc")
        if not m or not tc:
            raise AssertionError("skipped — select+args failed")
        r = chat(
            client,
            stack.model,
            [
                {"role": "user", "content": "What is the weather in Tokyo right now?"},
                _assistant_tool_message(m),
                {
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": json.dumps(
                        {
                            "error": "upstream_timeout",
                            "message": "Weather API timed out",
                        }
                    ),
                },
            ],
        )
        msg = r.choices[0].message
        require_no_tool("tool_error", msg)
        text = (msg.content or "").lower()
        if "timeout" not in text and "error" not in text and "issue" not in text:
            raise AssertionError(f"did not acknowledge error: {msg.content!r}")
        # Must not invent a temperature after failure
        if "18°" in text or "18c" in text.replace(" ", ""):
            raise AssertionError(f"hallucinated weather after error: {msg.content!r}")

    step("5 tool_error", tool_error)

    print()
    if failures:
        print(f"{len(failures)} failure(s): {', '.join(failures)}")
        return 1
    print("All behaviour checks passed — real tool calling confirmed.")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Module 1 tool-calling behaviour smoke")
    p.add_argument(
        "--endpoint",
        default="qwen3",
        choices=sorted({"qwen3", "kimi"}),
        help="Preset endpoint alias",
    )
    args = p.parse_args(argv)
    return run_suite(args.endpoint)


if __name__ == "__main__":
    sys.exit(main())
