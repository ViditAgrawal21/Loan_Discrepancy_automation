"""
Search automation — finds the account in the discrepancy list and clicks
MANAGE DISCREPANCIES.

Flow:
  1. Type account number into the search input (input[type="search"])
  2. Wait for the table to filter
  3. Detect "no records found" → raise AccountNotFoundError
  4. Find the row with the matching account number (6th column)
  5. Click MANAGE DISCREPANCIES button on that row
"""


class AccountNotFoundError(Exception):
    """Raised when the searched account number is not found in the list."""
    pass


def _check_no_records(page):
    """
    Check if the table shows a 'no records' / 'no data' message after search.
    Returns True if no records found.
    """
    try:
        # Check the full page text for any "no record" variant
        body_text = page.locator("table").first.inner_text().lower()
        no_record_phrases = [
            "no record",         # matches "No record(s) found", "No records found", etc.
            "no data available",
            "no matching",
        ]
        for phrase in no_record_phrases:
            if phrase in body_text:
                return True
    except Exception:
        pass

    # Also check: Total Count: 0
    try:
        count_text = page.locator("text=/Total Count/i").first.inner_text()
        if "0" in count_text:
            return True
    except Exception:
        pass

    # Also check: if table has zero visible data rows
    try:
        visible_rows = page.locator("table tbody tr").all()
        if len(visible_rows) == 0:
            return True
        # If the only row contains "no record" text, still no data
        if len(visible_rows) == 1:
            row_text = visible_rows[0].inner_text().lower()
            if "no record" in row_text or "no data" in row_text:
                return True
    except Exception:
        pass

    return False


def search_account(page, account_number: str, log_callback=None):
    """
    Search for an account number in the discrepancy list.
    Raises AccountNotFoundError if no matching records appear.
    """
    def log(msg):
        if log_callback:
            log_callback(msg)

    log(f"Searching for Account: {account_number}")

    try:
        search_input = page.locator("input[type='search']").first
        search_input.wait_for(state="visible", timeout=8000)

        # Clear and type
        search_input.fill("")
        search_input.fill(account_number)

        # Click the search icon button to trigger the search
        search_btn = page.locator(".searchBar button.btn-secondary").first
        search_btn.click()
        page.wait_for_timeout(300)  # Wait for table results to load

        log(f"Search entered & clicked: {account_number}")
    except Exception as e:
        raise RuntimeError(f"Could not find or use search input: {e}")

    # Check if account was found
    if _check_no_records(page):
        msg = f"ACCOUNT NOT FOUND: {account_number} — no matching records in discrepancy list"
        log(f"ERROR: {msg}")
        raise AccountNotFoundError(msg)


def click_manage_discrepancies(page, account_number: str, log_callback=None):
    """
    Click the MANAGE DISCREPANCIES button ONLY for the row that contains
    the exact account number. Never clicks a button on a different account's row.
    """
    def log(msg):
        if log_callback:
            log_callback(msg)

    log("Clicking MANAGE DISCREPANCIES...")

    # ONLY click on the row that actually contains our account number
    try:
        rows = page.locator("table tbody tr").all()
        for row in rows:
            try:
                # Check ALL cells in the row for the account number
                row_text = row.inner_text()
                if account_number in row_text:
                    manage_btn = row.locator(
                        "button:has-text('MANAGE DISCREPANCIES')"
                    ).first
                    if manage_btn.is_visible(timeout=2000):
                        manage_btn.click()
                        log(f"MANAGE DISCREPANCIES clicked for account {account_number}")
                        return
            except Exception:
                continue
    except Exception:
        pass

    # If we got here, the account number was NOT found in any row
    raise AccountNotFoundError(
        f"ACCOUNT NOT FOUND: {account_number} — no row with this account in the discrepancy list"
    )


def search_and_manage(page, account_number: str, log_callback=None):
    """
    Convenience function: search for account → click MANAGE DISCREPANCIES.
    Raises AccountNotFoundError if the account is not in the list.
    """
    search_account(page, account_number, log_callback=log_callback)
    click_manage_discrepancies(page, account_number, log_callback=log_callback)
