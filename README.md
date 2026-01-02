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

Note: The app works without any Gemini key. If no key is set, AI endpoints return built-in fallback guidance.

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

    Compatibility: `GOOGLE_API_KEY` is also accepted, but `GEMINI_API_KEY` is recommended.

   Keep keys out of git history. Do not commit API keys.

4. Run the server

   - `python app.py`
   - Open `http://127.0.0.1:5000`

Tip: You can also use `run.ps1` / `run.bat` if you prefer one-click start.

## Hackathon submission (ZIP)

If you're submitting as a zip file, see `SUBMISSION.md` for exactly what to include and the judge run steps.

## Deploy (public URL)

Pushing to GitHub does **not** automatically make a Flask app publicly accessible. To get a public URL, deploy it to a hosting platform.

### Option A: Render (recommended)

This repo includes `render.yaml`, so deployment is mostly click-through.

1. Go to Render → **New +** → **Web Service**
2. Connect your GitHub repo `CrediLume`
3. Render will detect `render.yaml` and use:
   - Build: `pip install -r requirements.txt`
   - Start: `gunicorn app:app --bind 0.0.0.0:$PORT`
4. Set environment variables:
   - `FLASK_DEBUG=0`
   - `FLASK_RELOADER=0`
   - `GEMINI_API_KEY` (optional)
5. Deploy → open the provided Render URL

Important: `loan_model.pkl` and `features.pkl` must be present in the deployed app (they are loaded from the project root at runtime).

### Option B: Railway / Fly.io / Heroku-like platforms

Use the same start command:

- `gunicorn app:app --bind 0.0.0.0:$PORT`

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