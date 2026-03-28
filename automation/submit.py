"""
Submit automation — handles the final submission flow:
  1. Click Preview button (Term Loan Details tab)
  2. Check the declaration checkbox
  3. Click SUBMIT
  4. Click CONFIRM on the confirmation dialog
  5. Extract loan application number from the success modal
  6. Click OK on the success modal

After submission, the Application ID is extracted from the success
modal's <h4> tag containing "Loan application XXXX submitted successfully".
"""

import re


def click_preview(page, log_callback=None):
    """
    Click the Preview button (button.btn.genPurpleBtn with text "Preview").
    """
    def log(msg):
        if log_callback:
            log_callback(msg)

    log("Clicking Preview...")

    try:
        preview_btn = page.locator(
            "button.btn.genPurpleBtn:has-text('Preview')"
        ).first
        preview_btn.wait_for(state="visible", timeout=10000)
        preview_btn.scroll_into_view_if_needed()
        preview_btn.click()
        page.wait_for_timeout(100)
        log("Preview opened")
    except Exception as e:
        # Fallback: broader selector
        try:
            page.locator("button:has-text('Preview')").first.click()
            page.wait_for_timeout(100)
            log("Preview opened (fallback)")
        except Exception:
            raise RuntimeError(f"Could not click Preview button: {e}")


def check_declaration(page, log_callback=None):
    """
    Check the declaration checkbox (input#declarationText[type="checkbox"]).
    """
    def log(msg):
        if log_callback:
            log_callback(msg)

    log("Checking declaration checkbox...")

    try:
        checkbox = page.locator("input#declarationText[type='checkbox']")
        checkbox.wait_for(state="visible", timeout=8000)

        if not checkbox.is_checked():
            checkbox.scroll_into_view_if_needed()
            checkbox.check()
            log("Declaration checkbox checked")
        else:
            log("Declaration checkbox already checked")
    except Exception as e:
        # Fallback: try clicking via JS
        try:
            page.evaluate("""() => {
                const cb = document.querySelector('#declarationText');
                if (cb && !cb.checked) {
                    cb.click();
                }
            }""")
            log("Declaration checkbox checked (JS fallback)")
        except Exception:
            raise RuntimeError(f"Could not check declaration: {e}")


def click_submit(page, log_callback=None):
    """
    Click the SUBMIT button (button.btn.genGreenBtn with text "SUBMIT").
    """
    def log(msg):
        if log_callback:
            log_callback(msg)

    log("Clicking SUBMIT...")

    try:
        submit_btn = page.locator(
            "button.btn.genGreenBtn:has-text('SUBMIT')"
        ).first
        submit_btn.wait_for(state="visible", timeout=8000)
        submit_btn.scroll_into_view_if_needed()
        submit_btn.click()
        page.wait_for_timeout(100)
        log("SUBMIT clicked")
    except Exception as e:
        try:
            page.locator("button:has-text('SUBMIT')").first.click()
            page.wait_for_timeout(100)
            log("SUBMIT clicked (fallback)")
        except Exception:
            raise RuntimeError(f"Could not click SUBMIT button: {e}")


def click_confirm(page, log_callback=None):
    """
    Click the CONFIRM button (button.green-btn with text "CONFIRM")
    on the confirmation dialog.
    """
    def log(msg):
        if log_callback:
            log_callback(msg)

    log("Clicking CONFIRM...")

    try:
        confirm_btn = page.locator("button.green-btn:has-text('CONFIRM')").first
        confirm_btn.wait_for(state="visible", timeout=8000)
        confirm_btn.click()
        page.wait_for_timeout(150)
        log("CONFIRM clicked")
    except Exception:
        try:
            page.locator("button:has-text('CONFIRM')").first.click()
            page.wait_for_timeout(150)
            log("CONFIRM clicked (fallback)")
        except Exception as e:
            raise RuntimeError(f"Could not click CONFIRM button: {e}")


def extract_application_id(page, log_callback=None) -> str:
    """
    Extract the loan application number from the success modal.

    The success modal contains an <h4> tag with text like:
    "Loan application 2327051671055072643 submitted successfully"

    Returns:
        The loan application number string, or 'UNKNOWN' if not found.
    """
    def log(msg):
        if log_callback:
            log_callback(msg)

    log("Extracting Loan Application Number...")

    page.wait_for_timeout(100)

    # Strategy 1: Look for <h4> in a visible modal with the success pattern
    try:
        modal_selectors = [
            "div.modal.show .modal-body h4",
            "div.modal.show h4",
            ".swal2-html-container h4",
            ".swal2-popup h4",
        ]
        for selector in modal_selectors:
            try:
                elements = page.locator(selector).all()
                for el in elements:
                    text = el.inner_text().strip()
                    app_id = _extract_id_from_success_text(text)
                    if app_id:
                        log(f"Loan Application Number: {app_id}")
                        return app_id
            except Exception:
                continue
    except Exception:
        pass

    # Strategy 2: Look for any text containing "Loan application" pattern
    try:
        elements = page.locator("text=/Loan application/i").all()
        for el in elements:
            try:
                text = el.inner_text().strip()
                app_id = _extract_id_from_success_text(text)
                if app_id:
                    log(f"Loan Application Number: {app_id}")
                    return app_id
            except Exception:
                continue
    except Exception:
        pass

    # Strategy 3: Search modal body text broadly
    try:
        modal_body_selectors = [
            "div.modal.show .modal-body",
            "div.modal.show",
            ".swal2-popup",
        ]
        for selector in modal_body_selectors:
            try:
                el = page.locator(selector).first
                if el.is_visible(timeout=2000):
                    text = el.inner_text()
                    app_id = _extract_id_from_success_text(text)
                    if app_id:
                        log(f"Loan Application Number: {app_id}")
                        return app_id
            except Exception:
                continue
    except Exception:
        pass

    # Strategy 4: Search full page body text
    try:
        body_text = page.locator("body").inner_text()
        app_id = _extract_id_from_success_text(body_text)
        if app_id:
            log(f"Loan Application Number: {app_id}")
            return app_id
    except Exception:
        pass

    log("WARNING: Could not extract Loan Application Number")
    return "UNKNOWN"


def click_ok_success_modal(page, log_callback=None):
    """
    Click OK on the success modal to dismiss it.
    """
    def log(msg):
        if log_callback:
            log_callback(msg)

    for txt in ["OK", "Close", "×"]:
        try:
            btn = page.locator(f"button:has-text('{txt}')").first
            if btn.is_visible(timeout=2000):
                btn.click()
                log(f"Success modal dismissed ({txt})")
                return
        except Exception:
            continue

    log("Warning: Could not dismiss success modal — may have closed automatically")


def submit_and_extract(page, log_callback=None) -> str:
    """
    Full submission sequence:
      Preview → Declaration → SUBMIT → CONFIRM → Extract ID → OK.
    Returns the extracted loan application number.
    """
    click_preview(page, log_callback=log_callback)
    check_declaration(page, log_callback=log_callback)
    click_submit(page, log_callback=log_callback)
    click_confirm(page, log_callback=log_callback)
    app_id = extract_application_id(page, log_callback=log_callback)
    click_ok_success_modal(page, log_callback=log_callback)
    return app_id


def _extract_id_from_success_text(text: str) -> str:
    """
    Extract loan application number from success text.

    Expected pattern: "Loan application 2327051671055072643 submitted successfully"
    Also handles variations like "Loan Application No: XXXX" etc.
    """
    if not text:
        return ""

    # Pattern 1: "Loan application XXXX submitted successfully"
    m = re.search(
        r"Loan\s+application\s+(\d{10,25})\s+submitted",
        text, re.IGNORECASE
    )
    if m:
        return m.group(1).strip()

    # Pattern 2: "Loan application XXXX" (without "submitted")
    m = re.search(
        r"Loan\s+application\s+(\d{10,25})",
        text, re.IGNORECASE
    )
    if m:
        return m.group(1).strip()

    # Pattern 3: Explicit label like "Application ID: XXXX"
    m = re.search(
        r"Application\s*(?:ID|Id|No\.?|Number)\s*[:\-–=\s]\s*(\d{10,25})",
        text, re.IGNORECASE
    )
    if m:
        return m.group(1).strip()

    # Pattern 4: Any long number (13+ digits)
    numbers = re.findall(r'\b(\d{13,25})\b', text)
    if numbers:
        return numbers[0]

    return ""
