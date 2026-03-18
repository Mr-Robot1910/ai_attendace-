from deepface.modules import verification
print("Cosine threshold:", verification.find_threshold("Facenet", "cosine"))
print("Euclidean threshold:", verification.find_threshold("Facenet", "euclidean"))
print("Euclidean L2 threshold:", verification.find_threshold("Facenet", "euclidean_l2"))
