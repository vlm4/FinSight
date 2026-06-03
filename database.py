"""
╔══════════════════════════════════════════════════════════════════╗
║  FinSight — database.py                                          ║
║  SQLite storage layer — all data stays on your laptop            ║
╚══════════════════════════════════════════════════════════════════╝
"""

import sqlite3, json, logging
from datetime import datetime
from pathlib import Path

log     = logging.getLogger("FinSight.DB")
DB_PATH = Path("finsight.db")

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS quotes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticker TEXT, name TEXT, asset_type TEXT,
        price REAL, currency TEXT, change_pct REAL,
        day_high REAL, day_low REAL, volume INTEGER,
        market_cap REAL, pe_ratio REAL, fetched_at TEXT
    );
    CREATE TABLE IF NOT EXISTS indicators (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticker TEXT, indicator TEXT, value REAL,
        signal TEXT, zone TEXT, date TEXT, fetched_at TEXT
    );
    CREATE TABLE IF NOT EXISTS indian_mf_nav (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        scheme_code TEXT, label TEXT, name TEXT,
        nav REAL, fund_house TEXT, category TEXT,
        change_1m REAL, fetched_at TEXT
    );
    CREATE TABLE IF NOT EXISTS commodities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticker TEXT, name TEXT, price REAL,
        currency TEXT, change_pct REAL, fetched_at TEXT
    );
    CREATE TABLE IF NOT EXISTS alerts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        alert_type TEXT, severity TEXT, message TEXT,
        ticker TEXT, triggered_at TEXT, notified INTEGER DEFAULT 0
    );
    CREATE TABLE IF NOT EXISTS ai_scores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        score INTEGER, overall_verdict TEXT,
        top_picks TEXT, caution TEXT, hold_steady TEXT,
        fetched_at TEXT
    );
    CREATE TABLE IF NOT EXISTS morning_briefs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        brief TEXT, fetched_at TEXT
    );
    CREATE TABLE IF NOT EXISTS wealth_snapshots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        total_cad REAL, by_market TEXT,
        fx_rates TEXT, fetched_at TEXT
    );
    CREATE INDEX IF NOT EXISTS idx_quotes_ticker  ON quotes(ticker);
    CREATE INDEX IF NOT EXISTS idx_quotes_fetched ON quotes(fetched_at);
    """)
    conn.commit()
    conn.close()
    log.info(f"FinSight database ready: {DB_PATH.resolve()}")

def save_quotes(quotes: list):
    conn = get_conn()
    now  = datetime.now().isoformat()
    rows = [(q.get("ticker"), q.get("name"), q.get("asset_type"),
             q.get("price"), q.get("currency"), q.get("change_pct"),
             q.get("day_high"), q.get("day_low"), q.get("volume"),
             q.get("market_cap"), q.get("pe_ratio"), now)
            for q in quotes if q.get("status") == "ok"]
    conn.executemany("""INSERT INTO quotes
        (ticker,name,asset_type,price,currency,change_pct,
         day_high,day_low,volume,market_cap,pe_ratio,fetched_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""", rows)
    conn.commit(); conn.close()

def save_indicator(data: dict):
    if "error" in data: return
    conn = get_conn()
    conn.execute("""INSERT INTO indicators
        (ticker,indicator,value,signal,zone,date,fetched_at)
        VALUES (?,?,?,?,?,?,?)""",
        (data.get("ticker"), data.get("indicator"),
         data.get("value") or data.get("macd"),
         data.get("signal") or data.get("crossover"),
         data.get("zone"), data.get("date"),
         datetime.now().isoformat()))
    conn.commit(); conn.close()

def save_indian_mfs(mfs: list):
    conn = get_conn()
    now  = datetime.now().isoformat()
    for m in mfs:
        if m.get("status") == "ok":
            conn.execute("""INSERT INTO indian_mf_nav
                (scheme_code,label,name,nav,fund_house,category,change_1m,fetched_at)
                VALUES (?,?,?,?,?,?,?,?)""",
                (m.get("scheme_code"), m.get("label"), m.get("name"),
                 m.get("nav"), m.get("fund_house"), m.get("category"),
                 m.get("change_1m"), now))
    conn.commit(); conn.close()

def save_commodities(items: list):
    conn = get_conn()
    now  = datetime.now().isoformat()
    for c in items:
        conn.execute("""INSERT INTO commodities
            (ticker,name,price,currency,change_pct,fetched_at)
            VALUES (?,?,?,?,?,?)""",
            (c.get("ticker"), c.get("friendly_name"),
             c.get("price"), c.get("currency"),
             c.get("change_pct"), now))
    conn.commit(); conn.close()

def save_alerts(alerts: list):
    conn = get_conn()
    now  = datetime.now().isoformat()
    for a in alerts:
        conn.execute("""INSERT INTO alerts
            (alert_type,severity,message,ticker,triggered_at)
            VALUES (?,?,?,?,?)""",
            (a.get("type"), a.get("severity"),
             a.get("message"), a.get("ticker",""), now))
    conn.commit(); conn.close()

def save_ai_score(score_data: dict):
    if "error" in score_data: return
    conn = get_conn()
    conn.execute("""INSERT INTO ai_scores
        (score,overall_verdict,top_picks,caution,hold_steady,fetched_at)
        VALUES (?,?,?,?,?,?)""",
        (score_data.get("score"),
         score_data.get("overall_verdict",""),
         json.dumps(score_data.get("top_picks",[])),
         json.dumps(score_data.get("caution",[])),
         json.dumps(score_data.get("hold_steady",[])),
         datetime.now().isoformat()))
    conn.commit(); conn.close()

def save_morning_brief(brief: str):
    conn = get_conn()
    conn.execute("INSERT INTO morning_briefs (brief,fetched_at) VALUES (?,?)",
                 (brief, datetime.now().isoformat()))
    conn.commit(); conn.close()

def save_wealth_snapshot(snap: dict):
    conn = get_conn()
    conn.execute("""INSERT INTO wealth_snapshots
        (total_cad,by_market,fx_rates,fetched_at) VALUES (?,?,?,?)""",
        (snap.get("total_cad"),
         json.dumps(snap.get("by_market",{})),
         json.dumps(snap.get("fx_rates",{})),
         datetime.now().isoformat()))
    conn.commit(); conn.close()

def get_latest_quotes(tickers: list = None) -> list:
    conn = get_conn()
    if tickers:
        ph   = ",".join("?"*len(tickers))
        rows = conn.execute(f"""SELECT q.* FROM quotes q
            INNER JOIN (SELECT ticker,MAX(fetched_at) mx FROM quotes
                        WHERE ticker IN ({ph}) GROUP BY ticker) l
            ON q.ticker=l.ticker AND q.fetched_at=l.mx""", tickers).fetchall()
    else:
        rows = conn.execute("""SELECT q.* FROM quotes q
            INNER JOIN (SELECT ticker,MAX(fetched_at) mx FROM quotes
                        GROUP BY ticker) l
            ON q.ticker=l.ticker AND q.fetched_at=l.mx""").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_price_history(ticker: str, days: int = 90) -> list:
    from datetime import timedelta
    since = (datetime.now()-timedelta(days=days)).isoformat()
    conn  = get_conn()
    rows  = conn.execute("""SELECT price,fetched_at FROM quotes
        WHERE ticker=? AND fetched_at>=? ORDER BY fetched_at""",
        (ticker, since)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_latest_ai_score() -> dict:
    conn = get_conn()
    row  = conn.execute("""SELECT * FROM ai_scores
        ORDER BY fetched_at DESC LIMIT 1""").fetchone()
    conn.close()
    if not row:
        return {}
    d = dict(row)
    d["top_picks"]   = json.loads(d.get("top_picks","[]"))
    d["caution"]     = json.loads(d.get("caution","[]"))
    d["hold_steady"] = json.loads(d.get("hold_steady","[]"))
    return d

def get_latest_brief() -> str:
    conn = get_conn()
    row  = conn.execute("""SELECT brief FROM morning_briefs
        ORDER BY fetched_at DESC LIMIT 1""").fetchone()
    conn.close()
    return row["brief"] if row else ""

def get_wealth_history(days: int = 30) -> list:
    from datetime import timedelta
    since = (datetime.now()-timedelta(days=days)).isoformat()
    conn  = get_conn()
    rows  = conn.execute("""SELECT total_cad,fetched_at FROM wealth_snapshots
        WHERE fetched_at>=? ORDER BY fetched_at""", (since,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_unnotified_alerts() -> list:
    conn = get_conn()
    rows = conn.execute("""SELECT * FROM alerts WHERE notified=0
        ORDER BY triggered_at DESC""").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def mark_notified(ids: list):
    conn = get_conn()
    conn.execute(f"""UPDATE alerts SET notified=1
        WHERE id IN ({','.join('?'*len(ids))})""", ids)
    conn.commit(); conn.close()

if __name__ == "__main__":
    init_db()
    print(f"✅ FinSight database initialised at {DB_PATH.resolve()}")
