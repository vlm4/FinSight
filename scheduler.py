"""
╔══════════════════════════════════════════════════════════════════╗
║  FinSight — scheduler.py                                         ║
║  Daily automation — runs every morning automatically             ║
╚══════════════════════════════════════════════════════════════════╝

WINDOWS — Task Scheduler:
  Program:   python
  Arguments: C:\path\to\finsight\scheduler.py
  Trigger:   Daily at 8:00 AM

MAC — cron:
  0 8 * * 1-5 python3 /path/to/finsight/scheduler.py >> finsight.log 2>&1
"""

import sys, json, logging, pathlib
from datetime import datetime

sys.path.insert(0, str(pathlib.Path(__file__).parent))

from fetcher  import (build_daily_report, send_email, send_slack,
                      format_morning_email, APP_NAME)
from database import (init_db, save_quotes, save_commodities, save_indian_mfs,
                      save_alerts, save_ai_score, save_morning_brief,
                      save_wealth_snapshot)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler("finsight.log"),
        logging.StreamHandler()
    ]
)
log = logging.getLogger("FinSight.Scheduler")


def run():
    log.info("=" * 55)
    log.info(f"  {APP_NAME} — Daily Run {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    log.info("=" * 55)

    init_db()
    report = build_daily_report()

    # Save all data
    log.info("Saving to database...")
    for cat, quotes in report.get("markets",{}).items():
        save_quotes(quotes)
    save_commodities(report.get("commodities",[]))
    save_indian_mfs(report.get("indian_mfs",[]))
    save_alerts(report.get("alerts",[]))
    if report.get("ai_scoring"):
        save_ai_score(report["ai_scoring"])
    if report.get("morning_brief"):
        save_morning_brief(report["morning_brief"])
    if report.get("wealth_snapshot"):
        save_wealth_snapshot(report["wealth_snapshot"])

    # Save JSON backup
    pathlib.Path("reports").mkdir(exist_ok=True)
    fname = f"reports/finsight_{datetime.now().strftime('%Y%m%d')}.json"
    with open(fname,"w") as f:
        json.dump(report, f, indent=2, default=str)
    log.info(f"Report saved: {fname}")

    # Send morning email
    brief   = report.get("morning_brief","")
    alerts  = report.get("alerts",[])
    snap    = report.get("wealth_snapshot",{})
    subject, body = format_morning_email(brief, alerts, snap)
    send_email(subject, body)

    # Send Slack brief
    slack_msg = f"*📊 FinSight — {datetime.now().strftime('%d %b %Y')}*\n\n"
    slack_msg += brief + "\n\n"
    if alerts:
        slack_msg += f"*{len(alerts)} alerts:*\n"
        for a in alerts[:4]:
            slack_msg += f"• {a['emoji']} {a['message'][:80]}...\n"
    else:
        slack_msg += "✅ No major alerts today."
    send_slack(slack_msg)

    log.info(f"FinSight daily run complete ✅")


if __name__ == "__main__":
    run()
