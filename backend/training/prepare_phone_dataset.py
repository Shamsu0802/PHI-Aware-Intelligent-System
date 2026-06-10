import os
import cv2
import random

# ==================== PATHS ====================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

IMAGE_DIR = os.path.join(BASE_DIR, "data", "cell phone")
LABEL_DIR = os.path.join(BASE_DIR, "data", "cell phone", "labels")

PHONE_DIR = os.path.join(BASE_DIR, "data", "phone_classifier_data", "phone")
NOT_PHONE_DIR = os.path.join(BASE_DIR, "data", "phone_classifier_data", "not_phone")

os.makedirs(PHONE_DIR, exist_ok=True)
os.makedirs(NOT_PHONE_DIR, exist_ok=True)

# ==================== HELPERS ====================
def yolo_to_bbox(xc, yc, w, h, img_w, img_h):
    x1 = int((xc - w / 2) * img_w)
    y1 = int((yc - h / 2) * img_h)
    x2 = int((xc + w / 2) * img_w)
    y2 = int((yc + h / 2) * img_h)

    return max(0, x1), max(0, y1), min(img_w, x2), min(img_h, y2)

# ==================== MAIN ====================
phone_count = 0
not_phone_count = 0

for img_name in os.listdir(IMAGE_DIR):
    if not img_name.lower().endswith((".jpg", ".png", ".jpeg")):
        continue

    img_path = os.path.join(IMAGE_DIR, img_name)
    label_path = os.path.join(LABEL_DIR, img_name.replace(".jpg", ".txt"))

    if not os.path.exists(label_path):
        continue

    img = cv2.imread(img_path)
    if img is None:
        continue

    h, w, _ = img.shape

    with open(label_path, "r") as f:
        lines = f.readlines()

    for line in lines:
        parts = line.strip().split()
        if len(parts) != 5:
            continue

        _, xc, yc, bw, bh = map(float, parts)

        x1, y1, x2, y2 = yolo_to_bbox(xc, yc, bw, bh, w, h)

        phone_crop = img[y1:y2, x1:x2]
        if phone_crop.size == 0:
            continue

        phone_crop = cv2.resize(phone_crop, (64, 128))
        cv2.imwrite(
            os.path.join(PHONE_DIR, f"phone_{phone_count}.jpg"),
            phone_crop
        )
        phone_count += 1

        # -------- Negative sample --------
        for _ in range(2):
            rx = random.randint(0, w - 64)
            ry = random.randint(0, h - 128)

            neg_crop = img[ry:ry+128, rx:rx+64]
            if neg_crop.size == 0:
                continue

            neg_crop = cv2.resize(neg_crop, (64, 128))
            cv2.imwrite(
                os.path.join(NOT_PHONE_DIR, f"not_{not_phone_count}.jpg"),
                neg_crop
            )
            not_phone_count += 1

print("✅ Dataset preparation complete")
print(f"📱 Phone images: {phone_count}")
print(f"🚫 Non-phone images: {not_phone_count}")
