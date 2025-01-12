import numpy as np
from tensorflow.keras.preprocessing import image
import joblib
import os

# Constants
MODEL_PATH = os.path.join(os.path.dirname(__file__), 'weed_crop_model.joblib')
IMG_SIZE = (128, 128)

# Load the model
try:
    model = joblib.load(MODEL_PATH)
except FileNotFoundError:
    raise Exception(f"Model file not found at {MODEL_PATH}. Ensure the path is correct.")

def predict_image(img_path: str) -> str:
    """Predict whether the image contains weed or crop."""
    try:
        img = image.load_img(img_path, target_size=IMG_SIZE)
        img_array = image.img_to_array(img) / 255.0
        img_array = np.expand_dims(img_array, axis=0)

        prediction = model.predict(img_array)
        return "Weed detected" if prediction > 0.5 else "Crop detected"
    except Exception as e:
        raise Exception(f"Error during prediction: {e}")
