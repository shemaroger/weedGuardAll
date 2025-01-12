import joblib
import numpy as np
from tensorflow.keras.preprocessing import image  # type: ignore
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
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
import os
from .models import Prediction
from .ml_model import predict_image  # Assuming this is your prediction logic
from django.core.files.storage import default_storage
from django.shortcuts import get_object_or_404

# Create a new prediction
@api_view(['POST'])
@permission_classes([IsAuthenticated])  # Ensure only authenticated users can access this
def predict_view(request):
    """
    Handles custom prediction requests and directly returns the prediction result.
    This view will save the prediction details and return them at the same time.
    """
    if 'image' in request.FILES:
        try:
            # Retrieve the uploaded image file
            image_file = request.FILES['image']
            
            # Save image temporarily
            temp_image_path = os.path.join('temp_images', image_file.name)
            os.makedirs('temp_images', exist_ok=True)

            # Save image to the temp directory
            with open(temp_image_path, 'wb') as f:
                for chunk in image_file.chunks():
                    f.write(chunk)

            # Perform the prediction using the image
            prediction_result = predict_image(temp_image_path)

            # Get additional metadata from the request
            location = request.POST.get('location', '')
            site_name = request.POST.get('site_name', '')

            # Save the prediction to the database
            prediction = Prediction.objects.create(
                image=image_file,
                result=prediction_result,
                location=location,
                site_name=site_name,
                user=request.user  # Associated with the currently authenticated user
            )

            # Clean up the temporary image file after processing
            os.remove(temp_image_path)

            # Serialize the prediction details and return the response
            prediction_data = {
                'id': prediction.id,
                'result': prediction_result,
                'location': prediction.location,
                'site_name': prediction.site_name,
                'timestamp': prediction.timestamp,
            }
            return JsonResponse(prediction_data, status=201)
        
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    else:
        return JsonResponse({'error': 'No image file provided'}, status=400)

# Read a list of predictions
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_predictions(request):
    """
    Retrieve a list of all predictions made by the authenticated user.
    """
    predictions = Prediction.objects.filter(user=request.user)  # Filter by the authenticated user
    predictions_data = [
        {
            'id': prediction.id,
            'result': prediction.result,
            'location': prediction.location,
            'site_name': prediction.site_name,
            'timestamp': prediction.timestamp,
        } for prediction in predictions
    ]
    return JsonResponse({'predictions': predictions_data}, safe=False)

# Read a specific prediction by ID
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_prediction(request, prediction_id):
    """
    Retrieve a specific prediction by ID.
    """
    prediction = get_object_or_404(Prediction, id=prediction_id, user=request.user)  # Ensure it belongs to the user
    prediction_data = {
        'id': prediction.id,
        'result': prediction.result,
        'location': prediction.location,
        'site_name': prediction.site_name,
        'timestamp': prediction.timestamp,
    }
    return JsonResponse(prediction_data)

# Update a prediction
@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_prediction(request, prediction_id):
    """
    Update the result or metadata of a specific prediction.
    """
    prediction = get_object_or_404(Prediction, id=prediction_id, user=request.user)

    # Update fields from request data
    result = request.data.get('result', prediction.result)
    location = request.data.get('location', prediction.location)
    site_name = request.data.get('site_name', prediction.site_name)

    # Save the updated prediction
    prediction.result = result
    prediction.location = location
    prediction.site_name = site_name
    prediction.save()

    updated_prediction_data = {
        'id': prediction.id,
        'result': prediction.result,
        'location': prediction.location,
        'site_name': prediction.site_name,
        'timestamp': prediction.timestamp,
    }
    return JsonResponse(updated_prediction_data)

# Delete a prediction
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_prediction(request, prediction_id):
    """
    Delete a specific prediction.
    """
    prediction = get_object_or_404(Prediction, id=prediction_id, user=request.user)

    # Delete the prediction record
    prediction.delete()
    return JsonResponse({'message': 'Prediction deleted successfully'}, status=204)

