# CrediLume — Zip Submission Guide (Hackathon)

## What to include in the ZIP
Include these files/folders (they are needed to run):

- `app.py`
- `loan_fin.py`
- `requirements.txt`
- `run.ps1` / `run.bat`
- `templates/`
- `static/`
- `loan_model.pkl`
- `features.pkl`
- `README.md`

## What NOT to include
Do **not** include:

- `.venv/`
- `__pycache__/`
- `*.pyc`
- Any API keys or secrets

## Judge/Reviewer run steps (Windows)
1. Extract the zip.
2. Open PowerShell in the extracted folder.
3. Create and activate a virtual environment:
   - `python -m venv .venv`
   - `& .\.venv\Scripts\Activate.ps1`
4. Install dependencies:
   - `pip install -r requirements.txt`
5. Run the app:
   - `python app.py`
6. Open:
   - `http://127.0.0.1:5000`

## Gemini AI (optional)
The app works **without** Gemini.

If someone wants the AI features, they can set their own key before running:

- PowerShell:
  - `$env:GEMINI_API_KEY="THEIR_KEY_HERE"`

(Compatibility: `GOOGLE_API_KEY` is also accepted, but `GEMINI_API_KEY` is recommended.)
