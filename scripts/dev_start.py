from __future__ import annotations

import argparse
import json
import os
import socket
import subprocess
import time
import webbrowser
from pathlib import Path
from urllib.error import URLError
from urllib.request import ProxyHandler, build_opener


ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT / "backend"
FRONTEND_DIR = ROOT / "frontend"
BACKEND_PYTHON = BACKEND_DIR / ".venv" / "Scripts" / "python.exe"


def main() -> int:
    args = parse_args()
    backend_python = resolve_backend_python()
    node = resolve_node()
    vite = FRONTEND_DIR / "node_modules" / "vite" / "bin" / "vite.js"
    if not vite.exists():
        raise SystemExit("Frontend dependencies were not found. Run 'pnpm install' in frontend first.")

    for host, port in [(args.backend_host, args.backend_port), (args.frontend_host, args.frontend_port)]:
        with socket.socket() as probe:
            if probe.connect_ex((host, port)) == 0:
                if args.open and open_existing_app(args):
                    return 0
                raise SystemExit(
                    f"Port {port} is already in use. If NovelAgent is already running, open "
                    f"http://{args.frontend_host}:{args.frontend_port}/. Otherwise stop the conflicting service first."
                )

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
        str(node),
        str(vite),
        "--host",
        args.frontend_host,
        "--port",
        str(args.frontend_port),
        "--strictPort",
    ]

    print("[dev] Starting NovelAgent", flush=True)
    print(f"[dev] Backend:  http://{args.backend_host}:{args.backend_port}", flush=True)
    print(f"[dev] Frontend: http://{args.frontend_host}:{args.frontend_port}", flush=True)
    print("[dev] Press Ctrl+C to stop both processes.", flush=True)

    processes = []
    try:
        processes.append(subprocess.Popen(backend_cmd, cwd=BACKEND_DIR, env=backend_env))
        processes.append(subprocess.Popen(frontend_cmd, cwd=FRONTEND_DIR, env=frontend_env))
        if args.open:
            url = f"http://{args.frontend_host}:{args.frontend_port}/"
            wait_until_ready(processes, [f"http://{args.backend_host}:{args.backend_port}/health", url])
            webbrowser.open(url)
        return wait_for_processes(processes)
    except KeyboardInterrupt:
        print("\n[dev] Stopping NovelAgent...")
        return 0
    except (OSError, RuntimeError) as exc:
        print(f"[dev] Startup failed: {exc}", flush=True)
        return 1
    finally:
        stop_processes(processes)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Start NovelAgent backend and frontend together.")
    parser.add_argument("--backend-host", default="127.0.0.1")
    parser.add_argument("--backend-port", type=int, default=8000)
    parser.add_argument("--frontend-host", default="127.0.0.1")
    parser.add_argument("--frontend-port", type=int, default=5173)
    parser.add_argument("--no-reload", action="store_true", help="Run FastAPI without uvicorn reload.")
    parser.add_argument("--open", action="store_true", help="Open the browser after both services are ready.")
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


def resolve_node() -> Path:
    candidates = [Path(folder) / "node.exe" for folder in os.get_exec_path()]
    # NVM for Windows can have installed versions even when its active shim is broken.
    roots = [os.environ.get("NVM_HOME"), os.environ.get("NVM_ROOT")]
    roots.append(str(Path.home() / "AppData" / "Local" / "Author Software" / "nvm"))
    if os.environ.get("LOCALAPPDATA"):
        roots.append(str(Path(os.environ["LOCALAPPDATA"]) / "Author Software" / "nvm"))
    for root in roots:
        if root:
            candidates.extend(sorted(Path(root).glob("installs/*/node.exe"), reverse=True))
            candidates.extend(sorted(Path(root).glob("v*/node.exe"), reverse=True))
    for candidate in candidates:
        if not candidate.is_file():
            continue
        try:
            check = subprocess.run(
                [str(candidate), "--version"], capture_output=True, text=True, timeout=5,
            )
            if check.returncode == 0 and check.stdout.strip().startswith("v"):
                return candidate
        except (OSError, subprocess.TimeoutExpired):
            continue
    raise SystemExit("No working Node.js installation was found. Install or activate Node.js, then try again.")


def wait_until_ready(processes: list[subprocess.Popen], urls: list[str]) -> None:
    opener = build_opener(ProxyHandler({}))
    pending = set(urls)
    deadline = time.monotonic() + 60
    while pending and time.monotonic() < deadline:
        if any(process.poll() is not None for process in processes):
            raise RuntimeError("A service exited before it was ready. Check its log above.")
        for url in list(pending):
            try:
                with opener.open(url, timeout=1) as response:
                    if response.status == 200:
                        pending.remove(url)
            except (OSError, URLError):
                pass
        if pending:
            time.sleep(0.25)
    if pending:
        raise RuntimeError("Services did not become ready within 60 seconds.")


def open_existing_app(args: argparse.Namespace) -> bool:
    opener = build_opener(ProxyHandler({}))
    url = f"http://{args.frontend_host}:{args.frontend_port}/"
    try:
        with opener.open(f"http://{args.backend_host}:{args.backend_port}/openapi.json", timeout=2) as response:
            if json.load(response).get("info", {}).get("title") != "NovelAgent":
                return False
        with opener.open(url, timeout=2) as response:
            if "<title>NovelAgent" not in response.read(65536).decode("utf-8"):
                return False
    except (OSError, ValueError):
        return False
    print(f"[dev] NovelAgent is already running. Opening {url}", flush=True)
    webbrowser.open(url)
    return True


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
