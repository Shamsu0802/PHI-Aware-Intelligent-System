import cv2
import os
import numpy as np

# Folder containing all authorized person folders
BASE_FOLDER = "screen_privacy/face_data/authorized"

# Number of augmented images per original image
AUG_PER_IMAGE = 15

for person_name in os.listdir(BASE_FOLDER):

    person_folder = os.path.join(BASE_FOLDER, person_name)

    # Skip if not a folder
    if not os.path.isdir(person_folder):
        continue

    print(f"\nProcessing: {person_name}")

    image_files = [
        f for f in os.listdir(person_folder)
        if f.lower().endswith((".jpg", ".jpeg", ".png"))
        and not f.startswith("aug_")
    ]

    img_count = 0

    for image_file in image_files:

        image_path = os.path.join(person_folder, image_file)
        image = cv2.imread(image_path)

        if image is None:
            print(f"Could not read {image_file}")
            continue

        h, w = image.shape[:2]

        for i in range(AUG_PER_IMAGE):

            img = image.copy()

            # Random rotation
            angle = np.random.randint(-25, 25)
            M = cv2.getRotationMatrix2D((w / 2, h / 2), angle, 1)
            img = cv2.warpAffine(img, M, (w, h))

            # Random brightness
            brightness = np.random.randint(-40, 40)
            img = cv2.convertScaleAbs(img, beta=brightness)

            # Random zoom
            scale = np.random.uniform(0.9, 1.1)
            resized = cv2.resize(img, None, fx=scale, fy=scale)

            rh, rw = resized.shape[:2]

            if scale > 1:
                start_x = (rw - w) // 2
                start_y = (rh - h) // 2
                img = resized[start_y:start_y+h, start_x:start_x+w]
            else:
                canvas = np.zeros_like(img)
                start_x = (w - rw) // 2
                start_y = (h - rh) // 2
                canvas[start_y:start_y+rh, start_x:start_x+rw] = resized
                img = canvas

            # Random horizontal flip
            if np.random.rand() > 0.5:
                img = cv2.flip(img, 1)

            # Slight blur sometimes
            if np.random.rand() > 0.7:
                img = cv2.GaussianBlur(img, (5, 5), 0)

            filename = f"aug_{img_count}.jpg"
            save_path = os.path.join(person_folder, filename)

            cv2.imwrite(save_path, img)
            img_count += 1

    print(f"Generated {img_count} augmented images for {person_name}")

print("\nAll authorized faces augmented successfully.")