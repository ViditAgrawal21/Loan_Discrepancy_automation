"""
Navigation automation — handles the reconciliation page setup:
  1. Navigate to /reconciliation/loan-application
  2. Select Financial Year from select[name="financialYear"]
  3. Select Application Status = DISCREPANCY from select[name="status"]
  4. Click PROCEED button

This must be called once after login, and again after each row reset
in multi-mode.
"""

from utils.constants import RECONCILIATION_URL, WELCOME_URL, STATUS_DISCREPANCY


def navigate_to_reconciliation(page, log_callback=None):
    """
    Navigate to the Reconciliation / Loan Application page.
    Forces a fresh page load so the FY/status selection appears clean.
    """
    def log(msg):
        if log_callback:
            log_callback(msg)

    log("Navigating to Reconciliation page...")

    # Dismiss any lingering modals / alerts from a previous submission
    try:
        page.keyboard.press("Escape")
    except Exception:
        pass

    # Navigate to welcome first to reset SPA state, then to reconciliation
    try:
        page.goto(WELCOME_URL, wait_until="domcontentloaded")
    except Exception:
        pass

    page.goto(RECONCILIATION_URL, wait_until="domcontentloaded")
    log("On Reconciliation page")


def select_financial_year(page, financial_year: str, log_callback=None):
    """
    Select the Financial Year from the dropdown on the reconciliation page.
    Uses select[name="financialYear"].
    """
    def log(msg):
        if log_callback:
            log_callback(msg)

    log(f"Selecting Financial Year: {financial_year}")

    try:
        fy_dropdown = page.locator("select[name='financialYear']")
        fy_dropdown.wait_for(state="visible", timeout=10000)
        fy_dropdown.select_option(label=financial_year)
        log(f"Financial Year '{financial_year}' selected")
    except Exception as e:
        # Fallback: try selecting by value pattern
        try:
            page.select_option("select[name='financialYear']", label=financial_year)
            log(f"Financial Year '{financial_year}' selected (fallback)")
        except Exception:
            log(f"Warning: Could not select Financial Year: {e}")


def select_status_discrepancy(page, log_callback=None):
    """
    Select Application Status = DISCREPANCY (value "0") from select[name="status"].
    """
    def log(msg):
        if log_callback:
            log_callback(msg)

    log("Selecting Application Status: DISCREPANCY")

    try:
        status_dropdown = page.locator("select[name='status']")
        status_dropdown.wait_for(state="visible", timeout=8000)
        status_dropdown.select_option(value=STATUS_DISCREPANCY)
        log("Application Status 'DISCREPANCY' selected")
    except Exception as e:
        log(f"Warning: Could not select status: {e}")


def click_proceed(page, log_callback=None):
    """
    Click the PROCEED button (button.btn.genGreenBtn).
    """
    def log(msg):
        if log_callback:
            log_callback(msg)

    log("Clicking PROCEED...")

    try:
        proceed_btn = page.locator("button.btn.genGreenBtn:has-text('PROCEED')").first
        proceed_btn.wait_for(state="visible", timeout=8000)
        proceed_btn.click()
        page.wait_for_timeout(150)
        log("PROCEED clicked — loading discrepancy list")
    except Exception as e:
        # Fallback: broader selector
        try:
            page.locator("button:has-text('PROCEED')").first.click()
            page.wait_for_timeout(150)
            log("PROCEED clicked (fallback)")
        except Exception:
            raise RuntimeError(f"Could not click PROCEED button: {e}")


def setup_reconciliation_page(page, financial_year: str, log_callback=None):
    """
    Full setup sequence: navigate → select FY → select status → PROCEED.
    Convenience function that calls all navigation steps in order.
    """
    navigate_to_reconciliation(page, log_callback=log_callback)
    select_financial_year(page, financial_year, log_callback=log_callback)
    select_status_discrepancy(page, log_callback=log_callback)
    click_proceed(page, log_callback=log_callback)
