# Loan_Discrepancy_automation

Automates the discrepancy management workflow on [fasalrin.gov.in](https://fasalrin.gov.in) — reads account data from Excel, searches for each account on the reconciliation portal, updates discrepancy fields, submits, and writes the loan application number back to Excel.

## Setup

```bash
pip install -r requirements.txt
python -m playwright install chromium
```

## Run

```bash
python main.py
```

## Build (standalone .exe)

```bash
python build.py
```
