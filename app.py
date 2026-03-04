"""
VeriTruth AI — One-click launcher
Run:  python app.py
Starts: FastAPI backend + Celery worker + Next.js frontend
Press Ctrl+C to stop everything.
"""

import os
import subprocess
import sys
import time
from pathlib import Path

# Force UTF-8 output so arrow/bullet characters don't crash on Windows CP1252
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
ROOT = Path(__file__).parent
BACKEND = ROOT / "backend"
FRONTEND = ROOT / "frontend"

# ── colours ──────────────────────────────────────────────────
GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
CYAN   = "\033[96m"
RESET  = "\033[0m"

def log(colour: str, tag: str, msg: str) -> None:
    print(f"{colour}[{tag}]{RESET} {msg}")

# ── helpers ───────────────────────────────────────────────────
def find_python() -> str:
    """Return the Python executable (prefer .venv inside backend)."""
    venv_win  = BACKEND / ".venv" / "Scripts" / "python.exe"
    venv_unix = BACKEND / ".venv" / "bin" / "python"
    if venv_win.exists():
        return str(venv_win)
    if venv_unix.exists():
        return str(venv_unix)
    return sys.executable


def find_node_cmd(cmd: str) -> str:
    """Return npm / npx path — works on Windows and Unix."""
    npm_win = FRONTEND / "node_modules" / ".bin" / f"{cmd}.cmd"
    if npm_win.exists():
        return str(npm_win)
    return cmd  # rely on PATH


def ensure_backend_deps(python: str) -> None:
    req = BACKEND / "requirements.txt"
    if not req.exists():
        return
    # Skip if marker file exists (already installed this session baseline)
    marker = BACKEND / ".deps_installed"
    if marker.exists():
        log(GREEN, "setup", "Backend deps already installed (delete backend/.deps_installed to reinstall)")
        return
    log(YELLOW, "setup", "Installing backend dependencies (this may take a few minutes) …")
    result = subprocess.run(
        [python, "-m", "pip", "install", "-r", str(req)],
        cwd=str(BACKEND),
    )
    if result.returncode != 0:
        log(RED, "setup", "Some packages failed to install — continuing anyway. Check requirements.txt if the server fails to start.")
    else:
        marker.touch()
        log(GREEN, "setup", "Backend deps OK")


def ensure_frontend_deps() -> None:
    if not (FRONTEND / "node_modules").exists():
        log(YELLOW, "setup", "Installing frontend node_modules …")
        subprocess.run(["npm", "install"], cwd=str(FRONTEND), check=True)
        log(GREEN, "setup", "Frontend deps OK")


# ── process registry ──────────────────────────────────────────
processes: list[subprocess.Popen] = []

def start_process(label: str, cmd: list[str], cwd: str) -> subprocess.Popen:
    log(CYAN, label, "Starting -> " + " ".join(cmd))
    proc = subprocess.Popen(
        cmd,
        cwd=cwd,
        stdout=None,   # inherit — output flows straight to terminal
        stderr=None,
        env=os.environ.copy(),
    )
    processes.append(proc)
    return proc


def stop_all() -> None:
    log(YELLOW, "shutdown", "Stopping all services …")
    for proc in reversed(processes):
        if proc.poll() is None:
            try:
                if sys.platform == "win32":
                    # CTRL_C_EVENT kills the whole process group including us;
                    # use taskkill instead so only the child is terminated.
                    subprocess.run(
                        ["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                else:
                    proc.terminate()
                proc.wait(timeout=5)
            except Exception:
                try:
                    proc.kill()
                except Exception:
                    pass
    log(GREEN, "shutdown", "All services stopped.")


def main() -> None:
    print(f"\n{GREEN}{'='*55}")
    print("   VeriTruth AI — Launcher")
    print(f"{'='*55}{RESET}\n")

    python = find_python()

    # ── 1. Install dependencies (first run only) ──────────────
    ensure_backend_deps(python)
    ensure_frontend_deps()

    # ── 2. Determine uvicorn command ──────────────────────
    uvicorn_win  = BACKEND / ".venv" / "Scripts" / "uvicorn.exe"
    uvicorn_unix = BACKEND / ".venv" / "bin" / "uvicorn"
    if uvicorn_win.exists():
        uvicorn_args = [str(uvicorn_win)]
    elif uvicorn_unix.exists():
        uvicorn_args = [str(uvicorn_unix)]
    else:
        # Use python -m uvicorn when not in a venv
        uvicorn_args = [python, "-m", "uvicorn"]

    # ── 3. Launch services ────────────────────────────────────
    # Redis (use local binary if no system redis-server)
    redis_server = ROOT / "redis" / "redis-server.exe"
    system_redis = None
    try:
        import socket
        s = socket.create_connection(("localhost", 6379), timeout=1)
        s.close()
        log(GREEN, "redis", "Redis already running on :6379")
    except OSError:
        if redis_server.exists():
            redis_conf = ROOT / "redis" / "redis.windows.conf"
            redis_args = [str(redis_server)]
            if redis_conf.exists():
                redis_args.append(str(redis_conf))
            start_process("redis", redis_args, cwd=str(ROOT / "redis"))
            time.sleep(1)
        else:
            log(YELLOW, "redis", "Redis not found — start Redis manually on :6379")

    # MongoDB (use local binary if present)
    mongo_server = ROOT / "mongodb"
    mongo_bin = None
    for candidate in mongo_server.rglob("mongod.exe"):
        mongo_bin = candidate
        break
    try:
        import socket as _sock
        _s = _sock.create_connection(("localhost", 27017), timeout=1)
        _s.close()
        log(GREEN, "mongodb", "MongoDB already running on :27017")
    except OSError:
        if mongo_bin and mongo_bin.exists():
            data_dir = ROOT / "mongodb" / "data" / "db"
            data_dir.mkdir(parents=True, exist_ok=True)
            start_process(
                "mongodb",
                [str(mongo_bin), "--dbpath", str(data_dir), "--port", "27017"],
                cwd=str(ROOT / "mongodb"),
            )
            time.sleep(2)
            log(GREEN, "mongodb", "MongoDB started on :27017")
        else:
            log(YELLOW, "mongodb", "MongoDB not found — features requiring MongoDB will be limited")

    # FastAPI
    api_proc = start_process(
        "api",
        uvicorn_args + ["app.main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"],
        cwd=str(BACKEND),
    )
    time.sleep(2)  # give FastAPI a moment before worker tries to connect

    # Celery worker
    # Celery worker — use solo pool on Windows (no fork support)
    pool_arg = "solo" if sys.platform == "win32" else "prefork"
    celery_cmd = str(BACKEND / ".venv" / "Scripts" / "celery.exe") \
        if (BACKEND / ".venv" / "Scripts" / "celery.exe").exists() \
        else None
    if celery_cmd:
        celery_args = [celery_cmd, "-A", "app.worker.celery_app", "worker",
                       f"--loglevel=info", f"--pool={pool_arg}", "-Q", "default,analysis,maintenance"]
    else:
        # Use python -m celery when celery isn't a venv-local script
        celery_args = [python, "-m", "celery", "-A", "app.worker.celery_app", "worker",
                       f"--loglevel=info", f"--pool={pool_arg}", "-Q", "default,analysis,maintenance"]
    start_process(
        "worker",
        celery_args,
        cwd=str(BACKEND),
    )

    # Next.js dev server
    npm_cmd = "npm.cmd" if sys.platform == "win32" else "npm"
    start_process(
        "frontend",
        [npm_cmd, "run", "dev"],
        cwd=str(FRONTEND),
    )

    # ── 4. Check Neo4j ────────────────────────────────────────
    import socket as _ns
    try:
        _s = _ns.create_connection(("localhost", 7687), timeout=1); _s.close()
        log(GREEN, "neo4j", "Neo4j already running on :7687")
    except OSError:
        log(YELLOW, "neo4j",
            "Neo4j not running on :7687 — Knowledge Graph features will be disabled.\n"
            "          To enable: Open Neo4j Desktop → start your DBMS → set password in backend/.env")

    # ── 5. Print URLs ─────────────────────────────────────────
    time.sleep(2)
    print(f"\n{GREEN}{'='*55}")
    print("  Services running:")
    print(f"  * Frontend   -> http://localhost:3000")
    print(f"  * Backend    -> http://localhost:8000")
    print(f"  * API Docs   -> http://localhost:8000/docs")
    print(f"\n  Neo4j Desktop: start a DBMS and set NEO4J_PASSWORD in backend/.env")
    print(f"\n  Press Ctrl+C to stop everything.")
    print(f"{'='*55}{RESET}\n")

    # ── 5. Wait until Ctrl+C ──────────────────────────────────
    try:
        while True:
            # Restart a crashed service
            for proc in processes:
                if proc.poll() is not None:
                    log(RED, "watch", f"A service exited unexpectedly (pid={proc.pid})")
            time.sleep(3)
    except KeyboardInterrupt:
        pass
    finally:
        stop_all()


if __name__ == "__main__":
    main()
