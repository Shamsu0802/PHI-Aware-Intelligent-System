import os
import cv2
import numpy as np
import joblib
from skimage.feature import hog
from sklearn.svm import LinearSVC
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

# ==================== PATHS ====================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PHONE_DIR = os.path.join(BASE_DIR, "data", "phone_classifier_data", "phone")
NOT_PHONE_DIR = os.path.join(BASE_DIR, "data", "phone_classifier_data", "not_phone")

MODEL_DIR = os.path.join(BASE_DIR, "models")
os.makedirs(MODEL_DIR, exist_ok=True)

MODEL_PATH = os.path.join(MODEL_DIR, "phone_svm.pkl")

# ==================== LOAD DATA ====================
X = []
y = []

def load_images(folder, label):
    for img_name in os.listdir(folder):
        img_path = os.path.join(folder, img_name)
        img = cv2.imread(img_path)
        if img is None:
            continue

        img = cv2.resize(img, (64, 128))
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        features = hog(
            gray,
            orientations=9,
            pixels_per_cell=(8, 8),
            cells_per_block=(2, 2),
            block_norm="L2-Hys"
        )

        X.append(features)
        y.append(label)

print("🔹 Loading phone images...")
load_images(PHONE_DIR, 1)

print("🔹 Loading non-phone images...")
load_images(NOT_PHONE_DIR, 0)

X = np.array(X)
y = np.array(y)

print("📊 Dataset size:", X.shape)

# ==================== TRAIN / TEST SPLIT ====================
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# ==================== MODEL ====================
model = Pipeline([
    ("scaler", StandardScaler()),
    ("svm", LinearSVC(max_iter=5000))
])

print("🚀 Training SVM...")
model.fit(X_train, y_train)

# ==================== EVALUATION ====================
y_pred = model.predict(X_test)
print("\n📈 Classification Report:")
print(classification_report(y_test, y_pred))

# ==================== SAVE MODEL ====================
joblib.dump(model, MODEL_PATH)
print(f"\n✅ Model saved at: {MODEL_PATH}")