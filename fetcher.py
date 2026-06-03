"""
╔══════════════════════════════════════════════════════════════════╗
║                        F I N S I G H T                          ║
║              See beyond the numbers.                             ║
║   Markets: India (NSE/BSE) · Canada (TSX) · US (NYSE/NASDAQ)    ║
║   Assets:  Stocks · ETFs · MFs · F&O · Indices · Commodities    ║
║                      fetcher.py                                  ║
╚══════════════════════════════════════════════════════════════════╝
"""

import os, json, time, logging, smtplib
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

import yfinance as yf
import pandas as pd
import requests
import finnhub
from mftool import Mftool

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("FinSight")

AV_KEY      = os.getenv("ALPHA_VANTAGE_KEY", "demo")
FH_KEY      = os.getenv("FINNHUB_KEY", "")
FRED_KEY    = os.getenv("FRED_KEY", "")
GMAIL_USER  = os.getenv("GMAIL_USER", "")
GMAIL_PASS  = os.getenv("GMAIL_APP_PASSWORD", "")
ALERT_EMAIL = os.getenv("ALERT_EMAIL", "")
SLACK_HOOK  = os.getenv("SLACK_WEBHOOK_URL", "")
CLAUDE_KEY   = "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"

APP_NAME    = "FinSight"
TAGLINE     = "See beyond the numbers."

# ── Currency conversion (live via yfinance) ───────────────────────
def get_fx_rates() -> dict:
    pairs = {"USD_CAD": "USDCAD=X", "USD_INR": "USDINR=X", "CAD_INR": "CADINR=X"}
    rates = {}
    for label, ticker in pairs.items():
        try:
            info = yf.Ticker(ticker).info
            rates[label] = info.get("regularMarketPrice") or info.get("previousClose", 1)
        except:
            rates[label] = 1
    return rates

# ── Watchlists ────────────────────────────────────────────────────
WATCHLIST = {
    "IN_STOCKS": [
        "RELIANCE.NS","TCS.NS","INFY.NS","HDFCBANK.NS","ICICIBANK.NS",
        "WIPRO.NS","HINDUNILVR.NS","LT.NS","BAJFINANCE.NS","SBIN.NS",
        "ADANIENT.NS","TATAMOTORS.NS","MARUTI.NS","SUNPHARMA.NS","ONGC.NS",
    ],
    "IN_ETFS":    ["NIFTYBEES.NS","GOLDBEES.NS","JUNIORBEES.NS","BANKBEES.NS","ITBEES.NS"],
    "IN_INDICES": ["^NSEI","^BSESN","^NSEBANK","^CNXIT"],
    "CA_STOCKS":  ["RY.TO","TD.TO","BNS.TO","BMO.TO","CM.TO","CNR.TO","CP.TO","SU.TO","SHOP.TO"],
    "CA_ETFS":    ["XIU.TO","XEQT.TO","VFV.TO","ZAG.TO","XBAL.TO","VGRO.TO"],
    "US_STOCKS":  ["AAPL","MSFT","NVDA","GOOGL","AMZN","META","TSLA","JPM","V","BRK-B"],
    "US_ETFS":    ["SPY","QQQ","VTI","VWO","GLD","VNQ","SCHD","BND"],
    "US_INDICES": ["^GSPC","^IXIC","^DJI","^VIX"],
    "COMMODITIES":["GC=F","SI=F","CL=F","BZ=F","NG=F","HG=F","ZW=F","ZC=F"],
    "REAL_ESTATE":["VNQ","REET","XRE.TO","MINDSPACE.NS","EMBASSY.NS","DLF.NS"],
    "CA_ETFS_MF": ["XEQT.TO","XBAL.TO","XCNS.TO","VGRO.TO","VBAL.TO","ZGRO.TO"],
    "US_MF":      ["VFINX","FXAIX","VTSAX","VBTLX"],
}

INDIAN_MF_SCHEMES = {
    "HDFC_TOP100":     "100016",
    "SBI_BLUECHIP":    "119598",
    "MIRAE_LARGECAP":  "118834",
    "AXIS_MIDCAP":     "120503",
    "PARAG_FLEXICAP":  "122639",
    "ICICI_BALANCED":  "120586",
    "NIPPON_SMALLCAP": "118778",
    "KOTAK_EMERGING":  "120257",
}

COMMODITY_NAMES = {
    "GC=F":"Gold","SI=F":"Silver","CL=F":"Crude Oil (WTI)",
    "BZ=F":"Brent Crude","NG=F":"Natural Gas","HG=F":"Copper",
    "ZW=F":"Wheat","ZC=F":"Corn",
}

# ── Core quote fetcher ────────────────────────────────────────────
def get_quote(ticker: str) -> dict:
    try:
        i = yf.Ticker(ticker).info
        price = (i.get("currentPrice") or i.get("regularMarketPrice")
                 or i.get("navPrice") or i.get("previousClose"))
        return {
            "ticker": ticker, "status": "ok",
            "name":           i.get("longName") or i.get("shortName", ticker),
            "price":          price,
            "currency":       i.get("currency",""),
            "change_pct":     i.get("regularMarketChangePercent"),
            "day_high":       i.get("dayHigh"),
            "day_low":        i.get("dayLow"),
            "volume":         i.get("volume"),
            "market_cap":     i.get("marketCap"),
            "52w_high":       i.get("fiftyTwoWeekHigh"),
            "52w_low":        i.get("fiftyTwoWeekLow"),
            "pe_ratio":       i.get("trailingPE"),
            "dividend_yield": i.get("dividendYield"),
            "asset_type":     i.get("quoteType","UNKNOWN"),
            "exchange":       i.get("exchange",""),
            "timestamp":      datetime.now().isoformat(),
        }
    except Exception as e:
        return {"ticker": ticker, "status": "error", "error": str(e)}

def scan_category(category: str) -> list:
    results = []
    for t in WATCHLIST.get(category, []):
        results.append(get_quote(t))
        time.sleep(0.3)
    return results

def scan_all() -> dict:
    return {cat: scan_category(cat) for cat in WATCHLIST}

def get_history(ticker: str, period: str = "1y", interval: str = "1d") -> pd.DataFrame:
    df = yf.Ticker(ticker).history(period=period, interval=interval)
    if hasattr(df.index, 'tz') and df.index.tz is not None: df.index = df.index.tz_localize(None)
    return df[["Open","High","Low","Close","Volume"]]

# ── Technical indicators ──────────────────────────────────────────
def _av(params: dict) -> dict:
    params["apikey"] = AV_KEY
    return requests.get("https://www.alphavantage.co/query", params=params).json()

def get_rsi(ticker: str, period: int = 14) -> dict:
    data = _av({"function":"RSI","symbol":ticker,"interval":"daily",
                "time_period":period,"series_type":"close"})
    ts = data.get("Technical Analysis: RSI", {})
    if not ts:
        return {"ticker":ticker,"indicator":"RSI","error":"No data / rate limit"}
    latest = sorted(ts)[-1]
    val = round(float(ts[latest]["RSI"]), 2)
    return {
        "ticker": ticker, "indicator": f"RSI-{period}",
        "date": latest, "value": val,
        "signal": "Overbought — consider trimming" if val > 70
                  else "Oversold — potential opportunity" if val < 30
                  else "Neutral — hold and watch",
        "zone": "red" if val > 70 else "green" if val < 30 else "amber",
    }

def get_macd(ticker: str) -> dict:
    data = _av({"function":"MACD","symbol":ticker,
                "interval":"daily","series_type":"close"})
    ts = data.get("Technical Analysis: MACD", {})
    if not ts:
        return {"ticker":ticker,"indicator":"MACD","error":"No data / rate limit"}
    latest = sorted(ts)[-1]
    macd = round(float(ts[latest]["MACD"]), 4)
    sig  = round(float(ts[latest]["MACD_Signal"]), 4)
    return {
        "ticker": ticker, "indicator": "MACD", "date": latest,
        "macd": macd, "signal_line": sig,
        "histogram": round(float(ts[latest]["MACD_Hist"]), 4),
        "crossover": "Bullish — momentum turning positive" if macd > sig
                     else "Bearish — momentum turning negative",
        "zone": "green" if macd > sig else "red",
    }

# ── Indian Mutual Funds ───────────────────────────────────────────
def get_indian_mf_nav(scheme_code: str) -> dict:
    try:
        mf   = Mftool()
        data = mf.get_scheme_quote(scheme_code)
        hist = mf.get_scheme_historical_nav(scheme_code, as_Dataframe=True)
        nav_series = hist["nav"].astype(float)
        change_1m  = round(
            ((nav_series.iloc[0] - nav_series.iloc[21]) / nav_series.iloc[21]) * 100, 2
        ) if len(nav_series) > 21 else None
        return {
            "scheme_code": scheme_code, "status": "ok",
            "name":        data.get("scheme_name"),
            "nav":         float(data.get("nav", 0)),
            "date":        data.get("last_updated"),
            "change_1m":   change_1m,
            "fund_house":  data.get("fund_house"),
            "category":    data.get("scheme_category"),
        }
    except Exception as e:
        return {"scheme_code": scheme_code, "status": "error", "error": str(e)}

def get_all_indian_mfs() -> list:
    results = []
    for label, code in INDIAN_MF_SCHEMES.items():
        r = get_indian_mf_nav(code)
        r["label"] = label
        results.append(r)
        time.sleep(0.5)
    return results

def search_indian_mf(query: str) -> list:
    mf = Mftool()
    schemes = mf.get_scheme_codes()
    q = query.lower()
    return [{"code": c, "name": n} for c, n in schemes.items() if q in n.lower()][:20]

# ── Commodities ───────────────────────────────────────────────────
def get_commodities() -> list:
    results = []
    for ticker, name in COMMODITY_NAMES.items():
        q = get_quote(ticker)
        q["friendly_name"] = name
        results.append(q)
        time.sleep(0.2)
    return results

# ── Real estate ───────────────────────────────────────────────────
def get_real_estate_reits() -> list:
    tickers = {
        "VNQ":"US REIT ETF","REET":"Global REIT ETF",
        "XRE.TO":"Canadian REIT ETF","MINDSPACE.NS":"Mindspace REIT India",
        "EMBASSY.NS":"Embassy REIT India","DLF.NS":"DLF — India RE",
    }
    results = []
    for t, desc in tickers.items():
        q = get_quote(t)
        q["description"] = desc
        results.append(q)
        time.sleep(0.3)
    return results

RE_POCKETS = {
    "India": [
        {"city":"Hyderabad","zones":"HITEC City, Gachibowli, Financial District",
         "drivers":"IT corridor, low stamp duty, NRI demand","appreciation":"10–14%/yr"},
        {"city":"Bengaluru","zones":"Whitefield, Sarjapur, Electronic City",
         "drivers":"IT hub, metro expansion, startup ecosystem","appreciation":"8–12%/yr"},
        {"city":"Pune","zones":"Hinjewadi, Wakad, Baner",
         "drivers":"IT park, Pune metro, affordability","appreciation":"7–10%/yr"},
    ],
    "Canada": [
        {"city":"Calgary","zones":"NW Calgary, Airdrie, Cochrane",
         "drivers":"No provincial income tax, oil rebound, migration","appreciation":"8–12%/yr"},
        {"city":"Edmonton","zones":"South Edmonton, Sherwood Park",
         "drivers":"Most affordable major Canadian city, LRT expansion","appreciation":"6–9%/yr"},
        {"city":"Hamilton","zones":"Downtown Hamilton, Waterloo",
         "drivers":"Toronto overflow, GO transit, tech sector","appreciation":"5–8%/yr"},
    ],
    "USA": [
        {"city":"Austin TX","zones":"Round Rock, Cedar Park",
         "drivers":"Tech relocation, no state income tax","appreciation":"7–11%/yr"},
        {"city":"Phoenix AZ","zones":"Scottsdale, Mesa, Chandler",
         "drivers":"Sun Belt migration, data center boom","appreciation":"6–9%/yr"},
        {"city":"Charlotte NC","zones":"Ballantyne, Huntersville",
         "drivers":"Banking hub, affordable vs Northeast","appreciation":"7–10%/yr"},
    ],
}

# ── News & sentiment ──────────────────────────────────────────────
def get_news(ticker: str, days: int = 7) -> dict:
    if not FH_KEY:
        return {"error": "FINNHUB_KEY not set"}
    client = finnhub.Client(api_key=FH_KEY)
    today  = datetime.now().strftime("%Y-%m-%d")
    past   = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    news   = client.company_news(ticker, _from=past, to=today)
    sent   = client.news_sentiment(ticker)
    return {
        "ticker":      ticker,
        "bullish_pct": sent.get("sentiment",{}).get("bullishPercent"),
        "bearish_pct": sent.get("sentiment",{}).get("bearishPercent"),
        "top_news": [
            {"headline": n["headline"], "source": n["source"],
             "date": datetime.fromtimestamp(n["datetime"]).strftime("%Y-%m-%d")}
            for n in news[:5]
        ],
    }

# ── Options chain ─────────────────────────────────────────────────
def get_options_chain(ticker: str) -> dict:
    try:
        t   = yf.Ticker(ticker)
        exp = t.options
        if not exp:
            return {"ticker": ticker, "error": "No options data"}
        chain = t.option_chain(exp[0])
        cols  = ["strike","lastPrice","volume","openInterest","impliedVolatility"]
        return {
            "ticker":      ticker, "status": "ok", "expiry": exp[0],
            "all_expiries": list(exp),
            "calls": chain.calls[cols].head(10).to_dict("records"),
            "puts":  chain.puts[cols].head(10).to_dict("records"),
        }
    except Exception as e:
        return {"ticker": ticker, "status": "error", "error": str(e)}

# ════════════════════════════════════════════════════════════════════
#  TIER 1 FEATURES
# ════════════════════════════════════════════════════════════════════

# ── T1-A: AI Portfolio Scoring ────────────────────────────────────
def ai_portfolio_score(quotes: list) -> dict:
    """
    Calls Claude API to score every stock in plain English.
    Returns: top picks, caution list, hold list, overall verdict.
    """
    if not CLAUDE_KEY:
        return {"error": "ANTHROPIC_API_KEY not set in .env"}

    # Build compact summary for AI
    summary_rows = []
    for q in quotes:
        if q.get("status") != "ok" or not q.get("price"):
            continue
        chg = q.get("change_pct") or 0
        summary_rows.append(
            f"{q['ticker']} | price={q['price']} {q.get('currency','')} | "
            f"change={chg:+.1f}% | pe={q.get('pe_ratio','—')} | "
            f"52w_high={q.get('52w_high','—')} | 52w_low={q.get('52w_low','—')}"
        )

    if not summary_rows:
        return {"error": "No valid quotes to score"}

    prompt = f"""You are FinSight, an AI wealth analysis assistant.
Analyse this portfolio watchlist data and return ONLY valid JSON — no markdown, no extra text.

Data:
{chr(10).join(summary_rows)}

Return this exact JSON structure:
{{
  "overall_verdict": "2 sentence plain English summary of the overall portfolio health today",
  "top_picks": [
    {{"ticker": "X", "reason": "plain English reason in 1 sentence"}}
  ],
  "caution": [
    {{"ticker": "X", "reason": "plain English reason in 1 sentence"}}
  ],
  "hold_steady": [
    {{"ticker": "X", "reason": "plain English reason in 1 sentence"}}
  ],
  "score": 72
}}

Rules:
- top_picks: stocks showing positive momentum, reasonable valuation
- caution: stocks that may be overbought, high PE, or losing momentum
- hold_steady: everything else — no strong signal either way
- score: overall portfolio health 0-100 (100 = everything looks great)
- Keep all reasons under 15 words. Plain English only. No financial jargon.
- IMPORTANT: Return ONLY the JSON object, nothing else."""

    try:
        resp = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key":         CLAUDE_KEY,
                "anthropic-version": "2023-06-01",
                "content-type":      "application/json",
            },
            json={
                "model":      "claude-sonnet-4-20250514",
                "max_tokens": 1000,
                "messages":   [{"role": "user", "content": prompt}],
            },
            timeout=30,
        )
        text = resp.json()["content"][0]["text"].strip()
        # Strip any accidental markdown fences
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        return json.loads(text)
    except Exception as e:
        return {"error": f"AI scoring failed: {str(e)}"}


# ── T1-B: Cross-market correlation alerts ─────────────────────────
def cross_market_correlation(all_quotes: dict) -> list:
    """
    Detects when multiple markets move together — signals macro events.
    Returns plain English alerts.
    """
    alerts = []

    def avg_change(category: str) -> float:
        items = [q.get("change_pct", 0) or 0
                 for q in all_quotes.get(category, [])
                 if q.get("status") == "ok"]
        return sum(items) / len(items) if items else 0

    india_chg  = avg_change("IN_STOCKS")
    us_chg     = avg_change("US_STOCKS")
    ca_chg     = avg_change("CA_STOCKS")
    gold_chg   = next((q.get("change_pct",0) or 0
                       for q in all_quotes.get("COMMODITIES",[])
                       if q.get("ticker") == "GC=F"), 0)
    oil_chg    = next((q.get("change_pct",0) or 0
                       for q in all_quotes.get("COMMODITIES",[])
                       if q.get("ticker") == "CL=F"), 0)

    # Pattern 1: All markets falling together — global risk-off
    if india_chg < -1.5 and us_chg < -1.5 and ca_chg < -1.5:
        alerts.append({
            "type":     "GLOBAL_SELLOFF",
            "severity": "high",
            "message":  f"All three markets falling together — India {india_chg:+.1f}%, US {us_chg:+.1f}%, Canada {ca_chg:+.1f}%. This is a global risk-off event, not specific to one market. Usually means macro fear — hold steady, don't panic sell.",
            "emoji":    "🌍",
        })

    # Pattern 2: Gold up + stocks down — flight to safety
    if gold_chg > 1.0 and (india_chg < -0.5 or us_chg < -0.5):
        alerts.append({
            "type":     "FLIGHT_TO_SAFETY",
            "severity": "medium",
            "message":  f"Gold is up {gold_chg:+.1f}% while equities are falling. Investors are moving to safe havens. Your gold holdings (GOLDBEES.NS, GLD) are acting as your cushion right now — this is why diversification works.",
            "emoji":    "🥇",
        })

    # Pattern 3: Oil up + India down — inflation risk for India
    if oil_chg > 2.0 and india_chg < -0.5:
        alerts.append({
            "type":     "OIL_INDIA_PRESSURE",
            "severity": "medium",
            "message":  f"Crude oil is up {oil_chg:+.1f}% and Indian markets are down {india_chg:+.1f}%. India imports 85% of its oil — rising oil prices squeeze Indian corporate margins and can trigger RBI rate concerns.",
            "emoji":    "🛢️",
        })

    # Pattern 4: India outperforming both Canada and US
    if india_chg > 1.0 and india_chg > us_chg + 1.0 and india_chg > ca_chg + 1.0:
        alerts.append({
            "type":     "INDIA_OUTPERFORMING",
            "severity": "low",
            "message":  f"India ({india_chg:+.1f}%) is outperforming Canada ({ca_chg:+.1f}%) and US ({us_chg:+.1f}%) today. Domestic FII/DII flows likely strong. Good sign for your Indian holdings.",
            "emoji":    "🇮🇳",
        })

    # Pattern 5: All markets up together — risk-on
    if india_chg > 1.0 and us_chg > 1.0 and ca_chg > 1.0:
        alerts.append({
            "type":     "GLOBAL_RALLY",
            "severity": "low",
            "message":  f"All three markets rallying together — India {india_chg:+.1f}%, US {us_chg:+.1f}%, Canada {ca_chg:+.1f}%. Global risk-on mood. Your diversified portfolio is working in your favour today.",
            "emoji":    "🚀",
        })

    # Pattern 6: Big movers
    for cat, items in all_quotes.items():
        for q in items:
            chg = q.get("change_pct") or 0
            if abs(chg) >= 4 and q.get("status") == "ok":
                direction = "surging" if chg > 0 else "falling sharply"
                alerts.append({
                    "type":     "BIG_MOVER",
                    "severity": "medium" if abs(chg) >= 5 else "low",
                    "message":  f"{q.get('name', q['ticker'])} ({q['ticker']}) is {direction} {chg:+.1f}% today.",
                    "emoji":    "⚡",
                    "ticker":   q["ticker"],
                })

    return alerts


# ── T1-C: Plain English morning brief (AI-generated) ──────────────
def generate_morning_brief(all_quotes: dict, alerts: list, fx_rates: dict) -> str:
    """
    Calls Claude to write a personalised 5-line morning brief.
    Returns plain text — used in email, Slack, and app.
    """
    if not CLAUDE_KEY:
        return _fallback_brief(all_quotes, alerts)

    def avg_chg(cat):
        items = [q.get("change_pct",0) or 0 for q in all_quotes.get(cat,[]) if q.get("status")=="ok"]
        return round(sum(items)/len(items), 2) if items else 0

    context = f"""
Date: {datetime.now().strftime('%A, %d %B %Y')}
Markets:
  Nifty avg change:  {avg_chg('IN_STOCKS'):+.1f}%
  S&P 500 avg:       {avg_chg('US_STOCKS'):+.1f}%
  TSX avg:           {avg_chg('CA_STOCKS'):+.1f}%
  Gold:              {next((q.get('change_pct',0) or 0 for q in all_quotes.get('COMMODITIES',[]) if q.get('ticker')=='GC=F'), 0):+.1f}%
FX rates:
  1 USD = {fx_rates.get('USD_CAD', '—')} CAD
  1 USD = {fx_rates.get('USD_INR', '—')} INR
Alerts today: {len(alerts)}
Top alert: {alerts[0]['message'] if alerts else 'No major alerts'}
"""

    prompt = f"""You are FinSight, a personal AI wealth assistant.
Write a warm, smart, plain English morning brief for the investor.
It should feel like a trusted friend who knows finance — not a robot.

Context:
{context}

Rules:
- Exactly 5 sentences. No more, no less.
- Start with "Good morning." 
- Sentence 1: Overall mood of markets today in plain English.
- Sentence 2: The most important thing happening across India, Canada, or US markets.
- Sentence 3: One specific thing to watch or act on today.
- Sentence 4: Real estate or commodity insight if relevant, otherwise macro context.
- Sentence 5: One encouraging closing thought about long-term wealth building.
- No bullet points. No headers. Just 5 flowing sentences.
- No financial advice language. Keep it informational and warm."""

    try:
        resp = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key":         CLAUDE_KEY,
                "anthropic-version": "2023-06-01",
                "content-type":      "application/json",
            },
            json={
                "model":      "claude-sonnet-4-20250514",
                "max_tokens": 300,
                "messages":   [{"role": "user", "content": prompt}],
            },
            timeout=20,
        )
        return resp.json()["content"][0]["text"].strip()
    except Exception as e:
        log.warning(f"Morning brief AI failed: {e}")
        return _fallback_brief(all_quotes, alerts)


def _fallback_brief(all_quotes: dict, alerts: list) -> str:
    """Fallback brief without AI — uses raw data."""
    def avg(cat):
        items = [q.get("change_pct",0) or 0 for q in all_quotes.get(cat,[]) if q.get("status")=="ok"]
        return round(sum(items)/len(items),2) if items else 0
    in_c, us_c, ca_c = avg("IN_STOCKS"), avg("US_STOCKS"), avg("CA_STOCKS")
    mood = "positive" if (in_c+us_c+ca_c)/3 > 0 else "cautious"
    return (
        f"Good morning. Markets are broadly {mood} today. "
        f"India is {in_c:+.1f}%, US is {us_c:+.1f}%, and Canada is {ca_c:+.1f}%. "
        f"There are {len(alerts)} alerts active in your watchlist. "
        f"Check the FinSight dashboard for full details. "
        f"Stay consistent with your investment plan — markets reward patience."
    )


# ── T1-D: Unified Wealth Snapshot ────────────────────────────────
def unified_wealth_snapshot(all_quotes: dict, holdings: dict = None) -> dict:
    """
    Converts all portfolio values into a single CAD number.
    holdings = {"RELIANCE.NS": 10, "AAPL": 5, "RY.TO": 20} (shares owned)
    If holdings not provided, uses watchlist prices as reference only.
    """
    fx = get_fx_rates()
    usd_to_cad = fx.get("USD_CAD", 1.35)
    inr_to_cad = 1 / fx.get("CAD_INR", 60)

    snapshot = {
        "total_cad":      0,
        "by_market":      {"India_CAD": 0, "Canada_CAD": 0, "US_CAD": 0, "Other_CAD": 0},
        "by_asset":       {},
        "fx_rates":       fx,
        "generated_at":   datetime.now().isoformat(),
        "note":           "Based on watchlist prices. Add your actual holdings in .env for personal totals.",
        "holdings_mode":  holdings is not None,
    }

    # Flatten all quotes
    all_q = {}
    for items in all_quotes.values():
        for q in items:
            if q.get("status") == "ok" and q.get("price"):
                all_q[q["ticker"]] = q

    # If holdings provided, calculate actual value
    if holdings:
        for ticker, shares in holdings.items():
            q = all_q.get(ticker)
            if not q:
                continue
            price    = q.get("price", 0)
            currency = q.get("currency", "USD")
            if currency == "INR":
                value_cad = price * shares * inr_to_cad
                snapshot["by_market"]["India_CAD"] += value_cad
            elif currency == "CAD":
                value_cad = price * shares
                snapshot["by_market"]["Canada_CAD"] += value_cad
            else:
                value_cad = price * shares * usd_to_cad
                snapshot["by_market"]["US_CAD"] += value_cad
            snapshot["total_cad"] += value_cad
            snapshot["by_asset"][ticker] = {
                "shares":    shares,
                "price":     price,
                "currency":  currency,
                "value_cad": round(value_cad, 2),
            }
    else:
        # Reference mode — show top holdings by value
        for ticker, q in list(all_q.items())[:30]:
            price    = q.get("price", 0)
            currency = q.get("currency", "USD")
            if currency == "INR":
                value_cad = price * inr_to_cad
            elif currency == "CAD":
                value_cad = price
            else:
                value_cad = price * usd_to_cad
            snapshot["by_asset"][ticker] = {
                "price":     price,
                "currency":  currency,
                "value_cad": round(value_cad, 2),
            }

    snapshot["total_cad"] = round(snapshot["total_cad"], 2)
    for k in snapshot["by_market"]:
        snapshot["by_market"][k] = round(snapshot["by_market"][k], 2)

    return snapshot


# ── Alerts ────────────────────────────────────────────────────────
def send_email(subject: str, body_html: str):
    if not all([GMAIL_USER, GMAIL_PASS, ALERT_EMAIL]):
        log.warning("Email not configured")
        return
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = f"FinSight <{GMAIL_USER}>"
    msg["To"]      = ALERT_EMAIL
    msg.attach(MIMEText(body_html, "html"))
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
        s.login(GMAIL_USER, GMAIL_PASS)
        s.send_message(msg)
    log.info("Email sent ✓")

def send_slack(message: str):
    if not SLACK_HOOK:
        return
    requests.post(SLACK_HOOK, json={"text": message})
    log.info("Slack sent ✓")

def format_morning_email(brief: str, alerts: list, snapshot: dict) -> tuple:
    subject = f"📈 FinSight Morning Brief — {datetime.now().strftime('%d %b %Y')}"
    alert_rows = "".join(
        f"<tr><td>{a['emoji']}</td><td>{a['message']}</td></tr>"
        for a in alerts[:8]
    ) or "<tr><td>✅</td><td>No major alerts today</td></tr>"

    body = f"""
<html><body style="font-family:Arial,sans-serif;max-width:620px;margin:auto;color:#333">
<div style="background:#0F6E56;padding:20px;border-radius:8px 8px 0 0">
  <h1 style="color:#fff;margin:0;font-size:22px">FinSight</h1>
  <p style="color:#9FE1CB;margin:4px 0 0;font-size:13px">See beyond the numbers.</p>
</div>
<div style="padding:20px;background:#f9f9f9;border-radius:0 0 8px 8px;border:1px solid #e0e0e0">
  <h2 style="font-size:16px;color:#333">{datetime.now().strftime('%A, %d %B %Y')}</h2>
  <div style="background:#fff;border-left:4px solid #0F6E56;padding:16px;border-radius:4px;margin-bottom:20px;line-height:1.8;font-size:14px">
    {brief}
  </div>
  <h3 style="font-size:14px;color:#555;margin-bottom:8px">Today's alerts</h3>
  <table style="width:100%;border-collapse:collapse;font-size:13px">
    {alert_rows}
  </table>
  <div style="margin-top:20px;padding:12px;background:#E1F5EE;border-radius:6px;font-size:13px">
    <strong>Portfolio snapshot</strong><br>
    Total tracked value: <strong>CAD {snapshot.get('total_cad', 0):,.2f}</strong><br>
    FX: 1 USD = {snapshot.get('fx_rates',{}).get('USD_CAD','—')} CAD &nbsp;|&nbsp;
    1 USD = {snapshot.get('fx_rates',{}).get('USD_INR','—')} INR
  </div>
  <p style="font-size:11px;color:#999;margin-top:20px">
    FinSight — for informational purposes only. Not financial advice.<br>
    {datetime.now().strftime('%Y')} · Your personal wealth intelligence tool.
  </p>
</div>
</body></html>"""
    return subject, body


# ── Full daily report ─────────────────────────────────────────────
def build_daily_report() -> dict:
    log.info(f"{'='*50}")
    log.info(f"FinSight Daily Report — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    log.info(f"{'='*50}")

    report = {
        "app":          APP_NAME,
        "generated_at": datetime.now().isoformat(),
        "markets":      {},
        "indian_mfs":   [],
        "commodities":  [],
        "real_estate":  [],
        "fx_rates":     {},
        "alerts":       [],
        "ai_scoring":   {},
        "morning_brief":"",
        "wealth_snapshot": {},
    }

    # Markets
    for cat in WATCHLIST:
        log.info(f"Fetching {cat}...")
        report["markets"][cat] = scan_category(cat)

    # Supporting data
    log.info("Fetching Indian MFs...")
    report["indian_mfs"] = get_all_indian_mfs()
    log.info("Fetching commodities...")
    report["commodities"] = get_commodities()
    log.info("Fetching REITs...")
    report["real_estate"] = get_real_estate_reits()
    log.info("Fetching FX rates...")
    report["fx_rates"] = get_fx_rates()

    # Tier 1 features
    log.info("Running cross-market correlation...")
    report["alerts"] = cross_market_correlation(report["markets"])

    log.info("Running AI portfolio scoring...")
    all_quotes_flat = [q for items in report["markets"].values() for q in items]
    report["ai_scoring"] = ai_portfolio_score(all_quotes_flat)

    log.info("Generating AI morning brief...")
    report["morning_brief"] = generate_morning_brief(
        report["markets"], report["alerts"], report["fx_rates"]
    )

    log.info("Building wealth snapshot...")
    report["wealth_snapshot"] = unified_wealth_snapshot(report["markets"])

    return report


if __name__ == "__main__":
    import sys
    mode = sys.argv[1] if len(sys.argv) > 1 else "quick"
    if mode == "quick":
        print(f"\n{'='*40}\n  FinSight — Quick Scan\n{'='*40}")
        for cat in ["IN_INDICES","US_INDICES"]:
            print(f"\n{cat}:")
            for q in scan_category(cat):
                chg = q.get("change_pct")
                print(f"  {q['ticker']:20} {str(q.get('price','—')):>12}  {f'{chg:+.2f}%' if chg else '—'}")
    elif mode == "full":
        report = build_daily_report()
        fname  = f"reports/finsight_{datetime.now().strftime('%Y%m%d')}.json"
        import pathlib; pathlib.Path("reports").mkdir(exist_ok=True)
        with open(fname,"w") as f:
            json.dump(report, f, indent=2, default=str)
        print(f"\n✅ FinSight report saved: {fname}")
        print(f"\n📋 Morning Brief:\n{report['morning_brief']}")
