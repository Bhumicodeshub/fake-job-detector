import streamlit as st
import joblib
import time
import json

st.set_page_config(page_title="Fake Job Posting Detector", page_icon="🔍", layout="centered")

st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}
.block-container {
    background: white;
    border-radius: 16px;
    padding: 2.5rem;
    box-shadow: 0 20px 50px rgba(0,0,0,0.2);
    margin-top: 2rem;
    max-width: 700px;
}
h1, .stMarkdown p, label, .stCaption {
    color: #2c3e50 !important;
}
.stTextInput input, .stTextArea textarea {
    background-color: #f4f6f8 !important;
    color: #2c3e50 !important;
    border: 1px solid #ccc !important;
}
.stTextInput input::placeholder, .stTextArea textarea::placeholder {
    color: #8a94a0 !important;
    -webkit-text-fill-color: #8a94a0 !important;
    opacity: 1 !important;
}
.stButton>button {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white !important;
    font-weight: 600;
    border: none;
    border-radius: 10px;
    padding: 0.6rem 1.5rem;
    width: 100%;
}
.stButton>button:hover {
    box-shadow: 0 8px 20px rgba(118, 75, 162, 0.4);
}
</style>
""", unsafe_allow_html=True)

model = joblib.load("model/model.pkl")
vectorizer = joblib.load("model/vectorizer.pkl")

with open("model/metrics.json") as f:
    metrics = json.load(f)


def box(text, bg, border, color):
    st.markdown(
        f'<div style="background:{bg};border-left:5px solid {border};color:{color};'
        f'padding:14px 18px;border-radius:10px;margin:12px 0;font-size:16px;">{text}</div>',
        unsafe_allow_html=True,
    )


st.title("🔍 Fake Job Posting Detector")
st.write("Fill in the details of a job posting to check if it looks real or fake.")

st.markdown(
    f"""
<div style="background:#f4f6f8;border-radius:12px;padding:16px;margin:12px 0;">
  <div style="font-weight:600;color:#2c3e50;margin-bottom:10px;">📊 Model performance: Linear SVM</div>
  <div style="display:flex;gap:12px;text-align:center;">
    <div style="flex:1;">
      <div style="font-size:13px;color:#2c3e50;">Training accuracy</div>
      <div style="font-size:28px;font-weight:700;color:#2c3e50;">{metrics['training_accuracy']}%</div>
    </div>
    <div style="flex:1;">
      <div style="font-size:13px;color:#2c3e50;">Validation accuracy</div>
      <div style="font-size:28px;font-weight:700;color:#2c3e50;">{metrics['validation_accuracy']}%</div>
    </div>
    <div style="flex:1;">
      <div style="font-size:13px;color:#2c3e50;">Testing accuracy</div>
      <div style="font-size:28px;font-weight:700;color:#2c3e50;">{metrics['test_accuracy']}%</div>
    </div>
  </div>
</div>
""",
    unsafe_allow_html=True,
)

col1, col2 = st.columns(2)
with col1:
    title = st.text_input("Job Title", placeholder="e.g. Marketing Intern")
with col2:
    company = st.text_input("Company Name", placeholder="e.g. Acme Corp")

description = st.text_area("Job Description", height=220, placeholder="Paste the full job description here...")

if st.button("🔎 Analyze Posting"):
    combined_text = f"{title} {company} {description}"

    if len(description.split()) < 30:
        box(
            "Please paste the full job description (at least 30 words). A name or a few words is not enough for the model to judge.",
            "#fff8e1", "#f1c40f", "#7d6608",
        )
    else:
        with st.spinner("Analyzing posting..."):
            time.sleep(0.8)
            vec = vectorizer.transform([combined_text])
            prediction = model.predict(vec)[0]
            proba = model.predict_proba(vec)[0]
            confidence = round(max(proba) * 100, 2)

        st.markdown("---")
        if prediction == 1:
            box("<b style='font-size:20px;'>⚠️ This posting looks FAKE</b>", "#fdecea", "#e74c3c", "#c0392b")
            st.progress(int(confidence))
            box(f"<b>Confidence: {confidence}%</b>", "#f4f6f8", "#c0c6cc", "#2c3e50")
            box(
                "Watch out for: vague company details, unrealistic pay, requests for personal/bank info, urgency language, generic email domains.",
                "#f4f6f8", "#c0c6cc", "#555555",
            )
        else:
            box("<b style='font-size:20px;'>✅ This posting looks REAL</b>", "#e6f9ec", "#2ecc71", "#1e8449")
            st.progress(int(confidence))
            box(f"<b>Confidence: {confidence}%</b>", "#f4f6f8", "#c0c6cc", "#2c3e50")