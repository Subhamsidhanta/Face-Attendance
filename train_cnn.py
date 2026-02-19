import cv2
import os
import numpy as np

dataset_path = "dataset"
faces = []
ids = []
names = []

current_id = 0

# ===== LOAD DATASET =====
for person in os.listdir(dataset_path):

    person_path = os.path.join(dataset_path, person)
    if not os.path.isdir(person_path):
        continue

    names.append(person)

    for img_name in os.listdir(person_path):
        img_path = os.path.join(person_path, img_name)

        img = cv2.imread(img_path, 0)
        if img is None:
            continue

        faces.append(img)
        ids.append(current_id)

    current_id += 1

# ===== TRAIN MODEL =====
recognizer = cv2.face.LBPHFaceRecognizer_create()
recognizer.train(faces, np.array(ids))

os.makedirs("models", exist_ok=True)
recognizer.save("models/recognizer.yml")

# save names list
with open("models/names.txt", "w") as f:
    for n in names:
        f.write(n+"\n")

print("✅ Training Complete")
print("Names:", names)
