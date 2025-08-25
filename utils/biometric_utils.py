from deepface import DeepFace
from PIL import Image
import tempfile, numpy as np

def compare_faces(badge_path, snapshot_img, threshold=30):
    img2 = Image.open(snapshot_img)
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as temp_img:
        Image.fromarray(np.array(img2)).save(temp_img.name)
        img2_path = temp_img.name
    result = DeepFace.verify(
        img1_path=badge_path,
        img2_path=img2_path,
        model_name="VGG-Face",
        enforce_detection=False
    )
    return result["verified"], (1 - result["distance"]) * 100