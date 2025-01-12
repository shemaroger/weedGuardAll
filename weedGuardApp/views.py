import logging
import os
import traceback
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.core.files.storage import default_storage
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from .models import *
from django.contrib.auth import login
from django.core.files.base import ContentFile
from .serializers import *
from django.contrib.auth import authenticate
from .ml_model import predict_image  # Assuming this is your prediction logic
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count
from django.db.models.functions import TruncMonth, TruncWeek
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Q

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@api_view(['POST'])
@permission_classes([AllowAny])
def create_user(request):
    data = request.data
    logger.info("Create user request received with data: %s", data)
    permission_classes = [AllowAny]
    # Use serializer for validation
    serializer = UserSerializer(data=data)
    if not serializer.is_valid():
        logger.error("Validation failed: %s", serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    try:
        # Create and save the user
        serializer.save()
        logger.info("User created successfully: %s", serializer.data)
        return Response({"message": "User created successfully."}, status=status.HTTP_201_CREATED)
    except Exception as e:
        logger.error("Error creating user: %s", str(e))
        return Response({"detail": "Error creating user."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class UserRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        logger.info("Retrieve user request by user: %s", request.user)
        return super().get(request, *args, **kwargs)

class SignupView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({"message": "User created successfully."}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            login(request, user)  # Ensure this is properly imported

            # Generate tokens for the user
            refresh = RefreshToken.for_user(user)

            # Return the response including the access token and refresh token
            return Response({
                "message": "Login successful",
                "user_id": user.id,
                "email": user.email,
                "access_token": str(refresh.access_token),
                "refresh_token": str(refresh)
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Prediction View
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def predict_view(request):
    """
    Handle image prediction for authenticated users
    """
    try:
        # Log the authenticated user
        logger.info(f"Prediction request from user: {request.user.email}")

        # Validate image file
        if 'image' not in request.FILES:
            logger.warning("No image file provided in prediction request")
            return JsonResponse({
                'error': 'No image file provided'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Process uploaded image
        image_file = request.FILES['image']
        
        # Validate file size (optional)
        max_upload_size = 5 * 1024 * 1024  # 5 MB
        if image_file.size > max_upload_size:
            logger.warning(f"Image file too large: {image_file.size} bytes")
            return JsonResponse({
                'error': 'Image file too large. Maximum size is 5 MB'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Validate file type (optional)
        allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif']
        file_ext = os.path.splitext(image_file.name)[1].lower()
        if file_ext not in allowed_extensions:
            logger.warning(f"Invalid file type: {file_ext}")
            return JsonResponse({
                'error': 'Invalid file type. Allowed types: jpg, jpeg, png, gif'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Create secure temporary directory for image storage
        temp_dir = os.path.join(settings.BASE_DIR, 'temp_images')
        os.makedirs(temp_dir, exist_ok=True)

        # Generate unique filename to prevent conflicts
        import uuid
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        temp_image_path = os.path.join(temp_dir, unique_filename)

        # Save image securely
        with open(temp_image_path, 'wb+') as destination:
            for chunk in image_file.chunks():
                destination.write(chunk)

        logger.info(f"Temporary image saved: {temp_image_path}")

        try:
            # Perform prediction
            prediction_result = predict_image(temp_image_path)

            # Extract additional metadata
            location = request.POST.get('location', '')
            site_name = request.POST.get('site_name', '')

            # Create prediction record
            prediction = Prediction.objects.create(
                user=request.user,
                image=image_file,
                result=prediction_result,
                location=location,
                site_name=site_name
            )

            # Clean up temporary file
            os.remove(temp_image_path)
            logger.info(f"Prediction saved with ID: {prediction.id}")

            # Prepare response
            prediction_data = {
                'id': prediction.id,
                'result': prediction_result,
                'location': prediction.location,
                'site_name': prediction.site_name,
                'timestamp': prediction.timestamp.isoformat()
            }

            return JsonResponse(prediction_data, status=status.HTTP_201_CREATED)

        except Exception as prediction_error:
            # Handle prediction-specific errors
            logger.error(f"Prediction error: {str(prediction_error)}")
            
            # Remove temporary file if prediction fails
            if os.path.exists(temp_image_path):
                os.remove(temp_image_path)

            return JsonResponse({
                'error': 'Image prediction failed',
                'details': str(prediction_error)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    except Exception as global_error:
        # Catch any unexpected errors
        logger.critical(f"Unexpected error in prediction view: {str(global_error)}")
        return JsonResponse({
            'error': 'An unexpected error occurred during prediction'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
# List all predictions for the authenticated user
class PredictionListView(generics.ListAPIView):
    serializer_class = PredictionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        This method filters the predictions based on the authenticated user.
        Additionally, you can implement further filtering based on query parameters
        if needed, such as filtering by prediction date, or other fields.
        """
        queryset = Prediction.objects.filter(user=self.request.user)

        # Optional: Handle additional query parameters if needed
        # Example: Filtering predictions based on a date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')

        if start_date:
            queryset = queryset.filter(predicted_at__gte=start_date)
        if end_date:
            queryset = queryset.filter(predicted_at__lte=end_date)

        return queryset
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_predictions(request):
    """
    Fetch all predictions for the authenticated user.
    """
    try:
        # Fetch predictions for the logged-in user
        predictions = Prediction.objects.filter(user=request.user).order_by('-timestamp')
        
        # Serialize the predictions
        serializer = PredictionSerializer(predictions, many=True)
        
        # Return the serialized predictions as a response
        return Response({
            'predictions': serializer.data
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        # Log the error (optional)
        logger.error(f"Error fetching predictions: {str(e)}")
        
        return Response({
            'error': 'Failed to retrieve predictions'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
# Get a specific prediction by ID for the authenticated user
class PredictionDetailView(generics.RetrieveAPIView):
    serializer_class = PredictionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Filter predictions based on the authenticated user
        return Prediction.objects.filter(user=self.request.user)

# Update a prediction for the authenticated user
@api_view(['PUT', 'PATCH'])
def update_prediction(request, pk):
    try:
        # Get the prediction and check if it belongs to the authenticated user
        prediction = Prediction.objects.get(pk=pk, user=request.user)

        serializer = PredictionSerializer(prediction, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    except Prediction.DoesNotExist:
        return Response({'error': 'Prediction not found or not owned by the user'}, status=status.HTTP_404_NOT_FOUND)

# Delete a prediction for the authenticated user
@api_view(['DELETE'])
def delete_prediction(request, pk):
    try:
        # Get the prediction and check if it belongs to the authenticated user
        prediction = Prediction.objects.get(pk=pk, user=request.user)
        prediction.delete()
        return Response({'message': 'Prediction deleted successfully'}, status=status.HTTP_204_NO_CONTENT)
    
    except Prediction.DoesNotExist:
        return Response({'error': 'Prediction not found or not owned by the user'}, status=status.HTTP_404_NOT_FOUND)
    

class FarmerAnalyticsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        # Get all predictions for the logged-in user
        predictions = Prediction.objects.filter(user=user)

        # Calculate time ranges
        today = timezone.now()
        last_30_days = today - timedelta(days=30)
        last_7_days = today - timedelta(days=7)

        # Basic statistics
        total_predictions = predictions.count()
        recent_predictions = predictions.filter(timestamp__gte=last_30_days).count()
        
        # Weed detection statistics
        weed_statistics = predictions.values('result').annotate(
            count=Count('id')
        ).order_by('-count')

        # Location-based analysis
        location_statistics = predictions.values('location').annotate(
            count=Count('id')
        ).order_by('-count')

        # Time-based analysis (monthly)
        monthly_trends = predictions.annotate(
            month=TruncMonth('timestamp')
        ).values('month').annotate(
            count=Count('id')
        ).order_by('month')

        # Weekly analysis
        weekly_trends = predictions.filter(
            timestamp__gte=last_30_days
        ).annotate(
            week=TruncWeek('timestamp')
        ).values('week').annotate(
            count=Count('id')
        ).order_by('week')

        # Site-specific analysis
        site_statistics = predictions.values('site_name').annotate(
            count=Count('id')
        ).order_by('-count')

        # Recent activity
        recent_activity = predictions.filter(
            timestamp__gte=last_7_days
        ).values('id', 'result', 'timestamp', 'location', 'site_name'
        ).order_by('-timestamp')[:10]

        return Response({
            'overview': {
                'total_predictions': total_predictions,
                'recent_predictions': recent_predictions,
                'unique_locations': predictions.values('location').distinct().count(),
                'unique_sites': predictions.values('site_name').distinct().count()
            },
            'weed_statistics': weed_statistics,
            'location_statistics': location_statistics,
            'monthly_trends': monthly_trends,
            'weekly_trends': weekly_trends,
            'site_statistics': site_statistics,
            'recent_activity': recent_activity
        })    