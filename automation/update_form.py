"""
Update form automation — handles the discrepancy update flow:
  1. Click UPDATE button
  2. Fill only fields that have data in Excel (using JS nativeInputValueSetter)
  3. Click UPDATE & CONTINUE
  4. Click OK on the confirmation modal

Only fields present in the Excel with non-empty values are overwritten.
Existing portal values for empty Excel cells remain untouched.
"""

from utils.constants import FORM_FIELD_MAP


def _fill_react_input(page, input_name: str, value: str):
    """
    Fill a React-controlled input field using the nativeInputValueSetter
    trick. This bypasses React's synthetic event system and correctly
    triggers state updates.
    """
    page.evaluate("""([inputName, val]) => {
        const el = document.querySelector(`input[name='${inputName}']`);
        if (el) {
            const setter = Object.getOwnPropertyDescriptor(
                window.HTMLInputElement.prototype, 'value').set;
            setter.call(el, val);
            el.dispatchEvent(new Event('input',  { bubbles: true }));
            el.dispatchEvent(new Event('change', { bubbles: true }));
        }
    }""", [input_name, value])


def click_update(page, log_callback=None):
    """
    Click the UPDATE button (button.btn.genDarkCyanBtn with text "UPDATE").
    This opens the editable form for the discrepancy record.
    """
    def log(msg):
        if log_callback:
            log_callback(msg)

    log("Clicking UPDATE...")

    try:
        # Specific: button with exact text UPDATE (not UPDATE & CONTINUE)
        update_btn = page.locator(
            "button.btn.genDarkCyanBtn"
        ).filter(has_text="UPDATE").first

        # Make sure we're not clicking "UPDATE & CONTINUE"
        all_btns = page.locator("button.btn.genDarkCyanBtn").all()
        for btn in all_btns:
            try:
                btn_text = btn.inner_text().strip()
                if btn_text == "UPDATE":
                    btn.wait_for(state="visible", timeout=10000)
                    btn.click()
                    page.wait_for_timeout(800)
                    log("UPDATE clicked — form is now editable")
                    return
            except Exception:
                continue

        # Fallback: click the first button with text UPDATE
        update_btn.wait_for(state="visible", timeout=10000)
        update_btn.click()
        page.wait_for_timeout(800)
        log("UPDATE clicked (fallback)")

    except Exception as e:
        raise RuntimeError(f"Could not click UPDATE button: {e}")


def fill_discrepancy_fields(page, row_data: dict, log_callback=None):
    """
    Fill fields in the discrepancy form using data from Excel.
    Only fields with non-empty values in Excel are updated.
    Uses the FORM_FIELD_MAP from constants to map Excel keys → HTML input names.

    Args:
        page: Playwright page object.
        row_data: Dictionary from excel_engine.reader.read_row().
        log_callback: Logging function.
    """
    def log(msg):
        if log_callback:
            log_callback(msg)

    log("Updating discrepancy fields...")
    fields_updated = 0

    for excel_key, input_name in FORM_FIELD_MAP.items():
        value = row_data.get(excel_key, "")
        if value:  # Only fill if Excel has data
            try:
                # Check if the input exists and is visible on the page
                input_el = page.locator(f"input[name='{input_name}']").first
                if input_el.is_visible(timeout=2000):
                    _fill_react_input(page, input_name, value)
                    page.wait_for_timeout(150)
                    log(f"  Updated {input_name}: {value}")
                    fields_updated += 1
                else:
                    log(f"  Skipped {input_name} — field not visible on page")
            except Exception as e:
                log(f"  Warning: Could not fill {input_name}: {e}")

    if fields_updated == 0:
        log("  No fields updated (no matching Excel data found)")
    else:
        log(f"  {fields_updated} field(s) updated")


def click_update_and_continue(page, log_callback=None):
    """
    Click the UPDATE & CONTINUE button (button.btn.genDarkCyanBtn).
    """
    def log(msg):
        if log_callback:
            log_callback(msg)

    log("Clicking UPDATE & CONTINUE...")

    try:
        btn = page.locator(
            "button.btn.genDarkCyanBtn:has-text('UPDATE & CONTINUE')"
        ).first
        btn.wait_for(state="visible", timeout=10000)
        btn.scroll_into_view_if_needed()
        page.wait_for_timeout(200)
        btn.click()
        page.wait_for_timeout(1000)
        log("UPDATE & CONTINUE clicked")
    except Exception as e:
        # Fallback: broader selector
        try:
            page.locator("button:has-text('UPDATE & CONTINUE')").first.click()
            page.wait_for_timeout(1000)
            log("UPDATE & CONTINUE clicked (fallback)")
        except Exception:
            raise RuntimeError(f"Could not click UPDATE & CONTINUE: {e}")


def click_ok_modal(page, log_callback=None):
    """
    Click the OK button on the confirmation modal
    (button.existAccountBtn.outline-btn with text "OK").
    """
    def log(msg):
        if log_callback:
            log_callback(msg)

    log("Handling confirmation modal...")

    try:
        ok_btn = page.locator("button.existAccountBtn.outline-btn:has-text('OK')").first
        ok_btn.wait_for(state="visible", timeout=10000)
        ok_btn.click()
        page.wait_for_timeout(800)
        log("OK clicked on confirmation modal")
    except Exception:
        # Fallback: try any OK button in a visible modal
        try:
            modal = page.locator("div.modal.show[role='dialog']").first
            ok_btn = modal.locator("button:has-text('OK')").first
            if ok_btn.is_visible(timeout=3000):
                ok_btn.click()
                page.wait_for_timeout(800)
                log("OK clicked (modal fallback)")
        except Exception:
            # Broader fallback: any OK button on the page
            try:
                page.locator("button:has-text('OK')").first.click()
                page.wait_for_timeout(800)
                log("OK clicked (broadest fallback)")
            except Exception as e:
                log(f"Warning: No OK modal found — may not be required: {e}")


def update_discrepancy(page, row_data: dict, log_callback=None):
    """
    Full update sequence: UPDATE → fill fields → UPDATE & CONTINUE → OK modal.
    Convenience function that handles the entire update flow.
    """
    click_update(page, log_callback=log_callback)
    fill_discrepancy_fields(page, row_data, log_callback=log_callback)
    click_update_and_continue(page, log_callback=log_callback)
    click_ok_modal(page, log_callback=log_callback)
