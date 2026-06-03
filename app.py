"""
╔══════════════════════════════════════════════════════════════════╗
║  FinSight — app.py                                               ║
║  Streamlit web app · Phone-accessible via ngrok                  ║
║  Run: streamlit run app.py                                       ║
╚══════════════════════════════════════════════════════════════════╝
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import json, requests, os, time
from datetime import datetime
from dotenv import load_dotenv

from fetcher  import (
    get_quote, scan_category, get_history, get_all_indian_mfs,
    get_commodities, get_real_estate_reits, get_rsi, get_macd,
    get_news, search_indian_mf, get_options_chain, get_fx_rates,
    ai_portfolio_score, cross_market_correlation,
    generate_morning_brief, unified_wealth_snapshot,
    WATCHLIST, INDIAN_MF_SCHEMES, RE_POCKETS, APP_NAME, TAGLINE,
)
from database import (
    init_db, save_quotes, save_commodities, save_indian_mfs,
    save_alerts, save_ai_score, save_morning_brief, save_wealth_snapshot,
    get_latest_quotes, get_price_history, get_latest_ai_score,
    get_latest_brief, get_wealth_history,
)

load_dotenv()
CLAUDE_KEY = "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"

# ── Page config ───────────────────────────────────────────────────
st.set_page_config(
    page_title="FinSight",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Security: simple password gate ───────────────────────────────
APP_PASSWORD = os.getenv("FINSIGHT_PASSWORD","finsight1304")
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.markdown("""
    <div style='text-align:center;padding:60px 0 20px'>
      <h1 style='font-size:36px;margin-bottom:4px'>📊 FinSight</h1>
      <p style='color:gray;font-size:15px'>See beyond the numbers.</p>
    </div>
    """, unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        pwd = st.text_input("Enter your password", type="password",
                            placeholder="Password")
        if st.button("Sign in", use_container_width=True):
            if pwd == APP_PASSWORD:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Incorrect password")
    st.stop()

# ── Init ──────────────────────────────────────────────────────────
init_db()

# ── Sidebar ───────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='padding:8px 0 16px'>
      <span style='font-size:22px;font-weight:600'>📊 FinSight</span><br>
      <span style='font-size:12px;color:gray'>See beyond the numbers.</span>
    </div>
    """, unsafe_allow_html=True)

    page = st.radio("Navigate", [
        "🏠 Dashboard",
        "🤖 Ask AI",
        "🇮🇳 India Markets",
        "🇨🇦 Canada Markets",
        "🇺🇸 US Markets",
        "🪙 Commodities",
        "🏘️ Real Estate",
        "🏦 Mutual Funds",
        "📊 F&O / Options",
        "🔍 Search Any Asset",
        "⚠️ Alerts & Signals",
    ], label_visibility="collapsed")

    st.divider()
    st.caption(f"Updated: {datetime.now().strftime('%d %b %Y %H:%M')}")
    st.caption("⚠️ Informational only. Not financial advice.")

# ── Helpers ───────────────────────────────────────────────────────
def color_badge(val):
    if val is None: return "—"
    color = "#22a06b" if val > 0 else "#e34935"
    arrow = "▲" if val > 0 else "▼"
    return f'<span style="color:{color};font-weight:600">{arrow} {abs(val):.2f}%</span>'

def show_table(quotes: list, save: bool = True):
    if save:
        save_quotes(quotes)
    rows = [{"Ticker": q.get("ticker",""),
             "Name":   (q.get("name") or "")[:28],
             "Price":  q.get("price"),
             "CCY":    q.get("currency",""),
             "Chg %":  q.get("change_pct"),
             "High":   q.get("day_high"),
             "Low":    q.get("day_low"),
             "P/E":    q.get("pe_ratio")}
            for q in quotes if q.get("status") != "error"]
    if rows:
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else:
        st.info("No data returned.")

def price_chart(ticker: str, period: str = "1y"):
    try:
        df  = get_history(ticker, period=period).reset_index()
        fig = px.line(df, x=df.columns[0], y="Close",
                      title=f"{ticker} — {period} price history",
                      template="plotly_white", color_discrete_sequence=["#0F6E56"])
        fig.update_layout(margin=dict(l=0,r=0,t=40,b=0), height=280)
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.warning(f"Chart error: {e}")


# ─────────────────────────────────────────────────────────────────
# DASHBOARD
# ─────────────────────────────────────────────────────────────────
if page == "🏠 Dashboard":
    st.title("📊 FinSight Dashboard")

    # Morning brief
    brief = get_latest_brief()
    if brief:
        st.info(f"**Today's brief:** {brief}")
    else:
        st.info("Run your daily report to generate today's morning brief.")

    st.divider()

    # ── Wealth snapshot ──────────────────────────────────────────
    st.subheader("💰 Wealth snapshot")
    snap_history = get_wealth_history(days=30)
    if snap_history:
        latest_snap = snap_history[-1]
        cols = st.columns(4)
        cols[0].metric("Total tracked (CAD)", f"${latest_snap['total_cad']:,.0f}")
        try:
            by_mkt = json.loads(latest_snap.get("by_market","{}"))
            cols[1].metric("India holdings", f"${by_mkt.get('India_CAD',0):,.0f} CAD")
            cols[2].metric("Canada holdings", f"${by_mkt.get('Canada_CAD',0):,.0f} CAD")
            cols[3].metric("US holdings", f"${by_mkt.get('US_CAD',0):,.0f} CAD")
        except: pass
        if len(snap_history) > 1:
            df_snap = pd.DataFrame(snap_history)
            df_snap["fetched_at"] = pd.to_datetime(df_snap["fetched_at"])
            fig = px.area(df_snap, x="fetched_at", y="total_cad",
                          title="Portfolio value over time (CAD)",
                          template="plotly_white",
                          color_discrete_sequence=["#0F6E56"])
            fig.update_layout(height=200, margin=dict(l=0,r=0,t=36,b=0))
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.caption("Run a full daily report to populate your wealth snapshot.")

    st.divider()

    # ── AI portfolio score ────────────────────────────────────────
    st.subheader("🤖 AI portfolio score")
    score_data = get_latest_ai_score()
    if score_data:
        score = score_data.get("score", 0)
        color = "#1D9E75" if score >= 70 else "#BA7517" if score >= 50 else "#E24B4A"
        c1, c2 = st.columns([1,3])
        with c1:
            st.markdown(f"""
            <div style='text-align:center;background:#f5f5f5;
                        border-radius:12px;padding:20px'>
              <div style='font-size:42px;font-weight:700;color:{color}'>{score}</div>
              <div style='font-size:12px;color:gray'>Portfolio health</div>
            </div>""", unsafe_allow_html=True)
        with c2:
            st.write(score_data.get("overall_verdict","—"))
            picks = score_data.get("top_picks",[])
            if picks:
                st.success("**Top picks today:** " +
                           " · ".join(f"{p['ticker']} — {p['reason']}" for p in picks[:3]))
            caution = score_data.get("caution",[])
            if caution:
                st.warning("**Watch closely:** " +
                           " · ".join(f"{c['ticker']} — {c['reason']}" for c in caution[:3]))
    else:
        st.caption("AI score will appear after your first full daily report run.")

    st.divider()

    # ── Quick indices ─────────────────────────────────────────────
    st.subheader("📈 Market pulse")
    if st.button("🔄 Refresh market pulse"):
        with st.spinner("Fetching live indices..."):
            tickers = {"^NSEI":"Nifty 50","^GSPC":"S&P 500",
                       "^OSPTSX":"TSX","GC=F":"Gold"}
            cols = st.columns(4)
            for i,(ticker,name) in enumerate(tickers.items()):
                q   = get_quote(ticker)
                chg = q.get("change_pct")
                cols[i].metric(name,
                    f"{q.get('price','—')} {q.get('currency','')}",
                    f"{chg:+.2f}%" if chg else "—")

    # FX rates
    st.subheader("💱 FX rates")
    if st.button("Get live FX"):
        with st.spinner("Fetching..."):
            fx = get_fx_rates()
            c1,c2,c3 = st.columns(3)
            c1.metric("USD → CAD", f"{fx.get('USD_CAD','—'):.4f}")
            c2.metric("USD → INR", f"{fx.get('USD_INR','—'):.2f}")
            c3.metric("CAD → INR", f"{fx.get('CAD_INR','—'):.2f}")


# ─────────────────────────────────────────────────────────────────
# ASK AI — AI CHAT TAB
# ─────────────────────────────────────────────────────────────────
elif page == "🤖 Ask AI":
    st.title("🤖 Ask FinSight AI")
    st.caption("Ask anything about your portfolio, markets, or investment strategy.")

    if not CLAUDE_KEY:
        st.error("ANTHROPIC_API_KEY not set in your .env file. Add it to enable AI chat.")
        st.stop()

    # Init chat history
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content":
             f"Good morning! I'm your FinSight AI assistant. I can see your tracked "
             f"market data from the SQLite database. Ask me anything about your "
             f"watchlist, signals, real estate, or market trends — and I'll explain "
             f"everything in plain English."}
        ]

    # Quick question chips
    st.write("**Quick questions:**")
    chip_cols = st.columns(4)
    chips = [
        ("Today's summary", "Give me a plain English summary of what's happening in markets today across India, Canada, and US."),
        ("RSI alerts?", "Which stocks in my watchlist are showing RSI signals above 70 or below 30? Explain what that means."),
        ("Gold signal", "What's the current gold signal and should I be paying attention to it?"),
        ("TFSA strategy", "What's the best strategy for my Canadian TFSA given the current market conditions?"),
    ]
    for i,(label,prompt) in enumerate(chips):
        if chip_cols[i].button(label, use_container_width=True):
            st.session_state.messages.append({"role":"user","content":prompt})

    # Show chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    # Chat input
    if user_input := st.chat_input("Ask anything about your portfolio..."):
        st.session_state.messages.append({"role":"user","content":user_input})
        with st.chat_message("user"):
            st.write(user_input)

        # Build context from DB
        recent_quotes  = get_latest_quotes()
        recent_score   = get_latest_ai_score()
        recent_brief   = get_latest_brief()
        wealth_history = get_wealth_history(days=7)

        # Compact data summary for context
        quote_summary = "\n".join(
            f"{q['ticker']}: {q.get('price','—')} {q.get('currency','')} "
            f"({q.get('change_pct',0):+.1f}%)" if q.get('change_pct') else
            f"{q['ticker']}: {q.get('price','—')} {q.get('currency','')}"
            for q in recent_quotes[:40]
        )

        system_prompt = f"""You are FinSight AI, a personal wealth intelligence assistant.
You are talking to an investor who tracks markets across India, Canada, and the US.
You explain everything in plain English — no jargon, no complexity.
You are informational only — you never give direct buy/sell advice.
You are warm, smart, and direct. You get to the point.

Current data from the investor's database:
--- RECENT QUOTES ---
{quote_summary or 'No quotes fetched yet today.'}

--- AI SCORE (latest) ---
Score: {recent_score.get('score','—')}
Verdict: {recent_score.get('overall_verdict','Not available')}

--- MORNING BRIEF (latest) ---
{recent_brief or 'Not yet generated.'}

--- REAL ESTATE POCKETS ---
India: Hyderabad (10-14%/yr), Bengaluru (8-12%/yr), Pune (7-10%/yr)
Canada: Calgary (8-12%/yr), Edmonton (6-9%/yr)
USA: Austin TX (7-11%/yr), Phoenix AZ (6-9%/yr)

Always:
- Answer in plain English
- Be specific using the data above when relevant
- Keep answers concise — 3-5 sentences for simple questions, more for complex ones
- End with one practical next step the investor can take
- Never say "I cannot provide financial advice" repeatedly — say it once if needed then be helpful"""

        # Build messages for API
        api_messages = []
        for m in st.session_state.messages[:-1]:  # Exclude last (just added)
            api_messages.append({"role": m["role"], "content": m["content"]})
        api_messages.append({"role": "user", "content": user_input})

        with st.chat_message("assistant"):
            with st.spinner("FinSight is thinking..."):
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
                            "max_tokens": 600,
                            "system":     system_prompt,
                            "messages":   api_messages,
                        },
                        timeout=30,
                    )
                    reply = resp.json().get("content", [{}])[0].get("text", "Sorry, I could not get a response. Please try again.")
                except Exception as e:
                    reply = f"Sorry, I couldn't connect to the AI right now. Error: {e}"

                st.write(reply)
                st.session_state.messages.append({"role":"assistant","content":reply})

    if st.button("🗑️ Clear chat"):
        st.session_state.messages = []
        st.rerun()


# ─────────────────────────────────────────────────────────────────
# INDIA MARKETS
# ─────────────────────────────────────────────────────────────────
elif page == "🇮🇳 India Markets":
    st.title("🇮🇳 India Markets — NSE / BSE")
    tab1,tab2,tab3,tab4 = st.tabs(["Stocks","ETFs","Indices","Signals"])

    with tab1:
        if st.button("Fetch Indian stocks"):
            with st.spinner("Fetching..."):
                show_table(scan_category("IN_STOCKS"))
        t = st.selectbox("Price chart", WATCHLIST["IN_STOCKS"])
        price_chart(t)

    with tab2:
        if st.button("Fetch Indian ETFs"):
            with st.spinner("Fetching..."):
                show_table(scan_category("IN_ETFS"))

    with tab3:
        if st.button("Fetch indices"):
            with st.spinner("Fetching..."):
                show_table(scan_category("IN_INDICES"))

    with tab4:
        ticker = st.selectbox("Signal check", WATCHLIST["IN_STOCKS"])
        if st.button("Get RSI + MACD"):
            with st.spinner("Fetching from Alpha Vantage (free tier — takes ~30s)..."):
                rsi  = get_rsi(ticker)
                time.sleep(13)
                macd = get_macd(ticker)
            c1,c2 = st.columns(2)
            with c1:
                val  = rsi.get("value","—")
                zone = rsi.get("zone","amber")
                icon = {"green":"🟢","red":"🔴","amber":"🟡"}.get(zone,"⚪")
                st.metric("RSI-14", val)
                st.write(f"{icon} {rsi.get('signal','—')}")
            with c2:
                st.metric("MACD", macd.get("crossover","—"))
                z2 = macd.get("zone","amber")
                i2 = {"green":"🟢","red":"🔴"}.get(z2,"⚪")
                st.write(f"{i2} MACD {macd.get('macd','—')} | Signal {macd.get('signal_line','—')}")
            st.info(f"**Plain English:** RSI of {val} means {rsi.get('signal','—').lower()}. "
                    f"MACD shows {macd.get('crossover','—').lower()}. "
                    f"Use these as one signal among many — not as the only reason to act.")


# ─────────────────────────────────────────────────────────────────
# CANADA MARKETS
# ─────────────────────────────────────────────────────────────────
elif page == "🇨🇦 Canada Markets":
    st.title("🇨🇦 Canada Markets — TSX")
    tab1,tab2,tab3 = st.tabs(["Stocks","ETFs","MF Proxies"])
    with tab1:
        if st.button("Fetch Canadian stocks"):
            with st.spinner("Fetching..."):
                show_table(scan_category("CA_STOCKS"))
        t = st.selectbox("Price chart", WATCHLIST["CA_STOCKS"])
        price_chart(t)
    with tab2:
        if st.button("Fetch Canadian ETFs"):
            with st.spinner("Fetching..."):
                show_table(scan_category("CA_ETFS"))
    with tab3:
        st.caption("Asset allocation ETFs — closest equivalent to mutual funds on TSX.")
        if st.button("Fetch CA MF proxies"):
            with st.spinner("Fetching..."):
                show_table(scan_category("CA_ETFS_MF"))
        st.info("💡 **XEQT.TO** = 100% equity global. **XBAL.TO** = 60/40 balanced. **XCNS.TO** = conservative. All TFSA/RRSP friendly.")


# ─────────────────────────────────────────────────────────────────
# US MARKETS
# ─────────────────────────────────────────────────────────────────
elif page == "🇺🇸 US Markets":
    st.title("🇺🇸 US Markets — NYSE / NASDAQ")
    tab1,tab2,tab3 = st.tabs(["Stocks","ETFs + MFs","Indices"])
    with tab1:
        if st.button("Fetch US stocks"):
            with st.spinner("Fetching..."):
                show_table(scan_category("US_STOCKS"))
        t = st.selectbox("Price chart", WATCHLIST["US_STOCKS"])
        price_chart(t)
    with tab2:
        c1,c2 = st.columns(2)
        with c1:
            if st.button("Fetch US ETFs"):
                with st.spinner("Fetching..."):
                    show_table(scan_category("US_ETFS"))
        with c2:
            if st.button("Fetch US MFs"):
                with st.spinner("Fetching..."):
                    show_table(scan_category("US_MF"))
    with tab3:
        if st.button("Fetch US indices"):
            with st.spinner("Fetching..."):
                show_table(scan_category("US_INDICES"))


# ─────────────────────────────────────────────────────────────────
# COMMODITIES
# ─────────────────────────────────────────────────────────────────
elif page == "🪙 Commodities":
    st.title("🪙 Commodities")
    if st.button("Fetch all commodities"):
        with st.spinner("Fetching..."):
            comms = get_commodities()
            save_commodities(comms)
            rows = [{"Commodity": c.get("friendly_name",c["ticker"]),
                     "Price":     c.get("price"),
                     "Currency":  c.get("currency"),
                     "Change %":  c.get("change_pct")}
                    for c in comms]
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    price_chart("GC=F")


# ─────────────────────────────────────────────────────────────────
# REAL ESTATE
# ─────────────────────────────────────────────────────────────────
elif page == "🏘️ Real Estate":
    st.title("🏘️ Real Estate Markets")
    tab1,tab2 = st.tabs(["REITs & Proxies","Pocket Analysis"])

    with tab1:
        if st.button("Fetch REITs"):
            with st.spinner("Fetching..."):
                show_table(get_real_estate_reits(), save=False)

    with tab2:
        country = st.selectbox("Country", ["India","Canada","USA"])
        for loc in RE_POCKETS.get(country,[]):
            with st.expander(f"📍 {loc['city']}"):
                c1,c2 = st.columns(2)
                with c1:
                    st.write(f"**Zones:** {loc['zones']}")
                    st.write(f"**Why:** {loc['drivers']}")
                with c2:
                    st.metric("Avg appreciation", loc["appreciation"])
        st.warning("Data sourced from CREA, NAR, NHB Residex, PropTech research. Consult a local advisor before investing.")


# ─────────────────────────────────────────────────────────────────
# MUTUAL FUNDS
# ─────────────────────────────────────────────────────────────────
elif page == "🏦 Mutual Funds":
    st.title("🏦 Mutual Funds")
    tab1,tab2 = st.tabs(["Indian MFs","Search MF"])

    with tab1:
        if st.button("Fetch Indian MF NAVs"):
            with st.spinner("Fetching NAVs..."):
                mfs = get_all_indian_mfs()
                save_indian_mfs(mfs)
                rows = [{"Fund":      m.get("label",""),
                         "Name":      (m.get("name") or "")[:35],
                         "NAV (₹)":   m.get("nav"),
                         "1M Chg %":  m.get("change_1m"),
                         "Category":  m.get("category","")}
                        for m in mfs]
                st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    with tab2:
        q = st.text_input("Search Indian MFs", placeholder="e.g. HDFC, SBI, Axis")
        if q:
            results = search_indian_mf(q)
            if results:
                st.dataframe(pd.DataFrame(results), use_container_width=True, hide_index=True)
            else:
                st.info("No matches found.")


# ─────────────────────────────────────────────────────────────────
# F&O / OPTIONS
# ─────────────────────────────────────────────────────────────────
elif page == "📊 F&O / Options":
    st.title("📊 F&O / Options")
    ticker = st.text_input("Enter ticker", value="RELIANCE.NS")
    if st.button("Get options chain"):
        with st.spinner("Fetching..."):
            chain = get_options_chain(ticker)
            if chain.get("status") == "error":
                st.error(chain.get("error"))
            else:
                st.success(f"Nearest expiry: **{chain.get('expiry')}**")
                c1,c2 = st.columns(2)
                with c1:
                    st.subheader("Calls")
                    st.dataframe(pd.DataFrame(chain.get("calls",[])),
                                 use_container_width=True, hide_index=True)
                with c2:
                    st.subheader("Puts")
                    st.dataframe(pd.DataFrame(chain.get("puts",[])),
                                 use_container_width=True, hide_index=True)
                st.info("**Calls** = bets price goes up. **Puts** = bets price goes down. **OI** = active contracts. Full NSE F&O lot data needs Zerodha account.")


# ─────────────────────────────────────────────────────────────────
# SEARCH ANY ASSET
# ─────────────────────────────────────────────────────────────────
elif page == "🔍 Search Any Asset":
    st.title("🔍 Search Any Asset")
    st.caption("Any ticker worldwide — stocks, ETFs, crypto, indices, commodities, MFs")
    ticker = st.text_input("Ticker", placeholder="e.g. ZOMATO.NS  BTC-USD  TSLA  ENB.TO")
    c1,c2 = st.columns(2)
    if c1.button("Get live quote") and ticker:
        with st.spinner("Fetching..."):
            q = get_quote(ticker.strip().upper())
            if q.get("status") == "error":
                st.error(q.get("error"))
            else:
                col1,col2,col3,col4 = st.columns(4)
                col1.metric("Price", f"{q.get('price','—')} {q.get('currency','')}")
                col2.metric("Change", f"{q.get('change_pct',0):+.2f}%" if q.get('change_pct') else "—")
                col3.metric("52w High", q.get("52w_high","—"))
                col4.metric("52w Low",  q.get("52w_low","—"))
                st.json(q)
    if c2.button("Price chart") and ticker:
        price_chart(ticker.strip().upper())


# ─────────────────────────────────────────────────────────────────
# ALERTS & SIGNALS
# ─────────────────────────────────────────────────────────────────
elif page == "⚠️ Alerts & Signals":
    st.title("⚠️ Alerts & Signals")

    st.subheader("Cross-market correlation check")
    st.caption("Detects when India, Canada, and US markets move together — signals macro events.")
    if st.button("Run correlation check now"):
        with st.spinner("Fetching all markets..."):
            all_q = {}
            for cat in ["IN_STOCKS","US_STOCKS","CA_STOCKS","COMMODITIES"]:
                all_q[cat] = scan_category(cat)
            alerts = cross_market_correlation(all_q)
            save_alerts(alerts)
            if alerts:
                for a in alerts:
                    sev = a.get("severity","low")
                    if sev == "high":
                        st.error(f"{a['emoji']} {a['message']}")
                    elif sev == "medium":
                        st.warning(f"{a['emoji']} {a['message']}")
                    else:
                        st.success(f"{a['emoji']} {a['message']}")
            else:
                st.success("✅ No correlation alerts today — markets moving independently.")

    st.divider()
    st.subheader("RSI signal scanner")
    tickers = st.multiselect("Select tickers",
        WATCHLIST["IN_STOCKS"]+WATCHLIST["US_STOCKS"]+WATCHLIST["CA_STOCKS"],
        default=["RELIANCE.NS","AAPL","RY.TO"])
    if st.button("Scan RSI") and tickers:
        prog = st.progress(0)
        for i,t in enumerate(tickers):
            rsi = get_rsi(t)
            zone = rsi.get("zone","amber")
            icon = {"green":"🟢","red":"🔴","amber":"🟡"}.get(zone,"⚪")
            if "error" not in rsi:
                st.write(f"{icon} **{t}** — RSI {rsi['value']} — {rsi['signal']}")
            prog.progress((i+1)/len(tickers))
            time.sleep(13)
