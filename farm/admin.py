from django.contrib import admin
from .models import Crop, IrrigationTask, FarmCondition, FarmAlert, ChatMessage


@admin.register(Crop)
class CropAdmin(admin.ModelAdmin):
    list_display = ('name', 'plot_name', 'planting_date', 'condition', 'created_at')
    list_filter = ('condition', 'planting_date')
    search_fields = ('name', 'plot_name', 'notes')


@admin.register(IrrigationTask)
class IrrigationTaskAdmin(admin.ModelAdmin):
    list_display = ('crop_or_plot', 'scheduled_date', 'water_amount', 'status', 'created_at')
    list_filter = ('status', 'scheduled_date')
    search_fields = ('crop_or_plot', 'notes')


@admin.register(FarmCondition)
class FarmConditionAdmin(admin.ModelAdmin):
    list_display = ('location', 'temperature', 'condition_text', 'humidity', 'soil_moisture', 'is_active', 'recorded_at')
    list_filter = ('is_active', 'location')


@admin.register(FarmAlert)
class FarmAlertAdmin(admin.ModelAdmin):
    list_display = ('title', 'severity', 'is_active', 'created_at')
    list_filter = ('severity', 'is_active')


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'short_content', 'created_at')
    list_filter = ('role', 'created_at')
    search_fields = ('content', 'user__username')

    def short_content(self, obj):
        return obj.content[:60] + ('...' if len(obj.content) > 60 else '')
    short_content.short_description = 'Message'


