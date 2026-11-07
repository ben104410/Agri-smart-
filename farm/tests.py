from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from farm.models import Crop, IrrigationTask, FarmCondition, FarmAlert


class FarmAppTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.crop = Crop.objects.create(
            name="Sorghum",
            plot_name="Plot B",
            condition="healthy"
        )
        self.task = IrrigationTask.objects.create(
            crop_or_plot="Plot B",
            water_amount="300L",
            status="pending"
        )
        self.condition = FarmCondition.objects.create(
            location="Coastal Kenya",
            temperature=28.0,
            soil_moisture=65
        )

    def test_dashboard_view(self):
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Good morning, Farmer")
        self.assertContains(response, "Sorghum")

    def test_crop_list_and_create(self):
        response = self.client.get(reverse('crop_list'))
        self.assertEqual(response.status_code, 200)

        # Create a new crop via POST
        post_response = self.client.post(reverse('crop_list'), {
            'name': 'Beans',
            'plot_name': 'Plot C',
            'planting_date': '2026-11-06',
            'condition': 'healthy',
            'notes': 'Demo note'
        })
        self.assertEqual(post_response.status_code, 302)
        self.assertTrue(Crop.objects.filter(name='Beans').exists())

    def test_weather_view(self):
        response = self.client.get(reverse('weather'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Coastal Kenya")

    def test_irrigation_toggle(self):
        response = self.client.get(reverse('irrigation_toggle', args=[self.task.pk]))
        self.assertEqual(response.status_code, 302)
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, 'completed')

    def test_reports_view(self):
        response = self.client.get(reverse('reports'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Crop report")


class FarmAPITests(TestCase):
    def setUp(self):
        self.client = Client()
        self.crop = Crop.objects.create(
            name="Maize",
            plot_name="Plot 1",
            condition="healthy"
        )
        self.task = IrrigationTask.objects.create(
            crop_or_plot="Plot 1 (Maize)",
            water_amount="500L",
            status="pending"
        )
        self.condition = FarmCondition.objects.create(
            location="Coastal Kenya",
            temperature=28.0,
            soil_moisture=65,
            is_active=True
        )
        self.alert = FarmAlert.objects.create(
            title="Pest Warning",
            severity="warning",
            is_active=True
        )

    def test_api_dashboard(self):
        response = self.client.get('/api/dashboard/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['total_crops'], 1)
        self.assertEqual(data['weather']['location'], "Coastal Kenya")
        self.assertEqual(data['irrigation_tasks_count'], 1)
        self.assertEqual(data['alerts_count'], 1)
        self.assertIn('conditions_breakdown', data)

    def test_api_crop_crud(self):
        # List
        res_list = self.client.get('/api/crops/')
        self.assertEqual(res_list.status_code, 200)

        # Create
        res_create = self.client.post('/api/crops/', {
            'name': 'Cassava',
            'plot_name': 'Plot 2',
            'condition': 'healthy',
            'planting_date': '2026-11-06'
        }, content_type='application/json')
        self.assertEqual(res_create.status_code, 201)
        crop_id = res_create.json()['id']

        # Read detail
        res_detail = self.client.get(f'/api/crops/{crop_id}/')
        self.assertEqual(res_detail.status_code, 200)
        self.assertEqual(res_detail.json()['name'], 'Cassava')

        # Update
        res_patch = self.client.patch(f'/api/crops/{crop_id}/', {
            'condition': 'needs_attention'
        }, content_type='application/json')
        self.assertEqual(res_patch.status_code, 200)
        self.assertEqual(res_patch.json()['condition'], 'needs_attention')

        # Delete
        res_del = self.client.delete(f'/api/crops/{crop_id}/')
        self.assertEqual(res_del.status_code, 204)

    def test_api_irrigation_toggle(self):
        res = self.client.post(f'/api/irrigation/{self.task.id}/toggle/')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()['status'], 'completed')

    def test_api_weather_current_and_update(self):
        # GET current
        res = self.client.get('/api/weather/current/')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()['location'], "Coastal Kenya")

        # Update current
        res_update = self.client.post('/api/weather/update-current/', {
            'temperature': 31.5,
            'soil_moisture': 55
        }, content_type='application/json')
        self.assertEqual(res_update.status_code, 200)
        self.assertEqual(float(res_update.json()['temperature']), 31.5)
        self.assertEqual(res_update.json()['soil_moisture'], 55)

    def test_api_alert_dismiss(self):
        res = self.client.post(f'/api/alerts/{self.alert.id}/dismiss/')
        self.assertEqual(res.status_code, 200)
        self.assertFalse(res.json()['is_active'])

    def test_api_reports(self):
        response = self.client.get('/api/reports/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('total_crops', data)
        self.assertIn('healthy_count', data)
        self.assertIn('crops', data)


class AuthTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.test_user = User.objects.create_user(
            username='farmer_joe',
            email='farmer.joe@example.com',
            password='StrongPassword123!',
            first_name='Joe',
            last_name='Farmer'
        )

    # 1. Web Views
    def test_web_login_get(self):
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Sign in to AgriSmart")

    def test_web_register_get(self):
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Create your AgriSmart account")

    def test_web_login_post_success(self):
        response = self.client.post(reverse('login'), {
            'username': 'farmer_joe',
            'password': 'StrongPassword123!'
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('dashboard'))

    def test_web_login_with_email_success(self):
        response = self.client.post(reverse('login'), {
            'username': 'farmer.joe@example.com',
            'password': 'StrongPassword123!'
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('dashboard'))

    def test_web_login_invalid(self):
        response = self.client.post(reverse('login'), {
            'username': 'farmer_joe',
            'password': 'WrongPassword'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Invalid username/email or password.")

    def test_web_register_post_success(self):
        response = self.client.post(reverse('register'), {
            'username': 'mary_green',
            'email': 'mary@farm.com',
            'first_name': 'Mary',
            'last_name': 'Green',
            'password': 'SuperSecretPassword2026!',
            'password_confirm': 'SuperSecretPassword2026!',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username='mary_green').exists())

    def test_web_logout(self):
        self.client.login(username='farmer_joe', password='StrongPassword123!')
        response = self.client.get(reverse('logout'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('login'))

    # 2. REST API Auth
    def test_api_register(self):
        response = self.client.post('/api/auth/register/', {
            'username': 'api_farmer',
            'email': 'api_farmer@example.com',
            'password': 'SecureApiPassword123!',
            'password_confirm': 'SecureApiPassword123!',
            'first_name': 'Api',
            'last_name': 'Farmer'
        }, content_type='application/json')
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertIn('token', data)
        self.assertEqual(data['user']['username'], 'api_farmer')

    def test_api_login(self):
        response = self.client.post('/api/auth/login/', {
            'username': 'farmer_joe',
            'password': 'StrongPassword123!'
        }, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('token', data)
        self.assertEqual(data['user']['username'], 'farmer_joe')

    def test_api_me_with_token(self):
        token, _ = Token.objects.get_or_create(user=self.test_user)
        response = self.client.get('/api/auth/me/', HTTP_AUTHORIZATION=f'Token {token.key}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['username'], 'farmer_joe')

    def test_api_logout(self):
        token, _ = Token.objects.get_or_create(user=self.test_user)
        response = self.client.post('/api/auth/logout/', HTTP_AUTHORIZATION=f'Token {token.key}')
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Token.objects.filter(user=self.test_user).exists())



