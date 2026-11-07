import logging
from django.conf import settings
from django.utils import timezone
from .models import Crop, IrrigationTask, FarmCondition, FarmAlert

logger = logging.getLogger(__name__)


def build_system_context(user=None) -> str:
    """
    Builds a rich live context snapshot of the farm database and website capabilities
    to guide the Google Gemini model.
    """
    now = timezone.now()
    farmer_name = (
        user.get_full_name() or user.username
        if user and user.is_authenticated
        else "Farmer"
    )

    # 1. Live Crops
    crops = Crop.objects.all().order_by('-created_at')
    total_crops = crops.count()
    crop_lines = []
    healthy_count = 0
    attention_count = 0
    at_risk_count = 0

    for c in crops:
        if c.condition == 'healthy':
            healthy_count += 1
        elif c.condition == 'needs_attention':
            attention_count += 1
        elif c.condition == 'at_risk':
            at_risk_count += 1

        notes_str = f" | Notes: {c.notes}" if c.notes else ""
        crop_lines.append(
            f"  - [ID: {c.id}] {c.name} in '{c.plot_name}' | Planted: {c.planting_date} | "
            f"Condition: {c.get_condition_display()}{notes_str}"
        )

    # 2. Irrigation Tasks
    tasks = IrrigationTask.objects.all().order_by('scheduled_date')
    pending_tasks = tasks.filter(status='pending')
    completed_tasks = tasks.filter(status='completed')
    task_lines = []
    for t in tasks[:15]:
        task_lines.append(
            f"  - [ID: {t.id}] {t.crop_or_plot} | Scheduled: {t.scheduled_date} | "
            f"Water: {t.water_amount} | Status: {t.status.upper()}"
        )

    # 3. Weather / Farm Condition
    condition = FarmCondition.objects.filter(is_active=True).first()
    forecast_lines = []
    if condition:
        weather_summary = (
            f"Location: {condition.location}\n"
            f"Temperature: {condition.temperature}°C\n"
            f"Condition: {condition.condition_text}\n"
            f"Soil Moisture: {condition.soil_moisture}%\n"
            f"Relative Humidity: {condition.humidity}%\n"
            f"Rainfall Probability: {condition.rainfall_chance}% (Forecast: {condition.rainfall_forecast})\n"
            f"Wind Speed: {condition.wind_speed} km/h\n"
            f"Last Recorded: {condition.recorded_at.strftime('%Y-%m-%d %H:%M')}"
        )
        try:
            from .weather_service import fetch_live_weather
            live_w = fetch_live_weather(condition.location)
            for day in live_w.get('forecast', [])[:5]:
                forecast_lines.append(
                    f"  - {day['day_name']} ({day['day_full']}): {day['condition_icon']} {day['condition_text']} | High: {day['temp_max']}°C, Low: {day['temp_min']}°C | Rain Chance: {day['rain_chance']}% (Est. Rain: {day['precip_sum']}mm)"
                )
        except Exception:
            pass
    else:
        weather_summary = "No active weather sensor record found."

    forecast_text = "\n".join(forecast_lines) if forecast_lines else "  No multi-day forecast available."

    # 4. Alerts
    alerts = FarmAlert.objects.filter(is_active=True).order_by('-created_at')
    alert_lines = []
    for a in alerts:
        alert_lines.append(f"  - [{a.severity.upper()}] {a.title}: {a.message}")

    crops_text = "\n".join(crop_lines) if crop_lines else "  No crops currently registered."
    tasks_text = "\n".join(task_lines) if task_lines else "  No irrigation tasks currently recorded."
    alerts_text = "\n".join(alert_lines) if alert_lines else "  No active warnings or alerts."

    return f"""You are AgriSmart AI, an agricultural expert, smart farming advisor, and complete assistant for the AgriSmart platform.
You are assisting {farmer_name}.
Current Date: {now.strftime('%A, %d %B %Y')}.

==================================================
AGRISMART PLATFORM ARCHITECTURE & WEBSITE GUIDE
==================================================
Farmers and visitors can ask you about how to navigate and use ANY feature of AgriSmart. Here is the structure:

1. Dashboard (/):
   - Executive farm overview: total crops, live weather widget, pending irrigation count, active farm alerts.
   - Quick "Register New Crop" form directly on the dashboard.
   - Quick table of recently registered crops.

2. Crop Management (/crops/):
   - Crop registry with total crop counts and status badges.
   - Crop registration form (Crop Name, Plot Name, Planting Date, Condition: Healthy / Needs attention / At risk, and Notes).
   - Edit crop details at /crops/<id>/edit/.
   - Delete crop at /crops/<id>/delete/.

3. Weather Telemetry (/weather/):
   - Real-time farm telemetry: Temperature, Soil Moisture %, Relative Humidity %, Rainfall Chance %, Wind Speed.
   - Live location switcher to fetch real-time satellite & numerical weather data for any farm or city.
   - 7-Day agricultural weather forecast cards (temperatures, precipitation chance, rain volume).
   - "Manual Sensor Override" form to adjust sensor data and simulations.

4. Irrigation Scheduling (/irrigation/):
   - List of scheduled irrigation tasks with status (Pending, Completed, Cancelled).
   - "Schedule Irrigation" form (Crop or Plot, Scheduled Date, Water Amount, Notes).
   - Instant "Mark Completed" / "Mark Pending" toggle button (/irrigation/<id>/toggle/).
   - Delete task (/irrigation/<id>/delete/).

5. Reports & Analytics (/reports/):
   - High-level farm summary, crop health breakdown, irrigation execution stats.
   - Integrated "Print / Save PDF" button for official farm audit logs.

6. REST API Endpoints (/api/):
   - JSON endpoints: /api/crops/, /api/weather/, /api/irrigation/, /api/alerts/, and token auth at /api/auth/token/.

7. AI Assistant (/ai-assistant/):
   - Full dedicated chat workspace and floating quick-chat widget available on every page.

==================================================
CURRENT LIVE FARM DATABASE SNAPSHOT
==================================================
CURRENT WEATHER & SOIL STATUS:
{weather_summary}

UPCOMING 5-DAY AGRICULTURAL WEATHER FORECAST:
{forecast_text}

ACTIVE SYSTEM ALERTS ({alerts.count()} active):
{alerts_text}
   - Quick "Register New Crop" form directly on the dashboard.
   - Quick table of recently registered crops.

2. Crop Management (/crops/):
   - Crop registry with total crop counts and status badges.
   - Crop registration form (Crop Name, Plot Name, Planting Date, Condition: Healthy / Needs attention / At risk, and Notes).
   - Edit crop details at /crops/<id>/edit/.
   - Delete crop at /crops/<id>/delete/.

3. Weather Telemetry (/weather/):
   - Real-time farm telemetry: Temperature, Soil Moisture %, Relative Humidity %, Rainfall Chance %, Wind Speed.
   - 7-Day agricultural weather forecast cards.
   - "Update Farm Conditions" form to adjust sensor data and simulations.

4. Irrigation Scheduling (/irrigation/):
   - List of scheduled irrigation tasks with status (Pending, Completed, Cancelled).
   - "Schedule Irrigation" form (Crop or Plot, Scheduled Date, Water Amount, Notes).
   - Instant "Mark Completed" / "Mark Pending" toggle button (/irrigation/<id>/toggle/).
   - Delete task (/irrigation/<id>/delete/).

5. Reports & Analytics (/reports/):
   - High-level farm summary, crop health breakdown, irrigation execution stats.
   - Integrated "Print / Save PDF" button for official farm audit logs.

6. REST API Endpoints (/api/):
   - JSON endpoints: /api/crops/, /api/weather/, /api/irrigation/, /api/alerts/, and token auth at /api/auth/token/.

7. AI Assistant (/ai-assistant/):
   - Full dedicated chat workspace and floating quick-chat widget available on every page.

==================================================
CURRENT LIVE FARM DATABASE SNAPSHOT
==================================================
CURRENT WEATHER & SOIL STATUS:
{weather_summary}

ACTIVE SYSTEM ALERTS ({alerts.count()} active):
{alerts_text}

CROP INVENTORY ({total_crops} total | {healthy_count} healthy, {attention_count} needs attention, {at_risk_count} at risk):
{crops_text}

IRRIGATION SCHEDULE ({tasks.count()} total | {pending_tasks.count()} pending, {completed_tasks.count()} completed):
{tasks_text}

==================================================
YOUR INSTRUCTIONS & RESPONSE GUIDELINES
==================================================
1. WEBSITE QUESTIONS: If the user asks how to do anything on the website (e.g. how to add a crop, how to change weather conditions, how to complete an irrigation task, how to print reports), give clear, concise, step-by-step instructions referencing the exact page or button.
2. FARM DATA QUESTIONS: If the user asks about their farm (e.g., "what crops need attention?", "what is my soil moisture?", "what is scheduled for watering?"), use the exact numbers and records from the snapshot above.
3. AGRONOMIC & FARMING ADVICE: Provide sound, practical agronomic recommendations (e.g. pest and disease management, optimal planting times, irrigation adjustments based on soil moisture and rain forecast, fertilizer application, crop rotation).
4. FORMATTING: Use clean, easy-to-read Markdown with short paragraphs, bold text for key points, and bulleted lists.
5. TONE: Warm, encouraging, expert, and professional.
"""


def _generate_fallback_response(user, user_prompt: str, error_reason: str = "") -> str:
    """
    Intelligent local response engine used when GEMINI_API_KEY is not configured
    or when external network/API quota is unavailable.
    Ensures the user always gets a rich, helpful answer based on their live farm data.
    """
    prompt_lower = user_prompt.lower()
    crops = Crop.objects.all()
    weather = FarmCondition.objects.filter(is_active=True).first()
    tasks = IrrigationTask.objects.filter(status='pending')
    alerts = FarmAlert.objects.filter(is_active=True)

    header = ""
    if not getattr(settings, 'GEMINI_API_KEY', None):
        header = (
            "> ℹ️ **Note:** `GEMINI_API_KEY` is not yet configured in your `.env` file. "
            "To activate full Google Gemini generative AI, add `GEMINI_API_KEY=your_key` to `.env`. "
            "In the meantime, I am providing answers directly from your AgriSmart farm database!\n\n"
        )

    # Intent detection for common queries
    if any(w in prompt_lower for w in ['crop', 'plant', 'maize', 'cassava', 'tomato']):
        at_risk = crops.filter(condition='at_risk')
        attention = crops.filter(condition='needs_attention')
        healthy = crops.filter(condition='healthy')

        lines = [f"### 🌾 Crop Status Overview ({crops.count()} registered)"]
        if at_risk.exists():
            lines.append(f"⚠️ **At Risk ({at_risk.count()}):** " + ", ".join([f"{c.name} ({c.plot_name})" for c in at_risk]))
        if attention.exists():
            lines.append(f"🔍 **Needs Attention ({attention.count()}):** " + ", ".join([f"{c.name} ({c.plot_name})" for c in attention]))
        if healthy.exists():
            lines.append(f"✅ **Healthy ({healthy.count()}):** " + ", ".join([f"{c.name} ({c.plot_name})" for c in healthy]))

        lines.append("\n**Quick Actions:**")
        lines.append("- To register or edit crops, navigate to **Crop Management** (`/crops/`).")
        lines.append("- Regularly inspect crops marked *Needs attention* or *At risk* for pest infestations, nutrient deficiencies, or underwatering.")
        return header + "\n".join(lines)

    if any(w in prompt_lower for w in ['weather', 'rain', 'temperature', 'moisture', 'soil', 'climate']):
        if weather:
            return (
                f"{header}### ⛅ Current Farm Weather & Soil Telemetry\n\n"
                f"- **Location:** {weather.location}\n"
                f"- **Condition:** {weather.condition_text}\n"
                f"- **Temperature:** {weather.temperature}°C\n"
                f"- **Soil Moisture:** {weather.soil_moisture}% ({'Optimal' if 60 <= weather.soil_moisture <= 80 else 'Check irrigation needs'})\n"
                f"- **Relative Humidity:** {weather.humidity}%\n"
                f"- **Rainfall Forecast:** {weather.rainfall_forecast} ({weather.rainfall_chance}% chance)\n"
                f"- **Wind Speed:** {weather.wind_speed} km/h\n\n"
                f"**Recommendation:** With soil moisture at {weather.soil_moisture}% and rain chance at {weather.rainfall_chance}%, "
                f"{'hold off on extensive overhead irrigation if rain is imminent' if weather.rainfall_chance > 50 else 'continue with scheduled drip irrigation as planned'}. "
                f"You can view forecasts and update sensor values in the **Weather** tab (`/weather/`)."
            )

    if any(w in prompt_lower for w in ['irrigation', 'water', 'task', 'schedule']):
        lines = [f"### 💧 Irrigation Schedule ({tasks.count()} pending tasks)"]
        if tasks.exists():
            for t in tasks:
                lines.append(f"- **{t.crop_or_plot}**: Scheduled for **{t.scheduled_date}** ({t.water_amount})")
            lines.append("\n**Action:** Visit the **Irrigation** tab (`/irrigation/`) to toggle tasks to Completed or schedule new watering cycles.")
        else:
            lines.append("You currently have no pending irrigation tasks. All watering schedules are up to date! You can schedule new tasks at `/irrigation/`.")
        return header + "\n".join(lines)

    if any(w in prompt_lower for w in ['alert', 'warning', 'risk', 'problem']):
        lines = [f"### 🚨 Farm Alerts ({alerts.count()} active)"]
        if alerts.exists():
            for a in alerts:
                lines.append(f"- **[{a.severity.upper()}] {a.title}**: {a.message}")
        else:
            lines.append("✅ There are currently no active warnings or critical alerts for your farm.")
        return header + "\n".join(lines)

    if any(w in prompt_lower for w in ['how', 'where', 'website', 'help', 'navigate', 'use', 'report', 'print']):
        return (
            f"{header}### 🧭 AgriSmart Platform Navigation Guide\n\n"
            f"Here is a summary of what you can do on AgriSmart:\n\n"
            f"1. **Dashboard** (`/`): View total farm stats, quick weather reading, alerts, and quickly register a crop.\n"
            f"2. **Crop Management** (`/crops/`): Register, edit, or delete crops and monitor condition status (Healthy, Needs attention, At risk).\n"
            f"3. **Weather Telemetry** (`/weather/`): View live sensors, soil moisture, humidity, 7-day agricultural forecast, and simulate telemetry data.\n"
            f"4. **Irrigation Schedule** (`/irrigation/`): Schedule water amounts, mark tasks complete with one click, or delete old tasks.\n"
            f"5. **Reports & Audit** (`/reports/`): View comprehensive farm analytics and click **Print / Save as PDF** for your farm records.\n"
            f"6. **Ask Me (AgriSmart AI)**: Use this page or the floating chat bubble on any page to ask anything!"
        )

    # General greeting or conversational query
    return (
        f"{header}Hello! I am **AgriSmart AI**, your agricultural advisor and guide for the AgriSmart portal.\n\n"
        f"You can ask me anything about:\n"
        f"- **Your Farm Data:** \"Which crops need attention?\", \"What is my soil moisture?\", \"Are there any pending irrigation tasks?\"\n"
        f"- **Website Navigation:** \"How do I register a new crop?\", \"Where do I print reports?\", \"How do I schedule watering?\"\n"
        f"- **Agronomy & Best Practices:** Pest management, drip irrigation advice, fertilizer schedules, and seasonal planting.\n\n"
        f"*How can I assist your farm today?*"
    )


def get_ai_chat_response(user, user_message: str, chat_history=None) -> str:
    """
    Sends the user message and conversation history with injected farm context
    to Google Gemini. Falls back gracefully if an API key is missing or an error occurs.
    """
    api_key = getattr(settings, 'GEMINI_API_KEY', '').strip()
    model_name = getattr(settings, 'GEMINI_MODEL', 'gemini-1.5-flash').strip()

    # Re-check .env file dynamically in case user just added/updated their key
    if not api_key or api_key == 'your_gemini_api_key_here':
        import os
        from dotenv import load_dotenv
        env_path = settings.BASE_DIR / '.env'
        if env_path.exists():
            load_dotenv(env_path, override=True)
            api_key = os.getenv('GEMINI_API_KEY', '').strip()
            model_name = os.getenv('GEMINI_MODEL', model_name).strip()

    if not api_key or api_key == 'your_gemini_api_key_here':
        return _generate_fallback_response(user, user_message, "No API key configured")

    system_instruction = build_system_context(user)

    # Attempt using the modern google.genai SDK
    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)

        # Build contents from history + current message
        contents = []
        if chat_history:
            for msg in chat_history[-6:]:
                role = "user" if msg.role == 'user' else "model"
                contents.append(
                    types.Content(
                        role=role,
                        parts=[types.Part.from_text(text=msg.content)]
                    )
                )

        contents.append(
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=user_message)]
            )
        )

        response = client.models.generate_content(
            model=model_name,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.7,
                max_output_tokens=1000,
            )
        )

        if response and response.text:
            return response.text.strip()

    except Exception as e:
        logger.warning(f"google.genai SDK call failed, trying legacy google.generativeai: {e}")
        # Attempt using legacy google.generativeai SDK if modern call failed
        try:
            import google.generativeai as legacy_genai

            legacy_genai.configure(api_key=api_key)
            model = legacy_genai.GenerativeModel(
                model_name=model_name,
                system_instruction=system_instruction
            )

            # Build history for start_chat
            legacy_history = []
            if chat_history:
                for msg in chat_history[-6:]:
                    legacy_history.append({
                        "role": "user" if msg.role == 'user' else "model",
                        "parts": [msg.content]
                    })

            chat = model.start_chat(history=legacy_history)
            response = chat.send_message(user_message)
            if response and response.text:
                return response.text.strip()
        except Exception as e_legacy:
            logger.error(f"Both Gemini SDKs failed: {e_legacy}")
            return _generate_fallback_response(user, user_message, str(e_legacy))

    return _generate_fallback_response(user, user_message, "Empty response from Gemini")
