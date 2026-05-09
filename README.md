# ImouPulse

**Weekly IoT security camera market intelligence, auto-generated.**

Tracks EZVIZ · Tapo · Eufy · Reolink across Reddit, Google News, crowdfunding, and Google Trends. Analyzed by DeepSeek, published as a bilingual (中文 / English) HTML report to GitHub Pages.

Inspired by [BuilderPulse](https://github.com/BuilderPulse/BuilderPulse).

---

## Reports

- [最新报告（中文）](https://ichts.github.io/ImouPulse/zh/)
- [Latest Report (English)](https://ichts.github.io/ImouPulse/en/)
- [Archive](https://ichts.github.io/ImouPulse/archive.html)

---

## How it works

```
GitHub Actions (manual trigger)
  → collect: Reddit RSS + Google News + ProductHunt/CrowdSupply/Indiegogo/TheAmbient/CNX + Google Trends
  → analyze: DeepSeek V4 Flash answers 8 questions × 2 languages
  → render:  Markdown → HTML (Jinja2 template)
  → publish: commit to docs/ → GitHub Pages
```

**8 questions per report:**

| # | Module | Question |
|---|---|---|
| Q1 | Competitor Updates | New products, feature updates, company news |
| Q2 | Competitor Sentiment | User feedback by brand (positive + negative) |
| Q3 | Scenario Pain Points | Specific unmet needs in concrete use cases |
| Q4 | Vehicle & Mobile Security | In-car, parking, dashcam discussions |
| Q5 | Innovation Radar | New hardware on crowdfunding platforms |
| Q6 | Technology Trends | Battery, privacy, Matter/Thread, edge AI |
| Q7 | Market Momentum | Google Trends changes (EU + Global) |
| Q8 | Top 3 Signals | This week's most noteworthy signals |

---

## Setup

**1. Fork or clone this repo**

**2. Configure GitHub Pages**

`Settings → Pages → Source → Deploy from branch → main / docs/`

**3. Add DeepSeek API key**

`Settings → Secrets and variables → Actions → New repository secret`

```
Name:  DEEPSEEK_API_KEY
Value: sk-...
```

Get a key at [platform.deepseek.com](https://platform.deepseek.com/api-keys).

**4. Run**

`Actions → ImouPulse → Run workflow`

Wait ~5–10 minutes. The report appears at your GitHub Pages URL.

---

## Local run

```bash
pip install -r requirements.txt
DEEPSEEK_API_KEY=sk-... python src/main.py
# open docs/zh/index.html
```

---

## Customize

Edit `src/config.py` to change:
- Competitors to monitor
- Subreddits
- Google News queries
- Innovation sources
- Google Trends keywords

---

## Cost

~$0.03–0.10 per report (DeepSeek V4 Flash pricing).

---

## License

MIT. For internal use only — do not republish competitor intelligence externally.
