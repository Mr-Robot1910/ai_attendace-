import cv2
import numpy as np
from deepface import DeepFace

img_path = r"d:\first_antigravity\ai_attendance_system\known_faces\2403031570097.jpg"
img_bgr = cv2.imread(img_path)

print("Testing BGR array...")
try:
    res = DeepFace.represent(img_path=img_bgr, model_name="Facenet", detector_backend="mtcnn", enforce_detection=True)
    print("BGR Success!")
except Exception as e:
    print("BGR Failed:", str(e))

print("Testing RGB array...")
img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
try:
    res = DeepFace.represent(img_path=img_rgb, model_name="Facenet", detector_backend="mtcnn", enforce_detection=True)
    print("RGB Success!")
except Exception as e:
    print("RGB Failed:", str(e))
