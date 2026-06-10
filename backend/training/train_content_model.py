#train_content_model.py

import pandas as pd
import joblib
import json
import os

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

# -------------------- PATHS --------------------

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATA_PATH = os.path.join(
    BASE_DIR, "data", "healthcare_comm_logs_runtime_clean.csv"
)

MODEL_PATH = os.path.join(
    BASE_DIR, "models", "content_sensitivity_model.pkl"
)

# -------------------- LOAD DATA --------------------

print("Loading dataset...")
df = pd.read_csv(DATA_PATH)

# -------------------- WEAK LABEL GENERATION --------------------
# NOTE: No hardcoded PHI rules — only weak signals

def weak_label(row):
    """
    Generates soft labels based on natural risk signals.
    This is weak supervision, NOT rule-based enforcement.
    """
    score = 0

    # Presence of detected entities
    try:
        entities = json.loads(row["entities"])
        score += len(entities)
    except:
        pass

    # External communication
    if row["recipient_type"] == "external":
        score += 2

    # Attachments raise sensitivity
    if row["attachment_present"]:
        score += 1

    # Late-night activity is riskier
    if row["time_of_day"] == "late_night":
        score += 1

    return 1 if score >= 3 else 0


print("Generating weak labels...")
df["label"] = df.apply(weak_label, axis=1)

# -------------------- MODEL PIPELINE --------------------

pipeline = Pipeline([
    ("tfidf", TfidfVectorizer(
        max_features=5000,
        ngram_range=(1, 2),
        stop_words="english"
    )),
    ("clf", LogisticRegression(
        max_iter=1000,
        class_weight="balanced"
    ))
])

# -------------------- TRAIN --------------------

print("Training content sensitivity model...")
pipeline.fit(df["text"], df["label"])

# -------------------- SAVE MODEL --------------------

os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
joblib.dump(pipeline, MODEL_PATH)

print("Content sensitivity model trained and saved successfully.")
