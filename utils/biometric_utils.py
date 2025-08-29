import mediapipe as mp
import cv2
import numpy as np
from PIL import Image
import tempfile
from sklearn.metrics.pairwise import cosine_similarity

# Initialize MediaPipe Face Detection and Face Mesh
mp_face_detection = mp.solutions.face_detection
mp_face_mesh = mp.solutions.face_mesh


def extract_face_landmarks(image_path):
    """Extract face landmarks using MediaPipe"""
    try:
        # Read image
        if isinstance(image_path, str):
            image = cv2.imread(image_path)
        else:
            # If it's already an image array
            image = np.array(image_path)

        if image is None:
            return None

        # Convert BGR to RGB
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        with mp_face_mesh.FaceMesh(
                static_image_mode=True,
                max_num_faces=1,
                refine_landmarks=True,
                min_detection_confidence=0.5
        ) as face_mesh:
            results = face_mesh.process(rgb_image)

            if results.multi_face_landmarks:
                # Extract landmark coordinates
                landmarks = []
                for face_landmarks in results.multi_face_landmarks:
                    for landmark in face_landmarks.landmark:
                        landmarks.append([landmark.x, landmark.y, landmark.z])
                return np.array(landmarks).flatten()

        return None
    except Exception as e:
        print(f"Error extracting landmarks: {e}")
        return None


def compare_faces_simple_fallback(badge_path, snapshot_path, threshold=30):
    """
    Fallback method using simple face detection and histogram comparison
    """
    try:
        # Load images
        img1 = cv2.imread(badge_path)
        img2 = cv2.imread(snapshot_path)

        if img1 is None or img2 is None:
            return False, 0.0

        # Detect faces and extract regions
        with mp_face_detection.FaceDetection(min_detection_confidence=0.3) as face_detection:
            # Process first image
            rgb_img1 = cv2.cvtColor(img1, cv2.COLOR_BGR2RGB)
            results1 = face_detection.process(rgb_img1)

            # Process second image
            rgb_img2 = cv2.cvtColor(img2, cv2.COLOR_BGR2RGB)
            results2 = face_detection.process(rgb_img2)

            if not (results1.detections and results2.detections):
                # No faces detected, return low confidence
                return False, 0.0

            # Get face bounding boxes
            h1, w1, _ = img1.shape
            h2, w2, _ = img2.shape

            # Extract first face from each image
            bbox1 = results1.detections[0].location_data.relative_bounding_box
            bbox2 = results2.detections[0].location_data.relative_bounding_box

            # Convert to pixel coordinates and extract face regions
            x1 = max(0, int(bbox1.xmin * w1))
            y1 = max(0, int(bbox1.ymin * h1))
            w1_face = int(bbox1.width * w1)
            h1_face = int(bbox1.height * h1)
            face1 = img1[y1:y1 + h1_face, x1:x1 + w1_face]

            x2 = max(0, int(bbox2.xmin * w2))
            y2 = max(0, int(bbox2.ymin * h2))
            w2_face = int(bbox2.width * w2)
            h2_face = int(bbox2.height * h2)
            face2 = img2[y2:y2 + h2_face, x2:x2 + w2_face]

            if face1.size == 0 or face2.size == 0:
                return False, 0.0

            # Resize faces to same size for comparison
            target_size = (100, 100)
            face1_resized = cv2.resize(face1, target_size)
            face2_resized = cv2.resize(face2, target_size)

            # Convert to grayscale for comparison
            face1_gray = cv2.cvtColor(face1_resized, cv2.COLOR_BGR2GRAY)
            face2_gray = cv2.cvtColor(face2_resized, cv2.COLOR_BGR2GRAY)

            # Calculate histogram correlation
            hist1 = cv2.calcHist([face1_gray], [0], None, [256], [0, 256])
            hist2 = cv2.calcHist([face2_gray], [0], None, [256], [0, 256])

            # Normalize histograms
            cv2.normalize(hist1, hist1, 0, 1, cv2.NORM_MINMAX)
            cv2.normalize(hist2, hist2, 0, 1, cv2.NORM_MINMAX)

            # Calculate correlation
            correlation = cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)

            # Convert to percentage and adjust scale to match original expectations
            confidence = max(0, correlation * 100)

            # Apply threshold
            is_verified = confidence >= threshold

            return is_verified, confidence

    except Exception as e:
        print(f"Error in fallback comparison: {str(e)}")
        return False, 0.0


def compare_faces_simple_fallback(badge_path, snapshot_path, threshold=30):
    """
    Fallback method using simple face detection and histogram comparison
    """
    try:
        # Load images
        img1 = cv2.imread(badge_path)
        img2 = cv2.imread(snapshot_path)

        if img1 is None or img2 is None:
            return False, 0.0

        # Detect faces and extract regions
        with mp_face_detection.FaceDetection(min_detection_confidence=0.3) as face_detection:
            # Process first image
            rgb_img1 = cv2.cvtColor(img1, cv2.COLOR_BGR2RGB)
            results1 = face_detection.process(rgb_img1)

            # Process second image
            rgb_img2 = cv2.cvtColor(img2, cv2.COLOR_BGR2RGB)
            results2 = face_detection.process(rgb_img2)

            if not (results1.detections and results2.detections):
                # No faces detected, return low confidence
                return False, 0.0

            # Get face bounding boxes
            h1, w1, _ = img1.shape
            h2, w2, _ = img2.shape

            # Extract first face from each image
            bbox1 = results1.detections[0].location_data.relative_bounding_box
            bbox2 = results2.detections[0].location_data.relative_bounding_box

            # Convert to pixel coordinates and extract face regions
            x1 = max(0, int(bbox1.xmin * w1))
            y1 = max(0, int(bbox1.ymin * h1))
            w1_face = int(bbox1.width * w1)
            h1_face = int(bbox1.height * h1)
            face1 = img1[y1:y1 + h1_face, x1:x1 + w1_face]

            x2 = max(0, int(bbox2.xmin * w2))
            y2 = max(0, int(bbox2.ymin * h2))
            w2_face = int(bbox2.width * w2)
            h2_face = int(bbox2.height * h2)
            face2 = img2[y2:y2 + h2_face, x2:x2 + w2_face]

            if face1.size == 0 or face2.size == 0:
                return False, 0.0

            # Resize faces to same size for comparison
            target_size = (100, 100)
            face1_resized = cv2.resize(face1, target_size)
            face2_resized = cv2.resize(face2, target_size)

            # Convert to grayscale for comparison
            face1_gray = cv2.cvtColor(face1_resized, cv2.COLOR_BGR2GRAY)
            face2_gray = cv2.cvtColor(face2_resized, cv2.COLOR_BGR2GRAY)

            # Calculate histogram correlation
            hist1 = cv2.calcHist([face1_gray], [0], None, [256], [0, 256])
            hist2 = cv2.calcHist([face2_gray], [0], None, [256], [0, 256])

            # Normalize histograms
            cv2.normalize(hist1, hist1, 0, 1, cv2.NORM_MINMAX)
            cv2.normalize(hist2, hist2, 0, 1, cv2.NORM_MINMAX)

            # Calculate correlation
            correlation = cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)

            # Convert to percentage and adjust scale to match original expectations
            confidence = max(0, correlation * 100)

            # Apply threshold
            is_verified = confidence >= threshold

            return is_verified, confidence

    except Exception as e:
        print(f"Error in fallback comparison: {str(e)}")
        return False, 0.0


def compare_faces(badge_path, snapshot_img, threshold=30):
    """
    Compare two faces using MediaPipe landmarks
    Maintains the same function signature as your original DeepFace version

    Args:
        badge_path (str): Path to the badge/reference image
        snapshot_img (str or PIL.Image): Path to snapshot image or PIL Image object
        threshold (float): Similarity threshold (0-100)

    Returns:
        tuple: (is_verified: bool, confidence_percentage: float)
    """
    try:
        # Handle snapshot_img - it could be a file path or PIL Image
        if isinstance(snapshot_img, str):
            # It's a file path
            img2_path = snapshot_img
        else:
            # It's likely a PIL Image, save it temporarily
            if hasattr(snapshot_img, 'save'):
                # It's a PIL Image
                with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as temp_img:
                    snapshot_img.save(temp_img.name)
                    img2_path = temp_img.name
            else:
                # Try to open it as PIL Image (in case it's passed differently)
                img2 = Image.open(snapshot_img)
                with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as temp_img:
                    img2.save(temp_img.name)
                    img2_path = temp_img.name

        # Extract landmarks from both images
        landmarks1 = extract_face_landmarks(badge_path)
        landmarks2 = extract_face_landmarks(img2_path)

        if landmarks1 is None or landmarks2 is None:
            # Fallback to simple face detection comparison
            return compare_faces_simple_fallback(badge_path, img2_path, threshold)

        # Calculate similarity using cosine similarity
        similarity = cosine_similarity([landmarks1], [landmarks2])[0][0]

        # Convert to confidence percentage (0-100)
        # Adjust the scaling to match your original threshold expectations
        confidence = max(0, similarity * 100)

        # Since your original threshold was 30, we'll use a similar scale
        is_verified = confidence >= threshold

        return is_verified, confidence

    except Exception as e:
        print(f"Error in face comparison: {str(e)}")
        # Return same format as original function
        return False, 0.0
