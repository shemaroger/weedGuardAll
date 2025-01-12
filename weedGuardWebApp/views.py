import os
from django.shortcuts import render, redirect
from django.contrib.auth import login,logout
from django.contrib import messages
from weedGuardApp.models import *
from django.contrib.auth import authenticate, login
from django.conf import settings
from weedGuardApp.models import Prediction
from weedGuardApp.ml_model import predict_image
from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib import messages
from django.db.models import Count, F
from django.contrib.auth.models import User
from django.contrib.auth.models import User  # Do not use the default auth.User model
from django.contrib.auth.hashers import make_password
from weedGuardApp.models import User  # Correct import
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from .prediction_utils import predict_image
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.files.storage import default_storage
from django.conf import settings
import os
from django.contrib.auth import get_user_model


def signup(request):
    if request.method == 'POST':
        fullname = request.POST.get('fullname')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        role = request.POST.get('role', 'admin')  # Default to 'admin' if role is not provided

        # Basic validation
        if password != confirm_password:
            messages.error(request, "Passwords do not match")
            return redirect('signup')

        # Check if email already exists
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already exists")
            return redirect('signup')

        # Create a new user
        user = User(
            fullname=fullname,
            email=email,
            password=make_password(password),
            role=role
        )
        user.save()
        messages.success(request, 'Account created successfully! Please log in.')
        return redirect('loginn')
    
    return render(request, 'weedGuardWebApp/signup.html')

def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        # Authenticate the user
        user = authenticate(request, username=email, password=password)

        if user is not None:
            # Login and create a session
            login(request, user)
            messages.success(request, 'Logged in successfully')
            return redirect('admin_dashboard')  # Redirect to the prediction creation page or dashboard
        else:
            messages.error(request, 'Invalid credentials')
            return redirect('loginn')  # Redirect back to the login page if authentication fails

    return render(request, 'weedGuardWebApp/login.html')

def home(request):
    return render(request, 'weedGuardWebApp/home.html')

def logout_view(request):
    logout(request)
    return redirect('login')
def prediction_list(request):
    """View to display all predictions"""
    predictions = Prediction.objects.all().order_by('-timestamp')
    return render(request, 'weedGuardWebApp/prediction_list.html', {'predictions': predictions})

def prediction_detail(request, pk):
    """View to display details of a specific prediction"""
    prediction = get_object_or_404(Prediction, pk=pk)
    return render(request, 'weedGuardWebApp/prediction_detail.html', {'prediction': prediction})


@login_required
def prediction_create(request):
    """View to create a new prediction (upload image and run prediction)"""
    result = None  # Variable to hold the prediction result

    if request.method == 'POST' and request.FILES.get('image'):
        # Retrieve the uploaded image
        uploaded_image = request.FILES['image']
        
        # Save the image manually
        image_path = os.path.join(settings.MEDIA_ROOT, 'predictions', uploaded_image.name)
        with default_storage.open(image_path, 'wb') as f:
            for chunk in uploaded_image.chunks():
                f.write(chunk)
        
        # Run the prediction logic on the uploaded image
        result = predict_image(image_path)
        
        # Get coordinates and other fields from the POST data
        coordinates = request.POST.get('coordinates', '')  # This will retrieve the coordinates
        site_name = request.POST.get('site_name', '')
        
        # Create the Prediction object and save it
        prediction_instance = Prediction(
            image=uploaded_image,
            result=result,
            user=request.user,  # Only works if user is logged in
            location=coordinates,  # Save the location (coordinates)
            site_name=site_name,
        )
        prediction_instance.save()  # Save the prediction instance to the database

        # Send success message (optional)
        messages.success(request, f"Prediction created successfully: {result}")
        
    return render(request, 'weedGuardWebApp/predict.html', {'result': result})


from datetime import datetime, timedelta
from django.utils.timezone import now
from django.db.models import Count
from django.db.models.functions import TruncMonth

def admin_dashboard(request):
    # Calculate the date 3 months ago
    three_months_ago = now() - timedelta(days=90)

    # Filter predictions from the last 3 months
    recent_predictions = Prediction.objects.filter(timestamp__gte=three_months_ago)

    # Group predictions by month for trends
    weed_trends = recent_predictions.filter(result='Weed detected').annotate(month=TruncMonth('timestamp')).values('month').annotate(count=Count('id')).order_by('month')
    crop_trends = recent_predictions.filter(result='Crop detected').annotate(month=TruncMonth('timestamp')).values('month').annotate(count=Count('id')).order_by('month')

    # Count total farmers
    total_farmers = User.objects.filter(role='farmer').count()

    # Calculate user growth by month
    user_growth = User.objects.filter(role='farmer', created_at__gte=three_months_ago).annotate(month=TruncMonth('created_at')).values('month').annotate(count=Count('id')).order_by('month')

    # Count total predictions in the last 3 months
    total_predictions = recent_predictions.count()

    # Prepare context for rendering the dashboard
    context = {
        'total_farmers': total_farmers,
        'total_predictions': total_predictions,
        'weed_detected_count': recent_predictions.filter(result='Weed detected').count(),
        'crop_detected_count': recent_predictions.filter(result='Crop detected').count(),
        'weed_trends': list(weed_trends),
        'crop_trends': list(crop_trends),
        'user_growth': list(user_growth),
    }

    return render(request, 'weedGuardWebApp/adminDashboard.html', context)

# Report View
def generate_report(request):
    # Get the date range from the request
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    if start_date and end_date:
        try:
            report_start_date = datetime.strptime(start_date, '%Y-%m-%d')
            report_end_date = datetime.strptime(end_date, '%Y-%m-%d')
        except ValueError:
            report_start_date = now() - timedelta(days=90)
            report_end_date = now()
    else:
        # Default to the last 3 months if no date range is provided
        report_start_date = now() - timedelta(days=90)
        report_end_date = now()

    # Farmers statistics
    total_farmers = User.objects.filter(role='farmer').count()
    new_farmers_by_month = (
        User.objects.filter(role='farmer', created_at__range=(report_start_date, report_end_date))
        .annotate(month=TruncMonth('created_at'))
        .values('month')
        .annotate(new_farmers=Count('id'))
        .order_by('month')
    )

    # Predictions statistics
    total_predictions = Prediction.objects.filter(timestamp__range=(report_start_date, report_end_date)).count()
    weed_predictions = Prediction.objects.filter(result='Weed detected', timestamp__range=(report_start_date, report_end_date)).count()
    crop_predictions = Prediction.objects.filter(result='Crop detected', timestamp__range=(report_start_date, report_end_date)).count()

    predictions_by_month = (
        Prediction.objects.filter(timestamp__range=(report_start_date, report_end_date))
        .annotate(month=TruncMonth('timestamp'))
        .values('month', 'result')
        .annotate(count=Count('id'))
        .order_by('month', 'result')
    )

    # Compile the report context
    context = {
        'report_start_date': report_start_date.strftime('%Y-%m-%d'),
        'report_end_date': report_end_date.strftime('%Y-%m-%d'),
        'total_farmers': total_farmers,
        'new_farmers_by_month': list(new_farmers_by_month),
        'total_predictions': total_predictions,
        'weed_predictions': weed_predictions,
        'crop_predictions': crop_predictions,
        'predictions_by_month': list(predictions_by_month),
    }

    return render(request, 'weedGuardWebApp/report.html', context)

# View to list all users
def user_list(request):
    users = get_user_model().objects.all()
    return render(request, 'weedGuardWebApp/user_list.html', {'users': users})

# View to create a new user
def create_user(request):
    if request.method == 'POST':
        fullname = request.POST.get('fullname')
        email = request.POST.get('email')
        password = request.POST.get('password')
        role = request.POST.get('role', 'farmer')
        is_active = request.POST.get('is_active', 'true') == 'true'
        
        # Check if email already exists
        if get_user_model().objects.filter(email=email).exists():
            messages.error(request, 'Email already exists!')
            return redirect('create_user')
        
        user = get_user_model().objects.create_user(
            email=email,
            fullname=fullname,
            password=password,
            role=role,
            is_active=is_active
        )
        messages.success(request, 'User created successfully!')
        return redirect('user_list')

    return render(request, 'weedGuardWebApp/create_user.html')

# View to update an existing user
def update_user(request, user_id):
    user = get_object_or_404(get_user_model(), id=user_id)
    
    if request.method == 'POST':
        fullname = request.POST.get('fullname', user.fullname)
        email = request.POST.get('email', user.email)
        password = request.POST.get('password', '').strip()
        role = request.POST.get('role', user.role)
        is_active = 'is_active' in request.POST  # Checkbox logic

        # Update user fields
        user.fullname = fullname
        user.email = email
        if password:  # Update password only if provided
            user.set_password(password)
        user.role = role
        user.is_active = is_active
        user.save()

        messages.success(request, 'User updated successfully!')
        return redirect('user_list')

    return render(request, 'weedGuardWebApp/update_user.html', {'user': user})


# View to delete a user
def delete_user(request, user_id):
    user = get_object_or_404(get_user_model(), id=user_id)
    user.delete()
    messages.success(request, 'User deleted successfully!')
    return redirect('user_list')

