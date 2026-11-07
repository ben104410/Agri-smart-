from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import Crop, IrrigationTask, FarmCondition


class CropForm(forms.ModelForm):
    class Meta:
        model = Crop
        fields = ['name', 'plot_name', 'planting_date', 'condition', 'notes']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Crop name (e.g. Maize, Cassava)',
                'required': True
            }),
            'plot_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Farm / plot name (e.g. Plot A, North Field)',
                'required': True
            }),
            'planting_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'required': True
            }),
            'condition': forms.Select(attrs={
                'class': 'form-control',
                'required': True
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Add notes or observations (optional)'
            }),
        }


class IrrigationTaskForm(forms.ModelForm):
    class Meta:
        model = IrrigationTask
        fields = ['crop_or_plot', 'crop', 'scheduled_date', 'water_amount', 'status', 'notes']
        widgets = {
            'crop_or_plot': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Crop / plot name (e.g. Field 1 or Maize)',
                'required': True
            }),
            'crop': forms.Select(attrs={
                'class': 'form-control',
            }),
            'scheduled_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'required': True
            }),
            'water_amount': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. 500 Litres or 25mm',
                'required': True
            }),
            'status': forms.Select(attrs={
                'class': 'form-control',
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Irrigation notes (optional)'
            }),
        }


class FarmConditionForm(forms.ModelForm):
    class Meta:
        model = FarmCondition
        fields = ['location', 'condition_text', 'temperature', 'soil_moisture', 'rainfall_forecast', 'rainfall_chance', 'humidity', 'wind_speed']
        widgets = {
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'condition_text': forms.TextInput(attrs={'class': 'form-control'}),
            'temperature': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'soil_moisture': forms.NumberInput(attrs={'class': 'form-control'}),
            'rainfall_forecast': forms.TextInput(attrs={'class': 'form-control'}),
            'rainfall_chance': forms.NumberInput(attrs={'class': 'form-control'}),
            'humidity': forms.NumberInput(attrs={'class': 'form-control'}),
            'wind_speed': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
        }


class UserRegisterForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Create a secure password',
            'required': True,
        }),
        help_text="At least 8 characters recommended."
    )
    password_confirm = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm your password',
            'required': True,
        }),
        label="Confirm Password"
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Choose a username (e.g. farmer_john)',
                'required': True,
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'your.email@example.com',
                'required': True,
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'First name (optional)',
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Last name (optional)',
            }),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email__iexact=email).exists():
            raise ValidationError("An account with this email address already exists.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')

        if password and password_confirm:
            if password != password_confirm:
                self.add_error('password_confirm', "Passwords do not match.")
            else:
                try:
                    validate_password(password)
                except ValidationError as e:
                    self.add_error('password', e)
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user


class UserLoginForm(forms.Form):
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Username or email',
            'autofocus': True,
            'required': True,
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your password',
            'required': True,
        })
    )

