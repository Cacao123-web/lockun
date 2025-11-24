from django import forms
from django.utils import timezone
from .models import Workout, Meal


class WorkoutForm(forms.ModelForm):
    class Meta:
        model = Workout
        fields = ("date", "type", "duration_min", "distance_km", "steps", "note")
        labels = {
            "date": "Ngày",
            "type": "Loại hình",
            "duration_min": "Thời gian (phút)",
            "distance_km": "Quãng đường (km)",
            "steps": "Bước chân",
            "note": "Ghi chú",
        }
        widgets = {
            "date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "type": forms.Select(attrs={"class": "form-select"}),
            "duration_min": forms.NumberInput(attrs={"class": "form-control", "min": 1}),
            "distance_km": forms.NumberInput(attrs={"class": "form-control", "step": 0.01}),
            "steps": forms.NumberInput(attrs={"class": "form-control", "min": 0}),
            "note": forms.TextInput(attrs={"class": "form-control"}),
        }


class MealForm(forms.ModelForm):
    date = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}),
        initial=timezone.now
    )

    quantity_gram = forms.FloatField(
        min_value=1,
        label="Khối lượng (gram)",
        widget=forms.NumberInput(attrs={"class": "form-control"})
    )

    class Meta:
        model = Meal
        fields = ("date", "meal_type", "food", "portion", "quantity_gram")
        labels = {
            "date": "Ngày",
            "meal_type": "Bữa",
            "food": "Món ăn",
            "portion": "Khẩu phần",
            "quantity_gram": "Khối lượng (gram)",
        }
        widgets = {
            "meal_type": forms.Select(attrs={"class": "form-select"}),
            "food": forms.Select(attrs={"class": "form-select"}),
            "portion": forms.TextInput(attrs={"class": "form-control"}),
        }
