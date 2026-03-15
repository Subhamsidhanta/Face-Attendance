"""
Trainer — wraps train_cnn.py logic and exposes it as an API-friendly class.
Trains the LBPH face recognizer in a background thread.
"""

import cv2
import os
import numpy as np
import threading


class Trainer:
    def __init__(self, dataset_dir=None, models_dir=None):
        self._dataset_dir = dataset_dir or os.path.join(
            os.path.dirname(__file__), "..", "dataset"
        )
        self._models_dir = models_dir or os.path.join(
            os.path.dirname(__file__), "..", "models"
        )
        self._training = False
        self._progress = ""
        self._thread = None
        self._lock = threading.Lock()

    @property
    def status(self):
        return {
            "training": self._training,
            "progress": self._progress,
        }

    def start_training(self):
        """Start LBPH model training in background."""
        if self._training:
            return False, "Already training."

        self._training = True
        self._progress = "Starting..."
        self._thread = threading.Thread(target=self._train, daemon=True)
        self._thread.start()
        return True, "Training started."

    def _train(self):
        try:
            faces = []
            ids = []
            names = []
            current_id = 0

            if not os.path.exists(self._dataset_dir):
                self._progress = "Error: No dataset directory found."
                self._training = False
                return

            people = [
                p for p in os.listdir(self._dataset_dir)
                if os.path.isdir(os.path.join(self._dataset_dir, p))
            ]
            if not people:
                self._progress = "Error: No registered persons found."
                self._training = False
                return

            total_people = len(people)
            for i, person in enumerate(people):
                person_path = os.path.join(self._dataset_dir, person)
                names.append(person)
                self._progress = f"Loading images for {person} ({i + 1}/{total_people})..."

                for img_name in os.listdir(person_path):
                    img_path = os.path.join(person_path, img_name)
                    img = cv2.imread(img_path, 0)
                    if img is None:
                        continue
                    faces.append(img)
                    ids.append(current_id)

                current_id += 1

            if not faces:
                self._progress = "Error: No face images found."
                self._training = False
                return

            self._progress = f"Training LBPH model on {len(faces)} images..."

            recognizer = cv2.face.LBPHFaceRecognizer_create()
            recognizer.train(faces, np.array(ids))

            os.makedirs(self._models_dir, exist_ok=True)
            recognizer.save(os.path.join(self._models_dir, "recognizer.yml"))

            with open(os.path.join(self._models_dir, "names.txt"), "w") as f:
                for n in names:
                    f.write(n + "\n")

            self._progress = f"✅ Training complete! {len(faces)} images, {len(names)} persons."
        except Exception as e:
            self._progress = f"Error: {str(e)}"
        finally:
            self._training = False
