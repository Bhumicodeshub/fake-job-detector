import streamlit as st
import joblib
import time

st.set_page_config(page_title="Fake Job Posting Detector", page_icon="🔍", layout="centered")

# Custom styling
st.markdown("""
<style>
.main {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}
.block-container {
    background: white;
    border-radius: 16px;
    padding: 2.5rem;
    box-shadow: 0 20px 50px rgba(0,0,0,0.2);
    margin-top: 2rem;
}
h1 {
    color: #2c3e50;
}
.stButton>button {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
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

st.title("🔍 Fake Job Posting Detector")
st.write("Fill in the details of a job posting to check if it looks real or fake.")

col1, col2 = st.columns(2)
with col1:
    title = st.text_input("Job Title", placeholder="e.g. Marketing Intern")
with col2:
    company = st.text_input("Company Name", placeholder="e.g. Acme Corp")

description = st.text_area("Job Description", height=180, placeholder="Paste the full job description here...")
requirements = st.text_area("Requirements (optional)", height=100, placeholder="Skills, experience, qualifications...")
benefits = st.text_area("Benefits (optional)", height=100, placeholder="Salary, perks, benefits offered...")

if st.button("🔎 Analyze Posting"):
    combined_text = f"{title} {company} {description} {requirements} {benefits}"

    if combined_text.strip() == "":
        st.warning("Please fill in at least the job title and description.")
    else:
        with st.spinner("Analyzing posting..."):
            time.sleep(0.8)
            vec = vectorizer.transform([combined_text])
            prediction = model.predict(vec)[0]
            proba = model.predict_proba(vec)[0]
            confidence = round(max(proba) * 100, 2)

        st.markdown("---")
        if prediction == 1:
            st.error(f"### ⚠️ This posting looks **FAKE**")
            st.progress(int(confidence))
            st.write(f"**Confidence: {confidence}%**")
            st.caption("Watch out for: vague company details, unrealistic pay, requests for personal/bank info, urgency language, generic email domains.")
        else:
            st.success(f"### ✅ This posting looks **REAL**")
            st.progress(int(confidence))
            st.write(f"**Confidence: {confidence}%**")