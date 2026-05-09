import time
import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta, timezone
from typing import Literal, Optional
from urllib.parse import quote_plus

import feedparser
import requests

import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from config import (
    SUBREDDITS, REDDIT_LOOKBACK_DAYS,
    GOOGLE_NEWS_QUERIES, NEWS_LOOKBACK_DAYS,
    INNOVATION_SOURCES, INNOVATION_LOOKBACK_DAYS,
    TRENDS_KW_EU, TRENDS_KW_GLOBAL, TRENDS_TIMEFRAME,
    HTTP_TIMEOUT, HTTP_HEADERS,
)


@dataclass
class CollectedItem:
    source: str
    title: str
    summary: str
    url: str
    published_at: str
    collected_at: str


@dataclass
class SourceResult:
    source_id: str
    status: Literal["ok", "failed", "empty"]
    error: Optional[str] = None
    items: list = field(default_factory=list)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_published(entry) -> Optional[datetime]:
    for attr in ("published_parsed", "updated_parsed"):
        t = getattr(entry, attr, None)
        if t:
            try:
                return datetime(*t[:6], tzinfo=timezone.utc)
            except Exception:
                pass
    return None


def _cutoff(days: int) -> datetime:
    return datetime.now(timezone.utc) - timedelta(days=days)


def _truncate(text: str, max_len: int) -> str:
    text = (text or "").strip()
    return text[:max_len] if len(text) > max_len else text


def _item_from_entry(source_id: str, entry, cutoff: datetime) -> Optional[CollectedItem]:
    pub = _parse_published(entry)
    if pub and pub < cutoff:
        return None
    title = _truncate(getattr(entry, "title", ""), 300)
    summary = _truncate(getattr(entry, "summary", "") or getattr(entry, "description", ""), 500)
    url = getattr(entry, "link", "")
    if not title or not url:
        return None
    return CollectedItem(
        source=source_id,
        title=title,
        summary=summary,
        url=url,
        published_at=pub.isoformat() if pub else "",
        collected_at=_now_iso(),
    )


def _dedup(items: list[CollectedItem]) -> list[CollectedItem]:
    seen: set[str] = set()
    out = []
    for it in items:
        if it.url not in seen:
            seen.add(it.url)
            out.append(it)
    return out


# ── Reddit ────────────────────────────────────────────────────────────────────

def collect_reddit() -> list[SourceResult]:
    results = []
    cutoff = _cutoff(REDDIT_LOOKBACK_DAYS)
    for sub in SUBREDDITS:
        source_id = f"reddit:r/{sub}"
        url = f"https://www.reddit.com/r/{sub}/new.rss?limit=25"
        try:
            resp = requests.get(url, headers=HTTP_HEADERS, timeout=HTTP_TIMEOUT)
            resp.raise_for_status()
            feed = feedparser.parse(resp.content)
            items = []
            for entry in feed.entries:
                item = _item_from_entry(source_id, entry, cutoff)
                if item:
                    items.append(item)
            status = "ok" if items else "empty"
            results.append(SourceResult(source_id=source_id, status=status, items=items))
        except Exception as e:
            results.append(SourceResult(source_id=source_id, status="failed", error=str(e)))
        time.sleep(0.5)
    return results


# ── Google News ───────────────────────────────────────────────────────────────

def collect_google_news() -> list[SourceResult]:
    results = []
    cutoff = _cutoff(NEWS_LOOKBACK_DAYS)
    base = "https://news.google.com/rss/search?hl=en-US&gl=US&ceid=US:en&q={q}"
    for query in GOOGLE_NEWS_QUERIES:
        source_id = f"googlenews:{query}"
        url = base.format(q=quote_plus(query))
        try:
            resp = requests.get(url, headers=HTTP_HEADERS, timeout=HTTP_TIMEOUT)
            resp.raise_for_status()
            feed = feedparser.parse(resp.content)
            items = []
            for entry in feed.entries[:10]:
                item = _item_from_entry(source_id, entry, cutoff)
                if item:
                    items.append(item)
            status = "ok" if items else "empty"
            results.append(SourceResult(source_id=source_id, status=status, items=items))
        except Exception as e:
            results.append(SourceResult(source_id=source_id, status="failed", error=str(e)))
        time.sleep(1.0)
    return results


# ── Innovation sources ────────────────────────────────────────────────────────

def _keyword_match(entry, keywords: list[str]) -> bool:
    if not keywords:
        return True
    text = (
        getattr(entry, "title", "") + " " +
        getattr(entry, "summary", "") + " " +
        getattr(entry, "description", "")
    ).lower()
    return any(kw.lower() in text for kw in keywords)


def collect_innovation() -> list[SourceResult]:
    results = []
    cutoff = _cutoff(INNOVATION_LOOKBACK_DAYS)
    for src in INNOVATION_SOURCES:
        source_id = src["id"]
        try:
            resp = requests.get(src["url"], headers=HTTP_HEADERS, timeout=HTTP_TIMEOUT)
            resp.raise_for_status()
            feed = feedparser.parse(resp.content)
            items = []
            for entry in feed.entries[:15]:
                if not _keyword_match(entry, src["keywords"]):
                    continue
                item = _item_from_entry(source_id, entry, cutoff)
                if item:
                    items.append(item)
            status = "ok" if items else "empty"
            results.append(SourceResult(source_id=source_id, status=status, items=items))
        except Exception as e:
            results.append(SourceResult(source_id=source_id, status="failed", error=str(e)))
        time.sleep(0.5)
    return results


# ── Google Trends ─────────────────────────────────────────────────────────────

def collect_trends() -> list[SourceResult]:
    try:
        from pytrends.request import TrendReq
    except ImportError:
        return [SourceResult(source_id="trends", status="failed", error="pytrends not installed")]

    results = []
    groups = [
        ("trends:eu", TRENDS_KW_EU, "GB"),
        ("trends:global", TRENDS_KW_GLOBAL, ""),
    ]
    for source_id, kws, geo in groups:
        for attempt in range(2):
            try:
                pt = TrendReq(hl="en-US", tz=0, timeout=(10, 30))
                pt.build_payload(kws, timeframe=TRENDS_TIMEFRAME, geo=geo)
                df = pt.interest_over_time()
                if df.empty:
                    results.append(SourceResult(source_id=source_id, status="empty"))
                    break
                # Serialize to a list of CollectedItem-like dicts for LLM formatting
                rows = []
                for kw in kws:
                    if kw in df.columns:
                        avg = int(df[kw].mean())
                        peak = int(df[kw].max())
                        rows.append(CollectedItem(
                            source=source_id,
                            title=f"Trend: {kw}",
                            summary=f"7-day average interest: {avg}/100, peak: {peak}/100 (geo={'EU(GB)' if geo else 'Global'})",
                            url="https://trends.google.com",
                            published_at=_now_iso(),
                            collected_at=_now_iso(),
                        ))
                results.append(SourceResult(source_id=source_id, status="ok", items=rows))
                break
            except Exception as e:
                if attempt == 0 and "429" in str(e):
                    time.sleep(60)
                else:
                    results.append(SourceResult(source_id=source_id, status="failed", error=str(e)))
                    break
    return results


# ── Entry point ───────────────────────────────────────────────────────────────

def collect_all() -> list[SourceResult]:
    print("Collecting Reddit...")
    reddit = collect_reddit()
    print("Collecting Google News...")
    news = collect_google_news()
    print("Collecting innovation sources...")
    innovation = collect_innovation()
    print("Collecting Google Trends...")
    trends = collect_trends()

    all_results = reddit + news + innovation + trends

    ok = sum(1 for r in all_results if r.status == "ok")
    failed = sum(1 for r in all_results if r.status == "failed")
    empty = sum(1 for r in all_results if r.status == "empty")
    total_items = sum(len(r.items) for r in all_results)
    print(f"Collection done: {ok} ok / {empty} empty / {failed} failed — {total_items} items total")

    if ok == 0 and empty == len(all_results):
        print("WARNING: all sources returned empty (no recent content)")
    if failed == len(all_results):
        raise RuntimeError("All sources failed. Aborting.")

    return all_results


if __name__ == "__main__":
    results = collect_all()
    out_path = os.path.join(os.path.dirname(__file__), "..", "reports", "raw_collected.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump([asdict(r) for r in results], f, ensure_ascii=False, indent=2, default=str)
    print(f"Saved to {out_path}")
