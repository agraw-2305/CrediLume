🌟 CrediLume
💡 Loan Eligibility & EMI Calculator

✨ Overview

CrediLume is a Flask-based web application that helps users understand
loan eligibility, EMI, and affordability using a trained machine learning model.

It also supports optional AI-powered guidance via Google Gemini, while remaining fully functional without any AI configuration.

🔍 What CrediLume Offers

🤖 ML-based loan eligibility prediction

💸 EMI, interest & total repayment calculation

📊 Debt-to-Income (DTI) affordability checks

🧠 Explainable outcomes (not just yes/no)

⚡ JSON API endpoints for dynamic UI updates

🔐 Optional Gemini AI guidance (with fallback logic)

🛠️ Tech Stack
Layer	Technology
Backend	Flask (Python)
Frontend	HTML, CSS, JavaScript
ML	Scikit-learn
Server	Gunicorn
Hosting	Render
📁 Project Structure
.
├── app.py
├── loan_fin.py
├── loan_model.pkl
├── features.pkl
├── requirements.txt
├── run.bat
├── run.ps1
├── static/
│   └── calculator.js
└── templates/
    ├── index.html
    └── premium.html

🚀 Quick Start (Windows)
1️⃣ Create a virtual environment
python -m venv .venv
& .\.venv\Scripts\Activate.ps1

2️⃣ Install dependencies
pip install -r requirements.txt

3️⃣ (Optional) Enable Gemini AI ✨
$env:GEMINI_API_KEY="YOUR_KEY_HERE"


🔐 Keep API keys out of git history
GOOGLE_API_KEY is also supported

4️⃣ Run the app ▶️
python app.py


🌐 Open: http://127.0.0.1:5000

🌍 Deployment
⭐ Render (Recommended)

This repository includes a render.yaml file.

Build: pip install -r requirements.txt

Start:

gunicorn app:app --bind 0.0.0.0:$PORT


Environment variables:

FLASK_DEBUG=0

FLASK_RELOADER=0

GEMINI_API_KEY (optional)

📌 Ensure loan_model.pkl and features.pkl are present at runtime.

🔌 API Endpoints
Method	Route	Description
GET	/	Web UI
GET	/health	Health check
POST	/predict	Form-based prediction
POST	/predict_json	JSON API response
🧪 Troubleshooting

❌ ML model not loading
→ Ensure loan_model.pkl & features.pkl exist in project root

🤖 Gemini AI not working
→ Confirm GEMINI_API_KEY is set in your environment

⚠️ Disclaimer

📌 This project provides estimates and informational output only.
It does not constitute financial advice. Loan terms vary by lender and region.

🤝 Contributing

Pull requests and suggestions are welcome!
Fork the repo and feel free to improve or extend functionality.

📄 License

📝 MIT License
