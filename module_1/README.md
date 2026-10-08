# Module 1 — Tool calling

**Branch outcome:** `python -m module_1.smoke_tools --endpoint qwen3` exits 0.

## Student path

1. Set `RUNPOD_API_KEY` in `.env` (first time keys are needed).
2. `pip install -r requirements.txt`
3. Read `smoke_tools.py` — especially `WEATHER_TOOLS` and the five steps.
4. Run the suite. Inspect PASS/FAIL lines.
5. If FAIL: check `../LESSON-LOG.md`, try `--endpoint kimi`, fix env/packages.

## Files

| File | Role |
|------|------|
| `config.py` | Resolves RunPod base URL + model; guided exit if key missing |
| `smoke_tools.py` | Behaviour matrix (select, args, use result, no tool, missing, error) |
