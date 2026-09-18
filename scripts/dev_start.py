from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT / "backend"
FRONTEND_DIR = ROOT / "frontend"
BACKEND_PYTHON = BACKEND_DIR / ".venv" / "Scripts" / "python.exe"


def main() -> int:
    args = parse_args()
    backend_python = resolve_backend_python()
    pnpm = resolve_pnpm()

    root_env = load_root_env()
    backend_env = os.environ.copy()
    backend_env.update(root_env)
    backend_env["PYTHONPATH"] = "."

    frontend_env = os.environ.copy()
    frontend_env.update({key: value for key, value in root_env.items() if key.startswith("VITE_")})

    backend_cmd = [
        str(backend_python),
        "-m",
        "uvicorn",
        "app.main:app",
        "--host",
        args.backend_host,
        "--port",
        str(args.backend_port),
    ]
    if args.reload:
        backend_cmd.append("--reload")

    frontend_cmd = [
        pnpm,
        "dev",
        "--host",
        args.frontend_host,
        "--port",
        str(args.frontend_port),
    ]

    print("[dev] Starting NovelAgent", flush=True)
    print(f"[dev] Backend:  http://{args.backend_host}:{args.backend_port}", flush=True)
    print(f"[dev] Frontend: http://{args.frontend_host}:{args.frontend_port}", flush=True)
    print("[dev] Press Ctrl+C to stop both processes.", flush=True)

    processes = [
        subprocess.Popen(backend_cmd, cwd=BACKEND_DIR, env=backend_env),
        subprocess.Popen(frontend_cmd, cwd=FRONTEND_DIR, env=frontend_env),
    ]

    try:
        return wait_for_processes(processes)
    except KeyboardInterrupt:
        print("\n[dev] Stopping NovelAgent...")
        return 0
    finally:
        stop_processes(processes)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Start NovelAgent backend and frontend together.")
    parser.add_argument("--backend-host", default="127.0.0.1")
    parser.add_argument("--backend-port", type=int, default=8000)
    parser.add_argument("--frontend-host", default="127.0.0.1")
    parser.add_argument("--frontend-port", type=int, default=5173)
    parser.add_argument("--no-reload", action="store_true", help="Run FastAPI without uvicorn reload.")
    args = parser.parse_args()
    args.reload = not args.no_reload
    return args


def resolve_backend_python() -> Path:
    if BACKEND_PYTHON.exists():
        return BACKEND_PYTHON
    raise SystemExit(
        "backend\\.venv was not found. Create it first:\n"
        "  cd backend\n"
        "  python -m venv .venv\n"
        "  .\\.venv\\Scripts\\python -m pip install -r requirements.txt"
    )


def resolve_pnpm() -> str:
    pnpm = shutil.which("pnpm")
    if pnpm:
        return pnpm
    raise SystemExit("pnpm was not found on PATH. Install pnpm, then run this script again.")


def load_root_env() -> dict[str, str]:
    env_path = ROOT / ".env"
    if not env_path.exists():
        return {}

    values: dict[str, str] = {}
    for line in env_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def wait_for_processes(processes: list[subprocess.Popen]) -> int:
    while True:
        for process in processes:
            return_code = process.poll()
            if return_code is not None:
                print(f"[dev] A child process exited with code {return_code}.")
                return return_code
        time.sleep(0.5)


def stop_processes(processes: list[subprocess.Popen]) -> None:
    for process in processes:
        if process.poll() is None:
            process.terminate()

    deadline = time.time() + 8
    for process in processes:
        while process.poll() is None and time.time() < deadline:
            time.sleep(0.1)

    for process in processes:
        if process.poll() is None:
            process.kill()


if __name__ == "__main__":
    raise SystemExit(main())
