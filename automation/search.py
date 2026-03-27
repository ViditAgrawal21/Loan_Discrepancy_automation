"""
Search automation — finds the account in the discrepancy list and clicks
MANAGE DISCREPANCIES.

Flow:
  1. Type account number into the search input (input[type="search"])
  2. Wait for the table to filter
  3. Find the row with the matching account number (6th column)
  4. Click MANAGE DISCREPANCIES button on that row
"""


def search_account(page, account_number: str, log_callback=None):
    """
    Search for an account number in the discrepancy list.

    Types the account number into the search field and waits for
    the table to filter results.
    """
    def log(msg):
        if log_callback:
            log_callback(msg)

    log(f"Searching for Account: {account_number}")

    try:
        search_input = page.locator("input[type='search']").first
        search_input.wait_for(state="visible", timeout=10000)

        # Clear any existing text and type the account number
        search_input.fill("")
        page.wait_for_timeout(200)
        search_input.fill(account_number)
        page.wait_for_timeout(1000)  # Wait for table to filter

        log(f"Search entered: {account_number}")
    except Exception as e:
        raise RuntimeError(f"Could not find or use search input: {e}")


def click_manage_discrepancies(page, account_number: str, log_callback=None):
    """
    Click the MANAGE DISCREPANCIES button for the matching account row.

    Strategy:
      1. First try: find the table row containing the account number text,
         then click the MANAGE DISCREPANCIES button within that row.
      2. Fallback: click the first visible MANAGE DISCREPANCIES button
         (since search should have already filtered to the correct row).
    """
    def log(msg):
        if log_callback:
            log_callback(msg)

    log("Clicking MANAGE DISCREPANCIES...")

    # Strategy 1: Find the row with matching account number and click its button
    try:
        # Look for a table row that contains the account number text
        rows = page.locator("table tbody tr").all()
        for row in rows:
            try:
                # Account number is in the 6th column (index 5)
                cells = row.locator("td").all()
                if len(cells) >= 6:
                    cell_text = cells[5].inner_text().strip()
                    if account_number in cell_text:
                        manage_btn = row.locator(
                            "button:has-text('MANAGE DISCREPANCIES')"
                        ).first
                        if manage_btn.is_visible(timeout=2000):
                            manage_btn.click()
                            page.wait_for_timeout(1000)
                            log(f"MANAGE DISCREPANCIES clicked for account {account_number}")
                            return
            except Exception:
                continue
    except Exception:
        pass

    # Strategy 2: Fallback — click the first visible MANAGE DISCREPANCIES button
    try:
        manage_btn = page.locator(
            "button.btn.genLinkBtn.genCyanLinkbtn:has-text('MANAGE DISCREPANCIES')"
        ).first
        manage_btn.wait_for(state="visible", timeout=10000)
        manage_btn.click()
        page.wait_for_timeout(1000)
        log("MANAGE DISCREPANCIES clicked (first visible button)")
        return
    except Exception:
        pass

    # Strategy 3: Broadest fallback
    try:
        page.locator("button:has-text('MANAGE DISCREPANCIES')").first.click()
        page.wait_for_timeout(1000)
        log("MANAGE DISCREPANCIES clicked (broadest fallback)")
        return
    except Exception as e:
        raise RuntimeError(
            f"Could not click MANAGE DISCREPANCIES for account {account_number}: {e}"
        )


def search_and_manage(page, account_number: str, log_callback=None):
    """
    Convenience function: search for account → click MANAGE DISCREPANCIES.
    """
    search_account(page, account_number, log_callback=log_callback)
    click_manage_discrepancies(page, account_number, log_callback=log_callback)
