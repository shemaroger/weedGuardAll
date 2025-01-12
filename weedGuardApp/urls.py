from django.conf import settings
from django.urls import path
from django.conf.urls.static import static
from .views import *
from . import views

urlpatterns = [
    path('user/', views.create_user, name='user-list-create'),
    path('users/<int:pk>/', UserRetrieveUpdateDestroyView.as_view(), name='user-detail'),
    path('login/', LoginView.as_view(), name='login'),
    path('predict/', predict_view, name='predict'),  # Create
    path('predictions/', views.PredictionListView.as_view(), name='prediction-list'),
    path('predictions/<int:pk>/', views.PredictionDetailView.as_view(), name='prediction-detail'),
    path('predictions/<int:pk>/update/', views.update_prediction, name='prediction-update'),
    path('predictions/<int:pk>/delete/', views.delete_prediction, name='prediction-delete'),
    path('predictions-list/', views.get_user_predictions, name='get_user_predictions'),
    path('analytics/', FarmerAnalyticsView.as_view(), name='farmer-analytics'),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
