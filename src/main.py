import json
import os
import sys
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))

from collect import collect_all
from analyze import analyze
from render import render_reports

ROOT = Path(__file__).parent.parent
REPORTS_DIR = ROOT / "reports"
DOCS_DIR = ROOT / "docs"
TEMPLATES_DIR = ROOT / "templates"


def main():
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    print(f"=== ImouPulse run: {date_str} ===")

    print("\n[1/3] Collecting...")
    source_results = collect_all()
    source_dicts = [asdict(r) for r in source_results]

    raw_path = REPORTS_DIR / f"raw_{date_str}.json"
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    raw_path.write_text(json.dumps(source_dicts, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(f"  Raw data saved to {raw_path}")

    print("\n[2/3] Analyzing...")
    answers = analyze(source_dicts)

    answers_path = REPORTS_DIR / f"answers_{date_str}.json"
    answers_path.write_text(json.dumps(answers, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  Answers saved to {answers_path}")

    print("\n[3/3] Rendering...")
    render_reports(
        date_str=date_str,
        answers=answers,
        templates_dir=str(TEMPLATES_DIR),
        docs_dir=str(DOCS_DIR),
    )
    print(f"  HTML written to {DOCS_DIR}/zh/ and {DOCS_DIR}/en/")

    print(f"\n=== Done. Open docs/zh/index.html to preview. ===")


if __name__ == "__main__":
    main()
