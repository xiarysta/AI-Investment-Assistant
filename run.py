from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = ROOT_DIR / "backend"
VENV_DIR = BACKEND_DIR / "venv"
REQUIREMENTS_FILE = BACKEND_DIR / "requirements.txt"

BACKEND_URL = "http://127.0.0.1:8001"
FRONTEND_URL = "http://127.0.0.1:5173/frontend/index.html"


def get_venv_python() -> Path:
    if os.name == "nt":
        return VENV_DIR / "Scripts" / "python.exe"
    return VENV_DIR / "bin" / "python"


def run_step(command: list[str], cwd: Path) -> None:
    printable = " ".join(command)
    print(f"> {printable}")
    subprocess.check_call(command, cwd=cwd)


def backend_dependencies_ready(python_path: Path) -> bool:
    check = subprocess.run(
        [
            str(python_path),
            "-c",
            "import fastapi, uvicorn, dotenv, httpx, yfinance",
        ],
        cwd=BACKEND_DIR,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return check.returncode == 0


def ensure_backend_environment() -> Path:
    python_path = get_venv_python()

    if not python_path.exists():
        print("Creating backend virtual environment...")
        run_step([sys.executable, "-m", "venv", str(VENV_DIR)], ROOT_DIR)

    if not backend_dependencies_ready(python_path):
        print("Installing backend dependencies...")
        run_step(
            [str(python_path), "-m", "pip", "install", "-r", str(REQUIREMENTS_FILE)],
            BACKEND_DIR,
        )

    return python_path


def start_process(command: list[str], cwd: Path) -> subprocess.Popen:
    printable = " ".join(command)
    print(f"> {printable}")
    return subprocess.Popen(command, cwd=cwd)


def stop_processes(processes: list[subprocess.Popen]) -> None:
    for process in processes:
        if process.poll() is None:
            process.send_signal(signal.SIGTERM)

    for process in processes:
        if process.poll() is None:
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()


def main() -> int:
    backend_python = ensure_backend_environment()
    processes: list[subprocess.Popen] = []

    try:
        processes.append(
            start_process(
                [
                    str(backend_python),
                    "-m",
                    "uvicorn",
                    "app.main:app",
                    "--host",
                    "127.0.0.1",
                    "--port",
                    "8001",
                    "--reload",
                ],
                BACKEND_DIR,
            )
        )
        processes.append(
            start_process(
                [sys.executable, "-m", "http.server", "5173"],
                ROOT_DIR,
            )
        )

        print()
        print("AI Investment Assistant is running.")
        print(f"Frontend: {FRONTEND_URL}")
        print(f"Backend:  {BACKEND_URL}")
        print("Press Ctrl+C to stop both servers.")

        while True:
            for process in processes:
                if process.poll() is not None:
                    return process.returncode or 0
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping servers...")
        return 0
    finally:
        stop_processes(processes)


if __name__ == "__main__":
    raise SystemExit(main())
