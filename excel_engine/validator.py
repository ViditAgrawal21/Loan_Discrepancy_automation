"""
Excel validator for ensuring data integrity before discrepancy automation.
Checks mandatory fields and data formats.
Single sheet only — no Survey_Data cross-checks needed.
"""

from utils.constants import Sheet1Col


def validate_row(sheet1_ws, row: int) -> list:
    """
    Validate a single row from Sheet1.
    Returns a list of error messages. Empty list = valid.
    Row is 1-based (row 2 = first data row).
    """
    errors = []

    # ── Account Number is mandatory for discrepancy search ──
    account = sheet1_ws.cell(row=row, column=Sheet1Col.ACCOUNT).value
    if account is None or str(account).strip() == "":
        errors.append(f"Row {row}: Account Number (D) is empty — required for discrepancy search")

    return errors
