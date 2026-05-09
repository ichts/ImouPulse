# ── Competitors ───────────────────────────────────────────────────────────────
COMPETITORS = ["EZVIZ", "Tapo", "Eufy", "Reolink"]

# ── Reddit subreddits (new feed, past 7 days) ─────────────────────────────────
SUBREDDITS = [
    "homesecurity",
    "homeautomation",
    "smarthome",
    "dashcam",
    "CarAV",
    "DIY",
    "homeimprovement",
    "europe",
    "AskEurope",
]
REDDIT_LOOKBACK_DAYS = 7

# ── Google News RSS queries (past 14 days) ────────────────────────────────────
GOOGLE_NEWS_QUERIES = [
    '"EZVIZ" camera',
    '"Tapo" camera',
    '"Eufy" security camera',
    '"Reolink" camera',
    'IoT security camera new',
    'smart home security Europe',
    'dashcam review 2026',
]
NEWS_LOOKBACK_DAYS = 14

# ── Innovation / crowdfunding sources ─────────────────────────────────────────
INNOVATION_SOURCES = [
    {
        "id": "producthunt",
        "name": "ProductHunt",
        "url": "https://www.producthunt.com/feed",
        # only keep items whose title/summary contain at least one keyword
        "keywords": ["camera", "security", "iot", "smart home", "surveillance", "dashcam", "doorbell"],
    },
    {
        "id": "crowdsupply",
        "name": "Crowd Supply",
        "url": "https://www.crowdsupply.com/feed.atom",
        "keywords": [],  # all hardware, no filter needed
    },
    {
        "id": "indiegogo",
        "name": "Indiegogo",
        "url": "https://www.indiegogo.com/projects/search.atom?q=security+camera",
        "keywords": [],
    },
    {
        "id": "theambient",
        "name": "The Ambient",
        "url": "https://www.the-ambient.com/feed",
        "keywords": [],  # smart home news, all relevant
    },
    {
        "id": "cnxsoftware",
        "name": "CNX Software",
        "url": "https://www.cnx-software.com/feed/",
        "keywords": [],  # embedded/IoT hardware news, all relevant
    },
]
INNOVATION_LOOKBACK_DAYS = 14

# ── Google Trends ─────────────────────────────────────────────────────────────
TRENDS_KW_EU = ["EZVIZ", "Eufy camera", "Tapo camera", "Reolink", "home security camera"]
TRENDS_KW_GLOBAL = ["EZVIZ", "Eufy camera", "Tapo camera", "Reolink", "home security camera", "dashcam", "smart doorbell"]
TRENDS_TIMEFRAME = "now 7-d"

# ── DeepSeek API ──────────────────────────────────────────────────────────────
# model=deepseek-chat is the API alias; at runtime it resolves to deepseek-v4-flash
DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEEPSEEK_MODEL = "deepseek-chat"
DEEPSEEK_TEMPERATURE = 0.3
DEEPSEEK_MAX_TOKENS = 1500
DEEPSEEK_TIMEOUT = 90       # seconds per call
DEEPSEEK_CALL_SLEEP = 1.5   # seconds between calls to avoid rate-limit

# ── HTTP ──────────────────────────────────────────────────────────────────────
HTTP_TIMEOUT = 30
HTTP_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; IMOUPulse/1.0)"
}
