"""
Build Script — Package Discrepancy Management Automation as a standalone .exe

Usage:
    python build.py

What it does:
  1. Installs PyInstaller (if needed)
  2. Locates the installed Playwright Chromium browser
  3. Runs PyInstaller to create a one-folder executable
  4. Copies Playwright Chromium browser into the dist folder
  5. Creates required directories (profiles/, logs/)
  6. Produces a ready-to-distribute folder: dist/DiscrepancyAutomation/

The entire dist/DiscrepancyAutomation/ folder can be zipped and given
to anyone on Windows 7+ — no Python install needed.
"""

import os
import sys
import shutil
import subprocess
import glob

# ── Paths ──
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
DIST_DIR = os.path.join(PROJECT_DIR, "dist")
BUILD_DIR = os.path.join(PROJECT_DIR, "build")
APP_NAME = "DiscrepancyAutomation"
OUTPUT_DIR = os.path.join(DIST_DIR, APP_NAME)


def step(msg):
    print(f"\n{'='*60}\n  {msg}\n{'='*60}")


def install_pyinstaller():
    step("Step 1: Checking PyInstaller")
    try:
        import PyInstaller
        print(f"  PyInstaller {PyInstaller.__version__} already installed.")
    except ImportError:
        print("  Installing PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--user", "pyinstaller"])
        print("  PyInstaller ready.")


def find_playwright_browsers():
    """Find the Playwright Chromium browser installation directory."""
    # Check custom env var first
    browsers_path = os.environ.get("PLAYWRIGHT_BROWSERS_PATH")
    if not browsers_path:
        # Default location on Windows
        local_app_data = os.environ.get("LOCALAPPDATA", "")
        browsers_path = os.path.join(local_app_data, "ms-playwright")

    if not os.path.exists(browsers_path):
        print(f"  WARNING: Playwright browsers not found at: {browsers_path}")
        print("  Run: python -m playwright install chromium")
        sys.exit(1)

    # Find chromium-* folder
    chromium_dirs = glob.glob(os.path.join(browsers_path, "chromium-*"))
    if not chromium_dirs:
        print(f"  WARNING: No chromium folder found in: {browsers_path}")
        print("  Run: python -m playwright install chromium")
        sys.exit(1)

    # Use the latest version
    chromium_dir = sorted(chromium_dirs)[-1]
    print(f"  Found Chromium: {chromium_dir}")
    return browsers_path, os.path.basename(chromium_dir)


def run_pyinstaller():
    step("Step 2: Building executable with PyInstaller")

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--name", APP_NAME,
        "--distpath", DIST_DIR,
        "--workpath", BUILD_DIR,
        # One-folder mode (required for bundling Chromium alongside)
        "--onedir",
        # Include all project modules
        "--add-data", f"automation;automation",
        "--add-data", f"excel_engine;excel_engine",
        "--add-data", f"ui;ui",
        "--add-data", f"utils;utils",
        "--add-data", f"path_helper.py;.",
        "--add-data", f"profile_manager.py;.",
        "--add-data", f"credential_encryptor.py;.",
        "--add-data", f"controller.py;.",
        # Hidden imports that PyInstaller might miss
        "--hidden-import", "playwright",
        "--hidden-import", "playwright.sync_api",
        "--hidden-import", "openpyxl",
        "--hidden-import", "pandas",
        "--hidden-import", "cryptography",
        "--hidden-import", "cryptography.fernet",
        "--hidden-import", "PIL",
        "--hidden-import", "tkinter",
        "--hidden-import", "tkinter.ttk",
        "--hidden-import", "tkinter.filedialog",
        "--hidden-import", "tkinter.messagebox",
        # Collect the full playwright package (includes its Node.js driver)
        "--collect-all", "playwright",
        # No console window (GUI app)
        "--windowed",
        # Entry point
        "main.py",
    ]

    print(f"  Running: {' '.join(cmd[-3:])}")
    subprocess.check_call(cmd, cwd=PROJECT_DIR)
    print(f"  Build complete: {OUTPUT_DIR}")


def bundle_chromium(browsers_path, chromium_folder_name):
    step("Step 3: Bundling Playwright Chromium browser")

    src = os.path.join(browsers_path, chromium_folder_name)
    dst = os.path.join(OUTPUT_DIR, "browsers", chromium_folder_name)

    if os.path.exists(dst):
        print(f"  Removing old: {dst}")
        shutil.rmtree(dst)

    print(f"  Copying Chromium ({chromium_folder_name})...")
    print(f"    From: {src}")
    print(f"    To:   {dst}")
    shutil.copytree(src, dst)
    print(f"  Chromium bundled successfully.")


def create_directories():
    step("Step 4: Creating required directories")
    for d in ["profiles", "logs"]:
        path = os.path.join(OUTPUT_DIR, d)
        os.makedirs(path, exist_ok=True)
        print(f"  Created: {d}/")


def print_summary():
    step("BUILD COMPLETE!")
    print(f"""
  Output folder:  {OUTPUT_DIR}

  To distribute:
    1. Zip the entire '{APP_NAME}' folder
    2. Send the zip to the end user
    3. They extract it and double-click: {APP_NAME}.exe

  Folder structure:
    {APP_NAME}/
      {APP_NAME}.exe       <-- Main application
      browsers/             <-- Playwright Chromium (bundled)
      profiles/             <-- User profiles (created at runtime)
      logs/                 <-- Log files (created at runtime)
      _internal/            <-- PyInstaller internal files
""")


def main():
    print(f"Building {APP_NAME}...")
    print(f"Project: {PROJECT_DIR}")

    install_pyinstaller()
    browsers_path, chromium_folder = find_playwright_browsers()
    run_pyinstaller()
    bundle_chromium(browsers_path, chromium_folder)
    create_directories()
    print_summary()


if __name__ == "__main__":
    main()
