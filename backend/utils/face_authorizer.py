import cv2
import os
import numpy as np
import torch
from facenet_pytorch import InceptionResnetV1

# -------------------------------------------------
# DEVICE (CPU ONLY – STABLE FOR FINAL YEAR DEMO)
# -------------------------------------------------
device = torch.device("cpu")

# -------------------------------------------------
# GLOBAL CACHED OBJECTS
# -------------------------------------------------
_facenet_model = None
_authorized_embeddings = None
_authorized_labels = None

# -------------------------------------------------
# PATH SETUP (ROBUST)
# -------------------------------------------------
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

EMBEDDING_PATH = os.path.join(BACKEND_DIR, "models", "authorized_embeddings.npy")
LABEL_PATH = os.path.join(BACKEND_DIR, "models", "authorized_labels.npy")

if not os.path.exists(EMBEDDING_PATH):
    raise FileNotFoundError(
        "❌ authorized_embeddings.npy not found. Run train_face.py first."
    )

if not os.path.exists(LABEL_PATH):
    raise FileNotFoundError(
        "❌ authorized_labels.npy not found. Run train_face.py first."
    )

# -------------------------------------------------
# FACE DETECTOR
# -------------------------------------------------
face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)

# -------------------------------------------------
# PARAMETERS
# -------------------------------------------------
DISTANCE_THRESHOLD = 0.95
FACE_PADDING = 10


# -------------------------------------------------
# LOADERS
# -------------------------------------------------
def _load_facenet():
    global _facenet_model

    if _facenet_model is None:
        _facenet_model = (
            InceptionResnetV1(pretrained="vggface2")
            .eval()
            .to(device)
        )

    return _facenet_model


def _load_authorized_embeddings():
    global _authorized_embeddings

    if _authorized_embeddings is None:

        emb = np.load(EMBEDDING_PATH)

        if emb.ndim == 1:
            emb = emb.reshape(1, -1)

        norms = np.linalg.norm(emb, axis=1, keepdims=True)
        norms[norms == 0] = 1e-6
        emb = emb / norms

        _authorized_embeddings = emb

    return _authorized_embeddings


def _load_authorized_labels():
    global _authorized_labels

    if _authorized_labels is None:
        _authorized_labels = np.load(LABEL_PATH)

    return _authorized_labels


# -------------------------------------------------
# PREPROCESS FACE
# -------------------------------------------------
def preprocess_face(face_bgr):

    face_rgb = cv2.cvtColor(face_bgr, cv2.COLOR_BGR2RGB)
    face_rgb = cv2.resize(face_rgb, (160, 160))

    face_rgb = face_rgb.astype(np.float32) / 255.0
    face_rgb = np.transpose(face_rgb, (2, 0, 1))

    return torch.tensor(face_rgb).unsqueeze(0).to(device)


# -------------------------------------------------
# CORE AUTHORIZATION FUNCTION
# -------------------------------------------------
def is_authorized(frame, debug=False, return_face_count=False):

    if frame is None:
        return (False, None, None, 0)

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    faces = face_cascade.detectMultiScale(
        gray,
        scaleFactor=1.2,
        minNeighbors=3,
        minSize=(50, 50)
    )

    face_count = int(len(faces))

    # -------------------------------------------------
    # NO FACE OR MULTIPLE FACES
    # -------------------------------------------------
    if face_count != 1:
        return (False, None, None, face_count)

    (x, y, w, h) = faces[0]

    x1 = max(0, x - FACE_PADDING)
    y1 = max(0, y - FACE_PADDING)
    x2 = min(frame.shape[1], x + w + FACE_PADDING)
    y2 = min(frame.shape[0], y + h + FACE_PADDING)

    face_bgr = frame[y1:y2, x1:x2]

    facenet = _load_facenet()
    authorized_embeddings = _load_authorized_embeddings()
    labels = _load_authorized_labels()

    face_tensor = preprocess_face(face_bgr)

    with torch.no_grad():
        test_embedding = facenet(face_tensor).cpu().numpy()[0]

    norm = np.linalg.norm(test_embedding)

    if norm == 0:
        return (False, None, None, face_count)

    test_embedding = test_embedding / norm

    distances = np.linalg.norm(
        authorized_embeddings - test_embedding,
        axis=1
    )

    best_index = int(np.argmin(distances))
    min_distance = float(distances[best_index])

    name = str(labels[best_index])

    authorized = bool(min_distance < DISTANCE_THRESHOLD)

    confidence = float(max(0, 1 - min_distance) * 100)

    if debug:
        print(f"[DEBUG] Face count     : {face_count}")
        print(f"[DEBUG] Min distance   : {min_distance:.4f}")
        print(f"[DEBUG] Identity       : {name}")
        print(f"[DEBUG] Confidence     : {confidence:.2f}%")

    return (authorized, name, confidence, face_count)