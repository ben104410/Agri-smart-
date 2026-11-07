from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import (
    CropViewSet,
    IrrigationTaskViewSet,
    FarmConditionViewSet,
    FarmAlertViewSet,
    DashboardAPIView,
    ReportsAPIView,
    RegisterAPIView,
    LoginAPIView,
    LogoutAPIView,
    CurrentUserAPIView,
)

router = DefaultRouter()
router.register(r'crops', CropViewSet, basename='api-crop')
router.register(r'irrigation', IrrigationTaskViewSet, basename='api-irrigation')
router.register(r'weather', FarmConditionViewSet, basename='api-weather')
router.register(r'alerts', FarmAlertViewSet, basename='api-alert')

urlpatterns = [
    path('auth/register/', RegisterAPIView.as_view(), name='api-auth-register'),
    path('auth/login/', LoginAPIView.as_view(), name='api-auth-login'),
    path('auth/logout/', LogoutAPIView.as_view(), name='api-auth-logout'),
    path('auth/me/', CurrentUserAPIView.as_view(), name='api-auth-me'),
    path('dashboard/', DashboardAPIView.as_view(), name='api-dashboard'),
    path('reports/', ReportsAPIView.as_view(), name='api-reports'),
    path('', include(router.urls)),
]
