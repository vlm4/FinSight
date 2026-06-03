"""
FinSight — cloud_sync.py (Google Drive only)
Auto-sync reports and backups to Google Drive desktop folder.
No API keys needed — uses the desktop app sync folder method.
"""

import os, shutil, json, csv, logging, platform
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
log = logging.getLogger("FinSight.CloudSync")

APP_FOLDER_NAME   = "FinSight"
GOOGLE_DRIVE_PATH = os.getenv("GOOGLE_DRIVE_PATH", "")


def detect_google_drive():
    system = platform.system()
    home   = Path.home()
    candidates = (
        [home/"Google Drive"/"My Drive",
         home/"GoogleDrive"/"My Drive",
         Path("C:/Users")/home.name/"Google Drive"/"My Drive"]
        if system == "Windows"
        else [home/"Google Drive"/"My Drive",
              home/"Library"/"CloudStorage"/"GoogleDrive-personal"/"My Drive"]
    )
    if system != "Windows":
        cloud = home/"Library"/"CloudStorage"
        if cloud.exists():
            for f in cloud.iterdir():
                if "GoogleDrive" in f.name:
                    candidates.append(f/"My Drive")
    for p in candidates:
        if p.exists():
            return p
    return None


def get_gdrive_base():
    if GOOGLE_DRIVE_PATH and Path(GOOGLE_DRIVE_PATH).exists():
        return Path(GOOGLE_DRIVE_PATH) / APP_FOLDER_NAME
    detected = detect_google_drive()
    if detected:
        return detected / APP_FOLDER_NAME
    log.warning("Google Drive not found. Install desktop app.")
    return None


def _ensure_folders(base):
    base.mkdir(parents=True, exist_ok=True)
    for f in ["reports","briefs","backups","snapshots","alerts"]:
        (base/f).mkdir(exist_ok=True)


def sync_daily_report(report):
    base = get_gdrive_base()
    if not base: return {"status":"error","error":"Google Drive not found"}
    try:
        _ensure_folders(base)
        fname = f"finsight_report_{datetime.now().strftime('%Y%m%d')}.json"
        dest  = base/"reports"/fname
        dest.write_text(json.dumps(report,indent=2,default=str),encoding="utf-8")
        return {"status":"ok","file":fname}
    except Exception as e:
        return {"status":"error","error":str(e)}


def sync_morning_brief(brief):
    base = get_gdrive_base()
    if not base: return {"status":"error","error":"Google Drive not found"}
    try:
        _ensure_folders(base)
        today = datetime.now().strftime("%Y-%m-%d %H:%M")
        entry = f"\n{'='*52}\n{today}\n{'='*52}\n{brief}\n"
        with open(base/"briefs"/"morning_briefs_archive.txt","a",encoding="utf-8") as f:
            f.write(entry)
        return {"status":"ok"}
    except Exception as e:
        return {"status":"error","error":str(e)}


def sync_database_backup():
    base    = get_gdrive_base()
    db_path = Path("finsight.db")
    if not base: return {"status":"error","error":"Google Drive not found"}
    if not db_path.exists(): return {"status":"error","error":"finsight.db not found"}
    try:
        _ensure_folders(base)
        fname      = f"finsight_backup_{datetime.now().strftime('%Y%m%d')}.db"
        backup_dir = base/"backups"
        shutil.copy2(db_path, backup_dir/fname)
        old = sorted(backup_dir.glob("finsight_backup_*.db"))
        for o in old[:-30]: o.unlink()
        return {"status":"ok","file":fname}
    except Exception as e:
        return {"status":"error","error":str(e)}


def sync_wealth_snapshot(snapshot):
    base = get_gdrive_base()
    if not base: return {"status":"error","error":"Google Drive not found"}
    try:
        _ensure_folders(base)
        csv_path   = base/"snapshots"/"wealth_history.csv"
        fieldnames = ["date","total_cad","india_cad","canada_cad","us_cad","usd_cad","usd_inr"]
        row = {
            "date":       datetime.now().strftime("%Y-%m-%d %H:%M"),
            "total_cad":  round(snapshot.get("total_cad",0),2),
            "india_cad":  round(snapshot.get("by_market",{}).get("India_CAD",0),2),
            "canada_cad": round(snapshot.get("by_market",{}).get("Canada_CAD",0),2),
            "us_cad":     round(snapshot.get("by_market",{}).get("US_CAD",0),2),
            "usd_cad":    snapshot.get("fx_rates",{}).get("USD_CAD",""),
            "usd_inr":    snapshot.get("fx_rates",{}).get("USD_INR",""),
        }
        write_header = not csv_path.exists()
        with open(csv_path,"a",newline="",encoding="utf-8") as f:
            w = csv.DictWriter(f,fieldnames=fieldnames)
            if write_header: w.writeheader()
            w.writerow(row)
        return {"status":"ok"}
    except Exception as e:
        return {"status":"error","error":str(e)}


def sync_alerts(alerts):
    base = get_gdrive_base()
    if not base: return {"status":"error","error":"Google Drive not found"}
    if not alerts: return {"status":"ok","info":"No alerts"}
    try:
        _ensure_folders(base)
        csv_path   = base/"alerts"/"alert_history.csv"
        fieldnames = ["date","type","severity","ticker","message"]
        write_header = not csv_path.exists()
        with open(csv_path,"a",newline="",encoding="utf-8") as f:
            w = csv.DictWriter(f,fieldnames=fieldnames)
            if write_header: w.writeheader()
            for a in alerts:
                w.writerow({"date":datetime.now().strftime("%Y-%m-%d"),
                            "type":a.get("type",""),"severity":a.get("severity",""),
                            "ticker":a.get("ticker",""),"message":a.get("message","")[:200]})
        return {"status":"ok","count":len(alerts)}
    except Exception as e:
        return {"status":"error","error":str(e)}


def run_full_sync(report):
    base = get_gdrive_base()
    if not base:
        return {"status":"error","message":"Google Drive not found"}
    return {
        "drive_path": str(base),
        "synced_at":  datetime.now().isoformat(),
        "report":     sync_daily_report(report),
        "brief":      sync_morning_brief(report.get("morning_brief","")),
        "database":   sync_database_backup(),
        "snapshot":   sync_wealth_snapshot(report.get("wealth_snapshot",{})),
        "alerts":     sync_alerts(report.get("alerts",[])),
    }


def get_sync_status():
    base = get_gdrive_base()
    if not base or not base.exists():
        return {"connected":False,"message":"Google Drive not detected"}
    rd = base/"reports"
    rc = len(list(rd.glob("*.json"))) if rd.exists() else 0
    bc = len(list((base/"backups").glob("*.db"))) if (base/"backups").exists() else 0
    lr = None
    if rc > 0:
        reports = sorted(rd.glob("*.json"))
        lr = reports[-1].stem.replace("finsight_report_","")
    return {
        "connected":True,"drive_path":str(base),
        "report_count":rc,"latest_report":lr,"backup_count":bc,
        "snapshot_csv":(base/"snapshots"/"wealth_history.csv").exists(),
        "alert_csv":(base/"alerts"/"alert_history.csv").exists(),
        "briefs_archive":(base/"briefs"/"morning_briefs_archive.txt").exists(),
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,format="%(asctime)s %(levelname)s %(message)s")
    print("\n📊 FinSight — Google Drive Sync Test\n" + "="*45)
    s = get_sync_status()
    if s["connected"]:
        print(f"✅ Connected: {s['drive_path']}")
        print(f"   Reports: {s['report_count']} | Backups: {s['backup_count']}")
        print(f"   Wealth CSV: {s['snapshot_csv']} | Alert log: {s['alert_csv']}")
        print(f"\n✅ Sync will run automatically after each daily report.")
    else:
        print(f"❌ {s['message']}")
        print("\nFix: go to google.com/drive/download — install and sign in.")
