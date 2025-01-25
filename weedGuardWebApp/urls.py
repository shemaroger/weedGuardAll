from django.conf import settings
from django.urls import path
from django.conf.urls.static import static
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('signup/', views.signup, name='signup'),
    path('loginn/', views.login_view, name='loginn'),
    path('predict', views.prediction_create, name='prediction_create'),
    path('logoutt/', views.logoutt_view, name='logout'),
    path('prediction', views.prediction_list, name='prediction_list'),  # This should match the root URL
    path('prediction/<int:pk>/', views.prediction_detail, name='prediction_detail'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('generate-report/', views.generate_report, name='generate_report'),
    path('users/', views.user_list, name='user_list'),
    path('users/create/', views.create_user, name='create_user'),
    path('users/update/<int:user_id>/', views.update_user, name='update_user'),
    path('users/delete/<int:user_id>/', views.delete_user, name='delete_user'),
    path('predictions/<int:id>/edit/', views.prediction_edit, name='prediction_edit'),
    path('predictions/<int:id>/delete/', views.prediction_delete, name='prediction_delete'),
    path('contact/', views.create_contact_message, name='create_contact_message'),
    path('contact/success/', views.contact_success, name='contact_success'),
    path('contactmessages/', views.contactmessage_list, name='contactmessage_list'),
     
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
