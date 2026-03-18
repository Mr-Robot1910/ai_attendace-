import cv2
import numpy as np
from deepface import DeepFace

# Create a mock face image or just load an existing proper face
# Let's download a sample face image
import urllib.request
urllib.request.urlretrieve("https://raw.githubusercontent.com/serengil/deepface/master/tests/dataset/img1.jpg", "test_face.jpg")

img = cv2.imread("test_face.jpg")

# Test 1: BGR image directly (OpenCV default)
try:
    res = DeepFace.represent(img_path=img, model_name="Facenet", detector_backend="mtcnn")
    print("BGR numpy array worked!")
except Exception as e:
    print("BGR numpy array failed:", e)

# Test 2: RGB image
img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
try:
    res = DeepFace.represent(img_path=img_rgb, model_name="Facenet", detector_backend="mtcnn")
    print("RGB numpy array worked!")
except Exception as e:
    print("RGB numpy array failed:", e)
