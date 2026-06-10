import sys
import os
import cv2
import time
import threading
from collections import deque

# -------------------------------------------------
# PRIVACY STATE STABILITY
# -------------------------------------------------
last_block_reason = None
last_block_time = 0
BLOCK_HOLD_SECONDS = 2.0

SAFE_HOLD_SECONDS = 1.5
last_safe_time = 0

# -------------------------------------------------
# STREAM PERFORMANCE CONTROL
# -------------------------------------------------
TARGET_FPS = 20
FRAME_DELAY = 1.0 / TARGET_FPS

# -------------------------------------------------
# DECISION STABILIZATION
# -------------------------------------------------
DECISION_HISTORY_SIZE = 10
decision_history = deque(maxlen=DECISION_HISTORY_SIZE)

# -------------------------------------------------
# PATH SETUP
# -------------------------------------------------
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))

if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

# -------------------------------------------------
# IMPORTS
# -------------------------------------------------
from utils.face_authorizer import is_authorized
from screen_privacy.privacy_controller import (
    update_privacy_state,
    is_screen_guard_running
)

# -------------------------------------------------
# YOLO MODEL
# -------------------------------------------------
yolo_model = None
yolo_lock = threading.Lock()


def _load_yolo():
    global yolo_model

    if yolo_model is not None:
        return yolo_model

    with yolo_lock:
        if yolo_model is None:
            try:
                from ultralytics import YOLO

                print("📦 Loading YOLOv8 model...")

                # Stronger model for phone detection
                yolo_model = YOLO("yolov8s.pt")

                print("✅ YOLO model loaded")

            except Exception as e:
                print("❌ YOLO load failed:", e)
                yolo_model = None

    return yolo_model

# -------------------------------------------------
# CAMERA
# -------------------------------------------------
cap = None
camera_lock = threading.Lock()


def _open_camera():
    global cap

    with camera_lock:

        if cap is not None and cap.isOpened():
            return

        print("🎥 Attempting to open camera...")

        # Better webcam backend for Windows
        camera = cv2.VideoCapture(0, cv2.CAP_DSHOW)

        # Higher resolution helps detect small phones
        camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

        if not camera.isOpened():
            print("❌ Camera open failed")
            cap = None
            raise RuntimeError("Cannot access camera")

        cap = camera
        print("✅ Camera opened successfully")

def _release_camera():
    global cap

    with camera_lock:

        if cap is not None:

            try:
                if cap.isOpened():
                    print("🛑 Releasing camera")
                    cap.release()
            except Exception as e:
                print("⚠️ Camera release error:", e)

            cap = None


# -------------------------------------------------
# AUTHORIZATION SMOOTHING
# -------------------------------------------------
AUTH_HISTORY_SIZE = 12
REQUIRED_AUTH_FRAMES = 8
auth_history = deque(maxlen=AUTH_HISTORY_SIZE)

# -------------------------------------------------
# CAMERA COVER SMOOTHING
# -------------------------------------------------
covered_history = deque(maxlen=5)

# -------------------------------------------------
# YOLO PERFORMANCE CONTROL
# -------------------------------------------------
YOLO_SKIP_FRAMES = 5
yolo_counter = 0

last_phone_detected = False
last_phone_close = False

# -------------------------------------------------
# BIOMETRIC INFO
# -------------------------------------------------
last_authorized_name = None
last_authorized_confidence = None


# -------------------------------------------------
# DECISION STABILIZER
# -------------------------------------------------
def get_stable_reason(reason):

    decision_history.append(reason)

    counts = {}

    for r in decision_history:
        counts[r] = counts.get(r, 0) + 1

    stable_reason = max(counts, key=counts.get)

    return stable_reason


# -------------------------------------------------
# CAMERA COVER DETECTION
# -------------------------------------------------
def is_camera_covered(frame):

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    brightness = gray.mean()
    laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()

    covered = (brightness < 75 and laplacian_var < 35) or laplacian_var < 20

    covered_history.append(1 if covered else 0)

    return sum(covered_history) >= 3


# -------------------------------------------------
# PHONE DETECTION
# -------------------------------------------------
def detect_phone_usage(frame):

    phone_detected = False
    phone_close = False

    yolo = _load_yolo()

    if yolo is None:
        return False, False

    h, w, _ = frame.shape
    frame_area = h * w

    # Resize similar to your old working version
    yolo_frame = cv2.resize(frame, (640, 480))

    results = yolo(yolo_frame, conf=0.20, verbose=False)

    for r in results:
        boxes = getattr(r, "boxes", [])

        for box in boxes:
            cls_id = int(box.cls[0])
            label = yolo.names.get(cls_id, "")
            conf = float(box.conf[0])

            print(f"Detected: {label} ({conf:.2f})")

            # Phone may be misclassified depending on webcam quality
            if label in ["cell phone", "remote", "umbrella"]:

                phone_detected = True

                x1, y1, x2, y2 = map(int, box.xyxy[0])
                phone_area = (x2 - x1) * (y2 - y1)

                if phone_area / frame_area > 0.02:
                    phone_close = True
                    print(f"📱 Phone detected as: {label}")

    return phone_detected, phone_close

# -------------------------------------------------
# FRAME GENERATOR
# -------------------------------------------------
def generate_frames():

    global cap
    global auth_history
    global yolo_counter
    global last_phone_detected
    global last_phone_close
    global last_block_reason
    global last_block_time
    global last_safe_time
    global last_authorized_name
    global last_authorized_confidence

    while True:

        frame_start = time.time()

        try:

            if not is_screen_guard_running():

                _release_camera()
                auth_history.clear()
                covered_history.clear()

                time.sleep(0.2)
                continue

            if cap is None:
                _open_camera()

            success, frame = cap.read()

            if not success:
                print("⚠️ Frame read failed – resetting camera")

                _release_camera()
                time.sleep(0.5)

                continue

            camera_covered = is_camera_covered(frame)

            face_count = 0
            final_auth = False

            detected_name = None
            detected_confidence = None

            if not camera_covered:

                result = is_authorized(
                    frame,
                    debug=False,
                    return_face_count=True
                )

                authorized = False

                if isinstance(result, tuple):

                    if len(result) >= 4:
                        authorized = result[0]
                        detected_name = result[1]
                        detected_confidence = result[2]
                        face_count = result[3]

                    elif len(result) == 3:
                        authorized = result[0]
                        detected_name = result[1]
                        detected_confidence = result[2]
                        face_count = 1

                if face_count == 1:

                    auth_history.append(1 if authorized else 0)
                    final_auth = sum(auth_history) >= REQUIRED_AUTH_FRAMES

                else:
                    auth_history.clear()
                    final_auth = False

                if yolo_counter % YOLO_SKIP_FRAMES == 0:
                    last_phone_detected, last_phone_close = detect_phone_usage(frame)

                yolo_counter = (yolo_counter + 1) % 1000

            # -------------------------------------------------
            # RAW DECISION (PRIORITY FIXED)
            # -------------------------------------------------

            raw_reason = "AUTHORIZED"

            if camera_covered:
                raw_reason = "CAMERA_COVERED"

            elif last_phone_detected and last_phone_close:
                raw_reason = "PHONE_DETECTED"

            elif face_count > 1:
                raw_reason = "MULTIPLE_FACES"

            elif face_count == 0:
                raw_reason = "UNAUTHORIZED_USER"

            elif face_count == 1 and not final_auth:
                raw_reason = "UNAUTHORIZED_USER"

            elif face_count == 1 and final_auth:
                raw_reason = "AUTHORIZED"

            # -------------------------------------------------
            # STABILIZED DECISION
            # -------------------------------------------------

            stable_reason = get_stable_reason(raw_reason)

            if stable_reason != "AUTHORIZED":

                last_block_reason = stable_reason
                last_block_time = time.time()

                update_privacy_state(False, reason=stable_reason)

                frame = cv2.GaussianBlur(frame, (31, 31), 0)

                status = stable_reason.replace("_", " ")

            else:

                if time.time() - last_safe_time > SAFE_HOLD_SECONDS:

                    last_block_reason = None
                    last_safe_time = time.time()

                    update_privacy_state(True, reason="AUTHORIZED")

                    last_authorized_name = detected_name
                    last_authorized_confidence = detected_confidence

                if detected_name and detected_confidence is not None:
                    status = f"AUTHORIZED: {detected_name} ({detected_confidence:.1f}%)"
                else:
                    status = "AUTHORIZED USER"

            # -------------------------------------------------
            # OVERLAYS
            # -------------------------------------------------

            cv2.putText(
                frame,
                status,
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.9,
                (0, 255, 0) if "AUTHORIZED" in status else (0, 0, 255),
                2
            )

            cv2.putText(
                frame,
                f"Faces detected: {face_count}",
                (20, 80),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (255, 255, 255),
                2
            )

            # -------------------------------------------------
            # STREAM OUTPUT
            # -------------------------------------------------

            ret, buffer = cv2.imencode(".jpg", frame)

            if not ret:
                continue

            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n"
                + buffer.tobytes()
                + b"\r\n"
            )

            # -------------------------------------------------
            # FPS CONTROL
            # -------------------------------------------------

            elapsed = time.time() - frame_start
            sleep_time = FRAME_DELAY - elapsed

            if sleep_time > 0:
                time.sleep(sleep_time)

        except GeneratorExit:

            print("🛑 Client disconnected")
            _release_camera()
            break

        except Exception as e:

            print("🔥 Screen Guard Error:", e)

            auth_history.clear()
            covered_history.clear()

            _release_camera()
            time.sleep(0.5)