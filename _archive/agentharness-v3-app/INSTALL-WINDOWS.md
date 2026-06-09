# AgentHarness v3 — Windows Install Guide
## "Scripts are disabled on this system" Fix

Windows blocks PowerShell scripts by default (ExecutionPolicy = Restricted).
You have **3 options** — pick whichever is easiest.

---

## Option 1 — Run the installer from CMD (easiest, no policy change needed)

Open **Command Prompt** (not PowerShell) and paste this single line:

```cmd
powershell.exe -ExecutionPolicy Bypass -File ".agents\agentharness\app\v3\install.ps1"
```

The `-ExecutionPolicy Bypass` flag is per-process only — it doesn't change your system settings and doesn't require admin.

---

## Option 2 — Right-click the PS1 file

1. Open File Explorer → navigate to `.agents\agentharness\app\v3\`
2. Right-click `install.ps1`
3. Select **"Run with PowerShell"**

If that's still blocked, hold **Shift** while right-clicking and choose **"Open PowerShell window here"**, then type:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\install.ps1
```

---

## Option 3 — One-time policy unlock (safe, user-scope only)

Open **PowerShell as your normal user** (no admin needed) and run:

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

Then run the installer normally:

```powershell
.\.agents\agentharness\app\v3\install.ps1
```

`RemoteSigned` only blocks scripts downloaded from the internet without a signature. Scripts you write locally (like these) run fine.

---

## After install — Launch the app

Once install.ps1 completes, it creates `launch_v3.ps1` in the repo root.

**To launch AgentHarness v3:**

From CMD:
```cmd
powershell.exe -ExecutionPolicy Bypass -File "launch_v3.ps1"
```

From PowerShell (after Option 2 or 3 above):
```powershell
.\launch_v3.ps1
```

Or do it the manual way (always works, no policy needed):
```cmd
.venv\Scripts\python.exe .agents\agentharness\app\v3\main_m365.py
```

---

## Manual install (if you want to skip the PS1 entirely)

Open **Command Prompt** in the repo root and run these one at a time:

```cmd
:: 1. Create virtual environment
python -m venv .venv

:: 2. Upgrade pip
.venv\Scripts\python.exe -m pip install --upgrade pip wheel setuptools

:: 3. Install all packages
.venv\Scripts\pip.exe install langgraph langchain langchain-core langchain-openai langchain-community openai pydantic sqlite-utils requests python-dotenv python-dateutil markdown

:: 4. Create data folder
mkdir .agents\data
mkdir .agents\data\logs
echo [] > .agents\data\todos.json
echo [] > .agents\data\scheduled_runs.json

:: 5. Launch
.venv\Scripts\python.exe .agents\agentharness\app\v3\main_m365.py
```

That's it — no scripts, no policy, no PowerShell.

---

## Verify tkinter (required for the GUI)

```cmd
.venv\Scripts\python.exe -c "import tkinter; print('tkinter OK', tkinter.TkVersion)"
```

If you see an error, your Python is missing tkinter.
**Fix:** Uninstall Python, re-download from **https://python.org** (not the Microsoft Store),
and during install check **"tcl/tk and IDLE"** under Optional Features.
