import os
import time
from dataclasses import asdict

from openai import OpenAI

import sys
sys.path.insert(0, os.path.dirname(__file__))
from config import (
    DEEPSEEK_BASE_URL, DEEPSEEK_MODEL,
    DEEPSEEK_TEMPERATURE, DEEPSEEK_MAX_TOKENS,
    DEEPSEEK_TIMEOUT, DEEPSEEK_CALL_SLEEP,
    COMPETITORS,
)


QUESTIONS_ZH = {
    "q1": "本周 EZVIZ、Tapo、Eufy、Reolink 有哪些值得关注的新品发布、功能更新或重要公司动态？",
    "q2": "用户对这四个品牌最集中的正面反馈和负面抱怨是什么？请分品牌列举。",
    "q3": "用户在哪些具体使用场景中表达了现有产品无法满足的需求？请列举具体场景，不要泛化。",
    "q4": "关于停车安全、车内监控、移动场景摄像头的讨论有哪些？包括用户痛点和已有产品反馈。",
    "q5": "众筹平台（ProductHunt / Crowd Supply / Indiegogo）本周有哪些新型摄像头或安防硬件项目？列出项目名、核心卖点、链接。",
    "q6": "关于电池续航、本地存储与隐私、Matter/Thread 协议、边缘 AI 功能的讨论有什么新动向？",
    "q7": "Google Trends 数据显示，欧洲（GB）和全球范围内，哪些品牌或品类词出现了显著热度变化？",
    "q8": "综合以上所有信号，本周最值得关注的 3 个信号是什么？格式：信号描述 + 来源链接 + 为什么值得关注（1句）。不要给产品建议。",
}

QUESTIONS_EN = {
    "q1": "What notable new product launches, feature updates, or company news happened this week for EZVIZ, Tapo, Eufy, and Reolink?",
    "q2": "What are the most common positive feedback and complaints users have about these four brands? Please break down by brand.",
    "q3": "In what specific use-case scenarios are users expressing unmet needs that current products fail to address? Be concrete, not generic.",
    "q4": "What discussions exist around parking security, in-car monitoring, and mobile-scenario cameras? Include user pain points and product feedback.",
    "q5": "What new camera or security hardware projects appeared on crowdfunding platforms (ProductHunt / Crowd Supply / Indiegogo) this week? List name, key selling point, and link.",
    "q6": "What new developments are there in discussions about battery life, local storage & privacy, Matter/Thread protocol, and edge AI features?",
    "q7": "Based on Google Trends data, which brand or category keywords showed significant interest changes in Europe (GB) and globally?",
    "q8": "Based on all signals above, what are the 3 most noteworthy signals this week? Format: signal description + source link + one sentence on why it matters. No product recommendations.",
}

SYSTEM_ZH = """你是一位 IoT 安防摄像头行业的市场分析助手，服务于 IMOU 欧洲区产品团队。
你的任务是基于提供的原始信号数据，回答具体问题。

严格规则：
1. 只陈述信号和事实，不给产品建议，不写「IMOU 应该做 X」「建议 IMOU」等表述
2. 每条信号必须附上来源链接（markdown 格式）
3. 没有相关数据时，明确写「本周无相关信号」，不要编造内容
4. 摘要段不超过 4 句，原始信号列表每条一行
5. 语言：中文"""

SYSTEM_EN = """You are a market analysis assistant for the IoT security camera industry, serving IMOU's European product team.
Your task is to answer specific questions based on the raw signal data provided.

Strict rules:
1. State signals and facts only. No product recommendations. Do not write "IMOU should build X" or similar.
2. Every signal must include a source link in markdown format.
3. If no relevant data exists, write "No relevant signals this week." Do not fabricate content.
4. Summary paragraph: max 4 sentences. Signal list: one item per line.
5. Language: English"""

OUTPUT_FORMAT = """
Required output format (use exactly these markdown headers):

**摘要**
[2-4 sentence summary]

**原始信号**
- [Source Name](URL): one-line summary
- ...（max 8 items）

**注意**
[1-2 sentences preventing over-interpretation]
"""

OUTPUT_FORMAT_EN = """
Required output format (use exactly these markdown headers):

**Summary**
[2-4 sentence summary]

**Signals**
- [Source Name](URL): one-line summary
- ...（max 8 items）

**Caution**
[1-2 sentences preventing over-interpretation]
"""

FAILURE_PLACEHOLDER = "[Analysis failed for this question — please re-run or check API key]"


def _format_sources(results: list) -> str:
    lines = []
    for r in results:
        if r["status"] == "failed":
            lines.append(f"[SOURCE FAILED: {r['source_id']} — {r.get('error', '')}]")
            continue
        if not r["items"]:
            lines.append(f"[SOURCE EMPTY: {r['source_id']}]")
            continue
        lines.append(f"\n=== SOURCE: {r['source_id']} ===")
        for item in r["items"]:
            lines.append(f"Title: {item['title']}")
            if item["url"]:
                lines.append(f"URL: {item['url']}")
            if item["summary"]:
                lines.append(f"Summary: {item['summary'][:300]}")
            lines.append("---")
    return "\n".join(lines)


def _call(client: OpenAI, system: str, data_block: str, question: str, fmt: str) -> str:
    user_content = f"=== RAW DATA ===\n{data_block}\n\n=== QUESTION ===\n{question}\n\n=== REQUIRED OUTPUT FORMAT ==={fmt}"
    try:
        resp = client.chat.completions.create(
            model=DEEPSEEK_MODEL,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user_content},
            ],
            temperature=DEEPSEEK_TEMPERATURE,
            max_tokens=DEEPSEEK_MAX_TOKENS,
            timeout=DEEPSEEK_TIMEOUT,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        print(f"  DeepSeek call failed: {e}")
        return FAILURE_PLACEHOLDER


def analyze(source_results_dicts: list) -> dict:
    api_key = os.environ.get("DEEPSEEK_API_KEY", "")
    if not api_key:
        raise RuntimeError("DEEPSEEK_API_KEY environment variable not set")

    client = OpenAI(api_key=api_key, base_url=DEEPSEEK_BASE_URL)
    data_block = _format_sources(source_results_dicts)

    answers_zh: dict[str, str] = {}
    answers_en: dict[str, str] = {}

    consecutive_failures = 0

    print("Analyzing (ZH)...")
    for qid, question in QUESTIONS_ZH.items():
        print(f"  {qid}...", end=" ", flush=True)
        ans = _call(client, SYSTEM_ZH, data_block, question, OUTPUT_FORMAT)
        if ans == FAILURE_PLACEHOLDER:
            consecutive_failures += 1
            if consecutive_failures >= 3:
                raise RuntimeError("3 consecutive DeepSeek failures — aborting analysis")
        else:
            consecutive_failures = 0
        answers_zh[qid] = ans
        print("done")
        time.sleep(DEEPSEEK_CALL_SLEEP)

    print("Analyzing (EN)...")
    for qid, question in QUESTIONS_EN.items():
        print(f"  {qid}...", end=" ", flush=True)
        ans = _call(client, SYSTEM_EN, data_block, question, OUTPUT_FORMAT_EN)
        if ans == FAILURE_PLACEHOLDER:
            consecutive_failures += 1
            if consecutive_failures >= 3:
                raise RuntimeError("3 consecutive DeepSeek failures — aborting analysis")
        else:
            consecutive_failures = 0
        answers_en[qid] = ans
        print("done")
        time.sleep(DEEPSEEK_CALL_SLEEP)

    return {"zh": answers_zh, "en": answers_en}
