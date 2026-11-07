from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('crops/', views.crop_list, name='crop_list'),
    path('crops/<int:pk>/edit/', views.crop_edit, name='crop_edit'),
    path('crops/<int:pk>/delete/', views.crop_delete, name='crop_delete'),
    path('weather/', views.weather_view, name='weather'),
    path('irrigation/', views.irrigation_view, name='irrigation'),
    path('irrigation/<int:pk>/toggle/', views.irrigation_toggle_status, name='irrigation_toggle'),
    path('irrigation/<int:pk>/delete/', views.irrigation_delete, name='irrigation_delete'),
    path('reports/', views.reports_view, name='reports'),
    path('ai-assistant/', views.ai_assistant_view, name='ai_assistant'),
    path('ai-assistant/api/chat/', views.ai_chat_api, name='ai_chat_api'),
    path('ai-assistant/api/history/', views.ai_history_api, name='ai_history_api'),
    path('ai-assistant/clear/', views.ai_clear_history, name='ai_clear_history'),
]
