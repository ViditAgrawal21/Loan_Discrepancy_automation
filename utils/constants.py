"""
Constants for the Fasal Rin Discrepancy Management Automation.
All values match the portal at https://fasalrin.gov.in exactly.
"""

# ═══════════════════════════════════════════════════════════════
# Portal URLs
# ═══════════════════════════════════════════════════════════════
LOGIN_URL = "https://fasalrin.gov.in/login"
RECONCILIATION_URL = "https://fasalrin.gov.in/reconciliation/loan-application"
WELCOME_URL = "https://fasalrin.gov.in/welcome"

# ═══════════════════════════════════════════════════════════════
# Application Status dropdown values (select[name="status"])
# ═══════════════════════════════════════════════════════════════
STATUS_DISCREPANCY = "0"
STATUS_DROPPED = "4"
STATUS_DRAFT = "-2"
STATUS_SUBMITTED = "1"
STATUS_REJECTED = "3"
STATUS_APPROVED = "2"

# ═══════════════════════════════════════════════════════════════
# Excel Column Indices (1-based for openpyxl) — Sheet1 only
# ═══════════════════════════════════════════════════════════════

class Sheet1Col:
    """Column indices for Sheet1 (1-based)."""
    SR = 1                        # A - Serial Number
    AADHAAR = 2                   # B - Aadhaar Number
    DOB = 3                       # C - Date of Birth
    ACCOUNT = 4                   # D - Account Number *
    NAME = 5                      # E - Name
    VILLAGE = 6                   # F - Village
    LOAN_SECTION_DATE = 7         # G - Loan Section Date
    LOAN_SANCTIONED = 8           # H - Loan Sanctioned (INR)
    KCC_DRAWING_LIMIT = 9         # I - KCC Drawing Limit For Current FY (INR)
    LOAN_SANCTIONED_ACTIVITY = 10 # J - Loan Sanctioned for Activity (INR)
    APPLICATION_ID = 11           # K - Application Id (OUTPUT)
    AADHAAR_VALIDATION = 12       # L - Aadhaar validation status
    NAME_AS_PER_AADHAAR = 13      # M - Name (As Per Aadhaar)
    AADHAAR_NO_FULL = 14          # N - Aadhaar No.
    NAME_AS_PER_PASSBOOK = 15     # O - Name As Per Pass Book
    DOB_FORM = 16                 # P - DOB for form
    GENDER = 17                   # Q - Gender
    MOBILE = 18                   # R - Mobile No.
    SOCIAL_CATEGORY = 19          # S - Social Category
    FARMER_CATEGORY = 20          # T - Farmer Category
    FARMER_TYPE = 21              # U - Farmer Type
    PRIMARY_OCCUPATION = 22       # V - Primary Occupation
    RELATIVE_TYPE = 23            # W - Relative Type
    RELATIVE_NAME = 24            # X - Relative Name
    STATE = 25                    # Y - State
    DISTRICT = 26                 # Z - District
    BLOCK_SUBDISTRICT = 27        # AA - Block/Subdistrict
    VILLAGE_RESIDENTIAL = 28      # AB - Village (Residential)
    PINCODE = 29                  # AC - Pincode
    SEASON = 30                   # AD - Season

    # Mandatory columns for discrepancy (Account Number is required)
    MANDATORY = [ACCOUNT]


# ═══════════════════════════════════════════════════════════════
# Form Field Mapping: Excel key → HTML input name attribute
# Only fields with non-empty Excel values will be updated.
# ═══════════════════════════════════════════════════════════════

FORM_FIELD_MAP = {
    "name": "beneficiaryName",
    "name_as_per_passbook": "beneficiaryPassbookName",
}

# ═══════════════════════════════════════════════════════════════
# Profile Configuration Dropdowns
# ═══════════════════════════════════════════════════════════════

FINANCIAL_YEARS = [
    "2022-2023",
    "2023-2024",
    "2024-2025",
    "2025-2026",
    "2026-2027",
]

APPLICATION_TYPES = ["Normal", "PVTG"]

# ═══════════════════════════════════════════════════════════════
# States (from portal)
# ═══════════════════════════════════════════════════════════════

STATES = [
    "ANDAMAN AND NICOBAR ISLANDS",
    "ANDHRA PRADESH",
    "ARUNACHAL PRADESH",
    "ASSAM",
    "BIHAR",
    "CHANDIGARH",
    "CHHATTISGARH",
    "DADRA & NAGAR HAVELI",
    "DAMAN AND DIU",
    "DELHI",
    "GOA",
    "GUJARAT",
    "HARYANA",
    "HIMACHAL PRADESH",
    "JAMMU AND KASHMIR",
    "JHARKHAND",
    "KARNATAKA",
    "KERALA",
    "LADAKH",
    "LAKSHADWEEP",
    "MADHYA PRADESH",
    "MAHARASHTRA",
    "MANIPUR",
    "MEGHALAYA",
    "MIZORAM",
    "NAGALAND",
    "ODISHA",
    "PUDUCHERRY",
    "PUNJAB",
    "RAJASTHAN",
    "SIKKIM",
    "TAMIL NADU",
    "TELANGANA",
    "THE DADRA AND NAGAR HAVELI AND DAMAN AND DIU",
    "TRIPURA",
    "UTTAR PRADESH",
    "UTTARAKHAND",
    "WEST BENGAL",
]
