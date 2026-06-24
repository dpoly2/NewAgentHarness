"""
code_sandbox.py — Secure code execution sandbox for ArchonHub
=============================================================
Supports two isolation modes:
  1. Docker (production) — fully isolated container, no network, memory/CPU limits
  2. Subprocess (development) — restricted Python subprocess with timeout + resource limits

Usage:
    from code_sandbox import execute_code, SandboxResult

    result = execute_code(code="import pandas as pd; print(pd.__version__)", language="python")
    print(result.stdout)
"""

from __future__ import annotations

import base64
import json
import os
import platform
if platform.system() in ("Darwin", "Linux"):
    import resource
else:
    resource = None  # type: ignore[assignment]
import subprocess
import sys
import tempfile
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

HERE = Path(__file__).parent

# ── Config ────────────────────────────────────────────────────────────────────
SANDBOX_TIMEOUT_SECONDS = 30
SANDBOX_MAX_OUTPUT_BYTES = 64 * 1024   # 64 KB stdout cap
SANDBOX_MEMORY_MB = 512
DOCKER_IMAGE = "archonhub-sandbox:latest"
UPLOADS_DIR = HERE.parent.parent / "uploads"

# Packages available inside the sandbox
ALLOWED_IMPORTS = {
    "pandas", "numpy", "matplotlib", "matplotlib.pyplot", "seaborn",
    "scipy", "sklearn", "statsmodels", "json", "csv", "math", "datetime",
    "collections", "itertools", "functools", "re", "string", "textwrap",
    "decimal", "fractions", "statistics", "random", "base64",
    "typing", "dataclasses", "enum", "abc", "copy",
}

# Top-level imports blocked in user code (via AST scan)
BLOCKED_IMPORTS = {
    "os", "sys", "subprocess", "socket", "urllib", "http", "requests",
    "shutil", "ctypes", "multiprocessing", "threading", "importlib",
    "pkgutil", "imp", "zipfile", "tarfile", "gzip", "ftplib", "smtplib",
    "paramiko", "fabric", "pexpect",
    "io", "pathlib",  # can access arbitrary filesystem paths
}

# Blocked code patterns (string-level, before AST)
BLOCKED_PATTERNS = [
    "__import__(",
    "exec(",
    "eval(",
    "compile(",
    "globals()",
    "locals()",
    "open(",
    "getattr(",
    "builtins",
]


# ── Result model ──────────────────────────────────────────────────────────────

@dataclass
class SandboxResult:
    execution_id: str
    success: bool
    stdout: str
    stderr: str
    exit_code: int
    execution_time_ms: int
    generated_files: list[dict] = field(default_factory=list)  # [{name, content_b64, mime_type}]
    error: Optional[str] = None
    blocked_reason: Optional[str] = None
    mode: str = "subprocess"  # "docker" | "subprocess"


# ── Security scanner ─────────────────────────────────────────────────────────

def _scan_code(code: str) -> Optional[str]:
    """
    Return a reason string if code is blocked, else None.
    Uses AST analysis for import checks + string patterns for other risks.
    """
    # String-level checks first (fast)
    for pattern in BLOCKED_PATTERNS:
        if pattern in code:
            return f"Blocked pattern: '{pattern}'"

    if code.lower().count("while true") > 0 and "break" not in code.lower():
        return "Potential infinite loop (while True without break)"

    # AST-level import analysis
    import ast
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return None  # Let runtime report it

    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            if isinstance(node, ast.Import):
                names = [alias.name.split(".")[0] for alias in node.names]
            else:
                names = [node.module.split(".")[0]] if node.module else []
            for name in names:
                if name in BLOCKED_IMPORTS:
                    return f"Import of '{name}' is not allowed in sandbox"

    return None


def _extract_files(workdir: Path) -> list[dict]:
    """Collect any generated files (images, CSVs) from the work directory."""
    files = []
    for fpath in workdir.iterdir():
        if fpath.name.startswith("_") or fpath.suffix not in (".png", ".jpg", ".svg", ".csv", ".json", ".txt"):
            continue
        try:
            data = fpath.read_bytes()
            if len(data) > 5 * 1024 * 1024:  # skip files > 5MB
                continue
            mime = {
                ".png": "image/png",
                ".jpg": "image/jpeg",
                ".svg": "image/svg+xml",
                ".csv": "text/csv",
                ".json": "application/json",
                ".txt": "text/plain",
            }.get(fpath.suffix, "application/octet-stream")
            files.append({
                "name": fpath.name,
                "content_b64": base64.b64encode(data).decode(),
                "mime_type": mime,
                "size_bytes": len(data),
            })
        except Exception:
            pass
    return files


# ── Docker execution ──────────────────────────────────────────────────────────

def _ensure_docker_image() -> bool:
    """Build sandbox Docker image if not present. Returns True if available."""
    try:
        result = subprocess.run(
            ["docker", "image", "inspect", DOCKER_IMAGE],
            capture_output=True, timeout=10
        )
        if result.returncode == 0:
            return True
        # Build it
        dockerfile = _generate_dockerfile()
        with tempfile.TemporaryDirectory() as build_ctx:
            (Path(build_ctx) / "Dockerfile").write_text(dockerfile)
            build = subprocess.run(
                ["docker", "build", "-t", DOCKER_IMAGE, build_ctx],
                capture_output=True, timeout=120
            )
            return build.returncode == 0
    except Exception:
        return False


def _generate_dockerfile() -> str:
    return """FROM python:3.11-slim

RUN pip install --no-cache-dir \
    pandas==2.1.4 \
    numpy==1.26.2 \
    matplotlib==3.8.2 \
    seaborn==0.13.0 \
    scipy==1.11.4 \
    scikit-learn==1.3.2 \
    statsmodels==0.14.1

# No network access user
RUN useradd -m -u 1000 sandbox
USER sandbox
WORKDIR /workspace

ENTRYPOINT ["python3", "-u"]
"""


def _run_docker(code: str, exec_id: str, data_files: list[dict]) -> SandboxResult:
    """Execute code in Docker container with network isolation."""
    with tempfile.TemporaryDirectory() as workdir:
        wdir = Path(workdir)
        
        # Write code
        code_file = wdir / "code.py"
        code_file.write_text(_wrap_code(code))
        
        # Write any uploaded data files
        for df in data_files:
            try:
                safe_name = Path(df["name"]).name  # strip any directory traversal
                if not safe_name or safe_name.startswith("."):
                    continue
                content = base64.b64decode(df["content_b64"])
                (wdir / safe_name).write_bytes(content)
            except Exception:
                pass
        
        start = time.time()
        try:
            result = subprocess.run(
                [
                    "docker", "run",
                    "--rm",
                    "--network=none",
                    f"--memory={SANDBOX_MEMORY_MB}m",
                    "--memory-swap=-1",
                    "--cpus=0.5",
                    f"--volume={workdir}:/workspace",
                    "--user=1000",
                    DOCKER_IMAGE,
                    "/workspace/code.py",
                ],
                capture_output=True,
                timeout=SANDBOX_TIMEOUT_SECONDS + 2,
            )
            elapsed_ms = int((time.time() - start) * 1000)
            stdout = result.stdout.decode(errors="replace")[:SANDBOX_MAX_OUTPUT_BYTES]
            stderr = result.stderr.decode(errors="replace")[:8192]
            generated = _extract_files(wdir)
            return SandboxResult(
                execution_id=exec_id,
                success=result.returncode == 0,
                stdout=stdout,
                stderr=stderr,
                exit_code=result.returncode,
                execution_time_ms=elapsed_ms,
                generated_files=generated,
                mode="docker",
            )
        except subprocess.TimeoutExpired:
            return SandboxResult(
                execution_id=exec_id, success=False,
                stdout="", stderr="", exit_code=-1,
                execution_time_ms=SANDBOX_TIMEOUT_SECONDS * 1000,
                error="Execution timed out (30s limit)",
                mode="docker",
            )


# ── Subprocess execution (fallback) ──────────────────────────────────────────

_SUBPROCESS_PREAMBLE = """
# ArchonHub Sandbox — do not modify
import matplotlib as _mpl
_mpl.use('Agg')
"""


def _wrap_code(code: str) -> str:
    return _SUBPROCESS_PREAMBLE + "\n" + code


def _set_limits():
    """Set resource limits for subprocess (Unix only)."""
    if platform.system() != "Darwin" and platform.system() != "Linux":
        return
    try:
        mem_bytes = SANDBOX_MEMORY_MB * 1024 * 1024
        resource.setrlimit(resource.RLIMIT_AS, (mem_bytes, mem_bytes))
        resource.setrlimit(resource.RLIMIT_CPU, (SANDBOX_TIMEOUT_SECONDS, SANDBOX_TIMEOUT_SECONDS + 2))
    except Exception:
        pass


def _run_subprocess(code: str, exec_id: str, data_files: list[dict]) -> SandboxResult:
    """Execute code in a restricted subprocess."""
    with tempfile.TemporaryDirectory() as workdir:
        wdir = Path(workdir)
        
        # Write wrapped code
        code_file = wdir / "code.py"
        code_file.write_text(_wrap_code(code))
        
        # Write data files
        for df in data_files:
            try:
                safe_name = Path(df["name"]).name  # strip any directory traversal
                if not safe_name or safe_name.startswith("."):
                    continue
                content = base64.b64decode(df["content_b64"])
                (wdir / safe_name).write_bytes(content)
            except Exception:
                pass
        
        start = time.time()
        import site
        user_site = site.getusersitepackages()
        env = {
            "HOME": workdir,
            "PATH": "/usr/local/bin:/usr/bin:/bin",
            "PYTHONPATH": user_site + ":" + ":".join(p for p in sys.path if p),
            "MPLBACKEND": "Agg",
            "MPLCONFIGDIR": workdir,
        }
        
        # Matplotlib saves to cwd
        try:
            proc = subprocess.run(
                [sys.executable, "-u", str(code_file)],
                capture_output=True,
                timeout=SANDBOX_TIMEOUT_SECONDS,
                cwd=workdir,
                env=env,
                preexec_fn=_set_limits if platform.system() in ("Darwin", "Linux") else None,
            )
            elapsed_ms = int((time.time() - start) * 1000)
            stdout = proc.stdout.decode(errors="replace")[:SANDBOX_MAX_OUTPUT_BYTES]
            stderr = proc.stderr.decode(errors="replace")[:8192]
            # Strip preamble noise from stderr
            stderr_lines = [l for l in stderr.splitlines()
                            if "_safe_import" not in l and "_blocked" not in l
                            and "_real_import" not in l and "builtins.__import__" not in l]
            stderr = "\n".join(stderr_lines)
            generated = _extract_files(wdir)
            return SandboxResult(
                execution_id=exec_id,
                success=proc.returncode == 0,
                stdout=stdout,
                stderr=stderr,
                exit_code=proc.returncode,
                execution_time_ms=elapsed_ms,
                generated_files=generated,
                mode="subprocess",
            )
        except subprocess.TimeoutExpired:
            return SandboxResult(
                execution_id=exec_id, success=False,
                stdout="", stderr="", exit_code=-1,
                execution_time_ms=SANDBOX_TIMEOUT_SECONDS * 1000,
                error=f"Execution timed out ({SANDBOX_TIMEOUT_SECONDS}s limit)",
                mode="subprocess",
            )
        except Exception as e:
            return SandboxResult(
                execution_id=exec_id, success=False,
                stdout="", stderr=str(e), exit_code=-1,
                execution_time_ms=int((time.time() - start) * 1000),
                error=str(e),
                mode="subprocess",
            )


# ── Public API ────────────────────────────────────────────────────────────────

def execute_code(
    code: str,
    language: str = "python",
    data_files: Optional[list[dict]] = None,
    prefer_docker: bool = True,
) -> SandboxResult:
    """
    Execute code in the sandbox.
    
    Args:
        code:         Python source code to execute
        language:     Currently only "python" supported
        data_files:   List of {name, content_b64, mime_type} uploaded files
        prefer_docker: Try Docker first; fall back to subprocess
    
    Returns:
        SandboxResult with stdout, stderr, generated_files, timing
    """
    exec_id = str(uuid.uuid4())
    data_files = data_files or []
    
    if language != "python":
        return SandboxResult(
            execution_id=exec_id, success=False,
            stdout="", stderr="", exit_code=-1,
            execution_time_ms=0,
            error=f"Language '{language}' not supported. Only 'python' is available.",
        )
    
    # Security scan
    blocked_reason = _scan_code(code)
    if blocked_reason:
        return SandboxResult(
            execution_id=exec_id, success=False,
            stdout="", stderr="", exit_code=-1,
            execution_time_ms=0,
            blocked_reason=blocked_reason,
            error=blocked_reason,
        )
    
    # Choose execution mode
    if prefer_docker:
        try:
            docker_check = subprocess.run(
                ["docker", "info"], capture_output=True, timeout=3
            )
            if docker_check.returncode == 0:
                if _ensure_docker_image():
                    return _run_docker(code, exec_id, data_files)
        except Exception:
            pass
    
    # Subprocess fallback
    return _run_subprocess(code, exec_id, data_files)


def get_sandbox_status() -> dict:
    """Return current sandbox availability info."""
    docker_available = False
    try:
        r = subprocess.run(["docker", "info"], capture_output=True, timeout=3)
        docker_available = r.returncode == 0
    except Exception:
        pass
    
    return {
        "available": True,
        "mode": "docker" if docker_available else "subprocess",
        "docker_available": docker_available,
        "timeout_seconds": SANDBOX_TIMEOUT_SECONDS,
        "memory_limit_mb": SANDBOX_MEMORY_MB,
        "supported_languages": ["python"],
        "available_packages": sorted(ALLOWED_IMPORTS),
    }
