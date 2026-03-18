import cv2
import numpy as np
import pickle
import urllib.request
from deepface import DeepFace

url = "https://upload.wikimedia.org/wikipedia/commons/a/a2/Alberto_Salazar.jpg"
try:
    urllib.request.urlretrieve(url, "test_stranger.jpg")

    stranger_img = cv2.imread("test_stranger.jpg")
    stranger_emb = np.array(DeepFace.represent(stranger_img, model_name="Facenet", detector_backend="mtcnn")[0]["embedding"])

    # Load student from DB directly or just load their picture
    student_img = cv2.imread("d:/first_antigravity/ai_attendance_system/known_faces/2403031570097.jpg")
    student_emb = np.array(DeepFace.represent(student_img, model_name="Facenet", detector_backend="mtcnn")[0]["embedding"])

    euclidean_dist = np.linalg.norm(stranger_emb - student_emb)
    cosine_dist = 1 - np.dot(stranger_emb, student_emb) / (np.linalg.norm(stranger_emb) * np.linalg.norm(student_emb))

    print(f"Distance between Stranger and Student:")
    print(f"  Euclidean: {euclidean_dist:.4f}")
    print(f"  Cosine: {cosine_dist:.4f}")

    print("\nIs it a match?")
    print(f"  Euclidean (threshold <= 10.0): {euclidean_dist <= 10.0}")
    print(f"  Cosine (threshold <= 0.40): {cosine_dist <= 0.40}")

except Exception as e:
    print("Error:", e)
