# TruthLens - Fake News Detection System 🧠📰

**TruthLens** is an AI-powered full-stack fake news detection web app built with Python Flask and BERT-based NLP model. Developed during a virtual internship at **Pinnacle Labs**, it provides real-time prediction, analytics, and user feedback for detecting misinformation.

---

## 🚀 Key Features

- 🤖 **AI-Powered Prediction**
  - Uses a fine-tuned DistilBERT model trained on the LIAR dataset for binary classification (FAKE or REAL).
- 🔐 **User Authentication**
  - Secure login/signup with hashed passwords using Flask-Login.
- 📈 **Analytics Dashboard**
  - View total predictions, feedback accuracy, and interactive charts (via Chart.js).
- 📂 **Prediction History + Search**
  - Stores per-user prediction history in SQLite3 with filtering/search support.
- 📰 **Live News Headlines**
  - Integrates with News API to fetch and analyze latest headlines in real-time.
- 👍 **Feedback System**
  - Users can rate each prediction (accurate or wrong) to help improve the system.
- 🧪 **Confidence Score**
  - Each prediction includes a probability score from the model.
- 💾 **CSV Export**
  - Download prediction history in CSV format.
- 🎨 **Modern UI + Responsive Design**
  - Fully mobile-friendly layout with animated transitions and dark/light support.

---

## 🧰 Tech Stack

### 🔧 Backend
- Python
- Flask (with Jinja2 templating)
- Flask-Login
- SQLite3
- HuggingFace Transformers
- scikit-learn
- Joblib

### 🌐 Frontend
- HTML5, CSS3, JavaScript
- Chart.js
- Font Awesome

### 🧠 Machine Learning
- Model: DistilBERT (fine-tuned)
- Dataset: [LIAR dataset](https://www.cs.ucsb.edu/~william/data/liar_dataset.zip)
- Binary Labels: Fake = ["pants-fire", "false", "barely-true"], Real = ["half-true", "mostly-true", "true"]
- Text preprocessing included: lowercasing, punctuation removal, etc.

---

## 📁 Folder Structure

TruthLens/
│
├── bert_model/ # Fine-tuned DistilBERT model
├── bert_tokenizer/ # Tokenizer for DistilBERT
├── database/ # SQLite DBs (auth.db, feedback.db, truthlens.db)
├── liar_dataset/ # LIAR dataset (train.tsv, test.tsv, valid.tsv)
├── static/ # CSS, JS, Images
├── templates/ # HTML pages
├── train_bert_liar.py # BERT training script
├── predict_bert.py # Prediction using BERT model
├── app.py # Flask backend
├── config.py # Config file (paths, DB locations)
├── requirements.txt # Python dependencies
└── README.md # This file


---

## ⚙️ Setup Instructions

### 1️⃣ Clone the Repo
```bash
git clone https://github.com/yourusername/TruthLens.git
cd TruthLens


2️⃣ Create Virtual Environment

python -m venv venv
# Activate it
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate


3️⃣ Install Dependencies

pip install -r requirements.txt
4️⃣ Download LIAR Dataset
Manually download LIAR dataset:
🔗 LIAR Dataset (zip)
Extract files into: liar_dataset/

Make sure you have:

train.tsv

valid.tsv

test.tsv


5️⃣ Train BERT Model

python train_bert_liar.py
➡️ Outputs saved to: bert_model/ and bert_tokenizer/


6️⃣ Run the Web App

python app.py
Then open http://localhost:5000

🔒 Security Notes
Don’t use app.run(debug=True) in production

Set a secure secret key in app.secret_key

Use HTTPS + WSGI server (Gunicorn / uWSGI) behind Nginx for deployment

Recommended: use .env files for sensitive configs

🧠 Future Plans
 Integrate BERT model ✅

 Admin panel to view user feedback

 Host on Render or Vercel

 Continuous retraining pipeline

👨‍💻 Developer
Built with 💪 by Pranav (CS Student, MIT Academy of Engineering)
🏢 Internship: Pinnacle Labs
📌 From frontend → backend → ML training → deployment — this is a solo build project.

Let’s connect on LinkedIn 🔗 and work on more cool stuff together! 🚀


📄 License
MIT License — open source for learning and non-commercial use.
PRs and contributions welcome!