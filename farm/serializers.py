from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from .models import Crop, IrrigationTask, FarmCondition, FarmAlert


class CropSerializer(serializers.ModelSerializer):
    condition_display = serializers.CharField(source='get_condition_display', read_only=True)

    class Meta:
        model = Crop
        fields = [
            'id',
            'name',
            'plot_name',
            'planting_date',
            'condition',
            'condition_display',
            'notes',
            'created_at',
            'updated_at',
        ]


class IrrigationTaskSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    crop_name = serializers.CharField(source='crop.name', read_only=True)

    class Meta:
        model = IrrigationTask
        fields = [
            'id',
            'crop',
            'crop_name',
            'crop_or_plot',
            'scheduled_date',
            'water_amount',
            'status',
            'status_display',
            'notes',
            'created_at',
        ]


class FarmConditionSerializer(serializers.ModelSerializer):
    class Meta:
        model = FarmCondition
        fields = [
            'id',
            'location',
            'condition_text',
            'temperature',
            'soil_moisture',
            'rainfall_forecast',
            'rainfall_chance',
            'humidity',
            'wind_speed',
            'recorded_at',
            'is_active',
        ]


class FarmAlertSerializer(serializers.ModelSerializer):
    severity_display = serializers.CharField(source='get_severity_display', read_only=True)

    class Meta:
        model = FarmAlert
        fields = [
            'id',
            'title',
            'message',
            'severity',
            'severity_display',
            'is_active',
            'created_at',
        ]


class DashboardSummarySerializer(serializers.Serializer):
    total_crops = serializers.IntegerField()
    weather = FarmConditionSerializer()
    irrigation_tasks_count = serializers.IntegerField()
    alerts_count = serializers.IntegerField()
    alerts = FarmAlertSerializer(many=True)
    recent_crops = CropSerializer(many=True)
    conditions_breakdown = serializers.DictField()


class ReportsSummarySerializer(serializers.Serializer):
    total_crops = serializers.IntegerField()
    total_tasks = serializers.IntegerField()
    healthy_count = serializers.IntegerField()
    attention_count = serializers.IntegerField()
    risk_count = serializers.IntegerField()
    generated_date = serializers.DateTimeField()
    crops = CropSerializer(many=True)
    irrigation_tasks = IrrigationTaskSerializer(many=True)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'date_joined']


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True, required=True)
    email = serializers.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password_confirm', 'first_name', 'last_name']

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("An account with this email already exists.")
        return value

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password_confirm": "Password fields do not match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', '')
        )
        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)

    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')
        user = authenticate(username=username, password=password)
        if not user:
            raise serializers.ValidationError("Invalid username or password.")
        if not user.is_active:
            raise serializers.ValidationError("User account is disabled.")
        attrs['user'] = user
        return attrs

