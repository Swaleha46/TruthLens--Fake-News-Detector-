# config.py
import os

DB_DIR = "database"
MODEL_DIR = "models"

AUTH_DB = os.path.join(DB_DIR, "auth.db")
FEEDBACK_DB = os.path.join(DB_DIR, "feedback.db")
TRUTH_DB = os.path.join(DB_DIR, "truthlens.db")

MODEL_FILE = os.path.join(MODEL_DIR, "finalized_model.pkl")
VECTORIZER_FILE = os.path.join(MODEL_DIR, "vectorizer.pkl")
