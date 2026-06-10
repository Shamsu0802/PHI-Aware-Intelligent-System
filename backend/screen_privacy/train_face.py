import os
import cv2
import numpy as np
import torch
from facenet_pytorch import InceptionResnetV1

device = torch.device("cpu")

model = InceptionResnetV1(pretrained="vggface2").eval().to(device)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATA_DIR = os.path.join(BASE_DIR, "face_data", "authorized")

MODEL_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "models"))
os.makedirs(MODEL_DIR, exist_ok=True)

EMBEDDING_PATH = os.path.join(MODEL_DIR, "authorized_embeddings.npy")
LABEL_PATH = os.path.join(MODEL_DIR, "authorized_labels.npy")

def preprocess_face(img_path):

    img = cv2.imread(img_path)

    if img is None:
        return None

    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = cv2.resize(img, (160, 160))

    img = img.astype(np.float32) / 255.0
    img = np.transpose(img, (2, 0, 1))

    return torch.tensor(img).unsqueeze(0).to(device)


print("🔹 Computing FaceNet embeddings...")

embeddings = []
labels = []

people = os.listdir(DATA_DIR)

for person in people:

    person_dir = os.path.join(DATA_DIR, person)

    if not os.path.isdir(person_dir):
        continue

    images = os.listdir(person_dir)

    for file_name in images:

        if not file_name.lower().endswith((".jpg",".jpeg",".png")):
            continue

        img_path = os.path.join(person_dir, file_name)

        face_tensor = preprocess_face(img_path)

        if face_tensor is None:
            continue

        with torch.no_grad():
            embedding = model(face_tensor).cpu().numpy()[0]

        embeddings.append(embedding)
        labels.append(person)

        print(f"✔ {person} → {file_name}")

embeddings = np.array(embeddings)
labels = np.array(labels)

np.save(EMBEDDING_PATH, embeddings)
np.save(LABEL_PATH, labels)

print("\n✅ Face enrollment complete")
print(f"Embeddings: {embeddings.shape}")
print(f"Labels saved: {len(labels)}")