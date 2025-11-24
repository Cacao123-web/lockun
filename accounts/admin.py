# accounts/admin.py
from django.contrib import admin
from .models import Profile

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "full_name", "gender", "age", "height_cm", "weight_kg", "bmi", "bmr", "tdee", "activity_level")
    list_filter = ("gender", "activity_level")
    search_fields = ("user__username", "full_name")
