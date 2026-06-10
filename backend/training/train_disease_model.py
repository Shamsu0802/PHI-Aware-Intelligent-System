import pandas as pd
import joblib
import os

from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score

# ------------------ PATHS ------------------

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATA_PATH = os.path.join(BASE_DIR, "data", "Symptom2Disease.csv")
MODEL_DIR = os.path.join(BASE_DIR, "models")

os.makedirs(MODEL_DIR, exist_ok=True)

# ------------------ LOAD DATA ------------------

df = pd.read_csv(DATA_PATH)

df = df.rename(columns={
    "text": "symptoms",
    "label": "disease"
})

X = df["symptoms"]
y = df["disease"]

# ------------------ TRAIN / TEST SPLIT ------------------

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# ------------------ TF-IDF ------------------

vectorizer = TfidfVectorizer(
    stop_words="english",
    max_features=5000
)

X_train_vec = vectorizer.fit_transform(X_train)
X_test_vec = vectorizer.transform(X_test)

# ------------------ MODEL ------------------

model = LogisticRegression(max_iter=1000)
model.fit(X_train_vec, y_train)

# ------------------ EVALUATION ------------------

y_pred = model.predict(X_test_vec)
acc = accuracy_score(y_test, y_pred)

print(f"✅ Disease Model Accuracy: {acc * 100:.2f}%")

# ------------------ SAVE MODEL ------------------

joblib.dump(model, os.path.join(MODEL_DIR, "disease_model.pkl"))
joblib.dump(vectorizer, os.path.join(MODEL_DIR, "disease_vectorizer.pkl"))

print("✅ Model and vectorizer saved successfully")
