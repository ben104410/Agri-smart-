import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.utils import timezone
from .models import Crop, IrrigationTask, FarmCondition, FarmAlert, ChatMessage
from .ai_service import get_ai_chat_response
from .weather_service import fetch_live_weather, sync_live_weather
from .forms import (
    CropForm,
    IrrigationTaskForm,
    FarmConditionForm,
    UserRegisterForm,
    UserLoginForm,
)


def get_default_condition():
    condition = FarmCondition.objects.filter(is_active=True).first()
    if not condition:
        condition = FarmCondition.objects.create(
            location="Coastal Kenya",
            condition_text="Partly cloudy",
            temperature=28.0,
            soil_moisture=65,
            rainfall_forecast="Low",
            rainfall_chance=20,
            humidity=72,
            wind_speed=12.0,
            is_active=True
        )
    return condition


def dashboard(request):
    crops = Crop.objects.all()
    total_crops = crops.count()
    weather = get_default_condition()
    irrigation_pending = IrrigationTask.objects.filter(status='pending').count()
    active_alerts = FarmAlert.objects.filter(is_active=True)
    recent_crops = crops[:5]
    
    # Form for quick crop addition from dashboard
    crop_form = CropForm(request.POST or None)
    if request.method == 'POST' and 'add_crop' in request.POST:
        if crop_form.is_valid():
            crop_form.save()
            messages.success(request, "Crop registered successfully!")
            return redirect('dashboard')

    context = {
        'total_crops': total_crops,
        'weather': weather,
        'irrigation_tasks_count': irrigation_pending,
        'alerts_count': active_alerts.count(),
        'alerts': active_alerts,
        'recent_crops': recent_crops,
        'crop_form': crop_form,
        'today': timezone.now().date(),
        'active_nav': 'dashboard',
    }
    return render(request, 'farm/dashboard.html', context)


def crop_list(request):
    crops = Crop.objects.all()
    form = CropForm(request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            crop = form.save()
            messages.success(request, f"Registered crop '{crop.name}' for {crop.plot_name}!")
            return redirect('crop_list')
        else:
            messages.error(request, "Please correct the errors below.")

    context = {
        'crops': crops,
        'form': form,
        'total_records': crops.count(),
        'active_nav': 'crops',
    }
    return render(request, 'farm/crop_list.html', context)


def crop_edit(request, pk):
    crop = get_object_or_404(Crop, pk=pk)
    form = CropForm(request.POST or None, instance=crop)

    if request.method == 'POST':
        if form.is_valid():
            form.save()
            messages.success(request, f"Updated crop '{crop.name}' successfully.")
            return redirect('crop_list')

    context = {
        'crop': crop,
        'form': form,
        'active_nav': 'crops',
    }
    return render(request, 'farm/crop_edit.html', context)


def crop_delete(request, pk):
    crop = get_object_or_404(Crop, pk=pk)
    if request.method == 'POST':
        name = crop.name
        crop.delete()
        messages.success(request, f"Deleted crop '{name}'.")
    return redirect('crop_list')


def weather_view(request):
    weather = get_default_condition()
    form = FarmConditionForm(instance=weather)

    if request.method == 'POST':
        # Live weather synchronization action
        if 'sync_live' in request.POST:
            loc = request.POST.get('live_location', '').strip() or weather.location
            try:
                weather, live_data = sync_live_weather(loc)
                messages.success(
                    request,
                    f"Successfully synchronized live weather for '{weather.location}' from {live_data.get('source')}!"
                )
            except Exception as e:
                messages.error(request, f"Could not sync live weather: {e}")
            return redirect('weather')

        # Manual parameter update / simulation
        form = FarmConditionForm(request.POST, instance=weather)
        if form.is_valid():
            form.save()
            messages.success(request, "Farm weather condition updated manually!")
            return redirect('weather')

    # Fetch real-time 7-day agricultural forecast for current location
    forecast = []
    weather_source = "Live Weather API"
    condition_icon = "⛅"
    try:
        live_info = fetch_live_weather(weather.location)
        forecast = live_info.get('forecast', [])
        weather_source = live_info.get('source', 'Live Weather API')
        condition_icon = live_info.get('condition_icon', '⛅')
    except Exception:
        pass

    context = {
        'weather': weather,
        'form': form,
        'forecast': forecast,
        'weather_source': weather_source,
        'condition_icon': condition_icon,
        'active_nav': 'weather',
    }
    return render(request, 'farm/weather.html', context)


@require_POST
def weather_sync_api(request):
    """
    JSON API endpoint for syncing live weather from external API.
    """
    try:
        data = json.loads(request.body.decode('utf-8') or '{}')
    except Exception:
        data = {}

    location = data.get('location') or request.POST.get('location')
    try:
        weather, live_data = sync_live_weather(location)
        return JsonResponse({
            'success': True,
            'source': live_data.get('source'),
            'location': weather.location,
            'temperature': float(weather.temperature),
            'humidity': weather.humidity,
            'wind_speed': float(weather.wind_speed),
            'rainfall_chance': weather.rainfall_chance,
            'rainfall_forecast': weather.rainfall_forecast,
            'condition_text': weather.condition_text,
            'condition_icon': live_data.get('condition_icon', '⛅'),
            'forecast': live_data.get('forecast', []),
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)



def irrigation_view(request):
    tasks = IrrigationTask.objects.all()
    form = IrrigationTaskForm(request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            task = form.save()
            messages.success(request, f"Scheduled irrigation task for {task.crop_or_plot}!")
            return redirect('irrigation')
        else:
            messages.error(request, "Please check the form inputs.")

    context = {
        'tasks': tasks,
        'form': form,
        'active_nav': 'irrigation',
    }
    return render(request, 'farm/irrigation.html', context)


def irrigation_toggle_status(request, pk):
    task = get_object_or_404(IrrigationTask, pk=pk)
    if task.status == 'completed':
        task.status = 'pending'
    else:
        task.status = 'completed'
    task.save()
    messages.success(request, f"Task status updated to {task.get_status_display()}.")
    return redirect('irrigation')


def irrigation_delete(request, pk):
    task = get_object_or_404(IrrigationTask, pk=pk)
    if request.method == 'POST':
        task.delete()
        messages.success(request, "Irrigation task removed.")
    return redirect('irrigation')


def reports_view(request):
    crops = Crop.objects.all()
    irrigation_tasks = IrrigationTask.objects.all()
    
    total_crops = crops.count()
    healthy_count = crops.filter(condition='healthy').count()
    attention_count = crops.filter(condition='needs_attention').count()
    risk_count = crops.filter(condition='at_risk').count()
    total_tasks = irrigation_tasks.count()

    context = {
        'crops': crops,
        'total_crops': total_crops,
        'healthy_count': healthy_count,
        'attention_count': attention_count,
        'risk_count': risk_count,
        'total_tasks': total_tasks,
        'active_nav': 'reports',
        'generated_date': timezone.now(),
    }
    return render(request, 'farm/reports.html', context)


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    form = UserLoginForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            username_input = form.cleaned_data['username'].strip()
            password = form.cleaned_data['password']

            # Support login with email
            if '@' in username_input:
                user_match = User.objects.filter(email__iexact=username_input).first()
                if user_match:
                    username_input = user_match.username

            user = authenticate(request, username=username_input, password=password)
            if user is not None:
                auth_login(request, user)
                messages.success(request, f"Welcome back, {user.first_name or user.username}!")
                next_url = request.GET.get('next') or request.POST.get('next') or 'dashboard'
                return redirect(next_url)
            else:
                messages.error(request, "Invalid username/email or password.")

    return render(request, 'farm/login.html', {'form': form, 'active_nav': 'login'})


def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    form = UserRegisterForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            user = form.save()
            auth_login(request, user)
            messages.success(request, f"Welcome to AgriSmart, {user.first_name or user.username}! Your account has been created.")
            return redirect('dashboard')
        else:
            messages.error(request, "Please review and correct the errors below.")

    return render(request, 'farm/register.html', {'form': form, 'active_nav': 'register'})


def logout_view(request):
    if request.user.is_authenticated:
        auth_logout(request)
        messages.success(request, "You have been logged out safely.")
    return redirect('login')


@login_required
def ai_assistant_view(request):
    """
    Dedicated full-page AI Assistant workspace for logged-in farmers.
    """
    chat_history = ChatMessage.objects.filter(user=request.user).order_by('created_at')
    weather = get_default_condition()
    crops_count = Crop.objects.count()
    pending_tasks = IrrigationTask.objects.filter(status='pending').count()
    alerts_count = FarmAlert.objects.filter(is_active=True).count()

    context = {
        'chat_history': chat_history,
        'weather': weather,
        'crops_count': crops_count,
        'pending_tasks': pending_tasks,
        'alerts_count': alerts_count,
        'active_nav': 'ai_assistant',
    }
    return render(request, 'farm/ai_assistant.html', context)


@require_POST
def ai_chat_api(request):
    """
    JSON API endpoint for sending questions to AgriSmart AI.
    Used by both the dedicated page and the floating widget across all pages.
    """
    if not request.user.is_authenticated:
        return JsonResponse(
            {'error': 'Please log in to chat with AgriSmart AI.'},
            status=401
        )

    try:
        data = json.loads(request.body.decode('utf-8') or '{}')
    except Exception:
        return JsonResponse({'error': 'Invalid JSON request.'}, status=400)

    user_message = data.get('message', '').strip()
    if not user_message:
        return JsonResponse({'error': 'Message cannot be empty.'}, status=400)

    # 1. Record farmer's message
    user_msg_obj = ChatMessage.objects.create(
        user=request.user,
        role='user',
        content=user_message
    )

    # 2. Retrieve recent dialogue history for conversational context
    history = list(ChatMessage.objects.filter(user=request.user).order_by('-created_at')[:8])
    history.reverse()

    # 3. Call AI service with farm context
    try:
        ai_reply = get_ai_chat_response(request.user, user_message, chat_history=history)
    except Exception as e:
        ai_reply = f"I encountered an unexpected error processing your request: {str(e)}"

    # 4. Save assistant's reply
    ai_msg_obj = ChatMessage.objects.create(
        user=request.user,
        role='assistant',
        content=ai_reply
    )

    return JsonResponse({
        'reply': ai_reply,
        'created_at': ai_msg_obj.created_at.strftime('%H:%M'),
        'user_created_at': user_msg_obj.created_at.strftime('%H:%M'),
    })


def ai_history_api(request):
    """
    Returns recent chat messages for the current user (used by floating widget on page load).
    """
    if not request.user.is_authenticated:
        return JsonResponse({'messages': []})

    messages_qs = ChatMessage.objects.filter(user=request.user).order_by('created_at')[:40]
    data = [
        {
            'role': m.role,
            'content': m.content,
            'time': m.created_at.strftime('%H:%M')
        }
        for m in messages_qs
    ]
    return JsonResponse({'messages': data})


@login_required
@require_POST
def ai_clear_history(request):
    """
    Clears all previous chat history for the logged-in user.
    """
    ChatMessage.objects.filter(user=request.user).delete()
    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', ''):
        return JsonResponse({'status': 'cleared'})
    messages.success(request, "Chat history has been cleared.")
    return redirect('ai_assistant')



