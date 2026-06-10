import cv2
import os
import time

"""
Face Enrollment Script (FINAL – FACENET COMPATIBLE)

✔ Captures COLOR face images
✔ No histogram equalization
✔ No LBPH-style preprocessing
✔ Saves raw face crops for FaceNet
"""

# ==================== CONFIG ====================
MAX_SAMPLES = 20              # 15–20 is ideal
MIN_FACE_AREA = 8000          # allow realistic webcam distance
CAPTURE_DELAY = 0.7           # seconds between captures

# ==================== PATH SETUP ====================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_DIR = os.path.join(BASE_DIR, "face_data", "authorized")
os.makedirs(DATASET_DIR, exist_ok=True)

# ==================== FACE DETECTOR ====================
face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)

# ==================== CAMERA ====================
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

if not cap.isOpened():
    print("❌ Camera not accessible")
    exit()

print("📸 Face Enrollment Started (FaceNet)")
print("➡️ Good lighting, neutral face")
print("➡️ Slowly turn head (left / right)")
print("➡️ Press Q to stop")

count = 0
last_saved = time.time()

# ==================== MAIN LOOP ====================
while count < MAX_SAMPLES:
    ret, frame = cap.read()
    if not ret:
        print("⚠️ Frame capture failed")
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    faces = face_cascade.detectMultiScale(
        gray,
        scaleFactor=1.3,
        minNeighbors=5,
        minSize=(80, 80)
    )

    cv2.putText(
        frame,
        f"Captured: {count}/{MAX_SAMPLES}",
        (20, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.9,
        (255, 255, 0),
        2
    )

    if len(faces) == 1:
        (x, y, w, h) = faces[0]
        face_area = w * h

        if face_area >= MIN_FACE_AREA:
            if time.time() - last_saved >= CAPTURE_DELAY:
                # 🔑 SAVE COLOR FACE (NOT GRAYSCALE)
                face_color = frame[y:y + h, x:x + w]

                img_path = os.path.join(
                    DATASET_DIR, f"user_{count}.jpg"
                )
                cv2.imwrite(img_path, face_color)

                count += 1
                last_saved = time.time()

                print(f"✅ Saved sample {count}/{MAX_SAMPLES}")

            cv2.rectangle(frame, (x, y), (x + w, y + h),
                          (0, 255, 0), 2)
        else:
            cv2.putText(
                frame,
                "Move closer to camera",
                (20, 70),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 0, 255),
                2
            )
    else:
        cv2.putText(
            frame,
            "Ensure exactly ONE face",
            (20, 70),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 0, 255),
            2
        )

    cv2.imshow("Face Enrollment (FaceNet)", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        print("🛑 Enrollment stopped by user")
        break

# ==================== CLEANUP ====================
cap.release()
cv2.destroyAllWindows()

print(f"🎯 Enrollment complete: {count} samples saved")
print("➡️ Now run: python train_face.py")

