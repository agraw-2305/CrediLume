import warnings
warnings.filterwarnings("ignore")

from flask import Flask, render_template, request, jsonify
import os
import json
import urllib.request
import urllib.error
import pickle
import numpy as np
import google.generativeai as genai

# Configure Gemini API
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

app = Flask(__name__)

# Lazy-loaded ML artifacts (keeps server startup fast and avoids scipy/sklearn import stalls
# during Flask's debug reloader re-import).
model = None
FEATURE_NAMES = None
_ARTIFACT_ERROR = None


def _load_artifacts():
    global model, FEATURE_NAMES, _ARTIFACT_ERROR
    if model is not None and FEATURE_NAMES is not None:
        return

    if _ARTIFACT_ERROR is not None:
        raise RuntimeError(_ARTIFACT_ERROR)

    try:
        model = pickle.load(open("loan_model.pkl", "rb"))
        FEATURE_NAMES = pickle.load(open("features.pkl", "rb"))
    except Exception as e:
        _ARTIFACT_ERROR = f"Failed to load ML artifacts: {e}"
        raise RuntimeError(_ARTIFACT_ERROR)

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/health")
def health():
    return "ok", 200

@app.route("/predict", methods=["POST"])
def predict():
    payload = _predict_payload(request.form)
    return render_template("index.html", **payload)


@app.route("/predict_json", methods=["POST"])
def predict_json():
    try:
        payload = _predict_payload(request.form)
        # Only return the parts the client needs for inline rendering.
        response = {
            "ok": True,
            "prediction_text": payload.get("prediction_text"),
            "health_score": payload.get("health_score"),
            "reasons": payload.get("reasons") or [],
            "suggestions": payload.get("suggestions") or [],
            "cibil_info": payload.get("cibil_info") or [],
            "cibil_score": payload.get("cibil_score"),
            "guardrail_note": payload.get("guardrail_note"),
            "advisor_summary": payload.get("advisor_summary"),
            "advisor_advice": payload.get("advisor_advice") or [],
            "advisor_warnings": payload.get("advisor_warnings") or [],
            "dti_percent": payload.get("dti_percent"),
        }
        return jsonify(response)
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400


def _predict_payload(form):
    _load_artifacts()
    if FEATURE_NAMES is None:
        raise RuntimeError("features.pkl not found or could not be loaded")

    input_data = dict.fromkeys(FEATURE_NAMES, 0)

    def _get_float(name: str, default: float | None = None) -> float:
        raw = form.get(name)
        if raw is None or str(raw).strip() == "":
            if default is None:
                raise ValueError(f"Missing required field: {name}")
            return float(default)
        return float(raw)

    income = _get_float("income_annum")
    loan_amount = _get_float("loan_amount")
    cibil = _get_float("cibil_score")

    # Preserve user-entered term fields for UI (so "10 years" stays "10 years" on results)
    term_unit_display = (form.get("term_unit") or "months").strip().lower()
    if term_unit_display not in {"months", "years"}:
        term_unit_display = "months"
    loan_term_value_display = ""
    try:
        raw_term_value_display = (form.get("loan_term_value") or "").strip()
        if raw_term_value_display:
            parsed = float(raw_term_value_display)
            if np.isfinite(parsed) and parsed > 0:
                if term_unit_display == "years":
                    # Keep decimals for years (e.g., 7.5)
                    loan_term_value_display = raw_term_value_display
                else:
                    # Force whole numbers for months
                    loan_term_value_display = str(int(round(parsed)))
    except Exception:
        loan_term_value_display = ""

    # Loan term in months: prefer the hidden loan_term, but fall back to loan_term_value + unit
    # so the form still works even if JS fails.
    loan_term = None
    try:
        loan_term = _get_float("loan_term")
    except Exception:
        loan_term = None

    if loan_term is None or not np.isfinite(loan_term) or loan_term <= 0:
        term_value = _get_float("loan_term_value")
        unit = (form.get("term_unit") or "months").strip().lower()
        loan_term = float(round(term_value * 12)) if unit == "years" else float(round(term_value))

    loan_type = (form.get("loan_type") or "personal").strip().lower()
    applicant_profile = (form.get("applicant_profile") or "salaried").strip().lower()
    try:
        interest_rate = float(form.get("interest_rate") or 10)
    except Exception:
        interest_rate = 10.0
    try:
        existing_emi = float(form.get("existing_emi") or 0)
    except Exception:
        existing_emi = 0.0

    input_data["income_annum"] = income
    input_data["loan_amount"] = loan_amount
    input_data["loan_term"] = loan_term
    input_data["cibil_score"] = cibil

    final_input = np.array(list(input_data.values())).reshape(1, -1)

    model_prediction = int(model.predict(final_input)[0])
    model_probability = float(model.predict_proba(final_input)[0][1])

    def _format_inr(amount: float) -> str:
        try:
            return f"₹{amount:,.2f}"
        except Exception:
            return f"₹{amount}"

    def _compute_emi(principal: float, months: float, apr: float):
        if not np.isfinite(principal) or principal <= 0:
            return None
        if not np.isfinite(months) or months <= 0:
            return None
        if not np.isfinite(apr) or apr < 0:
            return None

        n = int(round(months))
        if n <= 0:
            return None

        r = (apr / 100.0) / 12.0
        if r == 0:
            payment = principal / n
        else:
            pow_ = (1 + r) ** n
            payment = principal * (r * pow_) / (pow_ - 1)

        total_cost = payment * n
        total_interest = max(0.0, total_cost - principal)
        return float(payment), float(total_interest), float(total_cost)

    # Pre-compute EMI/DTI for guardrails + advisor
    emi_tuple = _compute_emi(loan_amount, loan_term, interest_rate)
    monthly_income = (income / 12.0) if income > 0 else 0.0
    dti = None
    if emi_tuple is not None and monthly_income > 0:
        dti = float((emi_tuple[0] + max(0.0, existing_emi)) / monthly_income)

    def _build_advisor(final_pred: int):
        lt = loan_type if loan_type in {"education", "home", "business", "personal"} else "personal"
        ap = applicant_profile if applicant_profile in {"student", "salaried", "self_employed", "business_owner"} else "salaried"

        emi = emi_tuple
        monthly_income_local = monthly_income
        dti_local = dti

        label_map = {
            "education": "Education",
            "home": "Home",
            "business": "Business",
            "personal": "Personal",
        }
        profile_map = {
            "student": "student",
            "salaried": "salaried applicant",
            "self_employed": "self-employed applicant",
            "business_owner": "business owner",
        }

        if emi is None:
            summary = f"For a {label_map[lt]} loan, enter amount/term to estimate EMI."
            emi_monthly = None
            emi_interest = None
            emi_total = None
        else:
            summary = (
                f"For a {label_map[lt]} loan as a {profile_map[ap]}, "
                f"your estimated EMI is {_format_inr(emi[0])} per month at {interest_rate:.1f}% APR."
            )
            emi_monthly = _format_inr(emi[0])
            emi_interest = _format_inr(emi[1])
            emi_total = _format_inr(emi[2])

        advice = []
        warnings_list = []

        if lt == "education":
            advice.extend([
                "Check if moratorium is available during studies.",
                "Use the shortest tenure you can comfortably manage.",
            ])
            warnings_list.extend([
                "Interest can grow during moratorium; confirm the policy.",
                "Plan repayments around expected first-job income.",
            ])
        elif lt == "home":
            advice.extend([
                "Keep an emergency fund alongside EMIs.",
                "If possible, prepay small chunks to cut interest.",
            ])
            warnings_list.extend([
                "Long tenures greatly increase total interest paid.",
                "Rate changes can raise EMIs on floating-rate loans.",
            ])
        elif lt == "business":
            advice.extend([
                "Match EMI to business cash flow cycles.",
                "Keep a buffer for slow months and seasonal dips.",
            ])
            warnings_list.extend([
                "Irregular income can make fixed EMIs stressful.",
                "Avoid stretching tenure just to reduce EMI slightly.",
            ])
        else:
            advice.extend([
                "Use personal loans for needs, not lifestyle spends.",
                "Keep tenure short to reduce total interest.",
            ])
            warnings_list.extend([
                "Personal loans are usually higher interest (unsecured).",
                "Missing EMIs can hurt your credit score quickly.",
            ])

        if dti_local is not None:
            if dti_local >= 0.50:
                warnings_list.insert(0, "EMI burden looks very high vs monthly income.")
            elif dti_local >= 0.40:
                warnings_list.insert(0, "EMI burden looks high; keep a bigger buffer.")
            elif dti_local >= 0.30:
                warnings_list.insert(0, "EMI burden is moderate; avoid new debt." )

        if interest_rate >= 18:
            warnings_list.append("APR is high; compare offers and reduce tenure.")

        if loan_term >= 240:
            warnings_list.append("Long tenure increases total interest significantly.")

        if cibil < 650:
            warnings_list.append("Low CIBIL can mean rejection or higher rates.")

        if existing_emi > 0:
            advice.append("Keep total EMIs (existing + new) within a comfortable range.")

        if final_pred == 1:
            advice.append("Stay consistent: on-time EMIs improve your long-term profile.")
        else:
            advice.append("If rejected, try lower amount/tenure or add a co-applicant.")

        dti_percent = None
        if dti_local is not None and np.isfinite(dti_local):
            dti_percent = int(round(dti_local * 100))
            dti_percent = max(0, min(200, dti_percent))

        return summary, advice[:6], warnings_list[:6], emi_monthly, emi_interest, emi_total, dti_percent

    # NEW FEATURE: Financial Health Score (rule-based)
    income_safe = max(income, 1.0)
    loan_to_income = loan_amount / income_safe
    health_score = int((cibil / 900) * 60 + (max(0, 1 - loan_to_income) * 40))
    health_score = max(0, min(100, health_score))

    def rule_based_explain():
        reasons_local = []
        suggestions_local = []
        cibil_info_local = []

        if cibil < 650:
            reasons_local.append("Low CIBIL score")
            suggestions_local.append("Pay EMIs and credit card bills on time for 3–6 months")
            cibil_info_local.append("CIBIL below 650 is considered high risk by most banks")

        if loan_amount > income_safe * 0.6:
            reasons_local.append("Loan amount is high compared to income")
            suggestions_local.append("Reduce loan amount or add a co-applicant")

        if loan_term > 240:
            reasons_local.append("Very long loan tenure")
            suggestions_local.append("Opt for a shorter loan tenure if possible")

        if not cibil_info_local:
            cibil_info_local.append("Higher CIBIL scores generally increase approval odds")

        return reasons_local, suggestions_local, cibil_info_local

    reasons, suggestions, cibil_info = rule_based_explain()

    # HYBRID GUARDRAILS: Only override to APPROVE for obviously strong cases.
    guardrail_applied = False
    guardrail_note = None
    final_prediction = model_prediction
    final_probability = model_probability

    lt_norm = loan_type if loan_type in {"education", "home", "business", "personal"} else "personal"
    ap_norm = applicant_profile if applicant_profile in {"student", "salaried", "self_employed", "business_owner"} else "salaried"

    reasonable_term = loan_term <= 360

    # EMI-burden (DTI) is a more realistic affordability signal than loan_amount/income.
    dti_ok = (dti is not None) and np.isfinite(dti) and (dti <= 0.35)
    dti_strong = (dti is not None) and np.isfinite(dti) and (dti <= 0.25)

    # Slightly relaxed credit thresholds for education/student use-cases.
    credit_ok = cibil >= 700
    if lt_norm == "education" and ap_norm == "student":
        credit_ok = cibil >= 650

    strong_profile = reasonable_term and dti_strong and credit_ok
    acceptable_profile = reasonable_term and dti_ok and credit_ok

    if model_prediction == 0 and (strong_profile or acceptable_profile):
        guardrail_applied = True
        guardrail_note = "Hybrid guardrail: affordability (DTI) override"
        final_prediction = 1

        # Probability bump is modest for acceptable_profile, higher for strong_profile.
        floor = 0.80 if strong_profile else 0.70
        final_probability = max(model_probability, floor)

        if "Low CIBIL score" in reasons and credit_ok:
            reasons = [r for r in reasons if r != "Low CIBIL score"]
        if dti is not None and np.isfinite(dti):
            reasons.insert(0, f"Affordable EMI burden (~{int(round(dti*100))}% of monthly income)")
        else:
            reasons.insert(0, "Affordable EMI burden based on inputs")
        suggestions.insert(0, "Keep EMIs within comfort and maintain an emergency buffer")

    # Optional Gemini-enhanced explanations (REST; does not affect decision)
    # Prefer GEMINI_API_KEY (documented), but allow GOOGLE_API_KEY for compatibility.
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if api_key:
        try:
            model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
            endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"

            payload = {
                "inputs": {
                    "income_annum": income,
                    "loan_amount": loan_amount,
                    "loan_term_months": loan_term,
                    "cibil_score": cibil,
                    "loan_to_income": round(float(loan_to_income), 4),
                },
                "ml": {
                    "prediction": int(model_prediction),
                    "approval_probability": round(model_probability, 6),
                },
                "hybrid": {
                    "final_prediction": int(final_prediction),
                    "final_probability": round(final_probability, 6),
                    "guardrail_applied": bool(guardrail_applied),
                    "guardrail_note": guardrail_note,
                },
            }

            prompt = (
                "Return STRICT JSON with keys: reasons, suggestions, cibil_info. "
                "Each value is an array of short strings (<= 14 words). "
                "Be concrete and explainable.\n\n"
                f"Context: {json.dumps(payload, ensure_ascii=False)}"
            )

            body = {
                "contents": [
                    {
                        "role": "user",
                        "parts": [{"text": prompt}],
                    }
                ],
                "generationConfig": {
                    "temperature": 0.2,
                    "maxOutputTokens": 300,
                },
            }

            req = urllib.request.Request(
                endpoint,
                data=json.dumps(body).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )

            with urllib.request.urlopen(req, timeout=6) as resp:
                raw = resp.read().decode("utf-8", errors="replace")
            data = json.loads(raw)
            text = (
                data.get("candidates", [{}])[0]
                .get("content", {})
                .get("parts", [{}])[0]
                .get("text", "")
                .strip()
            )

            json_start = text.find("{")
            json_end = text.rfind("}")
            if json_start != -1 and json_end != -1 and json_end > json_start:
                parsed = json.loads(text[json_start : json_end + 1])
                if isinstance(parsed, dict):
                    reasons = parsed.get("reasons", reasons)
                    suggestions = parsed.get("suggestions", suggestions)
                    cibil_info = parsed.get("cibil_info", cibil_info)
        except Exception:
            # Silent fallback to rule-based explanations
            pass

    result = "✅ Loan Likely Approved" if final_prediction == 1 else "❌ Loan Likely Rejected"
    decision_suffix = " (Hybrid)" if guardrail_applied else ""

    advisor_summary, advisor_advice, advisor_warnings, emi_monthly, emi_total_interest, emi_total_cost, dti_percent = _build_advisor(final_prediction)

    return {
        "prediction_text": f"{result}{decision_suffix} (Approval Probability: {round(final_probability*100,2)}%)",
        "reasons": reasons,
        "suggestions": suggestions,
        "cibil_info": cibil_info,
        "health_score": health_score,
        "cibil_score": cibil,
        "guardrail_note": guardrail_note,
        "advisor_summary": advisor_summary,
        "advisor_advice": advisor_advice,
        "advisor_warnings": advisor_warnings,
        "emi_monthly": emi_monthly,
        "emi_total_interest": emi_total_interest,
        "emi_total_cost": emi_total_cost,
        "dti_percent": dti_percent,
        "income_annum": income,
        "loan_amount": loan_amount,
        "loan_term": loan_term,
        "loan_term_value": loan_term_value_display,
        "term_unit": term_unit_display,
        "interest_rate": interest_rate,
        "loan_type": loan_type,
        "applicant_profile": applicant_profile,
        "existing_emi": existing_emi,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# FINANCIAL ADVISOR - Personalized Tips & Strategies via Gemini API
# ═══════════════════════════════════════════════════════════════════════════════

# Fallback financial advice data when Gemini API is unavailable
FALLBACK_ADVICE = {
    "education": {
        "title": "Education Loan Financial Tips",
        "advice": [
            {
                "title": "Compare Interest Rates",
                "description": "Shop around with multiple lenders. Even a 0.5% difference can save thousands over the loan term.",
                "impact": "High",
                "category": "Savings"
            },
            {
                "title": "Start Paying Interest Early",
                "description": "If possible, pay interest while still in school to prevent capitalization and reduce total cost.",
                "impact": "Medium",
                "category": "Strategy"
            },
            {
                "title": "Set Up Autopay",
                "description": "Most lenders offer 0.25% rate reduction for automatic payments. Easy savings!",
                "impact": "Medium",
                "category": "Savings"
            },
            {
                "title": "Consider Refinancing Later",
                "description": "After graduation with stable income and good credit, refinancing can lower your rate significantly.",
                "impact": "High",
                "category": "Strategy"
            }
        ]
    },
    "home": {
        "title": "Home Loan Financial Tips",
        "advice": [
            {
                "title": "Improve Credit Score First",
                "description": "A score above 740 typically gets the best rates. Even 20 points can save thousands.",
                "impact": "High",
                "category": "Preparation"
            },
            {
                "title": "Save for 20% Down Payment",
                "description": "Avoid PMI (Private Mortgage Insurance) by putting 20% down, saving hundreds monthly.",
                "impact": "High",
                "category": "Savings"
            },
            {
                "title": "Get Multiple Quotes",
                "description": "Apply to at least 3 lenders. Rate shopping within 14-45 days counts as one inquiry.",
                "impact": "Medium",
                "category": "Strategy"
            },
            {
                "title": "Consider Points vs Rate",
                "description": "Buying points makes sense if you'll stay 5+ years. Calculate your break-even point.",
                "impact": "Medium",
                "category": "Strategy"
            }
        ]
    },
    "business": {
        "title": "Business Loan Financial Tips",
        "advice": [
            {
                "title": "Separate Personal & Business Credit",
                "description": "Build business credit history independently. It protects personal assets and improves terms.",
                "impact": "High",
                "category": "Preparation"
            },
            {
                "title": "Prepare Strong Financials",
                "description": "Have 2+ years of tax returns, profit/loss statements, and cash flow projections ready.",
                "impact": "High",
                "category": "Preparation"
            },
            {
                "title": "Start with a Line of Credit",
                "description": "A business line of credit builds history and provides flexibility. Use it and repay consistently.",
                "impact": "Medium",
                "category": "Strategy"
            },
            {
                "title": "Consider Collateral Options",
                "description": "Secured loans offer better rates. Equipment, inventory, or receivables can serve as collateral.",
                "impact": "Medium",
                "category": "Savings"
            }
        ]
    },
    "personal": {
        "title": "Personal Loan Financial Tips",
        "advice": [
            {
                "title": "Check Your Credit Report",
                "description": "Review for errors before applying. Dispute any inaccuracies - they can hurt your rate.",
                "impact": "High",
                "category": "Preparation"
            },
            {
                "title": "Lower Debt-to-Income Ratio",
                "description": "Pay down existing debts first. DTI below 36% significantly improves approval odds and rates.",
                "impact": "High",
                "category": "Preparation"
            },
            {
                "title": "Avoid Unnecessary Fees",
                "description": "Look for loans with no origination fees or prepayment penalties. Read the fine print!",
                "impact": "Medium",
                "category": "Savings"
            },
            {
                "title": "Choose the Right Term",
                "description": "Shorter terms mean higher payments but less total interest. Balance monthly budget with total cost.",
                "impact": "Medium",
                "category": "Strategy"
            }
        ]
    },
    "agriculture": {
        "title": "Agricultural Loan Financial Tips",
        "advice": [
            {
                "title": "Document Farm Income Properly",
                "description": "Keep detailed records of all farm revenue streams. Lenders want to see consistent cash flow.",
                "impact": "High",
                "category": "Preparation"
            },
            {
                "title": "Use Land as Leverage",
                "description": "Farm real estate can secure better rates. Consider using equity in existing land for new purchases.",
                "impact": "High",
                "category": "Strategy"
            },
            {
                "title": "Time Your Application",
                "description": "Apply after a good harvest season when financials look strongest. Timing matters for approval.",
                "impact": "Medium",
                "category": "Strategy"
            },
            {
                "title": "Explore Operating Lines",
                "description": "Seasonal operating lines of credit often have better terms than fixed loans for working capital.",
                "impact": "Medium",
                "category": "Savings"
            }
        ]
    }
}


@app.route("/smart_advisor", methods=["POST"])
def smart_advisor():
    """Get personalized financial advice based on loan type using Gemini AI."""
    try:
        data = request.get_json() or {}
        loan_type = data.get("loan_type", "personal").lower().strip()
        loan_amount = data.get("loan_amount", 0)
        income = data.get("income", 0)
        credit_score = data.get("credit_score", 700)
        currency = data.get("currency", "USD")
        applicant_profile = data.get("applicant_profile", "salaried")
        
        # Normalize loan type
        if loan_type not in FALLBACK_ADVICE:
            loan_type = "personal"
        
        # Try Gemini API first
        if GEMINI_API_KEY:
            try:
                response = _get_gemini_advice(loan_type, loan_amount, income, credit_score, currency, applicant_profile)
                if response:
                    return jsonify({
                        "ok": True,
                        "source": "gemini",
                        "loan_type": loan_type,
                        **response
                    })
            except Exception as e:
                print(f"Gemini API error: {e}")
        
        # Fallback to static data
        fallback = FALLBACK_ADVICE.get(loan_type, FALLBACK_ADVICE["personal"])
        return jsonify({
            "ok": True,
            "source": "fallback",
            "loan_type": loan_type,
            "title": fallback["title"],
            "advice": fallback["advice"],
            "quick_tips": _get_quick_tips(loan_type, loan_amount, income, credit_score)
        })
        
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400


def _get_gemini_advice(loan_type: str, loan_amount: float, income: float, credit_score: int, currency: str, profile: str):
    """Query Gemini API for personalized financial advice."""
    
    prompt = f"""You are a friendly, expert financial advisor. Provide personalized advice for someone seeking a {loan_type.upper()} LOAN with:
- Loan Amount: {currency} {loan_amount:,.0f}
- Annual Income: {currency} {income:,.0f}
- Credit Score: {credit_score}
- Profile: {profile}

Return a JSON object with this EXACT structure (no markdown, just pure JSON):
{{
    "title": "Your Personalized {loan_type.title()} Loan Advice",
    "advice": [
        {{
            "title": "Short actionable title",
            "description": "Specific, personalized advice in 1-2 sentences",
            "impact": "High/Medium/Low",
            "category": "Savings/Strategy/Preparation/Warning"
        }}
    ],
    "quick_tips": [
        "Quick tip 1 specific to their situation",
        "Quick tip 2",
        "Quick tip 3"
    ],
    "estimated_savings": "Potential savings estimate based on the advice"
}}

Provide 4-5 pieces of advice. Focus on:
1. How to get better interest rates based on their credit score
2. Specific savings strategies for their loan amount
3. Timing and preparation tips
4. Red flags to avoid
5. Ways to reduce total loan cost

Be specific and actionable. Tailor advice to their income level and credit score. If credit score is below 670, emphasize improvement strategies. If loan amount is high relative to income, include warnings."""

    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        
        # Parse JSON from response
        text = response.text.strip()
        # Remove markdown code blocks if present
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        text = text.strip()
        
        return json.loads(text)
    except Exception as e:
        print(f"Gemini parsing error: {e}")
        return None


def _get_quick_tips(loan_type: str, loan_amount: float, income: float, credit_score: int) -> list:
    """Generate quick tips based on financial situation."""
    tips = []
    
    # Credit score tips
    if credit_score < 670:
        tips.append("🎯 Focus on improving your credit score to 670+ for better rates")
    elif credit_score >= 740:
        tips.append("✨ Your excellent credit qualifies you for the best available rates")
    
    # DTI ratio tips
    if income > 0 and loan_amount > 0:
        monthly_income = income / 12
        estimated_emi = loan_amount / 60  # Rough estimate
        dti = (estimated_emi / monthly_income) * 100
        if dti > 40:
            tips.append(f"⚠️ Your estimated DTI ({dti:.0f}%) is high - consider a smaller loan or longer term")
        elif dti < 20:
            tips.append("💪 Your debt-to-income ratio looks healthy for this loan amount")
    
    # Loan type specific
    type_tips = {
        "education": "📚 Exhaust scholarships and grants before taking loans",
        "home": "🏠 Get pre-approved to strengthen your negotiating position",
        "business": "💼 Prepare detailed financial projections for better approval odds",
        "agriculture": "🌾 Document all revenue streams including seasonal variations",
        "personal": "💳 Compare at least 3 lenders before deciding"
    }
    tips.append(type_tips.get(loan_type, type_tips["personal"]))
    
    tips.append("📊 Use this calculator to compare different term lengths")
    
    return tips


# ═══════════════════════════════════════════════════════════════════════════════
# CHATBOT ENDPOINT - Gemini Conversational AI
# ═══════════════════════════════════════════════════════════════════════════════

@app.route("/chat_advisor", methods=["POST"])
def chat_advisor():
    """Handle chat messages with Gemini AI for EMI and loan advice."""
    try:
        data = request.get_json() or {}
        user_message = data.get("message", "").strip()
        history = data.get("history", [])
        context = data.get("context", {})
        
        if not user_message:
            return jsonify({"ok": False, "error": "No message provided"}), 400
        
        # Extract context values
        loan_amount = context.get('loan_amount', 0)
        tenure_months = context.get('tenure_months', 120)
        interest_rate = context.get('interest_rate', 10)
        income = context.get('income', 0)
        credit_score = context.get('credit_score', 700)
        currency = context.get('currency', 'USD')
        loan_type = context.get('loan_type', 'personal')
        age = context.get('age', 0)
        gender = context.get('gender', 'not specified')
        
        # Age eligibility rules
        age_rules = {
            'personal': {'min': 21, 'max': 60, 'tenure_max': 65},
            'home': {'min': 21, 'max': 65, 'tenure_max': 70},
            'education': {'min': 18, 'max': 35, 'tenure_max': 45},
            'business': {'min': 21, 'max': 65, 'tenure_max': 70}
        }
        
        rules = age_rules.get(loan_type, age_rules['personal'])
        tenure_years = tenure_months // 12
        age_at_loan_end = age + tenure_years if age > 0 else 0
        
        # Calculate EMI for context
        calculated_emi = 0
        total_interest = 0
        if loan_amount > 0 and tenure_months > 0:
            monthly_rate = (interest_rate / 100) / 12
            if monthly_rate > 0:
                emi = loan_amount * monthly_rate * ((1 + monthly_rate) ** tenure_months) / (((1 + monthly_rate) ** tenure_months) - 1)
                calculated_emi = round(emi, 2)
                total_interest = round((emi * tenure_months) - loan_amount, 2)
        
        # Build rich context string
        age_info = f"• Age: {age} years ({gender.title()})" if age > 0 else "• Age: Not specified"
        age_eligibility = ""
        if age > 0:
            if age < rules['min']:
                age_eligibility = f"⚠️ Below minimum age ({rules['min']}) for {loan_type} loan"
            elif age > rules['max']:
                age_eligibility = f"⚠️ Above maximum age ({rules['max']}) for {loan_type} loan"
            elif age_at_loan_end > rules['tenure_max']:
                max_tenure = rules['tenure_max'] - age
                age_eligibility = f"⚠️ Age at loan end ({age_at_loan_end}) exceeds {rules['tenure_max']}. Max tenure: {max_tenure} years"
            else:
                age_eligibility = f"✅ Age eligible for {loan_type} loan (ends at age {age_at_loan_end})"
        
        loan_context = f"""
📊 USER'S CURRENT LOAN CALCULATOR VALUES:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Loan Amount: {currency} {loan_amount:,.0f}
• Interest Rate: {interest_rate}% per annum
• Tenure: {tenure_months} months ({tenure_months//12} years {tenure_months%12} months)
• Loan Type: {loan_type.title()}
{age_info}
• Annual Income: {currency} {income:,.0f}
• Credit Score: {credit_score}
{f'• Age Eligibility: {age_eligibility}' if age_eligibility else ''}

📈 CALCULATED VALUES:
• Monthly EMI: {currency} {calculated_emi:,.2f}
• Total Interest Payable: {currency} {total_interest:,.2f}
• Total Amount Payable: {currency} {(loan_amount + total_interest):,.2f}
• Interest as % of Principal: {(total_interest/loan_amount*100) if loan_amount > 0 else 0:.1f}%
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        
        # Build conversation history
        history_text = ""
        if history:
            for msg in history[-6:]:
                role = "User" if msg.get("role") == "user" else "Assistant"
                history_text += f"{role}: {msg.get('content', '')}\n"
        
        # Enhanced EMI-focused system prompt
        system_prompt = f"""You are an expert EMI & Loan Advisor chatbot for CrediLume loan calculator. You specialize in helping users understand EMI, optimize their loans, and make smart financial decisions.

{loan_context}

YOUR EXPERTISE AREAS:
1. 📊 EMI CALCULATIONS - Explain how EMI works, the formula, components (principal vs interest)
2. 💰 INTEREST OPTIMIZATION - Tips to reduce total interest paid
3. ⏱️ TENURE PLANNING - Trade-offs between short and long tenures
4. 🎯 PREPAYMENT STRATEGIES - When and how much to prepay
5. 💵 AFFORDABILITY - Debt-to-income ratios, safe borrowing limits
6. 📉 RATE COMPARISON - Fixed vs floating, negotiating better rates
7. 🏦 LOAN SELECTION - Choosing the right loan type and lender
8. 👤 AGE ELIGIBILITY - Loan eligibility based on applicant's age

AGE ELIGIBILITY RULES:
- Personal Loan: Min age 21, Max age 60, Loan must end by age 65
- Home Loan: Min age 21, Max age 65, Loan must end by age 70
- Education Loan: Min age 18, Max age 35, Loan must end by age 45
- Business Loan: Min age 21, Max age 65, Loan must end by age 70

RESPONSE GUIDELINES:
- Give SPECIFIC advice using their actual loan numbers when relevant
- Use bullet points and clear formatting
- Include calculations/examples when explaining concepts
- Be concise but thorough (3-5 key points)
- Use emojis to make responses friendly but professional
- If they ask about their loan, reference their specific amounts
- Always provide actionable advice they can use immediately
- If age is provided, consider age eligibility in your advice

EMI FORMULA REFERENCE:
EMI = P × r × (1+r)^n / ((1+r)^n - 1)
Where: P = Principal, r = Monthly interest rate, n = Number of months

AFFORDABILITY RULES:
- EMI should ideally be ≤40% of monthly income
- Total debt payments ≤50% of income
- Emergency fund of 6 months expenses recommended before taking loan

Previous conversation:
{history_text}

User's question: {user_message}

Provide helpful, specific advice:"""

        if GEMINI_API_KEY:
            try:
                model = genai.GenerativeModel('gemini-1.5-flash')
                response = model.generate_content(system_prompt)
                
                return jsonify({
                    "ok": True,
                    "response": response.text.strip()
                })
            except Exception as e:
                print(f"Gemini chat error: {e}")
        
        # Enhanced fallback responses
        fallback_responses = _get_smart_fallback(
            user_message,
            loan_amount,
            tenure_months,
            interest_rate,
            income,
            credit_score,
            currency,
            calculated_emi,
            total_interest,
            loan_type,
            age,
            gender,
        )
        
        return jsonify({
            "ok": True,
            "response": fallback_responses
        })
        
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400


def _get_smart_fallback(message: str, loan_amount: float, tenure: int, rate: float, income: float, credit_score: int, currency: str, emi: float, total_interest: float, loan_type: str = 'personal', age: int = 0, gender: str = 'not specified') -> str:
    """Generate smart fallback responses based on keywords and user's loan data."""
    
    message_lower = message.lower()
    
    # Age eligibility check
    if any(word in message_lower for word in ["age", "eligible", "eligibility", "old enough", "too old", "too young"]):
        age_rules = {
            'personal': {'min': 21, 'max': 60, 'tenure_max': 65, 'desc': 'Personal Loan'},
            'home': {'min': 21, 'max': 65, 'tenure_max': 70, 'desc': 'Home Loan'},
            'education': {'min': 18, 'max': 35, 'tenure_max': 45, 'desc': 'Education Loan'},
            'business': {'min': 21, 'max': 65, 'tenure_max': 70, 'desc': 'Business Loan'}
        }
        
        rules = age_rules.get(loan_type, age_rules['personal'])
        tenure_years = tenure // 12
        age_at_end = age + tenure_years if age > 0 else 0
        max_allowed_tenure = rules['tenure_max'] - age if age > 0 else rules['tenure_max'] - rules['min']
        
        eligibility_status = "❓ Age not provided"
        if age > 0:
            if age < rules['min']:
                eligibility_status = f"❌ **Not Eligible** - You're {rules['min'] - age} years below minimum age ({rules['min']})"
            elif age > rules['max']:
                eligibility_status = f"❌ **Not Eligible** - You're {age - rules['max']} years above maximum age ({rules['max']})"
            elif age_at_end > rules['tenure_max']:
                eligibility_status = f"⚠️ **Partial Eligibility** - Age at loan end ({age_at_end}) exceeds {rules['tenure_max']}"
            else:
                eligibility_status = f"✅ **Eligible!** - You meet all age criteria"
        
        return f"""👤 **Age Eligibility Check for {rules['desc']}**

**Your Profile:**
• Current Age: {age if age > 0 else 'Not specified'} years
• Gender: {gender.title()}
• Loan Type: {loan_type.title()}
• Tenure: {tenure_years} years
• Age at Loan End: {age_at_end if age > 0 else 'N/A'}

**Eligibility Rules for {rules['desc']}:**
• Minimum Age: {rules['min']} years
• Maximum Age: {rules['max']} years
• Loan must end by age: {rules['tenure_max']}

**Your Status:** {eligibility_status}

**Maximum Tenure Allowed:** {max_allowed_tenure if age > 0 else tenure_years} years

📋 **All Loan Types Age Criteria:**
| Loan Type | Min Age | Max Age | Must End By |
|-----------|---------|---------|-------------|
| Personal  | 21      | 60      | 65          |
| Home      | 21      | 65      | 70          |
| Education | 18      | 35      | 45          |
| Business  | 21      | 65      | 70          |

💡 **Tip:** If you're near the upper age limit, consider a shorter tenure or add a co-applicant."""

    # EMI Calculation explanation
    if any(word in message_lower for word in ["emi", "calculate", "formula", "how is", "explain"]):
        return f"""📊 **How EMI is Calculated**

EMI = P × r × (1+r)^n / ((1+r)^n - 1)

Where:
• **P** = Principal (Loan Amount) = {currency} {loan_amount:,.0f}
• **r** = Monthly Interest Rate = {rate}% ÷ 12 = {rate/12:.4f}%
• **n** = Number of Months = {tenure}

**Your EMI Breakdown:**
• Monthly EMI: **{currency} {emi:,.2f}**
• Total Interest: {currency} {total_interest:,.2f}
• Total Payment: {currency} {(loan_amount + total_interest):,.2f}

💡 Each EMI payment includes both principal and interest. Early payments are interest-heavy, later ones are principal-heavy!"""

    # Interest reduction tips
    if any(word in message_lower for word in ["reduce", "lower", "save", "less interest", "minimize"]):
        potential_savings = total_interest * 0.15  # Rough estimate
        return f"""💰 **Ways to Reduce Your Interest ({currency} {total_interest:,.0f} currently)**

1. **Shorter Tenure** - Reducing from {tenure} to {tenure-24} months can save ~15-20% interest
2. **Prepayments** - Even {currency} {loan_amount*0.1:,.0f} extra/year reduces interest significantly  
3. **Better Rate** - 0.5% lower rate saves ~{currency} {total_interest*0.05:,.0f} over loan term
4. **Higher Down Payment** - Reduces principal = less interest
5. **Balance Transfer** - If rates have dropped, consider refinancing

🎯 **Quick Win:** Making one extra EMI payment per year can cut your loan tenure by 2-3 years!

Potential savings with these strategies: **{currency} {potential_savings:,.0f}+**"""

    # Tenure advice
    if any(word in message_lower for word in ["tenure", "term", "years", "months", "short", "long"]):
        short_tenure = max(12, tenure - 36)
        long_tenure = tenure + 36
        return f"""⏱️ **Tenure Trade-offs for Your {currency} {loan_amount:,.0f} Loan**

**Shorter Tenure ({short_tenure} months):**
✅ Less total interest paid
✅ Debt-free sooner
❌ Higher monthly EMI
Best for: Higher income, stable job

**Longer Tenure ({long_tenure} months):**
✅ Lower monthly EMI (easier to manage)
✅ More financial flexibility
❌ More total interest paid
Best for: Variable income, other investments

**Your Current:** {tenure} months = {currency} {emi:,.2f}/month

💡 **Pro Tip:** Start with longer tenure for lower mandatory EMI, but make voluntary prepayments when you have extra cash. Best of both worlds!"""

    # Prepayment advice
    if any(word in message_lower for word in ["prepay", "prepayment", "pay off", "early", "lump sum"]):
        prepay_amount = loan_amount * 0.1
        return f"""🎯 **Prepayment Strategy for Your Loan**

**When to Prepay:**
• Best in first half of loan tenure (when interest component is highest)
• When you have surplus funds beyond emergency fund
• After checking for prepayment penalties (most loans allow 5-25% free)

**Smart Prepayment Options:**

1. **Annual Bonus Method**
   - Put {currency} {prepay_amount:,.0f} (10% of loan) annually
   - Can reduce tenure by 3-4 years!

2. **EMI Top-up Method**  
   - Pay {currency} {emi*0.1:,.0f} extra each month
   - Barely noticeable, huge impact

3. **Part Prepay vs Full Closure**
   - Part prepay to reduce tenure (not EMI) for max savings

💡 **Your Potential Savings:** Prepaying {currency} {prepay_amount:,.0f} in year 1 could save ~{currency} {prepay_amount*0.3:,.0f} in interest!"""

    # Affordability check
    if any(word in message_lower for word in ["afford", "income", "budget", "can i", "how much", "salary"]):
        monthly_income = income / 12 if income > 0 else 0
        emi_ratio = (emi / monthly_income * 100) if monthly_income > 0 else 0
        max_affordable_emi = monthly_income * 0.4
        return f"""💵 **Affordability Analysis**

**Your Numbers:**
• Monthly Income: {currency} {monthly_income:,.0f}
• Current EMI: {currency} {emi:,.2f}
• EMI-to-Income Ratio: **{emi_ratio:.1f}%**

**Healthy Ranges:**
• ✅ Below 30%: Very comfortable
• ⚠️ 30-40%: Manageable, less flexibility  
• ❌ Above 40%: Risky, consider lower amount

**Recommendation:**
{"✅ Your EMI is within healthy limits!" if emi_ratio < 40 else "⚠️ Consider reducing loan amount or extending tenure for comfort."}

**Max Affordable EMI (40% rule):** {currency} {max_affordable_emi:,.0f}/month
**That supports a loan of approximately:** {currency} {max_affordable_emi * tenure * 0.85:,.0f}"""

    # Fixed vs Floating
    if any(word in message_lower for word in ["fixed", "floating", "variable", "type of rate"]):
        return f"""📉 **Fixed vs Floating Interest Rates**

**Fixed Rate:**
✅ EMI stays constant throughout
✅ Easy budgeting, no surprises  
✅ Good when rates might rise
❌ Usually 0.5-1% higher than floating
❌ Miss out if rates drop

**Floating Rate:**
✅ Lower initial rate
✅ Benefit when rates fall
✅ Good for short-term loans
❌ EMI can increase unpredictably
❌ Budgeting is harder

**For your {tenure//12}-year loan:**
• If rates are HIGH now → **Floating** (likely to decrease)
• If rates are LOW now → **Fixed** (lock in the good rate)
• If uncertain → **Floating with prepayment plan** (pay off faster if rates rise)

💡 Currently at {rate}%? Check if this is historically high or low in your region."""

    # Credit score
    if any(word in message_lower for word in ["credit", "score", "cibil", "rating"]):
        return f"""📈 **Credit Score Impact on Your Loan**

**Score Ranges & Rates:**
• 750+ (Excellent): Best rates, 0.5-1% lower
• 700-749 (Good): Standard rates
• 650-699 (Fair): +0.5-1% higher rates  
• Below 650: May face rejection or +2-3% rates

**Your Score: {int(credit_score)}**
{"✅ Great! You qualify for competitive rates." if credit_score >= 750 else "💡 Improving to 750+ could save " + currency + " " + str(int(total_interest * 0.1)) + "+ in interest!"}

**Quick Score Boosters:**
1. Pay all bills on time (35% of score)
2. Keep credit utilization under 30%
3. Don't close old credit cards
4. Avoid multiple loan applications at once
5. Check report for errors"""

    # Default helpful response
    return f"""🎯 **I can help you with:**

Based on your loan of **{currency} {loan_amount:,.0f}** at **{rate}%** for **{tenure} months**:

• 📊 **Your EMI:** {currency} {emi:,.2f}/month
• 💰 **Total Interest:** {currency} {total_interest:,.2f}

**Ask me about:**
- "How can I reduce my interest?"
- "Should I choose shorter or longer tenure?"
- "When should I prepay my loan?"
- "How much loan can I afford?"
- "Fixed vs floating rate?"
- "How is EMI calculated?"

I'll give you personalized advice based on your numbers! 💡"""


if __name__ == "__main__":
    # For hackathon/demo dev: enable auto-reload by default.
    # Artifacts are lazy-loaded, so reloader won't unpickle models on import.
    port = int(os.environ.get("PORT", "5000"))
    debug = (os.environ.get("FLASK_DEBUG", "1") != "0")
    use_reloader = (os.environ.get("FLASK_RELOADER", "1") != "0")
    app.run(host="127.0.0.1", port=port, debug=debug, use_reloader=use_reloader)