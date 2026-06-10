#!/usr/bin/env python3
"""
run_tests.py — ArchonHub test harness master runner.

Usage:
    python run_tests.py              # run all suites
    python run_tests.py db           # db layer only
    python run_tests.py server       # server API only
    python run_tests.py markets      # paper trading only
    python run_tests.py oauth        # OAuth connector only
    python run_tests.py ui           # Tkinter UI surfaces only

Options:
    --fast     skip server + ui (unit tests only)
    --verbose  show individual test output
"""
from __future__ import annotations

import os
import sys
import subprocess
import time
import argparse
from pathlib import Path

HERE    = Path(__file__).parent
APP_DIR = HERE.parent

SUITES = {
    "db":      HERE / "test_hub_db.py",
    "markets": HERE / "test_markets.py",
    "oauth":   HERE / "test_oauth_connector.py",
    "server":  HERE / "test_hub_server.py",
    "ui":      HERE / "test_ui_surfaces.py",
}

GREEN  = ""
RED    = ""
YELLOW = ""
CYAN   = ""
BOLD   = ""
RESET  = ""


def banner(text: str, char: str = "-", width: int = 60) -> str:
    pad = (width - len(text) - 2) // 2
    return f"{char * pad} {text} {char * (width - pad - len(text) - 2)}"


def run_suite(name: str, path: Path, verbose: bool) -> dict:
    """Run a single pytest suite, return results dict."""
    print(f"\n{CYAN}{banner(name.upper())}{RESET}")
    t0 = time.time()

    cmd = [
        sys.executable, "-m", "pytest",
        str(path),
        "--tb=short",
        "-q" if not verbose else "-v",
        "--no-header",
        f"--rootdir={APP_DIR}",
    ]
    env = os.environ.copy()
    env["PYTHONPATH"] = str(APP_DIR)
    env["PYTHONDONTWRITEBYTECODE"] = "1"

    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    elapsed = time.time() - t0

    if result.returncode == 0:
        status = "PASSED"
        ok = True
    elif result.returncode == 5:
        status = "NO TESTS"
        ok = True
    else:
        status = "FAILED"
        ok = False

    output = (result.stdout or "") + (result.stderr or "")
    lines = [l for l in output.splitlines() if l.strip()]

    if verbose:
        for line in lines:
            print(f"  {line}")
    else:
        for line in lines[-10:]:
            print(f"  {line}")

    print(f"  [{status}]  ({elapsed:.1f}s)")

    return {
        "name":    name,
        "passed":  ok,
        "rc":      result.returncode,
        "elapsed": elapsed,
        "output":  output,
    }


def main():
    parser = argparse.ArgumentParser(description="ArchonHub test harness")
    parser.add_argument("suites", nargs="*", help="Suite names to run (default: all)")
    parser.add_argument("--fast", action="store_true", help="Skip server + ui tests")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    selected = args.suites or list(SUITES.keys())
    if args.fast:
        selected = [s for s in selected if s not in ("server", "ui")]

    # Validate
    unknown = [s for s in selected if s not in SUITES]
    if unknown:
        print(f"{RED}Unknown suite(s): {unknown}. Available: {list(SUITES)}{RESET}")
        sys.exit(1)

    print(f"\n{'=' * 60}")
    print(f"  ArchonHub Test Harness  v1.0")
    print(f"  Suites: {', '.join(selected)}")
    print(f"{'=' * 60}")

    results = []
    total_start = time.time()

    for name in selected:
        path = SUITES[name]
        if not path.exists():
            print(f"{YELLOW}⚠️  {name}: file not found ({path}){RESET}")
            results.append({"name": name, "passed": False, "rc": -1, "elapsed": 0, "output": ""})
            continue
        results.append(run_suite(name, path, args.verbose))

    # ── Summary ──────────────────────────────────────────────────────────────
    total_elapsed = time.time() - total_start
    passed  = [r for r in results if r["passed"]]
    failed  = [r for r in results if not r["passed"]]

    print(f"\n{'=' * 60}")
    print(f"  RESULTS  ({total_elapsed:.1f}s total)")
    print(f"{'=' * 60}")

    for r in results:
        icon  = "PASS" if r["passed"] else "FAIL"
        print(f"  [{icon}] {r['name']:<20} {r['elapsed']:.1f}s")

    print(f"\n  {GREEN}{len(passed)} passed{RESET}  "
          f"{RED}{len(failed)} failed{RESET}  "
          f"of {len(results)} suites\n")

    if failed:
        print(f"{RED}Failed suites: {[r['name'] for r in failed]}{RESET}")
        if not args.verbose:
            print("Re-run with --verbose for full output.")
        sys.exit(1)
    else:
        print(f"{GREEN}{BOLD}All suites passed! 🎉{RESET}\n")
        sys.exit(0)


if __name__ == "__main__":
    main()
