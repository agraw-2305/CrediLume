# CrediLume — Loan Eligibility & EMI Calculator

CrediLume is a Flask web app that combines:

- Loan eligibility prediction (ML model)
- EMI estimation and basic affordability checks (DTI)
- Optional AI-generated guidance (Google Gemini), if configured

## Features

- Predict loan approval probability (based on a trained model)
- Estimate EMI, total interest, and total repayment
- Debt-to-income (DTI) guardrails
- JSON API endpoint for AJAX-based UI updates

## Requirements

- Python 3.10+ (the backend uses modern type hints)
- A trained model file and feature list:
  - `loan_model.pkl`
  - `features.pkl`

Optional:

- `GEMINI_API_KEY` environment variable (enables AI advice)

## Quick start (Windows)

1. Create and activate a virtual environment

   - PowerShell:
     - `python -m venv .venv`
     - `& .\.venv\Scripts\Activate.ps1`

2. Install dependencies

   - `pip install -r requirements.txt`

3. (Optional) Enable Gemini AI

   - PowerShell:
     - `$env:GEMINI_API_KEY="YOUR_KEY_HERE"`

   Keep keys out of git history. Do not commit API keys.

4. Run the server

   - `python app.py`
   - Open `http://127.0.0.1:5000`

Tip: You can also use `run.ps1` / `run.bat` if you prefer one-click start.

## API routes

- `GET /` — UI
- `GET /health` — health check (returns `ok`)
- `POST /predict` — form submit; renders `index.html` with results
- `POST /predict_json` — form submit; returns JSON for dynamic rendering

## Project structure

```
.
├── app.py
├── loan_fin.py
├── requirements.txt
├── run.bat
├── run.ps1
├── static/
│   └── calculator.js
└── templates/
    ├── index.html
    └── premium.html
```

## Troubleshooting

- "Failed to load ML artifacts": ensure `loan_model.pkl` and `features.pkl` exist in the project root.
- Gemini not working: confirm `GEMINI_API_KEY` is set in the environment where you launched Flask.

## Disclaimer

This project provides estimates and informational output only and is not financial advice. Loan terms vary by lender and region.