# 📊 FinSight — Solo Setup Guide
## See beyond the numbers.
### Written for: You — working alone, no technical help needed

---

> **How this guide works:**
> Each step tells you exactly what to type, what you should see, and what "done" looks like.
> Never move to the next step until the current one is confirmed working.
> Estimated total time: **2.5 to 3 hours** with breaks.

---

## BEFORE YOU START — What you need ready

- [ ] Your laptop (Windows or Mac — both work)
- [ ] A Gmail account you can use for alerts
- [ ] 3 browser tabs ready to open (links provided in each step)
- [ ] A coffee ☕

---

## PHASE 1 — Install the foundations
### ⏱️ Allow 30 minutes

---

### STEP 1 — Install Python
**What it is:** Python is the language FinSight is written in. Think of it as the engine.

1. Open your browser. Go to: **https://www.python.org/downloads/**
2. Click the big yellow "Download Python 3.x.x" button
3. Open the downloaded file
4. **IMPORTANT:** On the first screen you see, tick the box that says **"Add Python to PATH"**
   - This is the most common mistake people make — don't skip it
5. Click "Install Now"
6. Wait for it to finish (2–3 minutes)

**How to confirm it worked:**
- Windows: Press the Windows key, type `cmd`, press Enter
- Mac: Press Cmd+Space, type `terminal`, press Enter
- In the black window that opens, type exactly: `python --version`
- Press Enter
- You should see something like: `Python 3.11.5`
- If you see that — ✅ Step 1 done. Close this window.
- If you see an error — try restarting your laptop and trying again

---

### STEP 2 — Create your FinSight folder
**What it is:** A dedicated home for all FinSight files.

**Windows:**
1. Press Windows key + E (opens File Explorer)
2. Go to your Documents folder
3. Right-click → New → Folder
4. Name it: `FinSight`

**Mac:**
1. Open Finder
2. Go to Documents
3. Right-click → New Folder
4. Name it: `FinSight`

**Next:** Move all 5 FinSight files into this folder:
- `fetcher.py`
- `app.py`
- `database.py`
- `scheduler.py`
- `.env.template`

✅ Step 2 done when all 5 files are in the FinSight folder.

---

### STEP 3 — Rename and fill your .env file
**What it is:** Your private configuration file — holds all your API keys and passwords.

1. Find `.env.template` in your FinSight folder
2. Right-click it → Rename
3. Change the name to exactly: `.env` (remove the word "template")
   - Windows may warn you about changing the file extension — click Yes
   - Mac: it may hide the dot — that's fine, just name it `.env`
4. Right-click `.env` → Open with → Notepad (Windows) or TextEdit (Mac)

You will see something like:
```
FINSIGHT_PASSWORD=finsight2024
ANTHROPIC_API_KEY=your_anthropic_key_here
...
```

**Change this line first:**
```
FINSIGHT_PASSWORD=finsight2024
```
Replace `finsight2024` with a password only you know. Keep it simple but not obvious.

**Leave all other lines for now** — you will fill them in Step 5.

Save the file (Ctrl+S on Windows, Cmd+S on Mac).

✅ Step 3 done when .env is saved with your password.

---

### STEP 4 — Install FinSight libraries
**What it is:** Python add-ons that FinSight uses to pull market data.

1. Open your terminal / command prompt again (same as Step 1)
2. Navigate to your FinSight folder by typing:

**Windows:**
```
cd Documents\FinSight
```

**Mac:**
```
cd Documents/FinSight
```

3. Press Enter
4. Now type this entire line and press Enter:
```
pip install yfinance alpha_vantage finnhub-python mftool pandas requests python-dotenv streamlit plotly anthropic
```

5. Wait — this takes 3–5 minutes. You will see lots of text scrolling. That is normal.
6. When it stops and you see your cursor again — it is done.

**How to confirm it worked:**
Type: `python -c "import yfinance; print('ok')"` and press Enter.
You should see: `ok`

✅ Step 4 done when you see `ok`.

---

## PHASE 2 — Get your free API keys
### ⏱️ Allow 20 minutes

---

### STEP 5 — Register for free API keys
You need 4 keys. Each takes about 3 minutes to register.

**Key 1 — Alpha Vantage (for RSI and MACD signals)**
1. Go to: **https://www.alphavantage.co/support/#api-key**
2. Enter your name and email
3. Click "Get Free API Key"
4. Copy the key they show you (looks like: `ABC123XYZ456`)
5. Open your `.env` file
6. Replace `your_alpha_vantage_key_here` with your copied key
7. Save the file

**Key 2 — Finnhub (for news and sentiment)**
1. Go to: **https://finnhub.io/register**
2. Sign up with your email
3. After login, your API key is shown on the Dashboard
4. Copy it and paste into `.env` replacing `your_finnhub_key_here`
5. Save the file

**Key 3 — FRED (for US real estate macro data)**
1. Go to: **https://fred.stlouisfed.org/docs/api/api_key.html**
2. Click "Request API Key" — you need a free account
3. Fill in the form — takes 2 minutes
4. They email you a key
5. Paste it into `.env` replacing `your_fred_key_here`
6. Save the file

**Key 4 — Anthropic (for AI chat and morning brief)**
1. Go to: **https://console.anthropic.com**
2. Sign up or log in
3. Go to: API Keys → Create Key
4. Copy it and paste into `.env` replacing `your_anthropic_key_here`
5. Save the file

**Note:** Anthropic API costs a small amount (~$2–5/month for personal use). You can skip this for now and add it later — FinSight works without it, just without the AI chat features.

✅ Step 5 done when all 4 keys are saved in your `.env` file.

---

### STEP 6 — Set up Gmail alerts
**What it is:** Lets FinSight email you a morning brief automatically.

1. Log into your Gmail account
2. Go to: **https://myaccount.google.com/security**
3. Make sure "2-Step Verification" is ON (you need this first)
4. Search for "App Passwords" on that same page
5. Click App Passwords
6. Under "Select app" choose "Mail"
7. Under "Select device" choose "Windows Computer" (or Mac)
8. Click Generate
9. Copy the 16-character password they show (e.g. `abcd efgh ijkl mnop`)
10. In your `.env` file, replace:
    - `your.email@gmail.com` with your actual Gmail address (appears twice)
    - `xxxx_xxxx_xxxx_xxxx` with the 16-char password (remove spaces)
11. Save the `.env` file

✅ Step 6 done when Gmail details are saved in `.env`.

---

## PHASE 3 — Test FinSight
### ⏱️ Allow 20 minutes

---

### STEP 7 — First test run
**What it is:** Making sure the data fetching works before launching the app.

1. Open your terminal and make sure you are in the FinSight folder (see Step 4)
2. Type:
```
python fetcher.py quick
```
3. Press Enter

**What you should see:**
```
========================================
  FinSight — Quick Scan
========================================

IN_INDICES:
  ^NSEI                     24,351.00  +0.42%
  ^BSESN                    80,423.00  +0.38%

US_INDICES:
  ^GSPC                      5,892.00  +0.21%
  ^IXIC                     18,234.00  +0.15%
```

If you see real numbers — ✅ FinSight is fetching live data.

If you see errors:
- `ModuleNotFoundError` → Go back to Step 4 and run the pip install again
- `No data` → Normal for some tickers, not a problem

---

### STEP 8 — Initialise the database
**What it is:** Creates the local database where FinSight stores all your data.

1. In your terminal type:
```
python database.py
```
2. Press Enter

**What you should see:**
```
✅ FinSight database initialised at /path/to/finsight.db
```

A new file called `finsight.db` will appear in your FinSight folder.

✅ Step 8 done when you see the success message.

---

### STEP 9 — Launch FinSight app
**What it is:** Starting your personal wealth dashboard.

1. In your terminal type:
```
streamlit run app.py
```
2. Press Enter

**What you should see:**
```
  You can now view your Streamlit app in your browser.
  Local URL: http://localhost:8501
  Network URL: http://192.168.x.x:8501
```

3. Your browser will open automatically to `http://localhost:8501`
4. You should see the FinSight login screen
5. Enter the password you set in Step 3

**If the browser does not open automatically:**
Open your browser and go to: `http://localhost:8501`

✅ Step 9 done when you can log into the FinSight app.

---

## PHASE 4 — Phone access
### ⏱️ Allow 20 minutes

---

### STEP 10 — Install ngrok (phone tunnel)
**What it is:** Creates a secure web address so you can open FinSight on your phone.

1. Go to: **https://ngrok.com/download**
2. Download the version for your system (Windows or Mac)
3. Sign up for a free ngrok account at: **https://dashboard.ngrok.com/signup**
4. After signing up, go to: **https://dashboard.ngrok.com/get-started/your-authtoken**
5. Copy your authtoken

**Windows:**
- Unzip the downloaded file
- Move `ngrok.exe` to your FinSight folder

**Mac:**
- Unzip the downloaded file
- Open Terminal and type: `sudo mv ngrok /usr/local/bin`

6. In your terminal type (paste your actual token):
```
ngrok config add-authtoken YOUR_TOKEN_HERE
```
7. Press Enter — you should see: `Authtoken saved`

✅ Step 10 done when authtoken is saved.

---

### STEP 11 — Open FinSight on your phone
**What it is:** Making your laptop's app accessible from anywhere on your phone.

You need TWO terminal windows open at the same time:

**Terminal Window 1** (keep this running):
```
streamlit run app.py
```

**Terminal Window 2** (open a new terminal):
```
ngrok http 8501
```

In Terminal 2 you will see something like:
```
Forwarding    https://a1b2c3d4.ngrok-free.app → http://localhost:8501
```

Copy that `https://...ngrok-free.app` URL.

**On your phone:**
1. Open your phone browser
2. Paste the URL
3. You should see the FinSight login screen
4. Enter your password

**Add to home screen (makes it feel like an app):**
- iPhone: Tap Share → Add to Home Screen
- Android: Tap the 3 dots menu → Add to Home Screen

**Important:** The ngrok URL changes every time you restart it (free tier).
Keep the URL saved in your notes when you need it.

✅ Step 11 done when FinSight opens on your phone.

---

## PHASE 5 — Daily automation
### ⏱️ Allow 15 minutes

---

### STEP 12 — Schedule daily runs

**WINDOWS — Task Scheduler:**
1. Press Windows key, search "Task Scheduler", open it
2. Click "Create Basic Task" on the right
3. Name: `FinSight Daily`
4. Description: `FinSight morning market report`
5. Trigger: Daily
6. Start time: `8:00 AM`
7. Action: "Start a program"
8. Program/script: `python`
9. Add arguments: (paste your full path)
   `C:\Users\YourName\Documents\FinSight\scheduler.py`
10. Click Finish

**MAC — cron:**
1. Open Terminal
2. Type: `crontab -e`
3. Press `i` to enter insert mode
4. Type this line (replace the path with your actual path):
   `0 8 * * 1-5 python3 /Users/YourName/Documents/FinSight/scheduler.py`
5. Press Escape, then type `:wq` and press Enter

**Test it manually first:**
In your terminal:
```
python scheduler.py
```
This should run the full report, save to database, and send your morning email.

✅ Step 12 done when the test run completes and you receive the email.

---

## PHASE 6 — Security lock
### ⏱️ Allow 10 minutes

---

### STEP 13 — Protect your .env file
**What it is:** Making sure your API keys never accidentally get shared.

Create a file called `.gitignore` in your FinSight folder.
Open Notepad (Windows) or TextEdit (Mac), paste this:

```
.env
finsight.db
reports/
__pycache__/
*.pyc
finsight.log
```

Save it as `.gitignore` (not `.gitignore.txt`).

This ensures if you ever use GitHub, your keys and database are never uploaded.

✅ Step 13 done when `.gitignore` file exists in your FinSight folder.

---

## YOU ARE DONE 🎉

---

## What FinSight can now do for you

| Feature | How to use it |
|---|---|
| Live market data | Open app → any market tab → click Fetch |
| AI morning brief | Runs automatically at 8 AM, lands in your email |
| AI portfolio score | Dashboard tab — shows health score + plain English verdict |
| Cross-market alerts | Alerts tab → Run correlation check |
| Ask AI anything | Ask AI tab — type any question about your portfolio |
| Indian MF NAVs | Mutual Funds tab → Fetch Indian MF NAVs |
| Real estate pockets | Real Estate tab → Pocket Analysis |
| Commodities | Commodities tab → Fetch all |
| Options chain | F&O tab → Enter any ticker |
| Phone access | Open your saved ngrok URL on phone |

---

## Daily routine suggestion

| Time | What happens |
|---|---|
| 8:00 AM EST | FinSight runs automatically, saves data, sends email |
| 8:05 AM | You read the morning brief in your email |
| Evening | Open app on phone, check alerts, ask AI any questions |
| Weekend | Review wealth snapshot, check real estate pockets |

---

## Quick fixes for common problems

| Problem | Fix |
|---|---|
| `python not found` | Reinstall Python — tick "Add to PATH" |
| `ModuleNotFoundError` | Run `pip install [module name]` |
| `No data returned` | Alpha Vantage rate limit — wait 60 seconds |
| App not opening on phone | Restart ngrok, copy new URL |
| Login not working | Check FINSIGHT_PASSWORD in .env |
| Email not sending | Check Gmail App Password in .env |
| AI chat not working | Check ANTHROPIC_API_KEY in .env |

---

## When you are ready for Zerodha (Indian live data upgrade)

1. Open account at: https://zerodha.com/open-account
2. Processing takes 1–3 business days
3. Once active, apply for API access at: https://kite.trade
4. Add keys to `.env` (ZERODHA_API_KEY, ZERODHA_API_SECRET)
5. The code in `fetcher.py` is already ready — just uncomment 8 lines

---

*FinSight — See beyond the numbers.*
*Built for personal use. Data is informational only. Not financial advice.*
