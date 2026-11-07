from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User


class Crop(models.Model):
    CONDITION_CHOICES = [
        ('healthy', 'Healthy'),
        ('needs_attention', 'Needs attention'),
        ('at_risk', 'At risk'),
    ]

    name = models.CharField(max_length=100, help_text="Crop name, e.g., Maize, Cassava, Tomatoes")
    plot_name = models.CharField(max_length=100, help_text="Farm / plot name, e.g., Plot A, North Field")
    planting_date = models.DateField(default=timezone.now)
    condition = models.CharField(
        max_length=20,
        choices=CONDITION_CHOICES,
        default='healthy'
    )
    notes = models.TextField(blank=True, null=True, help_text="Optional observations or notes")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.plot_name})"


class IrrigationTask(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    crop = models.ForeignKey(
        Crop,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='irrigation_tasks'
    )
    crop_or_plot = models.CharField(
        max_length=120,
        help_text="Crop or Plot descriptor (e.g., Plot A / Maize)"
    )
    scheduled_date = models.DateField(default=timezone.now)
    water_amount = models.CharField(
        max_length=80,
        help_text="e.g. 500 Litres, 25mm, or 45 mins drip"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['scheduled_date', '-created_at']

    def __str__(self):
        return f"Irrigation for {self.crop_or_plot} on {self.scheduled_date}"


class FarmCondition(models.Model):
    location = models.CharField(max_length=120, default="Coastal Kenya")
    condition_text = models.CharField(max_length=100, default="Partly cloudy")
    temperature = models.DecimalField(max_digits=4, decimal_places=1, default=28.0, help_text="in °C")
    soil_moisture = models.PositiveIntegerField(default=65, help_text="Soil moisture percentage")
    rainfall_forecast = models.CharField(max_length=50, default="Low")
    rainfall_chance = models.PositiveIntegerField(default=20, help_text="Chance of rain percentage")
    humidity = models.PositiveIntegerField(default=72, help_text="Relative humidity percentage")
    wind_speed = models.DecimalField(max_digits=4, decimal_places=1, default=12.0, help_text="in km/h")
    recorded_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-recorded_at']

    def __str__(self):
        return f"{self.location}: {self.temperature}°C ({self.condition_text})"


class FarmAlert(models.Model):
    SEVERITY_CHOICES = [
        ('info', 'Information'),
        ('warning', 'Warning'),
        ('critical', 'Critical'),
    ]

    title = models.CharField(max_length=150)
    message = models.TextField(blank=True)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='warning')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.severity.upper()}] {self.title}"


class ChatMessage(models.Model):
    ROLE_CHOICES = [
        ('user', 'User'),
        ('assistant', 'Assistant'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='chat_messages',
        null=True,
        blank=True
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        username = self.user.username if self.user else "Anonymous"
        return f"{username} [{self.role}]: {self.content[:40]}"

