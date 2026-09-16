from flask import Flask, render_template, request
import joblib

app = Flask(__name__)

model = joblib.load("model/model.pkl")
vectorizer = joblib.load("model/vectorizer.pkl")

@app.route("/", methods=["GET", "POST"])
def home():
    result = None
    confidence = None

    if request.method == "POST":
        job_text = request.form["job_text"]
        vec = vectorizer.transform([job_text])
        prediction = model.predict(vec)[0]
        proba = model.predict_proba(vec)[0]

        result = "FAKE" if prediction == 1 else "REAL"
        confidence = round(max(proba) * 100, 2)

    return render_template("index.html", result=result, confidence=confidence)

if __name__ == "__main__":
    app.run(debug=True)