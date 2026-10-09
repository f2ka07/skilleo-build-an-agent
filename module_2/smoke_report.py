"""Prove the report agent saved a real file (Module 2 outcome).

Usage:
  python -m module_2.smoke_report --endpoint qwen3
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from module_2.report_agent import REPORTS_DIR, run_agent


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Module 2 report smoke")
    parser.add_argument("--endpoint", default="qwen3")
    parser.add_argument("--city", default="Tokyo")
    args = parser.parse_args(argv)

    before = set(REPORTS_DIR.glob("*.md")) if REPORTS_DIR.is_dir() else set()
    prompt = (
        f"Write a short weather brief for {args.city}. "
        "Use get_weather, then write_report. The report must name the city."
    )
    print(f"Smoke: report agent on {args.endpoint} for {args.city}")
    try:
        out = run_agent(prompt=prompt, endpoint=args.endpoint)
    except SystemExit as exc:
        print(exc, file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"FAIL  agent error: {exc}", file=sys.stderr)
        return 1

    path_s = out.get("saved_path")
    if not path_s:
        print("FAIL  1 save: write_report never produced a path")
        return 1
    path = Path(path_s)
    if not path.is_file():
        # Allow relative path from lab root
        from module_2.report_agent import ROOT

        path = ROOT / path_s
    if not path.is_file():
        print(f"FAIL  1 save: missing file {path_s}")
        return 1
    print(f"PASS  1 save → {path_s}")

    text = path.read_text(encoding="utf-8")
    city = args.city.strip()
    if city.lower() not in text.lower():
        print(f"FAIL  2 content: report does not mention {city}")
        return 1
    print(f"PASS  2 content mentions {city}")

    after = set(REPORTS_DIR.glob("*.md"))
    if path.resolve() not in {p.resolve() for p in after} and not path.is_file():
        print("FAIL  3 disk: report not under reports/")
        return 1
    new_files = after - before
    print(f"PASS  3 disk ({len(new_files) or 1} report file(s) in reports/)")
    print("All Module 2 checks green.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
