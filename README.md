# Build an Agent (RunPod)

Hands-on agent course adapted from [brevdev/workshop-build-an-agent](https://github.com/brevdev/workshop-build-an-agent),
using **RunPod OpenAI-compatible endpoints** instead of NVIDIA NIM.

## Pedagogy

1. Configure API keys when first needed (not a long platform tour).
2. Explain the code on screen.
3. Run the CLI — expect errors or success.
4. Explain what the output means.
5. Behaviour tests live **in the lab**: students observe tool selection, args, results, missing info, and failures.

## Repo layout (git branches = outcomes)

| Branch | Outcome |
|--------|---------|
| `main` | Scaffold + docs |
| `module-1-tool-calling` | Smoke suite proves real tool calling on a frozen endpoint |
| `module-1-report-agent` *(later)* | Report agent writes a useful saved report |
| `module-2+` | Provisional until M1 is solid |

## Quick start (Module 1)

```bash
cd workshops/build-an-agent-runpod
python -m venv .venv
# Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env   # set RUNPOD_API_KEY

python -m module_1.smoke_tools --endpoint qwen3
```

Pass rule: `message.tool_calls` must be present for tool cases. Text that only *describes* a call fails.

## Frozen stack (dev evidence 2026-10-09)

| Endpoint | Model id | Tool calling |
|----------|----------|--------------|
| `qwen3-32b-awq` | `Qwen/Qwen3-32B-AWQ` | Real `tool_calls` — preferred start |
| `moonshot-kimi` | `kimi-k2.6` | Real `tool_calls` |

See `LESSON-LOG.md` for behaviours observed and issues to teach.
