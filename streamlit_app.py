import streamlit as st
import joblib
import json
import re
import time
from html import escape

st.set_page_config(page_title="Fake Job Posting Detector", page_icon="🔍", layout="centered")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
.stApp {
    background: #f4f6fb;
}
html, body, .stApp, p, label, input, textarea, button {
    font-family: 'Inter', 'Segoe UI', sans-serif;
}
[data-testid="stHeader"] {
    background: transparent;
}
[data-testid="stToolbar"], [data-testid="stDeployButton"], #MainMenu, footer {
    display: none !important;
}
.block-container {
    max-width: 980px !important;
    padding-top: 2rem !important;
    padding-bottom: 3rem !important;
}
label, label p, [data-testid="stWidgetLabel"], [data-testid="stWidgetLabel"] * {
    color: #334155 !important;
    font-weight: 600 !important;
    font-size: 14px !important;
}
[data-testid="stTextInputRootElement"], [data-testid="stTextAreaRootElement"] {
    background-color: #ffffff !important;
    border: 1px solid #cbd5e1 !important;
    border-radius: 10px !important;
    overflow: hidden;
}
[data-baseweb="input"], [data-baseweb="base-input"], [data-baseweb="textarea"] {
    background-color: #ffffff !important;
    border: none !important;
}
.stTextInput input, .stTextArea textarea {
    background-color: #ffffff !important;
    color: #0f172a !important;
    -webkit-text-fill-color: #0f172a !important;
}
.stTextInput input::placeholder, .stTextArea textarea::placeholder {
    color: #94a3b8 !important;
    -webkit-text-fill-color: #94a3b8 !important;
    opacity: 1 !important;
}
[data-testid="stTextInputRootElement"]:focus-within, [data-testid="stTextAreaRootElement"]:focus-within {
    border-color: #2563eb !important;
    box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.15) !important;
}
.stButton > button {
    background: #2563eb;
    border: none;
    border-radius: 10px;
    padding: 0.7rem 1.5rem;
    font-weight: 600;
    width: 100%;
}
.stButton > button, .stButton > button * {
    color: #ffffff !important;
}
.stButton > button:hover {
    background: #1d4ed8;
}
[role="tablist"] {
    gap: 8px;
}
[role="tab"], [role="tab"] * {
    color: #475569 !important;
    font-weight: 600 !important;
}
[role="tab"][aria-selected="true"], [role="tab"][aria-selected="true"] * {
    color: #2563eb !important;
}
[data-baseweb="tab-highlight"], .react-aria-SelectionIndicator {
    background-color: #2563eb !important;
}
[data-baseweb="tab-border"] {
    background-color: #e2e8f0 !important;
}
[data-testid="stSpinner"], [data-testid="stSpinner"] * {
    color: #334155 !important;
}
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def load_assets():
    model = joblib.load("model/model.pkl")
    vectorizer = joblib.load("model/vectorizer.pkl")
    with open("model/metrics.json") as f:
        metrics = json.load(f)
    return model, vectorizer, metrics


model, vectorizer, metrics = load_assets()


def html(s):
    st.markdown(" ".join(s.split()), unsafe_allow_html=True)


CARD = "background:#ffffff;border:1px solid #e2e8f0;border-radius:14px;padding:22px 24px;box-shadow:0 1px 3px rgba(15,23,42,0.06);"


def stat_card(label, value, note):
    return (
        f'<div style="{CARD}flex:1 1 200px;">'
        f'<div style="font-size:13px;font-weight:600;color:#64748b;margin-bottom:8px;">{label}</div>'
        f'<div style="font-size:30px;font-weight:700;color:#0f172a;">{value}</div>'
        f'<div style="font-size:13px;color:#64748b;margin-top:6px;">{note}</div>'
        f'</div>'
    )


def prob_bar(label, pct, color):
    return (
        f'<div style="margin-bottom:14px;">'
        f'<div style="display:flex;justify-content:space-between;font-size:14px;font-weight:600;color:#334155;margin-bottom:6px;">'
        f'<span>{label}</span><span>{pct:.1f}%</span></div>'
        f'<div style="background:#e2e8f0;border-radius:999px;height:10px;overflow:hidden;">'
        f'<div style="background:{color};width:{pct}%;height:10px;border-radius:999px;"></div></div></div>'
    )


def pct(value):
    return f"{value * 100:.1f}%"


RED_FLAGS = [
    (
        "Asks for money",
        "Genuine employers do not charge candidates any fee.",
        [
            r"\b(?:registration|security|processing|training|joining|application|refundable)\s+(?:fee|deposit|charges?)\b",
            r"\bpay\s+(?:a\s+)?(?:small\s+)?(?:fee|deposit|amount)\b",
            r"\bsend\s+money\b",
        ],
    ),
    (
        "Asks for bank or ID details",
        "Banking and ID details are only needed after a formal offer, never at the start.",
        [
            r"\bbank\s+(?:account|details)\b",
            r"\b(?:debit|credit)\s+card\b",
            r"\b(?:aadhaar|aadhar|passport|ssn|social\s+security|otp)\b",
        ],
    ),
    (
        "Unrealistic pay or effortless work",
        "Very high pay for little work or no skills is a classic scam pattern.",
        [
            r"\bearn\s+(?:up\s+to\s+)?[$₹]?\s?\d[\d,]*\s*(?:dollars|usd|rupees|rs|inr)?\s*(?:per|a|every)?\s*(?:day|week|weekly|daily|month)\b",
            r"\bno\s+(?:experience|qualification|skills?)\s+(?:needed|required|necessary)\b",
            r"\bguaranteed\s+(?:income|salary|job|placement)\b",
            r"\beasy\s+money\b",
        ],
    ),
    (
        "Informal contact channels",
        "Real companies recruit through official email addresses and hiring platforms.",
        [
            r"\bwhats\s?app\b",
            r"\btelegram\b",
            r"\b(?:gmail|yahoo|hotmail)\b",
        ],
    ),
    (
        "Urgency and pressure",
        "Scammers rush candidates so they do not stop to check.",
        [
            r"\burgent(?:ly)?\b",
            r"\bimmediate(?:ly)?\s+(?:joining|start|hiring)\b",
            r"\blimited\s+(?:seats|vacancies|positions|slots)\b",
            r"\bhurry\b",
        ],
    ),
]


def find_red_flags(text):
    found = []
    for name, why, patterns in RED_FLAGS:
        hits = []
        for pattern in patterns:
            for m in re.finditer(pattern, text, flags=re.IGNORECASE):
                phrase = " ".join(m.group(0).split()).lower()
                if phrase not in hits:
                    hits.append(phrase)
        if hits:
            found.append((name, why, hits))
    return found


def flags_card(flags):
    header = '<div style="font-size:16px;font-weight:700;color:#0f172a;margin-bottom:6px;">Red flag scan</div>'
    if not flags:
        body = '<div style="font-size:15px;color:#15803d;line-height:1.6;">No common scam phrases were found in this posting.</div>'
        return f'<div style="{CARD}margin-top:16px;">{header}{body}</div>'
    rows = ""
    for name, why, hits in flags:
        chips = "".join(
            f'<span style="display:inline-block;background:#fee2e2;color:#b91c1c;font-size:13px;font-weight:600;padding:4px 10px;border-radius:999px;margin:6px 6px 0 0;">{escape(h)}</span>'
            for h in hits
        )
        rows += (
            f'<div style="padding:14px 0;border-top:1px solid #f1f5f9;">'
            f'<div style="font-size:15px;font-weight:700;color:#0f172a;">{name}</div>'
            f'<div style="font-size:14px;color:#64748b;margin-top:2px;">{why}</div>'
            f'<div>{chips}</div></div>'
        )
    count = f'<div style="font-size:14px;color:#64748b;margin-bottom:6px;">{len(flags)} warning sign(s) found in the text you pasted.</div>'
    return f'<div style="{CARD}margin-top:16px;">{header}{count}{rows}</div>'


html("""
<div style="background:linear-gradient(135deg,#0f172a 0%,#1e3a8a 100%);border-radius:18px;padding:36px 38px;margin-bottom:24px;">
<div style="display:inline-block;background:rgba(255,255,255,0.12);color:#bfdbfe;font-size:12px;font-weight:600;letter-spacing:0.08em;padding:6px 14px;border-radius:999px;margin-bottom:16px;">MACHINE LEARNING · TEXT CLASSIFICATION</div>
<div style="color:#ffffff;font-size:36px;font-weight:700;line-height:1.2;margin-bottom:10px;">Fake Job Posting Detector</div>
<div style="color:#cbd5e1;font-size:16px;line-height:1.6;max-width:640px;">Paste a job posting and get an instant estimate of whether it looks genuine or like a scam, powered by a Linear SVM text classifier.</div>
</div>
""")

tab_detect, tab_perf, tab_about = st.tabs(["Detector", "Model performance", "About"])

with tab_detect:
    c1, c2 = st.columns(2)
    with c1:
        title = st.text_input("Job title", placeholder="e.g. Marketing Intern")
    with c2:
        company = st.text_input("Company name", placeholder="e.g. Acme Corp")

    description = st.text_area("Job description", height=220, placeholder="Paste the full job description here (at least 30 words)...")

    analyze = st.button("Analyze posting")

    if analyze:
        if len(description.split()) < 30:
            html("""
            <div style="background:#fffbeb;border:1px solid #fde68a;border-radius:12px;padding:16px 20px;margin-top:16px;color:#92400e;font-size:15px;line-height:1.6;">
            <b>More detail needed.</b> Please paste the full job description (at least 30 words). A name or a few words is not enough for the model to judge.
            </div>
            """)
        else:
            with st.spinner("Analyzing posting..."):
                time.sleep(0.8)
                combined_text = f"{title} {company} {description}"
                vec = vectorizer.transform([combined_text])
                prediction = model.predict(vec)[0]
                proba = model.predict_proba(vec)[0]
                p_real = float(proba[0]) * 100
                p_fake = float(proba[1]) * 100

            if prediction == 1:
                bg, border, color = "#fef2f2", "#fecaca", "#b91c1c"
                headline = "Likely FAKE"
                message = "This posting shows patterns commonly found in fraudulent job ads. Do not share personal or payment details."
            else:
                bg, border, color = "#f0fdf4", "#bbf7d0", "#15803d"
                headline = "Likely REAL"
                message = "This posting looks consistent with genuine job ads. It is still worth verifying the company yourself."

            if p_fake >= 70:
                risk, risk_color, risk_bg = "High risk", "#b91c1c", "#fee2e2"
            elif p_fake >= 30:
                risk, risk_color, risk_bg = "Medium risk", "#b45309", "#fef3c7"
            else:
                risk, risk_color, risk_bg = "Low risk", "#15803d", "#dcfce7"

            html(f"""
            <div style="{CARD}margin-top:20px;">
            <div style="background:{bg};border:1px solid {border};border-radius:12px;padding:18px 20px;margin-bottom:20px;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px;">
            <div style="font-size:24px;font-weight:700;color:{color};">{headline}</div>
            <div style="background:{risk_bg};color:{risk_color};font-size:13px;font-weight:700;padding:6px 14px;border-radius:999px;">{risk}</div>
            </div>
            {prob_bar("Probability real", p_real, "#16a34a")}
            {prob_bar("Probability fake", p_fake, "#dc2626")}
            <div style="font-size:15px;color:#475569;line-height:1.6;margin-top:6px;">{message}</div>
            </div>
            """)

            flags = find_red_flags(combined_text)

            if prediction == 0 and len(flags) >= 2:
                html(f"""
                <div style="background:#fffbeb;border:1px solid #fde68a;border-radius:12px;padding:16px 20px;margin-top:16px;color:#92400e;font-size:15px;line-height:1.6;">
                <b>Be careful.</b> The model rates this posting as real, but {len(flags)} common scam warning signs were found in the text. Verify the company before you go further.
                </div>
                """)

            html(flags_card(flags))

            html("""
            <div style="background:#ffffff;border:1px solid #e2e8f0;border-radius:14px;padding:22px 24px;margin-top:16px;">
            <div style="font-size:16px;font-weight:700;color:#0f172a;margin-bottom:10px;">Stay safe checklist</div>
            <ul style="margin:0;padding-left:20px;color:#475569;font-size:15px;line-height:1.9;">
            <li>Never pay a registration, training or security fee to get a job.</li>
            <li>Do not share bank, card or ID details before a formal offer letter.</li>
            <li>Check the company's official website and make sure the recruiter email uses its domain.</li>
            <li>Be careful with recruiters who only use WhatsApp, Telegram or free email addresses.</li>
            </ul>
            </div>
            """)

with tab_perf:
    html(
        '<div style="display:flex;flex-wrap:wrap;gap:16px;margin-top:8px;margin-bottom:16px;">'
        + stat_card("Training accuracy", f"{metrics['training_accuracy']}%", "Data the model learned from")
        + stat_card("Validation accuracy", f"{metrics['validation_accuracy']}%", "Used to compare models")
        + stat_card("Testing accuracy", f"{metrics['test_accuracy']}%", "Never seen during training")
        + "</div>"
    )
    html(
        '<div style="display:flex;flex-wrap:wrap;gap:16px;margin-bottom:16px;">'
        + stat_card("Precision (fake)", pct(metrics["test_precision_fake"]), "Flagged postings that were truly fake")
        + stat_card("Recall (fake)", pct(metrics["test_recall_fake"]), "Fake postings the model caught")
        + stat_card("F1 score (fake)", pct(metrics["test_f1_fake"]), "Balance of precision and recall")
        + "</div>"
    )
    html("""
    <div style="background:#ffffff;border:1px solid #e2e8f0;border-radius:14px;padding:22px 24px;margin-bottom:16px;">
    <div style="font-size:16px;font-weight:700;color:#0f172a;margin-bottom:10px;">How to read these numbers</div>
    <div style="font-size:15px;color:#475569;line-height:1.7;">Training, validation and testing accuracy are close to each other, which shows the model is learning general patterns and not just memorizing its training data. Only about 5% of postings in the dataset are fake, so accuracy alone can look high even for a weak model. That is why the model was chosen using the F1 score on the fake class.</div>
    </div>
    """)
    html("""
    <div style="background:#ffffff;border:1px solid #e2e8f0;border-radius:14px;padding:22px 24px;">
    <div style="font-size:16px;font-weight:700;color:#0f172a;margin-bottom:14px;">Model comparison (validation set)</div>
    <div style="overflow-x:auto;">
    <table style="width:100%;border-collapse:collapse;font-size:15px;color:#334155;">
    <tr style="text-align:left;color:#64748b;font-size:13px;">
    <th style="padding:10px 12px;border-bottom:1px solid #e2e8f0;">Model</th>
    <th style="padding:10px 12px;border-bottom:1px solid #e2e8f0;">Training</th>
    <th style="padding:10px 12px;border-bottom:1px solid #e2e8f0;">Validation</th>
    <th style="padding:10px 12px;border-bottom:1px solid #e2e8f0;">F1 (fake)</th>
    </tr>
    <tr style="background:#eff6ff;font-weight:600;">
    <td style="padding:12px;">Linear SVM (selected)</td><td style="padding:12px;">99.92%</td><td style="padding:12px;">98.99%</td><td style="padding:12px;">0.892</td>
    </tr>
    <tr>
    <td style="padding:12px;border-top:1px solid #e2e8f0;">Random Forest</td><td style="padding:12px;border-top:1px solid #e2e8f0;">99.99%</td><td style="padding:12px;border-top:1px solid #e2e8f0;">98.66%</td><td style="padding:12px;border-top:1px solid #e2e8f0;">0.846</td>
    </tr>
    <tr>
    <td style="padding:12px;border-top:1px solid #e2e8f0;">Multinomial Naive Bayes</td><td style="padding:12px;border-top:1px solid #e2e8f0;">98.53%</td><td style="padding:12px;border-top:1px solid #e2e8f0;">98.36%</td><td style="padding:12px;border-top:1px solid #e2e8f0;">0.815</td>
    </tr>
    </table>
    </div>
    </div>
    """)

with tab_about:
    recall_pct = round(metrics["test_recall_fake"] * 100)
    steps = [
        ("1", "Text to numbers", "The title, company and description are combined and converted into TF-IDF features, which measure how important each word and word pair is."),
        ("2", "Classification", "A calibrated Linear SVM classifier compares those features with patterns learned from thousands of real and fake postings."),
        ("3", "Probability", "The classifier outputs the probability that the posting is real or fake, shown as the verdict and risk level. A separate rule-based scan also lists common scam phrases found in the text."),
    ]
    cards = "".join(
        f'<div style="{CARD}flex:1 1 260px;">'
        f'<div style="width:34px;height:34px;border-radius:50%;background:#dbeafe;color:#1d4ed8;font-weight:700;display:flex;align-items:center;justify-content:center;margin-bottom:12px;">{n}</div>'
        f'<div style="font-size:16px;font-weight:700;color:#0f172a;margin-bottom:6px;">{t}</div>'
        f'<div style="font-size:14px;color:#475569;line-height:1.6;">{d}</div></div>'
        for n, t, d in steps
    )
    html(f'<div style="display:flex;flex-wrap:wrap;gap:16px;margin-top:8px;margin-bottom:16px;">{cards}</div>')
    html(f"""
    <div style="background:#ffffff;border:1px solid #e2e8f0;border-radius:14px;padding:22px 24px;margin-bottom:16px;">
    <div style="font-size:16px;font-weight:700;color:#0f172a;margin-bottom:10px;">Dataset</div>
    <div style="font-size:15px;color:#475569;line-height:1.7;">Trained on the Kaggle dataset "Real or Fake Job Posting Prediction" with 17,880 job postings, of which about 5% are labelled fraudulent. The data was split into 70% training, 15% validation and 15% testing.</div>
    </div>
    <div style="background:#fffbeb;border:1px solid #fde68a;border-radius:14px;padding:22px 24px;">
    <div style="font-size:16px;font-weight:700;color:#92400e;margin-bottom:10px;">Limitations</div>
    <div style="font-size:15px;color:#92400e;line-height:1.7;">This tool gives an estimate, not a guarantee. On the test set it caught about {recall_pct}% of fake postings, so some scams can still look real to it. Always verify a company independently before sharing personal or payment details.</div>
    </div>
    """)