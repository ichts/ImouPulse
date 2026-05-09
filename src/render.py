import os
import re
from datetime import datetime, timezone
from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from markupsafe import Markup

import sys
sys.path.insert(0, os.path.dirname(__file__))


SECTION_TITLES_ZH = {
    "q1": "竞品动态",
    "q2": "竞品舆情",
    "q3": "场景痛点",
    "q4": "车载与移动安防",
    "q5": "创新发现",
    "q6": "技术趋势",
    "q7": "市场热度",
    "q8": "本周 3 个信号",
}

SECTION_TITLES_EN = {
    "q1": "Competitor Updates",
    "q2": "Competitor Sentiment",
    "q3": "Scenario Pain Points",
    "q4": "Vehicle & Mobile Security",
    "q5": "Innovation Radar",
    "q6": "Technology Trends",
    "q7": "Market Momentum",
    "q8": "Top 3 Signals This Week",
}


def _escape(text: str) -> str:
    return (text
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;"))


def _md_to_html(text: str) -> Markup:
    url_pattern = re.compile(r"\[([^\]]+)\]\((https?://[^)]+)\)")
    bold_pattern = re.compile(r"\*\*(.+?)\*\*")

    def render_inline(s: str) -> str:
        s = _escape(s)
        s = bold_pattern.sub(lambda m: f"<strong>{m.group(1)}</strong>", s)
        s = url_pattern.sub(
            lambda m: f'<a href="{_escape(m.group(2))}" target="_blank" rel="noopener noreferrer">{_escape(m.group(1))}</a>',
            _escape(text) if s == _escape(text) else s,
        )
        return s

    def render_inline_safe(raw: str) -> str:
        escaped = _escape(raw)
        escaped = bold_pattern.sub(lambda m: f"<strong>{_escape(m.group(1))}</strong>", _escape(raw))
        escaped = url_pattern.sub(
            lambda m: f'<a href="{_escape(m.group(2))}" target="_blank" rel="noopener noreferrer">{_escape(m.group(1))}</a>',
            escaped,
        )
        return escaped

    lines = text.split("\n")
    html_lines = []
    in_list = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("- "):
            if not in_list:
                html_lines.append("<ul>")
                in_list = True
            html_lines.append(f"<li>{render_inline_safe(stripped[2:])}</li>")
        else:
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            if stripped:
                html_lines.append(f"<p>{render_inline_safe(stripped)}</p>")
    if in_list:
        html_lines.append("</ul>")
    return Markup("\n".join(html_lines))


def _build_sections(answers: dict[str, str], titles: dict[str, str]) -> list[dict]:
    sections = []
    for qid, title in titles.items():
        raw = answers.get(qid, "[No data]")
        sections.append({
            "id": qid,
            "title": title,
            "html_content": _md_to_html(raw),
        })
    return sections


def render_reports(date_str: str, answers: dict, templates_dir: str, docs_dir: str) -> None:
    env = Environment(loader=FileSystemLoader(templates_dir), autoescape=True)
    tmpl = env.get_template("report.html.j2")

    for lang, titles, alt_lang, alt_label in [
        ("zh", SECTION_TITLES_ZH, "en", "English"),
        ("en", SECTION_TITLES_EN, "zh", "中文"),
    ]:
        sections = _build_sections(answers[lang], titles)
        html = tmpl.render(
            date=date_str,
            lang=lang,
            sections=sections,
            alt_lang=alt_lang,
            alt_label=alt_label,
        )
        out_dir = Path(docs_dir) / lang
        out_dir.mkdir(parents=True, exist_ok=True)

        (out_dir / f"{date_str}.html").write_text(html, encoding="utf-8")
        (out_dir / "index.html").write_text(html, encoding="utf-8")

    _render_root_index(docs_dir)
    _render_archive(docs_dir)


def _render_root_index(docs_dir: str) -> None:
    html = '<!DOCTYPE html><html><head><meta charset="utf-8">'
    html += '<meta http-equiv="refresh" content="0; url=zh/index.html"></head>'
    html += '<body><a href="zh/index.html">中文版</a></body></html>'
    (Path(docs_dir) / "index.html").write_text(html, encoding="utf-8")


def _render_archive(docs_dir: str) -> None:
    zh_dir = Path(docs_dir) / "zh"
    dates = sorted(
        [p.stem for p in zh_dir.glob("????-??-??.html")],
        reverse=True,
    )
    rows = []
    for d in dates:
        rows.append(
            f'<tr><td>{d}</td>'
            f'<td><a href="zh/{d}.html">中文版</a></td>'
            f'<td><a href="en/{d}.html">English</a></td></tr>'
        )
    html = f"""<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>ImouPulse Archive</title>
<style>
  body {{ font-family: system-ui, sans-serif; max-width: 600px; margin: 40px auto; padding: 0 20px; }}
  h1 {{ font-size: 1.4rem; }}
  table {{ border-collapse: collapse; width: 100%; }}
  td {{ padding: 8px 12px; border-bottom: 1px solid #eee; }}
  a {{ color: #0066cc; }}
  .nav {{ margin-bottom: 24px; font-size: 0.9rem; }}
</style>
</head>
<body>
<div class="nav"><a href="zh/index.html">最新报告（中文）</a> · <a href="en/index.html">Latest Report (English)</a></div>
<h1>ImouPulse — Archive</h1>
<table>
<thead><tr><th>Date</th><th>中文</th><th>English</th></tr></thead>
<tbody>{"".join(rows)}</tbody>
</table>
</body>
</html>"""
    (Path(docs_dir) / "archive.html").write_text(html, encoding="utf-8")
