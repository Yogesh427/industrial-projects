from __future__ import annotations

import subprocess
import sys
import time
import webbrowser
from pathlib import Path
from urllib.request import urlopen

PROJECT_ROOT = Path(__file__).resolve().parent
BACKEND_DIR = PROJECT_ROOT / "backend"
PYTHON = BACKEND_DIR / ".venv" / "Scripts" / "python.exe"
URL = "http://localhost:8000/ui/"
HEALTH_URL = "http://localhost:8000/health"


def server_is_ready() -> bool:
    try:
        with urlopen(HEALTH_URL, timeout=1) as response:
            return response.status == 200
    except Exception:
        return False


def main() -> int:
    if not PYTHON.exists():
        print(f"Backend Python was not found: {PYTHON}")
        print("Create the backend environment or update opener.py with your Python path.")
        return 1

    if not server_is_ready():
        print("Starting PhoenixML backend...")
        subprocess.Popen(
            [str(PYTHON), "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"],
            cwd=BACKEND_DIR,
            creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0,
        )
        for _ in range(30):
            if server_is_ready():
                break
            time.sleep(1)
        else:
            print("PhoenixML did not become ready on port 8000.")
            print("Check the backend terminal for the startup error.")
            return 1
    else:
        print("PhoenixML is already running.")

    webbrowser.open(URL)
    print(f"Opened {URL}")
    print("Login: admin / admin123")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
