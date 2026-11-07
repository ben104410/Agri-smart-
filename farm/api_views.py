from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.authtoken.models import Token
from django.contrib.auth import login as django_login, logout as django_logout
from django.utils import timezone

from .models import Crop, IrrigationTask, FarmCondition, FarmAlert
from .serializers import (
    CropSerializer,
    IrrigationTaskSerializer,
    FarmConditionSerializer,
    FarmAlertSerializer,
    DashboardSummarySerializer,
    ReportsSummarySerializer,
    UserSerializer,
    RegisterSerializer,
    LoginSerializer,
)
from .views import get_default_condition


class CropViewSet(viewsets.ModelViewSet):
    """
    CRUD API for Crop records.
    Supports filtering by condition (?condition=healthy) and searching (?search=Maize).
    """
    queryset = Crop.objects.all()
    serializer_class = CropSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        condition = self.request.query_params.get('condition')
        search = self.request.query_params.get('search')
        if condition:
            qs = qs.filter(condition=condition)
        if search:
            qs = qs.filter(name__icontains=search) | qs.filter(plot_name__icontains=search)
        return qs


class IrrigationTaskViewSet(viewsets.ModelViewSet):
    """
    CRUD API for Irrigation tasks.
    Supports filtering by status (?status=pending).
    Includes a toggle action: POST /api/irrigation/{id}/toggle/
    """
    queryset = IrrigationTask.objects.all()
    serializer_class = IrrigationTaskSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        task_status = self.request.query_params.get('status')
        if task_status:
            qs = qs.filter(status=task_status)
        return qs

    @action(detail=True, methods=['post'], url_path='toggle')
    def toggle_status(self, request, pk=None):
        task = self.get_object()
        task.status = 'pending' if task.status == 'completed' else 'completed'
        task.save()
        serializer = self.get_serializer(task)
        return Response(serializer.data, status=status.HTTP_200_OK)


class FarmConditionViewSet(viewsets.ModelViewSet):
    """
    API for managing farm weather conditions & sensor readings.
    Provides GET /api/weather/current/ for immediate access to current conditions.
    """
    queryset = FarmCondition.objects.all()
    serializer_class = FarmConditionSerializer

    @action(detail=False, methods=['get'], url_path='current')
    def current(self, request):
        condition = get_default_condition()
        serializer = self.get_serializer(condition)
        return Response(serializer.data)

    @action(detail=False, methods=['post', 'put', 'patch'], url_path='update-current')
    def update_current(self, request):
        condition = get_default_condition()
        serializer = self.get_serializer(condition, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class FarmAlertViewSet(viewsets.ModelViewSet):
    """
    API for Farm Alerts & Observations.
    """
    queryset = FarmAlert.objects.all()
    serializer_class = FarmAlertSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        active_only = self.request.query_params.get('active')
        if active_only in ['true', '1', 'True']:
            qs = qs.filter(is_active=True)
        return qs

    @action(detail=True, methods=['post'], url_path='dismiss')
    def dismiss(self, request, pk=None):
        alert = self.get_object()
        alert.is_active = False
        alert.save()
        serializer = self.get_serializer(alert)
        return Response(serializer.data, status=status.HTTP_200_OK)


class DashboardAPIView(APIView):
    """
    Aggregated single-call endpoint for frontend dashboards:
    GET /api/dashboard/
    """
    def get(self, request):
        crops = Crop.objects.all()
        weather = get_default_condition()
        pending_irrigation = IrrigationTask.objects.filter(status='pending').count()
        active_alerts = FarmAlert.objects.filter(is_active=True)
        recent_crops = crops[:5]

        data = {
            'total_crops': crops.count(),
            'weather': weather,
            'irrigation_tasks_count': pending_irrigation,
            'alerts_count': active_alerts.count(),
            'alerts': active_alerts,
            'recent_crops': recent_crops,
            'conditions_breakdown': {
                'healthy': crops.filter(condition='healthy').count(),
                'needs_attention': crops.filter(condition='needs_attention').count(),
                'at_risk': crops.filter(condition='at_risk').count(),
            }
        }
        serializer = DashboardSummarySerializer(data)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ReportsAPIView(APIView):
    """
    Aggregated single-call endpoint for farm reports:
    GET /api/reports/
    """
    def get(self, request):
        crops = Crop.objects.all()
        tasks = IrrigationTask.objects.all()

        data = {
            'total_crops': crops.count(),
            'total_tasks': tasks.count(),
            'healthy_count': crops.filter(condition='healthy').count(),
            'attention_count': crops.filter(condition='needs_attention').count(),
            'risk_count': crops.filter(condition='at_risk').count(),
            'generated_date': timezone.now(),
            'crops': crops,
            'irrigation_tasks': tasks,
        }
        serializer = ReportsSummarySerializer(data)
        return Response(serializer.data, status=status.HTTP_200_OK)


class RegisterAPIView(APIView):
    """
    POST /api/auth/register/
    Payload: { "username": "...", "email": "...", "password": "...", "password_confirm": "...", "first_name": "", "last_name": "" }
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token, _ = Token.objects.get_or_create(user=user)
            return Response({
                'message': 'Account created successfully.',
                'token': token.key,
                'user': UserSerializer(user).data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginAPIView(APIView):
    """
    POST /api/auth/login/
    Payload: { "username": "...", "password": "..." }
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            django_login(request, user)
            token, _ = Token.objects.get_or_create(user=user)
            return Response({
                'message': 'Logged in successfully.',
                'token': token.key,
                'user': UserSerializer(user).data
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutAPIView(APIView):
    """
    POST /api/auth/logout/
    """
    permission_classes = [AllowAny]

    def post(self, request):
        if request.user.is_authenticated:
            Token.objects.filter(user=request.user).delete()
            django_logout(request)
        return Response({'message': 'Logged out successfully.'}, status=status.HTTP_200_OK)


class CurrentUserAPIView(APIView):
    """
    GET /api/auth/me/
    Requires: Authorization: Token <token> OR active session
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

