import os
import math
import cv2
import numpy as np
from mtcnn import MTCNN

# ─── Lazy globals ─────────────────────────────────────────────────────────────
_deepface   = None
_detector   = None

# ─── Tunable constants ────────────────────────────────────────────────────────
THRESHOLD         = 0.28   # Cosine distance — tight to prevent false positives between individuals
MIN_FACE_SIZE     = 60     # px: relaxed for browser/mobile cameras
MIN_CONFIDENCE    = 0.90   # MTCNN confidence gate (relaxed for browser JPEG)
MAX_EYE_ANGLE_DEG = 12.0   # Strict frontal pose to ensure FaceNet accuracy without forced alignment


# ─── Lazy loaders ─────────────────────────────────────────────────────────────

def _get_deepface():
    global _deepface
    if _deepface is None:
        from deepface import DeepFace
        _deepface = DeepFace
    return _deepface


def _get_detector():
    global _detector
    if _detector is None:
        _detector = MTCNN()
    return _detector


def warm_up():
    """
    Eagerly load MTCNN + DeepFace/FaceNet by running a dummy inference.
    Call this once at server startup (in a background thread) so the
    first real attendance frame has zero model-loading latency.
    """
    try:
        import numpy as np
        blank = np.zeros((160, 160, 3), dtype=np.uint8)
        det = _get_detector()
        det.detect_faces(blank)          # loads MTCNN weights
        DF = _get_deepface()
        DF.represent(                    # loads FaceNet weights
            img_path=blank,
            model_name='Facenet',
            enforce_detection=False,
        )
        print('[SmartAttend] Face models pre-loaded ✓')
    except Exception as e:
        print(f'[SmartAttend] Model warm-up warning: {e}')

# ─── Quality gate helpers ─────────────────────────────────────────────────────

def _check_face_quality(face: dict) -> tuple[bool, str]:
    """
    Run all quality gates on an MTCNN face dict.
    Returns (passed: bool, reason: str).
    """
    x, y, w, h = face['box']
    confidence  = face.get('confidence', 0.0)
    keypoints   = face.get('keypoints', {})

    # Gate 1 — confidence
    if confidence < MIN_CONFIDENCE:
        return False, "Low confidence detection — please look directly at the camera"

    # Gate 2 — size (too far / blurry)
    if w < MIN_FACE_SIZE or h < MIN_FACE_SIZE:
        return False, "Please move closer to the camera"

    # Gate 3 — landmark occlusion (hand / mask blocking keypoints)
    required = {'left_eye', 'right_eye', 'nose', 'mouth_left', 'mouth_right'}
    if not required.issubset(keypoints.keys()):
        return False, "Face is partly hidden — please remove any obstruction"

    # Gate 4 — frontal pose (eye line angle)
    le = keypoints['left_eye']
    re = keypoints['right_eye']
    dx = re[0] - le[0]
    dy = re[1] - le[1]
    angle_deg = abs(math.degrees(math.atan2(dy, dx)))
    if angle_deg > MAX_EYE_ANGLE_DEG:
        return False, "Please look straight at the camera"

    # Gate 5 — aspect ratio sanity check
    aspect = h / max(w, 1)
    if not (0.9 <= aspect <= 2.2):
        return False, "Invalid face region detected"

    return True, "ok"


# ─── IoU / NMS helpers ────────────────────────────────────────────────────────

def _iou(boxA, boxB) -> float:
    """Returns IoU of two [x1,y1,x2,y2] boxes."""
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[2], boxB[2])
    yB = min(boxA[3], boxB[3])
    inter = max(0, xB - xA + 1) * max(0, yB - yA + 1)
    if inter == 0:
        return 0.0
    aA = (boxA[2] - boxA[0] + 1) * (boxA[3] - boxA[1] + 1)
    aB = (boxB[2] - boxB[0] + 1) * (boxB[3] - boxB[1] + 1)
    return inter / float(aA + aB - inter)


def _nms(faces: list, iou_thresh: float = 0.4) -> list:
    """Non-Maximum Suppression: remove overlapping phantom boxes."""
    if not faces:
        return []
    boxes = []
    for i, f in enumerate(faces):
        x, y, w, h = f['box']
        boxes.append([x, y, x + w, y + h, f.get('confidence', 0.0), i])
    boxes.sort(key=lambda b: b[4], reverse=True)
    picked = []
    while boxes:
        best = boxes.pop(0)
        picked.append(faces[best[5]])
        boxes = [b for b in boxes if _iou(best[:4], b[:4]) <= iou_thresh]
    return picked


# ─── Public API ───────────────────────────────────────────────────────────────

def get_embedding(img_array_bgr: np.ndarray):
    """
    Detect the single largest quality face and return its 128-d FaceNet embedding.
    Returns (embedding | None, error_str | None).
    """
    detector  = _get_detector()
    DeepFace  = _get_deepface()
    img_rgb   = cv2.cvtColor(img_array_bgr, cv2.COLOR_BGR2RGB)

    faces = detector.detect_faces(img_rgb)
    if not faces:
        return None, "No face detected. Please look directly at the camera."

    # Pick the largest and most confident face
    faces.sort(key=lambda f: f['box'][2] * f['box'][3], reverse=True)
    best = faces[0]

    passed, reason = _check_face_quality(best)
    if not passed:
        return None, reason

    x, y, w, h = best['box']
    x, y = max(0, x), max(0, y)
    crop = img_array_bgr[y:y + h, x:x + w]
    if crop.size == 0:
        return None, "Invalid face crop."

    try:
        result = DeepFace.represent(
            img_path=crop,
            model_name="Facenet",
            enforce_detection=False,
        )
        emb = np.array(result[0]["embedding"], dtype=np.float32)
        return emb, None
    except Exception as e:
        return None, f"Face processing error: {str(e)}"


def recognize_faces_in_frame(
    frame_bgr:        np.ndarray,
    known_embeddings: list,
    known_ids:        list,
    threshold:        float = THRESHOLD,
) -> tuple[np.ndarray, list, str]:
    """
    Detect, quality-gate, NMS-filter, and recognize faces in a BGR frame.
    Returns (annotated_frame, list_of_matched_ids, quality_status_message).
    """
    detector  = _get_detector()
    DeepFace  = _get_deepface()
    overlay   = frame_bgr.copy()
    matched_ids: list  = []
    quality_msg: str   = "No face detected"

    img_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
    raw_faces = detector.detect_faces(img_rgb)

    # Step 1 — NMS: eliminate phantom overlapping boxes
    faces = _nms(raw_faces)

    if not faces:
        return overlay, [], "No face detected"

    # Step 2 — Process each distinct face through all quality gates
    for f in faces:
        x, y, w, h = f['box']
        x, y = max(0, x), max(0, y)
        crop = frame_bgr[y:y + h, x:x + w]

        if crop.size == 0:
            continue

        # Run quality gates
        passed, reason = _check_face_quality(f)
        quality_msg = reason  # update global status with latest face message

        if not passed:
            # Draw an orange box + quality message for this face
            cv2.rectangle(overlay, (x, y), (x + w, y + h), (0, 140, 255), 2)
            cv2.rectangle(overlay, (x, y - 22), (x + w, y), (0, 140, 255), cv2.FILLED)
            cv2.putText(overlay, reason[:40], (x + 4, y - 6),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.42, (255, 255, 255), 1)
            continue  # Skip recognition for low-quality faces

        # Step 3 — Extract embedding
        try:
            result = DeepFace.represent(
                img_path=crop,
                model_name="Facenet",
                enforce_detection=False,
            )
            emb = np.array(result[0]["embedding"], dtype=np.float32)
        except Exception:
            quality_msg = "Face processing error — please try again"
            continue

        # Step 4 — Cosine distance matching
        label = "Unknown"
        color = (0, 0, 200)

        if known_embeddings:
            known_arr  = np.array(known_embeddings, dtype=np.float32)
            emb_norm   = np.linalg.norm(emb)
            k_norms    = np.linalg.norm(known_arr, axis=1)
            denom      = k_norms * emb_norm
            denom[denom == 0] = 1e-10
            dists      = 1 - (np.dot(known_arr, emb) / denom)
            best_idx   = int(np.argmin(dists))

            if dists[best_idx] <= threshold:
                mid = known_ids[best_idx]
                if mid not in matched_ids:   # never double-count same person
                    matched_ids.append(mid)
                    quality_msg = "Face detected — Verifying identity..."
                    color = (0, 200, 80)
            else:
                quality_msg = "Unknown person detected"

        # Draw bounding box + label
        if w > 0 and h > 0:
            cv2.rectangle(overlay, (x, y), (x + w, y + h), color, 2)
            cv2.rectangle(overlay, (x, y + h - 30), (x + w, y + h), color, cv2.FILLED)
            cv2.putText(overlay, label, (x + 6, y + h - 8),
                        cv2.FONT_HERSHEY_DUPLEX, 0.6, (255, 255, 255), 1)

    return overlay, matched_ids, quality_msg

