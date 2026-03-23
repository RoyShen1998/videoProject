"""Register/unregister this app in Windows Task Scheduler to auto-start at logon."""

import os
import sys
import subprocess
from pathlib import Path


TASK_NAME = "MeetingVideoSummarizer"
SCRIPT_DIR = Path(__file__).resolve().parent
PYTHON_EXE = sys.executable
MAIN_SCRIPT = SCRIPT_DIR / "main.py"


def install():
    """Create a scheduled task that runs main.py at user logon."""
    # Use pythonw.exe for no console window (swap python.exe → pythonw.exe)
    pythonw = Path(PYTHON_EXE).parent / "pythonw.exe"
    exe = str(pythonw) if pythonw.exists() else PYTHON_EXE

    cmd = [
        "schtasks", "/Create", "/F",
        "/TN", TASK_NAME,
        "/TR", f'"{exe}" "{MAIN_SCRIPT}"',
        "/SC", "ONLOGON",
        "/RL", "HIGHEST",
        "/DELAY", "0000:30",  # 30-second delay after logon
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"Task '{TASK_NAME}' created successfully.")
        print("The pipeline will auto-start at logon.")
    else:
        print(f"Failed to create task: {result.stderr}")
        sys.exit(1)


def uninstall():
    """Remove the scheduled task."""
    cmd = ["schtasks", "/Delete", "/F", "/TN", TASK_NAME]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"Task '{TASK_NAME}' removed.")
    else:
        print(f"Failed to remove task: {result.stderr}")
        sys.exit(1)


if __name__ == "__main__":
    if "--uninstall" in sys.argv:
        uninstall()
    else:
        install()
