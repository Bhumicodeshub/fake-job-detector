# Fake Job Posting Detector

A machine-learning web app that estimates whether a job posting is genuine or a scam. It combines a Linear SVM text classifier with a rule-based red flag scan and a recruiter email check.

**Live demo:** https://fake-job-detector-f7c4dqmurkcjavbqgcxbul.streamlit.app/

## Features

- Classifies a job posting as real or fake, with a probability and a risk level
- Red flag scan that lists scam phrases found in the text, such as registration fees, bank detail requests, unrealistic pay, WhatsApp or Gmail contact and urgency pressure
- Recruiter email check that warns about free email addresses and domains that do not match the company
- Quick links to verify a company through search, LinkedIn and its official website
- Optional fields for company profile, requirements and benefits
- A model performance tab showing training, validation and testing accuracy

## Model and results

The job title, company profile, description, requirements and benefits are combined into one text and converted to numbers using TF-IDF (single words and word pairs, 20,000 features). Three classifiers were trained and compared on a separate validation set. A Linear SVM was selected based on the F1 score for the fake class, then calibrated so it can output probabilities.

| Model | Training accuracy | Validation accuracy | Validation F1 (fake) |
|---|---|---|---|
| Linear SVM (selected) | 99.92% | 98.99% | 0.892 |
| Random Forest | 99.99% | 98.66% | 0.846 |
| Multinomial Naive Bayes | 98.53% | 98.36% | 0.815 |

Final model on the held-out test set:

| Metric | Value |
|---|---|
| Training accuracy | 99.92% |
| Validation accuracy | 99.03% |
| Testing accuracy | 98.77% |
| Precision (fake) | 96.2% |
| Recall (fake) | 77.7% |
| F1 score (fake) | 86.0% |

Only about 5% of the postings are fake, so accuracy alone is not enough. This is why the F1 score on the fake class was used to choose the model.

## Dataset

[Real or Fake Job Posting Prediction](https://www.kaggle.com/datasets/shivamb/real-or-fake-fake-jobposting-prediction) from Kaggle: 17,880 job postings, 866 labelled fraudulent. The data was split 70% training, 15% validation and 15% testing, keeping the same fake-to-real ratio in each part.

## Project structure

```
fake-job-detector/
├── data/
│   ├── fake_job_postings.csv
│   └── explore.ipynb
├── model/
│   ├── model.pkl
│   ├── vectorizer.pkl
│   └── metrics.json
├── streamlit_app.py
├── requirements.txt
└── README.md
```

## Run locally

```
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
streamlit run streamlit_app.py
```

To retrain the model, install `pandas` and `jupyter`, then run all cells in `data/explore.ipynb`. It saves the new model, vectorizer and metrics into the `model` folder.

## Limitations

- The model only reads text. It cannot confirm that a company exists, and a copied genuine description can fool it.
- On the test set it caught about 78% of fake postings, so some scams can still look real.
- The red flag scan and email check are rule-based and can produce false alarms.
- It gives an estimate, not a guarantee. Always verify a company independently.

## Tech stack

Python, scikit-learn, pandas, Streamlit