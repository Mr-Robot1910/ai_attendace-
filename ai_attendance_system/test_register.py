import requests
import cv2
import base64

# Use an image that I know exists in the folder
img_path = r"d:\first_antigravity\ai_attendance_system\known_faces\2403031570097.jpg"
img = cv2.imread(img_path)

if img is None:
    print("Could not load image.")
    exit(1)

_, buffer = cv2.imencode('.jpg', img)
base64_str = base64.b64encode(buffer).decode('utf-8')
data_uri = f"data:image/jpeg;base64,{base64_str}"

payload = {
    "name": "Test Student",
    "roll_no": "TEST1234",
    "image": data_uri
}

try:
    response = requests.post("http://127.0.0.1:5000/api/register", json=payload)
    print("Status Code:", response.status_code)
    print("Response text:", response.text)
except Exception as e:
    print("Failed to reach server:", e)
