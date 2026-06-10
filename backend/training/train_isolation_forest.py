#train_isolation_forest.py

import pandas as pd
import joblib
import numpy as np
import os

from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

from backend.features.feature_extractor import extract_features

# -------------------- PATH SETUP --------------------

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATA_PATH = os.path.join(
    BASE_DIR, "..", "healthcare_comm_logs_runtime_clean.csv"
)

MODEL_PATH = os.path.join(
    BASE_DIR, "models", "isolation_forest.pkl"
)

# -------------------- LOAD DATA --------------------

print("Loading dataset...")
df = pd.read_csv(DATA_PATH)
print(f"Total records loaded: {len(df)}")

# -------------------- FEATURE EXTRACTION --------------------

print("Extracting features...")

X = []
for _, row in df.iterrows():
    feature_row = {
        "entities": row.get("entities", "[]"),
        "recipient_type": row.get("recipient_type"),
        "attachment_present": row.get("attachment_present"),
        "time_of_day": row.get("time_of_day"),
        "content": row.get("content", "")
    }
    X.append(extract_features(feature_row))

X = np.array(X)

print(f"Raw feature matrix shape: {X.shape}")

# -------------------- FEATURE METADATA (NEW) --------------------

FEATURE_NAMES = [
    "num_entities",
    "num_identifiers",
    "num_persons",
    "num_medical_terms",
    "masked_ratio",
    "identity_linkage",
    "recipient_external",
    "attachment_present",
    "late_night",
    "message_length_norm"
]

# -------------------- FEATURE NORMALIZATION --------------------

print("Normalizing features...")
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# -------------------- TRAIN ISOLATION FOREST --------------------

print("Training Isolation Forest...")
iso_forest = IsolationForest(
    n_estimators=200,
    contamination=0.05,
    random_state=42,
    n_jobs=-1
)

iso_forest.fit(X_scaled)

# -------------------- TRAINING DIAGNOSTICS --------------------

anomaly_scores = iso_forest.decision_function(X_scaled)

print("Training diagnostics:")
print(f"  Mean anomaly score: {np.mean(anomaly_scores):.4f}")
print(f"  Std anomaly score : {np.std(anomaly_scores):.4f}")
print(f"  Min anomaly score : {np.min(anomaly_scores):.4f}")
print(f"  Max anomaly score : {np.max(anomaly_scores):.4f}")

# -------------------- BASELINE BEHAVIOR STATS (NEW) --------------------

baseline_stats = {
    "feature_names": FEATURE_NAMES,
    "mean": np.mean(X_scaled, axis=0).tolist(),
    "std": np.std(X_scaled, axis=0).tolist(),
    "p10": np.percentile(X_scaled, 10, axis=0).tolist(),
    "p90": np.percentile(X_scaled, 90, axis=0).tolist(),
}

# -------------------- SAVE MODEL ARTIFACT --------------------

print("Saving model artifact...")

model_artifact = {
    "model": iso_forest,
    "scaler": scaler,
    "baseline_stats": baseline_stats,
    "feature_count": X.shape[1]
}

joblib.dump(model_artifact, MODEL_PATH)

print("Isolation Forest training completed successfully.")
