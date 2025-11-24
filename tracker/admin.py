from django.contrib import admin
from .models import Workout, Meal, Food   # thêm Food

# ============================
#  FOOD
# ============================
@admin.register(Food)
class FoodAdmin(admin.ModelAdmin):
    list_display = ("name", "calories_per_100g")
    search_fields = ("name",)


# ============================
#  WORKOUT
# ============================
@admin.register(Workout)
class WorkoutAdmin(admin.ModelAdmin):
    list_display = ("user", "type", "date", "duration_min", "distance_km", "steps", "calories_out")
    search_fields = ("user__username",)
    list_filter = ("type", "date")


# ============================
#  MEAL
# ============================
@admin.register(Meal)
class MealAdmin(admin.ModelAdmin):
    list_display = ("user", "meal_type", "date", "food", "quantity_gram", "calories_in")
    search_fields = ("user__username", "food__name")
    list_filter = ("meal_type", "date")
