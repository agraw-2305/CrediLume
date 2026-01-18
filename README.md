CrediLume — Loan Eligibility & EMI Calculator

CrediLume is a Flask-based web application that provides loan eligibility prediction, EMI estimation, and affordability checks using a trained machine learning model.
It also supports optional AI-generated guidance using Google Gemini when configured.

Overview

CrediLume combines:

Loan eligibility prediction (machine learning)

EMI calculation and affordability analysis (DTI-based)

Optional AI-powered guidance via Google Gemini

JSON-based endpoints for dynamic UI updates

The application is designed to remain fully functional even when AI features are disabled.

Features

Predicts loan approval likelihood using a trained ML model

Calculates EMI, total interest, and total repayment

Applies debt-to-income (DTI) guardrails

Supports both HTML form submission and JSON-based API usage

Graceful fallback behavior when AI features are not enabled

Requirements

Python 3.10 or higher

Trained ML artifacts:

loan_model.pkl

features.pkl

Optional

GEMINI_API_KEY environment variable (enables AI guidance)

If no Gemini key is set, the app automatically uses built-in fallback logic.

Quick Start (Windows)
1. Create and activate a virtual environment

PowerShell

python -m venv .venv
& .\.venv\Scripts\Activate.ps1

2. Install dependencies
pip install -r requirements.txt

3. (Optional) Enable Gemini AI
$env:GEMINI_API_KEY="YOUR_KEY_HERE"


GOOGLE_API_KEY is also supported, but GEMINI_API_KEY is recommended.
Do not commit API keys to version control.

4. Run the application
python app.py


Open in browser:
http://127.0.0.1:5000

You may also use run.ps1 or run.bat for convenience.

Deployment

Pushing this repository to GitHub does not automatically make the app publicly accessible.
To obtain a public URL, deploy it to a hosting platform.

Option A: Render (recommended)

This repository includes a render.yaml configuration.

Go to Render → New + → Web Service

Connect your GitHub repository

Render will automatically detect:

Build command: pip install -r requirements.txt

Start command:
gunicorn app:app --bind 0.0.0.0:$PORT

Set environment variables:

FLASK_DEBUG=0

FLASK_RELOADER=0

GEMINI_API_KEY (optional)

Deploy and open the generated URL

Note:
loan_model.pkl and features.pkl must be present in the project root, as they are loaded at runtime.

Option B: Other Platforms (Railway, Fly.io, Heroku-like)

Use the same start command:

gunicorn app:app --bind 0.0.0.0:$PORT

API Routes

GET / — Web UI

GET /health — Health check (returns ok)

POST /predict — Form-based submission (HTML response)

POST /predict_json — JSON API endpoint (AJAX / dynamic UI)

Project Structure
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

Troubleshooting

ML artifacts not found
Ensure loan_model.pkl and features.pkl exist in the project root.

Gemini AI not responding
Confirm GEMINI_API_KEY is set in the environment where Flask is running.

Disclaimer

This project provides estimates and informational output only.
It does not constitute financial advice. Loan eligibility, interest rates, and repayment terms vary by lender and jurisdiction.
