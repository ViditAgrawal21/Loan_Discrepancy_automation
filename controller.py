"""
Main automation controller — orchestrates the entire discrepancy management flow.

Flow per row:
  1. Validate row data
  2. Navigate to Reconciliation page
  3. Select Financial Year & Application Status (DISCREPANCY)
  4. Click PROCEED
  5. Search by Account Number
  6. Click MANAGE DISCREPANCIES
  7. Click UPDATE
  8. Update form fields (only non-empty Excel values)
  9. Click UPDATE & CONTINUE → OK modal
  10. Preview → Declaration checkbox → SUBMIT → CONFIRM
  11. Extract Loan Application Number
  12. Write Application ID back to Excel
  13. Move to next row (if Multi mode)

Supports:
  - Single mode (one row) and Multi mode (batch processing)
  - Stop control via threading.Event() with frequent checks
  - Force-stop via browser process kill
  - Error handling with screenshots
  - Live log callbacks to UI
"""

import threading
import subprocess
import os
from datetime import datetime

from automation.browser import start_browser, close_browser, take_screenshot


class AutomationStoppedError(Exception):
    """Raised when the user requests stop — allows immediate exit."""
    pass


def _check_stop(stop_event, log=None):
    """
    Check if stop has been requested and raise immediately if so.
    Call this between every major step for responsive cancellation.
    """
    if stop_event is not None and stop_event.is_set():
        if log:
            log("STOP signal detected — aborting immediately...")
        raise AutomationStoppedError("Stopped by user")


def force_kill_browser(browser_ref: dict):
    """
    Force-kill the browser process. Called from UI thread for immediate stop.
    browser_ref should be a dict with keys 'p', 'browser' (set by the worker).
    """
    try:
        b = browser_ref.get("browser")
        p = browser_ref.get("p")
        if b:
            try:
                b.close()
            except Exception:
                pass
        if p:
            try:
                p.stop()
            except Exception:
                pass
    except Exception:
        pass

    # Fallback: kill all chromium child processes spawned by Playwright
    try:
        subprocess.run(
            ["taskkill", "/F", "/IM", "chromium.exe", "/T"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            timeout=5
        )
    except Exception:
        pass
    try:
        subprocess.run(
            ["taskkill", "/F", "/IM", "chrome.exe", "/T"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            timeout=5
        )
    except Exception:
        pass


from automation.login import perform_login
from automation.navigation import setup_reconciliation_page
from automation.search import search_and_manage
from automation.update_form import update_discrepancy
from automation.submit import submit_and_extract

from excel_engine.reader import load_workbook, read_row, get_total_rows, has_application_id
from excel_engine.validator import validate_row
from excel_engine.writer import ExcelWriteSession

from utils.logger import log_info, log_error


def _reset_page_for_next_row(page, log):
    """
    Reset the browser page to a clean state between rows.
    Dismisses lingering modals/dialogs and navigates to the welcome
    page so navigation starts fresh.
    """
    try:
        # Dismiss any confirmation / success modal
        page.keyboard.press("Escape")
        page.wait_for_timeout(100)
    except Exception:
        pass

    # Click OK / Close on any lingering dialog
    for txt in ["OK", "Close", "×"]:
        try:
            btn = page.locator(f"button:has-text('{txt}')").first
            if btn.is_visible(timeout=1000):
                btn.click()
                page.wait_for_timeout(200)
        except Exception:
            pass

    # Navigate to welcome page to fully reset the SPA state
    try:
        page.goto("https://fasalrin.gov.in/welcome",
                  wait_until="domcontentloaded")
        page.wait_for_timeout(200)
        log("Page reset for next row")
    except Exception as e:
        log(f"Warning — page reset: {e}")


def run(profile: dict, profile_name: str, excel_path: str, mode: str,
        start_row: int, stop_event: threading.Event, log_callback=None,
        captcha_callback=None, browser_ref: dict = None):
    """
    Main automation entry point.

    Args:
        profile: Decrypted profile dict.
        profile_name: Profile name (for session management).
        excel_path: Path to the Excel file.
        mode: 'single' or 'multi'.
        start_row: First data row to process (1-based, minimum 2).
        stop_event: Threading event for stop control.
        log_callback: Function to send log messages to UI.
        captcha_callback: Function to request captcha input from UI.
        browser_ref: Shared dict — will be populated with 'p' and 'browser'
                     so the UI can force-kill the browser on FORCE STOP.
    """
    if browser_ref is None:
        browser_ref = {}

    def log(msg):
        timestamp = datetime.now().strftime("%H:%M:%S")
        full_msg = f"[{timestamp}] {msg}"
        if log_callback:
            log_callback(full_msg)
        log_info(msg)

    def check():
        """Shorthand: raise AutomationStoppedError if stop requested."""
        _check_stop(stop_event, log)

    p = None
    browser = None
    writer = None

    try:
        # ── Step 1: Load Excel ──
        log("Loading Excel file...")
        sheet1_ws = load_workbook(excel_path)
        total_rows = get_total_rows(sheet1_ws)
        log(f"Excel loaded — {total_rows - 1} data rows found (rows 2 to {total_rows})")

        # Open a persistent write session
        writer = ExcelWriteSession(excel_path, save_interval=5)
        log("Excel write session ready")

        if start_row < 2:
            start_row = 2
        if start_row > total_rows:
            log(f"Start row {start_row} exceeds data rows ({total_rows}). Nothing to process.")
            return

        check()  # ← stop check

        # ── Step 2: Launch Browser ──
        log("Launching browser...")
        p, browser, context, page = start_browser(profile_name=profile_name, headless=False)
        # Expose references so UI can force-kill
        browser_ref["p"] = p
        browser_ref["browser"] = browser
        log("Browser launched")

        check()  # ← stop check

        # ── Step 3: Login ──
        perform_login(
            page=page,
            context=context,
            profile=profile,
            profile_name=profile_name,
            captcha_callback=captcha_callback,
            log_callback=log,
        )

        check()  # ← stop check after login

        # ── Step 4: Process Rows ──
        end_row = start_row + 1 if mode == "single" else total_rows + 1
        success_count = 0
        fail_count = 0

        for row_num in range(start_row, end_row):
            # Check stop control
            check()

            log(f"{'═' * 50}")
            log(f"Processing Row {row_num} of {total_rows}")
            log(f"{'═' * 50}")

            try:
                # Skip rows that already have Application ID
                if has_application_id(sheet1_ws, row_num):
                    existing_id = sheet1_ws.cell(row=row_num, column=11).value
                    log(f"Row {row_num} already processed — App ID: {existing_id}. Skipping.")
                    continue

                # ── Validate Row ──
                log(f"Validating row {row_num}...")
                errors = validate_row(sheet1_ws, row_num)
                if errors:
                    for err in errors:
                        log(f"  VALIDATION ERROR: {err}")
                    writer.write_status(row_num, f"VALIDATION FAILED: {'; '.join(errors)}")
                    fail_count += 1
                    continue

                # ── Read Row Data ──
                row_data = read_row(sheet1_ws, row_num)
                account_number = row_data["account"]
                log(f"Account Number: {account_number}")

                check()  # ← stop check before navigation

                # ── Navigate to Reconciliation & Setup ──
                financial_year = profile.get("financial_year", "")
                setup_reconciliation_page(page, financial_year, log_callback=log)
                check()

                # ── Search & Click MANAGE DISCREPANCIES ──
                search_and_manage(page, account_number, log_callback=log)
                check()

                # ── UPDATE → Fill Fields → UPDATE & CONTINUE → OK ──
                update_discrepancy(page, row_data, log_callback=log)
                check()

                # ── Preview → Declaration → SUBMIT → CONFIRM → Extract ID ──
                app_id = submit_and_extract(page, log_callback=log)
                check()

                # ── Write Application ID to Excel ──
                writer.write_app_id(row_num, app_id)
                log(f"Row {row_num} COMPLETED — Application ID: {app_id}")
                success_count += 1

                # ── Cleanup for next row (multi mode) ──
                if mode == "multi":
                    _reset_page_for_next_row(page, log)

            except AutomationStoppedError:
                log(f"Row {row_num} interrupted by STOP.")
                raise  # Propagate to outer handler

            except Exception as e:
                error_msg = str(e)
                log(f"ERROR on Row {row_num}: {error_msg}")
                log_error(f"Row {row_num}: {error_msg}")

                # Take screenshot on error
                try:
                    screenshot_name = f"error_row{row_num}_{datetime.now().strftime('%H%M%S')}.png"
                    take_screenshot(page, screenshot_name)
                    log(f"Screenshot saved: {screenshot_name}")
                except Exception:
                    pass

                # Write error status to Excel
                try:
                    writer.write_status(row_num, f"ERROR: {error_msg[:100]}")
                except Exception:
                    pass

                fail_count += 1

                # In multi mode, reset page and continue; in single mode, stop
                if mode == "single":
                    break
                else:
                    _reset_page_for_next_row(page, log)
                    continue

        # ── Summary ──
        log(f"{'═' * 50}")
        log(f"AUTOMATION COMPLETE")
        log(f"  Successful: {success_count}")
        log(f"  Failed: {fail_count}")
        log(f"  Stopped: {'Yes' if stop_event.is_set() else 'No'}")
        log(f"{'═' * 50}")

    except AutomationStoppedError:
        log("Automation STOPPED by user.")

    except Exception as e:
        log(f"FATAL ERROR: {str(e)}")
        log_error(f"Fatal: {str(e)}")
        try:
            take_screenshot(page, f"fatal_{datetime.now().strftime('%H%M%S')}.png")
        except Exception:
            pass

    finally:
        # Flush & close the Excel write session so no data is lost
        try:
            if writer:
                writer.close()
                log("Excel saved")
        except Exception:
            pass

        # Clear browser references
        browser_ref.pop("browser", None)
        browser_ref.pop("p", None)
        if p and browser:
            log("Closing browser...")
            close_browser(p, browser)
            log("Browser closed")
