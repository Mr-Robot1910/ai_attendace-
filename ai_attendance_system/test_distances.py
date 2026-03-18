import cv2
import numpy as np
import urllib.request
from deepface import DeepFace

url1 = "https://raw.githubusercontent.com/serengil/deepface/master/tests/dataset/img1.jpg" # person 1
url2 = "https://raw.githubusercontent.com/serengil/deepface/master/tests/dataset/img2.jpg" # person 1 different
url3 = "https://upload.wikimedia.org/wikipedia/commons/a/a2/Alberto_Salazar.jpg" # person 2

urllib.request.urlretrieve(url1, "face1.jpg")
urllib.request.urlretrieve(url2, "face2.jpg")
urllib.request.urlretrieve(url3, "face3.jpg")

img1 = cv2.imread("face1.jpg")
img2 = cv2.imread("face2.jpg")
img3 = cv2.imread("face3.jpg")

emb1 = np.array(DeepFace.represent(img1, model_name="Facenet", detector_backend="mtcnn")[0]["embedding"])
emb2 = np.array(DeepFace.represent(img2, model_name="Facenet", detector_backend="mtcnn")[0]["embedding"])
emb3 = np.array(DeepFace.represent(img3, model_name="Facenet", detector_backend="mtcnn")[0]["embedding"])

def euclidean(a, b):
    return np.linalg.norm(a - b)

def cosine(a, b):
    return 1 - np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

print("Same person (Euclidean):", euclidean(emb1, emb2))
print("Different person (Euclidean):", euclidean(emb1, emb3))

print("Same person (Cosine):", cosine(emb1, emb2))
print("Different person (Cosine):", cosine(emb1, emb3))
