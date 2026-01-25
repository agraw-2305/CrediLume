# 🌟 CrediLume
### 💡 Loan Eligibility & EMI Calculator

## ✨ Overview

**CrediLume** is a production-ready, Flask-based web application designed to help users assess **loan eligibility, affordability, and repayment details** using a trained machine learning model.

The application goes beyond a simple *approve / reject* response by providing **transparent financial insights**, including EMI breakdowns and debt-to-income (DTI) analysis. It also supports **optional AI-powered guidance via Google Gemini**, while remaining fully functional without any AI configuration.

## 🔍 What CrediLume Offers

**🤖 ML-based Loan Eligibility Prediction**  
Predicts approval likelihood using a trained Scikit-learn model.

**💸 EMI & Repayment Calculator**  
Calculates monthly EMI, total interest, and total repayment amount.

**📊 Debt-to-Income (DTI) Analysis**  
Evaluates affordability based on income and liabilities.

**🧠 Explainable Results**  
Provides reasoning and financial context instead of only binary outcomes.

**⚡ JSON API Support**  
Enables dynamic frontend updates and external integrations.

**🔐 Optional AI Guidance (Google Gemini)**  
Enhances explanations and user guidance with automatic fallback when AI is not configured.

## 🛠️ Tech Stack

| Layer | Technology |
|------|-----------|
| Backend | Flask (Python) |
| Frontend | HTML, CSS, JavaScript |
| Machine Learning | Scikit-learn |
| Server | Gunicorn |
| Hosting | Render |

## 📁 Project Structure

```text
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
```
## 🚀 Quick Start (Windows)

Step 1: Create and activate a virtual environment
```
python -m venv .venv
& .\.venv\Scripts\Activate.ps1
```
Step 2: Install dependencies
```
pip install -r requirements.txt
```
Step 4: Run the application
```
python app.py
```
Open in your browser:
http://127.0.0.1:5000

## 🌍 Deployment
Render (Recommended)

This repository includes a render.yaml configuration for deployment on Render.
Build Command
```
pip install -r requirements.txt
```
Start Command
```
gunicorn app:app --bind 0.0.0.0:$PORT
```
Environment Variables
```
FLASK_DEBUG=0
FLASK_RELOADER=0
GEMINI_API_KEY (optional)
```
Ensure loan_model.pkl and features.pkl are available at runtime.

## 🔌 API Endpoints

Method	    Endpoint	   Description
GET          	/	        Web UI
GET	        /health	        Health check
POST	    /predict	    Form-based prediction
POST	 /predict_json	    JSON API response


## 🧪 Troubleshooting

ML model not loading
Ensure loan_model.pkl and features.pkl exist in the project root.

Gemini AI not responding
Verify that GEMINI_API_KEY is correctly set in the environment.

## ⚠️ Disclaimer

CrediLume provides estimates for informational purposes only.
It does not constitute financial, legal, or lending advice.
Actual loan approval and terms depend on individual lenders and regional policies.

## 🤝 Contributing

Contributions are welcome.
Feel free to fork the repository, submit pull requests, or suggest improvements.

## 📄 License

This project is licensed under the MIT License.
You are free to use, modify, and distribute it with proper attribution.
