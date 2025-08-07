"""
main.py — Entry point for SAGE
"""

import sys
import time
import os
from pathlib import Path
import shutil
import threading
import runpy
import subprocess

ROOT_DIR = Path(__file__).resolve().parent
OTERM_PATH = ROOT_DIR / "oterm"
OTERM_SRC_PATH = OTERM_PATH / "src"

def get_resource_path(name: str) -> str:
    if getattr(sys, 'frozen', False):
        return os.path.join(sys._MEIPASS, name)
    return os.path.abspath(name)

def ensure_model_exists(model_name="mistral-7b-sage", modelfile="Modelfile", flag_file=".model_built"):
    if Path(flag_file).exists():
        print(f"[SAGE] Model already built. Skipping setup.")
        return

    if not shutil.which("ollama"):
        print("[SAGE] Ollama is not installed or not in PATH.")
        print("        → Please install it from https://ollama.com")
        input("Press Enter to exit...")
        sys.exit(1)

    print(f"[SAGE] Checking for '{model_name}'...")
    try:
        result = subprocess.run(["ollama", "list"], capture_output=True, text=True, check=True)
        if model_name in result.stdout:
            print(f"[SAGE] Model '{model_name}' exists.")
            Path(flag_file).touch()
            return
    except subprocess.CalledProcessError:
        print("[SAGE] Couldn't check existing Ollama models. Attempting build...")

    modelfile_path = get_resource_path(modelfile)
    print(f"[SAGE] Building model '{model_name}' from {modelfile_path}...")
    try:
        subprocess.run(["ollama", "create", model_name, "-f", modelfile_path], check=True)
        print(f"[SAGE] Model '{model_name}' created successfully.")
        Path(flag_file).touch()
    except subprocess.CalledProcessError as e:
        print(f"[SAGE] Error creating model: {e}")
        input("Press Enter to exit...")
        sys.exit(1)

def wait_for_keypress():
    print("\nPress any key to continue.")
    try:
        # Windows-only
        import msvcrt
        msvcrt.getch()
    except ImportError:
        # Unix-like systems
        import termios
        import tty
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
            
def launch_tui():
    print("[SAGE] Preparing interface...")
    tui_path = Path(__file__).resolve().parent / "oterm" / "src"
    subprocess.run([sys.executable, "-m", "oterm.cli.oterm"], cwd=tui_path)

def main(): 
    print("\n")
    print("             :::====  :::===   :::===== :::=====")
    print("             :::     :::  === :::       :::     ")
    print("              =====  ======== === ===== ======  ")
    print("                 === ===  === ===   === ===     ")
    print("             ======  ===  ===  =======  ========")
    print(" ")
    print(" ")
    print("             SAGE — Secure Agent for GPU Export ")
    print("                        Version 0.1.0           ")
    print(" ")
    print("     Copyright (C) Akhilan Celeis Raja. All rights reserved.")
    print("\n")
    print("----------------------------------------------------------------")

    ensure_model_exists()
    wait_for_keypress()
    launch_tui()

if __name__ == "__main__":
    import subprocess
    main()

