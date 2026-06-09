#!/usr/bin/env bash
# ============================================================
#  AgentHarness v3 — Full Install Script (macOS / Linux)
#  Run from repo root:
#      bash .agents/agentharness/app/v3/install.sh
#
#  What it does:
#    1. Detects Python 3.10+ (python3 / python)
#    2. Checks tkinter availability + guides OS-specific install
#    3. Creates .venv virtual environment at repo root
#    4. Upgrades pip, wheel, setuptools
#    5. Installs all required packages from requirements.txt
#    6. Verifies every critical import
#    7. Creates/updates .agents/.env interactively
#    8. Creates .agents/data/ directory structure
#    9. Writes start.sh convenience launcher
#   10. Prints final health report
# ============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../../.." && pwd)"
VENV_DIR="$REPO_ROOT/.venv"
ENV_FILE="$REPO_ROOT/.agents/.env"
DATA_DIR="$REPO_ROOT/.agents/data"
APP_SCRIPT="$SCRIPT_DIR/main_m365.py"
REQ_FILE="$SCRIPT_DIR/requirements.txt"

cd "$REPO_ROOT"

# ── Colours ──────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; GRAY='\033[0;37m'; RESET='\033[0m'; BOLD='\033[1m'

ok()   { echo -e "    ${GREEN}✅  $*${RESET}"; }
warn() { echo -e "    ${YELLOW}⚠️   $*${RESET}"; }
fail() { echo -e "    ${RED}❌  $*${RESET}"; }
info() { echo -e "        ${GRAY}$*${RESET}"; }
step() { echo -e "\n${CYAN}[$1/10] $2${RESET}"; }

echo ""
echo -e "${CYAN}╔══════════════════════════════════════════════════════╗${RESET}"
echo -e "${CYAN}║       AgentHarness v3 — Full Installer               ║${RESET}"
echo -e "${CYAN}║       Smith Capital Portfolio Agent System            ║${RESET}"
echo -e "${CYAN}╚══════════════════════════════════════════════════════╝${RESET}"
echo ""
echo "  Repo root : $REPO_ROOT"
echo "  App script: $APP_SCRIPT"
echo ""

# ── STEP 1: Python check ─────────────────────────────────────
step 1 "Checking Python installation"

PYTHON_CMD=""
for cmd in python3 python python3.12 python3.11 python3.10; do
    if command -v "$cmd" &>/dev/null; then
        VER=$("$cmd" --version 2>&1 | grep -oP '\d+\.\d+' | head -1)
        MAJOR=$(echo "$VER" | cut -d. -f1)
        MINOR=$(echo "$VER" | cut -d. -f2)
        if [ "$MAJOR" -ge 3 ] && [ "$MINOR" -ge 10 ]; then
            PYTHON_CMD="$cmd"
            ok "Found Python $VER (using '$cmd')"
            break
        else
            warn "Found Python $VER — need 3.10+. Trying next..."
        fi
    fi
done

if [ -z "$PYTHON_CMD" ]; then
    fail "Python 3.10+ not found."
    info "macOS:   brew install python@3.11"
    info "Ubuntu:  sudo apt install python3.11"
    info "Or download from: https://python.org/downloads"
    exit 1
fi

# ── STEP 2: Check tkinter ─────────────────────────────────────
step 2 "Checking tkinter (GUI framework)"

if "$PYTHON_CMD" -c "import tkinter" 2>/dev/null; then
    TK_VER=$("$PYTHON_CMD" -c "import tkinter; print(tkinter.TkVersion)" 2>/dev/null)
    ok "tkinter $TK_VER — available"
else
    fail "tkinter not found."
    OS_TYPE=$(uname -s)
    if [ "$OS_TYPE" = "Darwin" ]; then
        PY_VER=$("$PYTHON_CMD" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
        info "macOS fix: brew install python-tk@${PY_VER}"
        info "Then re-run this script."
        echo ""
        read -rp "  Install python-tk now via Homebrew? [y/N] " BREW_INSTALL
        if [[ "$BREW_INSTALL" =~ ^[Yy]$ ]]; then
            brew install "python-tk@${PY_VER}" || warn "brew install failed — install manually"
        fi
    elif [ "$OS_TYPE" = "Linux" ]; then
        info "Ubuntu/Debian: sudo apt-get install -y python3-tk"
        info "Fedora/RHEL:   sudo dnf install python3-tkinter"
        echo ""
        read -rp "  Attempt 'sudo apt-get install -y python3-tk' now? [y/N] " APT_INSTALL
        if [[ "$APT_INSTALL" =~ ^[Yy]$ ]]; then
            sudo apt-get install -y python3-tk || warn "apt install failed — install manually"
        fi
    fi
    # Re-check
    if "$PYTHON_CMD" -c "import tkinter" 2>/dev/null; then
        ok "tkinter now available"
    else
        warn "tkinter still missing — GUI will NOT launch. Continuing anyway..."
    fi
fi

# ── STEP 3: Create virtual environment ───────────────────────
step 3 "Setting up virtual environment"

if [ -f "$VENV_DIR/bin/python" ] || [ -f "$VENV_DIR/bin/python3" ]; then
    ok "Existing .venv found"
else
    info "Creating .venv at $VENV_DIR..."
    "$PYTHON_CMD" -m venv "$VENV_DIR"
    ok "Virtual environment created"
fi

# Determine venv python/pip paths
if [ -f "$VENV_DIR/bin/python" ]; then
    VENV_PYTHON="$VENV_DIR/bin/python"
else
    VENV_PYTHON="$VENV_DIR/bin/python3"
fi
VENV_PIP="$VENV_DIR/bin/pip"

# ── STEP 4: Upgrade pip / wheel / setuptools ─────────────────
step 4 "Upgrading pip, wheel, setuptools"

"$VENV_PYTHON" -m pip install --upgrade pip wheel setuptools --quiet
ok "pip, wheel, setuptools up to date"

# ── STEP 5: Install all packages ─────────────────────────────
step 5 "Installing Python packages"

info "Installing from requirements.txt..."
echo ""

FAILED_PKGS=()
while IFS= read -r line; do
    # Skip comments and blanks
    [[ "$line" =~ ^#.*$ || -z "$line" ]] && continue
    # Skip NOTE lines
    [[ "$line" =~ ^#.*NOTE ]] && continue
    PKG_NAME=$(echo "$line" | cut -d'>' -f1 | cut -d'=' -f1 | cut -d';' -f1 | xargs)
    printf "        Installing %-35s" "$PKG_NAME..."
    if "$VENV_PIP" install "$line" --quiet 2>/dev/null; then
        echo -e "${GREEN}✅${RESET}"
    else
        echo -e "${RED}❌${RESET}"
        FAILED_PKGS+=("$PKG_NAME")
    fi
done < "$REQ_FILE"

if [ ${#FAILED_PKGS[@]} -gt 0 ]; then
    warn "Some packages failed: ${FAILED_PKGS[*]}"
    info "These may be optional or platform-specific."
else
    ok "All packages installed"
fi

# ── STEP 6: Verify imports ────────────────────────────────────
step 6 "Verifying critical imports"

VERIFY_RESULT=$("$VENV_PYTHON" - <<'PYEOF'
import sys
checks = [
    ('tkinter',          'GUI framework'),
    ('langgraph',        'Agent graph engine'),
    ('langchain',        'LLM chain framework'),
    ('langchain_openai', 'OpenAI connector'),
    ('openai',           'OpenAI SDK'),
    ('pydantic',         'Data validation'),
    ('requests',         'HTTP client'),
    ('dotenv',           'Env file loader'),
    ('sqlite3',          'SQLite DB (stdlib)'),
    ('sqlite_utils',     'SQLite utilities'),
    ('threading',        'Threading (stdlib)'),
    ('tkinter.ttk',      'ttk widgets'),
    ('tkinter.font',     'Tk fonts'),
    ('tkinter.scrolledtext', 'ScrolledText'),
    ('json',             'JSON (stdlib)'),
    ('pathlib',          'Path utilities'),
    ('uuid',             'UUID (stdlib)'),
    ('datetime',         'Datetime (stdlib)'),
    ('re',               'Regex (stdlib)'),
    ('ast',              'AST parser (stdlib)'),
    ('urllib.request',   'HTTP urllib (stdlib)'),
]
fails = 0
for mod, label in checks:
    try:
        __import__(mod)
        print(f'  OK  {mod:<28} {label}')
    except ImportError as e:
        print(f'  FAIL {mod:<28} {label} -- {e}')
        fails += 1
sys.exit(fails)
PYEOF
)
VERIFY_EXIT=$?

echo "$VERIFY_RESULT" | while IFS= read -r line; do
    if [[ "$line" == *"  OK  "* ]]; then
        echo -e "    ${GREEN}✅${RESET} ${line#*OK  }"
    elif [[ "$line" == *"  FAIL"* ]]; then
        echo -e "    ${RED}❌${RESET} ${line#*FAIL }"
    fi
done

if [ $VERIFY_EXIT -eq 0 ]; then
    ok "All critical imports verified"
else
    warn "$VERIFY_EXIT import(s) failed — see above"
fi

# ── STEP 7: Create/update .agents/.env ───────────────────────
step 7 "Environment configuration (.agents/.env)"

mkdir -p "$(dirname "$ENV_FILE")"

declare -A EXISTING_ENV
if [ -f "$ENV_FILE" ]; then
    while IFS='=' read -r key val; do
        [[ "$key" =~ ^#.*$ || -z "$key" ]] && continue
        EXISTING_ENV["$key"]="$val"
    done < "$ENV_FILE"
    ok "Existing .env loaded (${#EXISTING_ENV[@]} keys)"
fi

set_env_key() {
    local KEY="$1" DESC="$2" REQUIRED="$3"
    if [ -n "${EXISTING_ENV[$KEY]}" ]; then
        ok "$KEY already set"
        return
    fi
    if [ "$REQUIRED" = "required" ]; then
        warn "$KEY not set"
    else
        info "$KEY not set (optional)"
    fi
    info "  $DESC"
    read -rp "  Enter $KEY (blank to skip): " VAL
    if [ -n "$VAL" ]; then
        echo "${KEY}=${VAL}" >> "$ENV_FILE"
        ok "$KEY saved to .env"
    else
        warn "Skipped — add manually to .agents/.env later"
    fi
}

set_env_key "OPENAI_API_KEY"    "OpenAI API key (sk-...) — required for AgentMajesty LLM chat" "required"
set_env_key "GITHUB_PAT"        "GitHub Personal Access Token — for code push/pull" "required"
set_env_key "ANTHROPIC_API_KEY" "Anthropic API key — optional, for Claude provider" "optional"

# ── STEP 8: Data directory structure ─────────────────────────
step 8 "Creating data directories"

for dir in "$DATA_DIR" "$DATA_DIR/logs" "$DATA_DIR/exports"; do
    if [ ! -d "$dir" ]; then
        mkdir -p "$dir"
        ok "Created: ${dir#$REPO_ROOT/}"
    else
        info "Exists : ${dir#$REPO_ROOT/}"
    fi
done

[ ! -f "$DATA_DIR/todos.json" ] && echo "[]" > "$DATA_DIR/todos.json" && ok "Created: .agents/data/todos.json"
[ ! -f "$DATA_DIR/scheduled_runs.json" ] && echo "[]" > "$DATA_DIR/scheduled_runs.json" && ok "Created: .agents/data/scheduled_runs.json"

# ── STEP 9: Write launch script ──────────────────────────────
step 9 "Writing launch scripts"

LAUNCH_SH="$SCRIPT_DIR/start.sh"
cat > "$LAUNCH_SH" << LAUNCHER
#!/usr/bin/env bash
# AgentHarness v3 — Launch script (auto-generated by install.sh)
SCRIPT_DIR="\$(cd "\$(dirname "\${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="\$(cd "\$SCRIPT_DIR/../../../.." && pwd)"
VENV_PYTHON="\$REPO_ROOT/.venv/bin/python"
APP_SCRIPT="\$SCRIPT_DIR/main_m365.py"
ENV_FILE="\$REPO_ROOT/.agents/.env"
cd "\$REPO_ROOT"
echo ""
echo "  ⬡  AgentHarness v3 — Starting..."
if [ ! -f "\$VENV_PYTHON" ]; then
    echo "  ❌ Virtual environment not found. Run install.sh first."
    exit 1
fi
if [ -f "\$ENV_FILE" ]; then
    set -a; source "\$ENV_FILE"; set +a
    echo "  ✅  .env loaded"
fi
echo "  🚀  Launching main_m365.py..."
echo ""
"\$VENV_PYTHON" "\$APP_SCRIPT"
LAUNCHER

chmod +x "$LAUNCH_SH"
ok "Written: .agents/agentharness/app/v3/start.sh"

# Root-level launcher
ROOT_LAUNCH="$REPO_ROOT/launch_v3.sh"
cat > "$ROOT_LAUNCH" << ROOT
#!/usr/bin/env bash
bash "\$(dirname "\$0")/.agents/agentharness/app/v3/start.sh"
ROOT
chmod +x "$ROOT_LAUNCH"
ok "Written: launch_v3.sh  (root-level convenience launcher)"

# ── STEP 10: Final health report ─────────────────────────────
step 10 "Final health report"

echo ""
echo -e "${CYAN}  ┌────────────────────────────────────────────────────┐${RESET}"
echo -e "${CYAN}  │         AgentHarness v3 — Install Report           │${RESET}"
echo -e "${CYAN}  └────────────────────────────────────────────────────┘${RESET}"
echo ""

REPORT_OK=true

check_item() {
    local LABEL="$1" COND="$2"
    if eval "$COND"; then
        echo -e "  ${GREEN}✅${RESET}  $LABEL"
    else
        echo -e "  ${RED}❌${RESET}  $LABEL"
        REPORT_OK=false
    fi
}

check_item "Python 3.10+"               "[ -n '$PYTHON_CMD' ]"
check_item "Virtual environment (.venv)" "[ -f '$VENV_PYTHON' ]"
check_item "App script (main_m365.py)"  "[ -f '$APP_SCRIPT' ]"
check_item ".agents/.env file"          "[ -f '$ENV_FILE' ]"
check_item ".agents/data/todos.json"    "[ -f '$DATA_DIR/todos.json' ]"
check_item "All imports verified"       "[ $VERIFY_EXIT -eq 0 ]"
check_item "Launch script written"      "[ -f '$LAUNCH_SH' ]"

echo ""
if [ "$REPORT_OK" = true ]; then
    echo -e "  ${GREEN}${BOLD}✅  Installation complete — everything looks good!${RESET}"
    echo ""
    echo -e "  ${CYAN}▶  To launch AgentHarness v3, run:${RESET}"
    echo -e "       ${BOLD}./launch_v3.sh${RESET}"
    echo -e "     or:"
    echo -e "       ${GRAY}bash .agents/agentharness/app/v3/start.sh${RESET}"
else
    echo -e "  ${YELLOW}${BOLD}⚠️   Installation completed with warnings.${RESET}"
    echo -e "  ${GRAY}Review the ❌ items above and re-run if needed.${RESET}"
    echo ""
    echo -e "  ${CYAN}▶  You can still try launching:${RESET}"
    echo -e "       ${BOLD}./launch_v3.sh${RESET}"
fi
echo ""
