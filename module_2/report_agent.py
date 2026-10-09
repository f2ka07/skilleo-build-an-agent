"""Small report agent: gather facts with tools, then save a markdown report.

Outcome: a real file under ``reports/`` — not only chat text.

Usage:
  python -m module_2.report_agent --endpoint qwen3 --city Tokyo
  python -m module_2.report_agent --endpoint qwen3 --prompt "Write a short weather brief for Paris"
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from openai import OpenAI

from module_2.config import resolve_stack

ROOT = Path(__file__).resolve().parent.parent
REPORTS_DIR = ROOT / "reports"

REPORT_TOOLS: list[dict[str, Any]] = [
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
    },
    {
        "type": "function",
        "function": {
            "name": "write_report",
            "description": (
                "Save a short markdown report to disk. "
                "Call this when you have enough facts to write a useful brief."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Report title"},
                    "body": {
                        "type": "string",
                        "description": "Markdown body with headings and short paragraphs",
                    },
                },
                "required": ["title", "body"],
            },
        },
    },
]


def _slug(text: str) -> str:
    raw = re.sub(r"[^a-zA-Z0-9]+", "-", (text or "").strip().lower()).strip("-")
    return (raw or "report")[:48]


def get_weather(city: str) -> dict[str, Any]:
    """Controlled lab weather — same idea as Module 1 (not a live feed)."""
    samples = {
        "tokyo": {"temp_c": 18, "condition": "cloudy", "city": "Tokyo"},
        "paris": {"temp_c": 14, "condition": "light rain", "city": "Paris"},
        "sydney": {"temp_c": 22, "condition": "sunny", "city": "Sydney"},
    }
    key = (city or "").strip().lower()
    hit = samples.get(key)
    if hit:
        return dict(hit)
    return {
        "temp_c": 20,
        "condition": "clear",
        "city": (city or "Unknown").strip() or "Unknown",
    }


def write_report(title: str, body: str) -> dict[str, Any]:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    path = REPORTS_DIR / f"{stamp}-{_slug(title)}.md"
    text = f"# {title.strip()}\n\n{body.strip()}\n"
    path.write_text(text, encoding="utf-8")
    return {"ok": True, "path": str(path.relative_to(ROOT)).replace("\\", "/")}


def run_tool(name: str, arguments: str) -> str:
    try:
        args = json.loads(arguments or "{}")
    except json.JSONDecodeError:
        return json.dumps({"error": "invalid JSON arguments"})
    if name == "get_weather":
        return json.dumps(get_weather(str(args.get("city") or "")))
    if name == "write_report":
        return json.dumps(
            write_report(str(args.get("title") or "Report"), str(args.get("body") or ""))
        )
    return json.dumps({"error": f"unknown tool {name}"})


def _assistant_message(message: Any) -> dict[str, Any]:
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
        "tool_calls": tool_calls or None,
    }


def run_agent(*, prompt: str, endpoint: str, max_rounds: int = 4) -> dict[str, Any]:
    stack = resolve_stack(endpoint)
    client = OpenAI(api_key=stack.api_key, base_url=stack.base_url)
    messages: list[dict[str, Any]] = [
        {
            "role": "system",
            "content": (
                "You are a report agent. Use tools when you need facts. "
                "When you have enough information, call write_report to save a short markdown brief. "
                "Do not claim you saved a file unless write_report returned ok."
            ),
        },
        {"role": "user", "content": prompt},
    ]
    saved_path: str | None = None
    for _ in range(max_rounds):
        resp = client.chat.completions.create(
            model=stack.model,
            messages=messages,
            tools=REPORT_TOOLS,
            tool_choice="auto",
            max_tokens=600,
        )
        message = resp.choices[0].message
        messages.append(_assistant_message(message))
        calls = message.tool_calls or []
        if not calls:
            break
        for tc in calls:
            name = tc.function.name
            result = run_tool(name, tc.function.arguments)
            if name == "write_report":
                try:
                    payload = json.loads(result)
                    if payload.get("ok") and payload.get("path"):
                        saved_path = str(payload["path"])
                except json.JSONDecodeError:
                    pass
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": result,
                }
            )
        if saved_path:
            break
    return {
        "endpoint": stack.label,
        "model": stack.model,
        "saved_path": saved_path,
        "final_text": (messages[-1].get("content") if messages else None),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Module 2 report agent")
    parser.add_argument("--endpoint", default="qwen3", help="qwen3 or kimi")
    parser.add_argument("--city", default="", help="City for a weather brief")
    parser.add_argument(
        "--prompt",
        default="",
        help="Full user prompt (overrides --city)",
    )
    args = parser.parse_args(argv)
    city = (args.city or "Tokyo").strip()
    prompt = (args.prompt or "").strip() or (
        f"Write a short weather brief for {city}. "
        "Use tools. Save a markdown report with the city name and conditions."
    )
    print(f"Running report agent ({args.endpoint})…")
    print(f"Prompt: {prompt}")
    try:
        out = run_agent(prompt=prompt, endpoint=args.endpoint)
    except SystemExit as exc:
        print(exc, file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"FAIL agent: {exc}", file=sys.stderr)
        return 1
    print(f"Endpoint: {out['endpoint']}")
    if out.get("saved_path"):
        print(f"PASS  report saved → {out['saved_path']}")
        return 0
    print("FAIL  no report file — model never called write_report successfully")
    if out.get("final_text"):
        print((out["final_text"] or "")[:400])
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
