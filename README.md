# AgriSmart · Precision Agriculture for Sustainable Crop Management

Academic prototype backend built with **Django 6**, **Django REST Framework**, and SQLite.

Includes full REST APIs and CORS support ready to connect with any modern frontend (React, Vite, Vue, Next.js, Flutter, React Native, or Vanilla JS).

---

## Features

- **Authentication & User Accounts**:
  - Web login (`/login/`) and registration (`/register/`) with password confirmation and validation.
  - Dual login support (log in with either **username** or **email** address).
  - Secure logout (`/logout/`).
  - Dynamic user avatar badge and personalized greetings for authenticated farmers.
  - REST API Token & Session authentication endpoints (`/api/auth/register/`, `/api/auth/login/`, `/api/auth/logout/`, `/api/auth/me/`).
- **REST API & CORS Enabled**:
  - Full CRUD endpoints under `/api/`.
  - Single-call aggregated endpoints for dashboard (`/api/dashboard/`) and reports (`/api/reports/`).
  - Preconfigured with `django-cors-headers` to allow frontend requests from any origin (e.g. `localhost:3000`, `localhost:5173`).
  - DRF Browsable API enabled for instant in-browser testing.
- **Dashboard**:
  - Live metric counters (Total crops, Weather conditions, Irrigation tasks count, Farm alerts).
  - Registered crops summary.
  - Farm condition indicators (Temperature, Soil Moisture %, Rainfall status).
  - AgriSmart tips.
- **Crop Management**:
  - Register, list, edit, and delete crops (Name, Farm / plot, Planting date, Condition: *Healthy*, *Needs attention*, *At risk*, Observations).
  - Filter crops by condition (`?condition=healthy`) or search by name (`?search=Maize`).
- **Weather Monitoring**:
  - Microclimate readings (Location, Condition, Temperature, Humidity %, Rainfall chance %, Wind speed).
  - Dedicated `/api/weather/current/` and `/api/weather/update-current/` endpoints.
- **Irrigation Management**:
  - Schedule watering tasks (Crop / plot, scheduled date, water amount, status).
  - Toggle tasks between *Pending* and *Completed* via `/api/irrigation/{id}/toggle/`.
- **Farm Reports**:
  - High-level summary (Total crops, total irrigation tasks, healthy crops breakdown).
  - Printable report view and `/api/reports/` JSON endpoint.
- **Django Admin**:
  - Full CRUD interface for all models (`/admin/`).

---

## REST API Reference

All API routes are prefixed with `/api/`:

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/auth/register/` | Register new account; returns user profile and auth token |
| `POST` | `/api/auth/login/` | Sign in; returns user profile and auth token |
| `POST` | `/api/auth/logout/` | Log out and revoke active auth token |
| `GET` | `/api/auth/me/` | Fetch authenticated user's profile (`Authorization: Token <token>`) |
| `GET` | `/api/dashboard/` | Consolidated dashboard data (metrics, weather, alerts, recent crops) |
| `GET` | `/api/reports/` | Consolidated report summary and crop inventory statistics |
| `GET`, `POST` | `/api/crops/` | List crops (supports `?condition=` and `?search=`) or create a crop |
| `GET`, `PUT`, `PATCH`, `DELETE` | `/api/crops/{id}/` | Retrieve, update, or delete a specific crop |
| `GET`, `POST` | `/api/irrigation/` | List or create irrigation tasks (supports `?status=pending`) |
| `GET`, `PUT`, `PATCH`, `DELETE` | `/api/irrigation/{id}/` | Retrieve, update, or delete an irrigation task |
| `POST` | `/api/irrigation/{id}/toggle/` | Toggle task status between `pending` and `completed` |
| `GET` | `/api/weather/current/` | Get current active farm weather and sensor readings |
| `POST`, `PATCH` | `/api/weather/update-current/` | Update current farm weather readings |
| `GET`, `POST` | `/api/alerts/` | List farm alerts (supports `?active=true`) or post new alert |
| `POST` | `/api/alerts/{id}/dismiss/` | Dismiss an alert (`is_active = false`) |

---

## Frontend Integration Examples

### 1. User Sign Up and Sign In (Auth Token)
```javascript
const API_BASE = 'http://127.0.0.1:8000/api';

// Register a new farmer account
async function registerUser(username, email, password) {
  const response = await fetch(`${API_BASE}/auth/register/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      username,
      email,
      password,
      password_confirm: password
    })
  });
  const data = await response.json();
  if (data.token) {
    localStorage.setItem('agri_token', data.token); // Save token for future calls
  }
  return data;
}

// Log in
async function loginUser(usernameOrEmail, password) {
  const response = await fetch(`${API_BASE}/auth/login/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username: usernameOrEmail, password })
  });
  const data = await response.json();
  if (data.token) {
    localStorage.setItem('agri_token', data.token);
  }
  return data;
}

// Fetch authenticated user profile
async function getProfile() {
  const token = localStorage.getItem('agri_token');
  const response = await fetch(`${API_BASE}/auth/me/`, {
    headers: { 'Authorization': `Token ${token}` }
  });
  return await response.json();
}
```

### 2. Fetch Dashboard Data (React / Vanilla JS)
```javascript
const API_BASE = 'http://127.0.0.1:8000/api';

async function fetchDashboard() {
  const response = await fetch(`${API_BASE}/dashboard/`);
  const data = await response.json();
  console.log('Total Crops:', data.total_crops);
  console.log('Weather:', data.weather.temperature, '°C');
  console.log('Pending Irrigation Tasks:', data.irrigation_tasks_count);
  return data;
}
```

### 2. Register a New Crop
```javascript
async function addCrop(cropData) {
  const response = await fetch(`${API_BASE}/crops/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      name: 'Tomatoes (Anna F1)',
      plot_name: 'Greenhouse 1',
      planting_date: '2026-11-06',
      condition: 'healthy',
      notes: 'Planted with drip irrigation'
    })
  });
  return await response.json();
}
```

### 3. Toggle an Irrigation Task
```javascript
async function toggleIrrigationTask(taskId) {
  const response = await fetch(`${API_BASE}/irrigation/${taskId}/toggle/`, {
    method: 'POST'
  });
  return await response.json();
}
```

---

## Quick Start

### 1. Activate the Virtual Environment
On Windows (PowerShell):
```powershell
.\.venv\Scripts\Activate.ps1
```

### 2. Run Database Migrations
```powershell
python manage.py migrate
```

### 3. (Optional) Seed Demonstration Data
```powershell
python manage.py seed_demo_data
```

### 4. Run Unit Tests
```powershell
python manage.py test
```

### 5. Start the Development Server
```powershell
python manage.py runserver
```

- Web UI: `http://127.0.0.1:8000/`
- Browsable API Explorer: `http://127.0.0.1:8000/api/`
- Django Admin: `http://127.0.0.1:8000/admin/`

---

## Project Structure

```
Agrismart/
├── .venv/                      # Python virtual environment
├── agrismart_project/          # Django project configuration (settings, urls, wsgi)
├── farm/                       # Core farming app
│   ├── models.py               # Crop, IrrigationTask, FarmCondition, FarmAlert
│   ├── serializers.py          # DRF Model & Summary Serializers
│   ├── api_views.py            # ViewSets & Aggregated API endpoints
│   ├── api_urls.py             # REST API URL router
│   ├── views.py                # Server-rendered prototype views
│   ├── forms.py                # Django ModelForms
│   ├── urls.py                 # Web UI URLs
│   ├── admin.py                # Django Admin configurations
│   ├── tests.py                # Comprehensive test suite (11 tests)
│   └── management/commands/    # Seed demo data command
├── static/
│   └── css/style.css           # Prototype styles
├── templates/                  # Server-rendered HTML templates
├── manage.py
└── requirements.txt
```
│   └── css/style.css           # Custom prototype stylesheet matching original layout
├── templates/
│   ├── base.html               # Main sidebar, topbar, and layout
│   └── farm/
│       ├── dashboard.html      # Farm overview & quick crops
│       ├── crop_list.html      # Crop registration & table
│       ├── crop_edit.html      # Crop editor
│       ├── weather.html        # Weather monitoring & simulator
│       ├── irrigation.html     # Irrigation task scheduler
│       └── reports.html        # Printable report summary
├── manage.py
└── requirements.txt
```
