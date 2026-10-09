# Module 2 — Report agent

**Branch outcome:** `python -m module_2.smoke_report --endpoint qwen3` exits 0 and leaves a file under `reports/`.

Prerequisite: Module 1 stack works (key + venv + smoke green). Same frozen endpoints.

## Student path

1. Stay in the lab folder (venv active, `.env` set).
2. Read `report_agent.py` — tools are `get_weather` and `write_report`.
3. Run: `python -m module_2.report_agent --endpoint qwen3 --city Tokyo`
4. Open the path printed under `reports/`.
5. Run smoke: `python -m module_2.smoke_report --endpoint qwen3`

## Pass rule

A chat-only answer is not enough. `write_report` must create a markdown file that names the city.
