from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from farm.models import Crop, IrrigationTask, FarmCondition, FarmAlert


class Command(BaseCommand):
    help = 'Seeds initial demonstration data matching the AgriSmart prototype'

    def handle(self, *args, **options):
        self.stdout.write("Seeding AgriSmart prototype demonstration data...")

        # 1. Weather / Farm conditions
        condition, created = FarmCondition.objects.get_or_create(
            location="Coastal Kenya",
            defaults={
                'condition_text': "Partly cloudy",
                'temperature': 28.0,
                'soil_moisture': 65,
                'rainfall_forecast': "Low",
                'rainfall_chance': 20,
                'humidity': 72,
                'wind_speed': 12.0,
                'is_active': True,
            }
        )
        if not created:
            condition.temperature = 28.0
            condition.condition_text = "Partly cloudy"
            condition.soil_moisture = 65
            condition.rainfall_forecast = "Low"
            condition.rainfall_chance = 20
            condition.humidity = 72
            condition.wind_speed = 12.0
            condition.save()

        # 2. Farm Alert
        FarmAlert.objects.get_or_create(
            title="Review crop observations",
            defaults={
                'message': "Recent soil moisture fluctuations observed in Sector 2. Please inspect crop leaves.",
                'severity': 'warning',
                'is_active': True,
            }
        )

        # 3. Sample Crops
        today = timezone.now().date()
        crop1, _ = Crop.objects.get_or_create(
            name="Maize (SC Duma 43)",
            plot_name="North Field Plot A",
            defaults={
                'planting_date': today - timedelta(days=24),
                'condition': 'healthy',
                'notes': 'Emergence complete, good vegetative growth.'
            }
        )

        crop2, _ = Crop.objects.get_or_create(
            name="Cassava (KME 4)",
            plot_name="South Terraces",
            defaults={
                'planting_date': today - timedelta(days=45),
                'condition': 'healthy',
                'notes': 'Regular weeding scheduled next week.'
            }
        )

        crop3, _ = Crop.objects.get_or_create(
            name="Tomatoes (Anna F1)",
            plot_name="Greenhouse Block 1",
            defaults={
                'planting_date': today - timedelta(days=12),
                'condition': 'needs_attention',
                'notes': 'Slight leaf discoloration noted after recent heat spike.'
            }
        )

        # 4. Irrigation Tasks
        IrrigationTask.objects.get_or_create(
            crop_or_plot="North Field Plot A (Maize)",
            scheduled_date=today,
            defaults={
                'crop': crop1,
                'water_amount': "500 Litres",
                'status': 'pending',
                'notes': 'Drip line cycle 1.'
            }
        )

        IrrigationTask.objects.get_or_create(
            crop_or_plot="Greenhouse Block 1 (Tomatoes)",
            scheduled_date=today + timedelta(days=1),
            defaults={
                'crop': crop3,
                'water_amount': "250 Litres",
                'status': 'pending',
                'notes': 'Precision micro-sprinkler session.'
            }
        )

        self.stdout.write(self.style.SUCCESS("Successfully seeded AgriSmart demonstration data!"))
