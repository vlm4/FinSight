"""
FinSight — market_screener.py
Full market screener for NSE, BSE, TSX, NYSE, NASDAQ
No fixed watchlist — searches all listed companies
"""

import yfinance as yf
import pandas as pd
import time
import requests
from datetime import datetime

# ── Popular stocks by market — seed lists ────────────────────────
# These are the most actively traded — not a fixed limit
# User can search beyond these at any time

NSE_TOP100 = [
    "RELIANCE.NS","TCS.NS","HDFCBANK.NS","INFY.NS","ICICIBANK.NS",
    "HINDUNILVR.NS","SBIN.NS","BHARTIARTL.NS","ITC.NS","KOTAKBANK.NS",
    "LT.NS","AXISBANK.NS","ASIANPAINT.NS","MARUTI.NS","TITAN.NS",
    "SUNPHARMA.NS","ULTRACEMCO.NS","NESTLEIND.NS","WIPRO.NS","BAJFINANCE.NS",
    "BAJAJFINSV.NS","HCLTECH.NS","POWERGRID.NS","NTPC.NS","ONGC.NS",
    "TATAMOTORS.NS","ADANIENT.NS","ADANIPORTS.NS","TECHM.NS","DIVISLAB.NS",
    "DRREDDY.NS","CIPLA.NS","EICHERMOT.NS","GRASIM.NS","HEROMOTOCO.NS",
    "INDUSINDBK.NS","JSWSTEEL.NS","M&M.NS","SBILIFE.NS","SHREECEM.NS",
    "TATACONSUM.NS","TATASTEEL.NS","APOLLOHOSP.NS","BAJAJ-AUTO.NS","BPCL.NS",
    "BRITANNIA.NS","COALINDIA.NS","HDFCLIFE.NS","HINDALCO.NS","IOC.NS",
    "ZOMATO.NS","PAYTM.NS","NYKAA.NS","POLICYBZR.NS","DELHIVERY.NS",
    "IRCTC.NS","HAL.NS","BEL.NS","BHEL.NS","SAIL.NS",
    "BANKBARODA.NS","PNB.NS","CANBK.NS","UNIONBANK.NS","IDFCFIRSTB.NS",
    "GODREJCP.NS","DABUR.NS","COLPAL.NS","MARICO.NS","PIDILITIND.NS",
    "BERGEPAINT.NS","HAVELLS.NS","VOLTAS.NS","WHIRLPOOL.NS","BLUESTARCO.NS",
    "JUBLFOOD.NS","DOMINOS.NS","DEVYANI.NS","WESTLIFE.NS","SAPPHIRE.NS",
    "TRENT.NS","ABFRL.NS","VEDL.NS","NMDC.NS","MOIL.NS",
    "RECLTD.NS","PFC.NS","IRFC.NS","HUDCO.NS","NBCC.NS",
    "DMART.NS","AVENUE.NS","SPENCERS.NS","VMART.NS","SHOPERSTOP.NS",
    "MUTHOOTFIN.NS","BAJAJHLDNG.NS","CHOLAFIN.NS","M&MFIN.NS","SHRIRAMFIN.NS",
]

TSX_TOP60 = [
    "RY.TO","TD.TO","BNS.TO","BMO.TO","CM.TO","NA.TO",
    "CNR.TO","CP.TO","CNQ.TO","SU.TO","CVE.TO","IMO.TO",
    "SHOP.TO","CSU.TO","MFC.TO","SLF.TO","GWO.TO","IAG.TO",
    "BCE.TO","T.TO","RCI-B.TO","QBR-B.TO","MRU.TO","L.TO",
    "ATD.TO","DOL.TO","CTC-A.TO","WN.TO","EMP-A.TO","GIL.TO",
    "ABX.TO","AGI.TO","K.TO","FNV.TO","WPM.TO","KL.TO",
    "TRP.TO","ENB.TO","PPL.TO","KEY.TO","GEI.TO","IPL.TO",
    "BAM.TO","BPY-UN.TO","REI-UN.TO","CAR-UN.TO","HR-UN.TO","AP-UN.TO",
    "WPT.TO","GRT-UN.TO","NXR-UN.TO","CHP-UN.TO","AAR-UN.TO","KMP-UN.TO",
    "TFII.TO","TIH.TO","STN.TO","WSP.TO","AEM.TO","LUN.TO",
]

US_TOP100 = [
    "AAPL","MSFT","NVDA","GOOGL","AMZN","META","TSLA","BRK-B","UNH","JPM",
    "V","XOM","JNJ","PG","MA","HD","CVX","MRK","ABBV","LLY",
    "COST","PEP","KO","AVGO","TMO","MCD","ACN","BAC","CRM","NFLX",
    "AMD","ADBE","CSCO","ABT","NKE","WMT","TXN","DHR","NEE","RTX",
    "LIN","ORCL","PM","QCOM","HON","UPS","AMGN","SBUX","IBM","GE",
    "CAT","LOW","SPGI","MDT","BLK","AXP","GS","MS","C","WFC",
    "DE","MMM","T","VZ","INTC","BA","NOW","ISRG","BKNG","GILD",
    "ADI","REGN","ZTS","SYK","MO","MDLZ","LRCX","KLAC","SNPS","CDNS",
    "ELV","CI","CVS","HUM","MCO","PLD","AMT","CCI","PSA","EQIX",
    "DIS","CMCSA","NFLX","PARA","WBD","FOX","NYT","IAC","SNAP","PINS",
]

COMMODITIES_EXTENDED = {
    "GC=F": "Gold", "SI=F": "Silver", "CL=F": "Crude Oil WTI",
    "BZ=F": "Brent Crude", "NG=F": "Natural Gas", "HG=F": "Copper",
    "ZW=F": "Wheat", "ZC=F": "Corn", "ZS=F": "Soybeans",
    "PL=F": "Platinum", "PA=F": "Palladium", "ALI=F": "Aluminium",
    "GF=F": "Feeder Cattle", "LE=F": "Live Cattle", "HE=F": "Lean Hogs",
    "ZO=F": "Oats", "ZR=F": "Rice", "CC=F": "Cocoa",
    "KC=F": "Coffee", "CT=F": "Cotton", "SB=F": "Sugar",
    "OJ=F": "Orange Juice", "LBS=F": "Lumber",
}

CRYPTO = [
    "BTC-USD", "ETH-USD", "BNB-USD", "XRP-USD", "ADA-USD",
    "DOGE-USD", "SOL-USD", "DOT-USD", "MATIC-USD", "LTC-USD",
]

GLOBAL_INDICES = {
    "^NSEI":    "Nifty 50 (India)",
    "^BSESN":   "Sensex (India)",
    "^NSEBANK": "Bank Nifty (India)",
    "^CNXIT":   "Nifty IT (India)",
    "^GSPC":    "S&P 500 (US)",
    "^IXIC":    "Nasdaq (US)",
    "^DJI":     "Dow Jones (US)",
    "^RUT":     "Russell 2000 (US)",
    "^VIX":     "VIX Volatility (US)",
    "^OSPTSX":  "TSX Composite (Canada)",
    "^FTSE":    "FTSE 100 (UK)",
    "^GDAXI":   "DAX (Germany)",
    "^FCHI":    "CAC 40 (France)",
    "^N225":    "Nikkei 225 (Japan)",
    "^HSI":     "Hang Seng (HK)",
    "000001.SS":"Shanghai Composite (China)",
    "^AXJO":    "ASX 200 (Australia)",
    "^BVSP":    "Bovespa (Brazil)",
    "^MXX":     "IPC Mexico",
    "^NSEI":    "Nifty 50 (India)",
}


def get_quote_safe(ticker: str, retries: int = 3) -> dict:
    """
    Fetch quote with retry logic for Streamlit Cloud rate limiting.
    """
    for attempt in range(retries):
        try:
            t    = yf.Ticker(ticker)
            info = t.info
            price = (info.get("currentPrice") or
                     info.get("regularMarketPrice") or
                     info.get("navPrice") or
                     info.get("previousClose"))
            if price:
                return {
                    "ticker":      ticker,
                    "name":        info.get("longName") or info.get("shortName", ticker),
                    "price":       price,
                    "currency":    info.get("currency", ""),
                    "change_pct":  info.get("regularMarketChangePercent"),
                    "day_high":    info.get("dayHigh"),
                    "day_low":     info.get("dayLow"),
                    "volume":      info.get("volume"),
                    "market_cap":  info.get("marketCap"),
                    "52w_high":    info.get("fiftyTwoWeekHigh"),
                    "52w_low":     info.get("fiftyTwoWeekLow"),
                    "pe_ratio":    info.get("trailingPE"),
                    "status":      "ok",
                    "timestamp":   datetime.now().isoformat(),
                }
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(2 ** attempt)  # exponential backoff
            else:
                return {"ticker": ticker, "status": "error", "error": str(e)}
    return {"ticker": ticker, "status": "error", "error": "Max retries exceeded"}


def scan_batch(tickers: list, delay: float = 0.5) -> list:
    """
    Scan a batch of tickers with polite rate limiting.
    Works on both local and Streamlit Cloud.
    """
    results = []
    for ticker in tickers:
        results.append(get_quote_safe(ticker))
        time.sleep(delay)
    return results


def search_stocks(query: str, market: str = "all") -> list:
    """
    Search for any stock by name or ticker across all markets.
    Uses yfinance search — covers NSE, BSE, TSX, NYSE, NASDAQ.
    Returns top 20 matches.
    """
    try:
        results = []
        # Direct ticker lookup first
        q = get_quote_safe(query.upper())
        if q.get("status") == "ok":
            results.append(q)

        # Add .NS suffix for Indian stocks
        if market in ["india", "all"] and not query.endswith(".NS"):
            q_ns = get_quote_safe(f"{query.upper()}.NS")
            if q_ns.get("status") == "ok":
                results.append(q_ns)

        # Add .TO suffix for Canadian stocks
        if market in ["canada", "all"] and not query.endswith(".TO"):
            q_to = get_quote_safe(f"{query.upper()}.TO")
            if q_to.get("status") == "ok":
                results.append(q_to)

        # Add .BO suffix for BSE stocks
        if market in ["india", "all"] and not query.endswith(".BO"):
            q_bo = get_quote_safe(f"{query.upper()}.BO")
            if q_bo.get("status") == "ok":
                results.append(q_bo)

        return results
    except Exception as e:
        return [{"ticker": query, "status": "error", "error": str(e)}]


def get_market_movers(market: str = "india", top_n: int = 20) -> list:
    """
    Returns top gainers and losers from the full market list.
    market: 'india', 'canada', 'us', 'all'
    """
    if market == "india":
        tickers = NSE_TOP100
    elif market == "canada":
        tickers = TSX_TOP60
    elif market == "us":
        tickers = US_TOP100
    else:
        tickers = NSE_TOP100[:30] + TSX_TOP60[:20] + US_TOP100[:30]

    results = scan_batch(tickers[:top_n], delay=0.3)
    valid   = [r for r in results if r.get("status") == "ok" and r.get("change_pct")]
    gainers = sorted(valid, key=lambda x: x.get("change_pct", 0), reverse=True)[:5]
    losers  = sorted(valid, key=lambda x: x.get("change_pct", 0))[:5]
    return {"gainers": gainers, "losers": losers, "all": valid}


def get_all_indices() -> list:
    """Fetch all global indices at once."""
    results = []
    for ticker, name in GLOBAL_INDICES.items():
        q = get_quote_safe(ticker)
        q["friendly_name"] = name
        results.append(q)
        time.sleep(0.3)
    return results


def get_crypto() -> list:
    """Fetch all tracked crypto."""
    return scan_batch(CRYPTO, delay=0.3)


def get_extended_commodities() -> list:
    """Fetch all commodities including soft commodities."""
    results = []
    for ticker, name in COMMODITIES_EXTENDED.items():
        q = get_quote_safe(ticker)
        q["friendly_name"] = name
        results.append(q)
        time.sleep(0.2)
    return results
