"""Endpoint config — students set RUNPOD_API_KEY in .env when first needed."""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()

ENDPOINTS = {
    "qwen3": {
        "endpoint": "qwen3-32b-awq",
        "model": "Qwen/Qwen3-32B-AWQ",
        "label": "Qwen3 32B AWQ",
    },
    "kimi": {
        "endpoint": "moonshot-kimi",
        "model": "kimi-k2.6",
        "label": "Moonshot Kimi",
    },
}


@dataclass(frozen=True)
class AgentStack:
    api_key: str
    endpoint: str
    model: str
    label: str

    @property
    def base_url(self) -> str:
        return f"https://api.runpod.ai/v2/{self.endpoint}/openai/v1"


def resolve_stack(alias: str | None = None) -> AgentStack:
    key = (os.environ.get("RUNPOD_API_KEY") or "").strip()
    if not key:
        raise SystemExit(
            "RUNPOD_API_KEY is missing.\n"
            "1) Create a key at https://www.runpod.io/console/user/settings\n"
            "2) Copy workshops/build-an-agent-runpod/.env.example → .env\n"
            "3) Set RUNPOD_API_KEY=… and re-run."
        )
    name = (alias or os.environ.get("AGENT_ENDPOINT_ALIAS") or "qwen3").strip().lower()
    if name in {"qwen3-32b-awq", "qwen"}:
        name = "qwen3"
    if name in {"moonshot-kimi", "kimi-k2.6"}:
        name = "kimi"
    preset = ENDPOINTS.get(name) or ENDPOINTS["qwen3"]
    endpoint = (os.environ.get("AGENT_ENDPOINT") or preset["endpoint"]).strip()
    model = (os.environ.get("AGENT_MODEL") or preset["model"]).strip()
    return AgentStack(
        api_key=key,
        endpoint=endpoint,
        model=model,
        label=preset["label"],
    )
