import streamlit as st
import joblib

st.set_page_config(page_title="Fake Job Posting Detector", page_icon="🔍")

model = joblib.load("model/model.pkl")
vectorizer = joblib.load("model/vectorizer.pkl")

st.title("🔍 Fake Job Posting Detector")
st.write("Paste a job posting below to check if it looks real or fake.")

job_text = st.text_area("Job posting text", height=250, placeholder="Paste the job title, description, requirements...")

if st.button("Check Posting"):
    if job_text.strip() == "":
        st.warning("Please paste a job posting first.")
    else:
        vec = vectorizer.transform([job_text])
        prediction = model.predict(vec)[0]
        proba = model.predict_proba(vec)[0]
        confidence = round(max(proba) * 100, 2)

        if prediction == 1:
            st.error(f"⚠️ This posting looks **FAKE** — {confidence}% confidence")
        else:
            st.success(f"✅ This posting looks **REAL** — {confidence}% confidence")