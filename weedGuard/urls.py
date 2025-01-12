from django.contrib import admin
from django.urls import path, include

urlpatterns = [
     
    path('admin/', admin.site.urls),
    path('', include('weedGuardWebApp.urls')), 
    path('api/', include('weedGuardApp.urls')),  # Include API URLs from the weedGuardApp app
]
