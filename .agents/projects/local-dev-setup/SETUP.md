# AgentHarness — Local Setup Guide (Windows)
**Updated:** 2026-05-27

---

## The Problem
`pip` is not recognized on Windows because Python wasn't added to PATH during install,
or you need to use `pip3` / `py -m pip` instead.

---

## Fix 1 — Try these commands first (PowerShell)

```powershell
# Option A — use py launcher (most common on Windows)
py -m pip install -r requirements.txt

# Option B — use python directly
python -m pip install -r requirements.txt

# Option C — use pip3
pip3 install -r requirements.txt
```

---

## Fix 2 — If Python isn't installed or not on PATH

1. Download Python 3.11 from https://www.python.org/downloads/
2. During install — **CHECK "Add Python to PATH"** (critical step, easy to miss)
3. Close and reopen PowerShell
4. Run: `py -m pip install -r requirements.txt`

---

## Fix 3 — If you have Python but it's not on PATH

```powershell
# Find where Python is installed
where python
where py

# Or check these common locations:
# C:\Users\<you>\AppData\Local\Programs\Python\Python311\
# C:\Python311\

# Add to PATH permanently (run as Admin):
[System.Environment]::SetEnvironmentVariable(
  "Path",
  $env:Path + ";C:\Users\YOUR_USERNAME\AppData\Local\Programs\Python\Python311\Scripts",
  [System.EnvironmentVariableTarget]::User
)
# Then restart PowerShell
```

---

## Full Setup Sequence (Windows PowerShell)

```powershell
# 1. Clone the repo (if not already done)
git clone https://github.com/dpoly2/AgentHarness.git
cd AgentHarness

# 2. Create a virtual environment (recommended)
py -m venv .venv
.venv\Scripts\Activate.ps1

# 3. Install dependencies
py -m pip install -r .agents/agentharness/requirements.txt

# 4. Set your OpenAI key
$env:OPENAI_API_KEY = "sk-..."

# 5. Test run
cd .agents
py -c "
import sys
sys.path.append('.')
from agentharness.graphs.reflexion_loop import run_agent
result = run_agent(
    agent_id='grants-research-agent',
    project='xftc',
    task='Find 3 active grants for youth track programs in Texas under 501c3 nonprofits',
    environment='local'
)
print(result['output'])
print(f'Score: {result[\"score\"]:.2f}')
"
```

---

## If PowerShell blocks script execution

```powershell
# Run this once as Admin to allow scripts:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

## LangGraph Studio (Visual UI)

```powershell
# After installing dependencies:
py -m pip install langgraph-cli

# Launch Studio from the agentharness folder:
cd .agents\agentharness
py -m langgraph dev
# Opens at http://localhost:8123
```

---

## Quick Verify (run this to confirm everything works)

```powershell
cd .agents
py -c "
import sys; sys.path.append('.')
from agentharness.state.agent_state import default_state
from agentharness.adapters.local_adapter import LocalAdapter
from agentharness.graphs.reflexion_loop import build_reflexion_graph
adapter = LocalAdapter()
graph = build_reflexion_graph(adapter)
print('✅ AgentHarness ready — all graphs compiled')
"
```
