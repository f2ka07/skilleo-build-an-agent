# Lesson log — Module 1 tool calling (dev)

Evidence from running the lab path in this environment. Slide narration should
walk students through the same issues and recoveries.

## Frozen stack that passed

- **Qwen3 32B AWQ** — `https://api.runpod.ai/v2/qwen3-32b-awq/openai/v1`  
  model `Qwen/Qwen3-32B-AWQ`
- **Kimi** — `https://api.runpod.ai/v2/moonshot-kimi/openai/v1`  
  model `kimi-k2.6` (select+args smoke only; full suite scripted for both)

### Behaviour matrix (Qwen3, 2026-10-09)

| # | Behaviour | Result | Teach |
|---|-----------|--------|-------|
| 1 | Select `get_weather` + `city=Tokyo` | PASS — `finish_reason=tool_calls`, structured `tool_calls` | Fail if model only writes “I would call get_weather…” |
| 2 | Use tool result (18°C cloudy) | PASS — answer cites tool payload | Show second-turn messages: assistant tool_calls + role=tool |
| 3 | No tool for `2+2` | PASS | Tools are optional; math should not invent weather |
| 4 | Missing city (“weather there?”) | PASS — asked for city, no tool | Watch for models that guess a city |
| 5 | Tool error (timeout JSON) | PASS — acknowledged timeout, offered retry | Must not invent weather after error |

Notes for slides:

- Qwen3 sometimes prefixes content with blank lines / light “thinking” prose before
  `<response>`-style text on missing-info. Students should inspect `tool_calls`
  first, then content — structured fields are the pass criteria.
- Cold public endpoints can take 10–30s on first call. Narrate waiting; do not
  treat latency as failure.
- `openai` Python package must be installed (`pip install -r requirements.txt`).
  Missing package is an early intentional stumble.

## Issues students should hit (and resolve)

1. **Missing `RUNPOD_API_KEY`** — script exits with setup steps (copy `.env.example`).
2. **Wrong / empty base URL** — 404 or auth errors; fix endpoint id.
3. **Missing `openai` package** — `ModuleNotFoundError`; `pip install -r requirements.txt`.
4. **Prose-only “tool call”** — if a model fails, show the failing printout; swap to
   the other preset (`--endpoint kimi`) or fix tool schema / prompt.
5. **Cold start wait** — first request slow; retry once before declaring fail.

## Next outcome branches

- `module-1-tool-calling` — this smoke suite green on Qwen3 (and optional Kimi).
- `module-2-report-agent` — `python -m module_2.smoke_report` green; file under `reports/`.
- Narrated Skilleo Module 1 — `docs-prompts/Build-An-Agent/module-1-script.md`.
- Narrated Skilleo Module 2 — `docs-prompts/Build-An-Agent/module-2-script.md`.

## Module 2 notes (report agent)

- Same `.env` and venv as Module 1 — no new key.
- Tools: `get_weather` (controlled test data) + `write_report` (writes `reports/*.md`).
- Pass rule: chat-only answers fail; `write_report` must create a file that names the city.
- Cold endpoint waits still apply; narrate the hold on Code + CLI slides.
