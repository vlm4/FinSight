# 📊 FinSight — Google Drive Setup Guide
## See beyond the numbers.
### Solo step-by-step · No technical help needed

---

## What this sets up

Every morning when FinSight runs automatically, it will copy your data into a
**FinSight folder inside your Google Drive**. You can then open that folder from
any device — phone, tablet, another laptop — and see everything.

Your Google Drive will look like this after setup:

```
Google Drive/
└── FinSight/
    ├── reports/          ← Daily JSON market reports
    ├── briefs/           ← Morning brief text archive
    ├── backups/          ← Database backups (last 30 days)
    ├── snapshots/        ← wealth_history.csv (open in Google Sheets)
    └── alerts/           ← alert_history.csv
```

---

## STEP 1 — Install Google Drive for Desktop
**Time needed: 5 minutes**

This is a small app that creates a Google Drive folder on your laptop.
Anything placed in that folder automatically uploads to your Google account.

1. Open your browser and go to:
   **https://www.google.com/drive/download/**

2. Click **"Download Drive for desktop"**

3. Open the downloaded file and follow the installer
   - Windows: double-click the `.exe` file
   - Mac: double-click the `.dmg` file, drag to Applications

4. When the installer finishes, Google Drive will open and ask you to sign in

5. Sign in with your Google account

6. When asked **"Where do you want your Google Drive folder?"** — leave the
   default location. Click Next / OK through any remaining screens.

7. Wait 1–2 minutes for the initial sync to complete
   - Windows: you will see a Google Drive icon in your taskbar (bottom right)
   - Mac: you will see a Google Drive icon in your menu bar (top right)

**How to confirm it worked:**
- Windows: Open File Explorer. In the left panel you should see "Google Drive"
- Mac: Open Finder. In the left panel you should see "Google Drive"

Click it — you should see a folder called "My Drive". That is your Google Drive.

✅ Step 1 done when you can see "My Drive" in your file explorer.

---

## STEP 2 — Find your Google Drive path
**Time needed: 2 minutes**

You need to know the exact folder path so FinSight can find it.

**Windows:**
1. Open File Explorer
2. Click on Google Drive in the left panel
3. Click on "My Drive"
4. Look at the address bar at the top of the window
5. You will see something like:
   `C:\Users\YourName\Google Drive\My Drive`
6. Write this down or copy it

**Mac:**
1. Open Finder
2. Click Google Drive in the left panel
3. Click on "My Drive"
4. Right-click (or Ctrl+click) on "My Drive" in the left panel
5. Select "Get Info"
6. Look for "Where:" — it shows the full path
7. It will look something like:
   `/Users/YourName/Google Drive/My Drive`
8. Write this down or copy it

✅ Step 2 done when you have your Google Drive path written down.

---

## STEP 3 — Add your path to the .env file
**Time needed: 2 minutes**

1. Open your FinSight folder on your laptop
2. Find the file called `.env`
3. Right-click it → Open with → Notepad (Windows) or TextEdit (Mac)
4. Find this line:
   ```
   GOOGLE_DRIVE_PATH=
   ```
5. Add your path after the `=` sign, for example:

   **Windows:**
   ```
   GOOGLE_DRIVE_PATH=C:\Users\YourName\Google Drive\My Drive
   ```

   **Mac:**
   ```
   GOOGLE_DRIVE_PATH=/Users/YourName/Google Drive/My Drive
   ```

6. Save the file (Ctrl+S on Windows, Cmd+S on Mac)

**Note:** If you leave this blank, FinSight will try to auto-detect Google Drive
automatically. Setting it manually is more reliable.

✅ Step 3 done when the path is saved in your .env file.

---

## STEP 4 — Add cloud_sync.py to your FinSight folder
**Time needed: 1 minute**

1. Download `cloud_sync.py` from this guide
2. Move it into your FinSight folder alongside the other files

Your FinSight folder should now contain:
```
FinSight/
├── fetcher.py
├── app.py
├── database.py
├── scheduler.py
├── cloud_sync.py      ← new file
├── .env
├── SETUP_GUIDE.md
└── finsight.db        (created after first run)
```

✅ Step 4 done when cloud_sync.py is in your FinSight folder.

---

## STEP 5 — Test the connection
**Time needed: 2 minutes**

1. Open your terminal / command prompt
2. Navigate to your FinSight folder:

   **Windows:**
   ```
   cd Documents\FinSight
   ```

   **Mac:**
   ```
   cd Documents/FinSight
   ```

3. Type this and press Enter:
   ```
   python cloud_sync.py
   ```

**What you should see if everything is working:**
```
📊 FinSight — Google Drive Sync Test
=============================================
✅ Connected: /Users/YourName/Google Drive/My Drive/FinSight
   Reports: 0 | Backups: 0
   Wealth CSV: False | Alert log: False

✅ Sync will run automatically after each daily report.
```

Reports showing 0 is completely normal — you have not run a daily report yet.
The important thing is it says **Connected** and shows your Google Drive path.

**What you should see if something is wrong:**
```
❌ Google Drive not detected
Fix: go to google.com/drive/download — install and sign in.
```

If you see this, go back to Step 1 and make sure Google Drive desktop is
installed and you are signed in. Then try Step 5 again.

✅ Step 5 done when you see "Connected" with your Google Drive path.

---

## STEP 6 — Wire sync into the daily scheduler
**Time needed: 3 minutes**

Open `scheduler.py` in Notepad or TextEdit.

Find this section near the top of the file:
```python
from fetcher  import (build_daily_report, send_email, send_slack,
                      format_morning_email, APP_NAME)
from database import (init_db, save_quotes, ...)
```

Add this line right after those import lines:
```python
from cloud_sync import run_full_sync
```

Then find this section near the bottom of the file (inside the `run()` function):
```python
    log.info(f"FinSight daily run complete ✅")
```

Add these two lines BEFORE that final log line:
```python
    log.info("Syncing to Google Drive...")
    sync_results = run_full_sync(report)
    log.info(f"Google Drive sync: {sync_results.get('report',{}).get('status','—')}")
```

Save the file.

✅ Step 6 done when the two additions are saved in scheduler.py.

---

## STEP 7 — Run a test sync
**Time needed: 5 minutes**

This runs the full daily report AND syncs everything to Google Drive.

In your terminal, type:
```
python scheduler.py
```

This will take 3–5 minutes to complete. You will see output scrolling.

**When it finishes, open Google Drive on your laptop:**
- Go to: Google Drive → My Drive → FinSight → reports
- You should see a file called `finsight_report_YYYYMMDD.json`

**Also check:**
- `briefs/` folder → `morning_briefs_archive.txt` should exist
- `backups/` folder → `finsight_backup_YYYYMMDD.db` should exist
- `snapshots/` folder → `wealth_history.csv` should exist

✅ Step 7 done when you can see files in your Google Drive FinSight folder.

---

## STEP 8 — View your wealth history in Google Sheets
**Time needed: 2 minutes**

This is one of the best features — your wealth data automatically becomes
a Google Sheet you can view on any device.

1. Open Google Drive on your browser: **https://drive.google.com**
2. Go to: FinSight → snapshots → wealth_history.csv
3. Right-click the file → Open with → Google Sheets
4. You will see your daily wealth data in a spreadsheet
5. Click Insert → Chart to create a graph of your portfolio over time

After this, every morning when FinSight runs, a new row is added automatically.
Your Google Sheet updates itself — no action needed from you.

✅ Step 8 done when you can see the CSV open in Google Sheets.

---

## What happens every morning from now on

```
8:00 AM — FinSight runs automatically (Task Scheduler / cron)
   ↓
Fetches all market data (India, Canada, US)
   ↓
Generates AI morning brief and portfolio score
   ↓
Sends email to your Gmail
   ↓
Saves everything to local SQLite database
   ↓
Copies everything to Google Drive automatically
   ↓
You wake up, check your email, open Google Drive on phone
```

---

## Accessing FinSight data from your phone

Once Google Drive is synced, you can access everything from your phone
without needing the ngrok tunnel:

1. Install the **Google Drive app** on your phone (free)
2. Sign in with the same Google account
3. Go to FinSight → briefs → morning_briefs_archive.txt
   → Read your morning brief from your phone
4. Go to FinSight → snapshots → wealth_history.csv
   → Tap to open in Google Sheets app
   → See your portfolio chart on your phone

For the full live app (with charts and AI chat), you still need the ngrok
tunnel — but for reading reports and history, Google Drive covers everything.

---

## Security reminder

| File | Syncs to Google Drive? |
|---|---|
| Daily JSON reports | ✅ Yes |
| Morning briefs | ✅ Yes |
| Database backup | ✅ Yes |
| Wealth CSV | ✅ Yes |
| Alert history | ✅ Yes |
| .env (API keys) | ❌ Never — stays on laptop only |
| Live finsight.db | ❌ Never — only backup copy syncs |
| Python source files | ❌ No — stays on laptop |

Your API keys and passwords never leave your laptop. Only data and reports
go to Google Drive.

---

## Quick fixes

| Problem | Fix |
|---|---|
| "Google Drive not detected" | Install desktop app, sign in, try again |
| Files not appearing in Google Drive | Wait 2 minutes for sync — check internet connection |
| Path error in .env | Copy path exactly from File Explorer / Finder address bar |
| wealth_history.csv not updating | Check scheduler.py has the run_full_sync lines added |
| Google Drive full | Free tier is 15GB — FinSight uses less than 100MB per year |

---

*FinSight — See beyond the numbers.*
*Data is informational only. Not financial advice.*
