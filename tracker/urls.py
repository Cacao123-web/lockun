# tracker/urls.py
from django.urls import path
from . import views

app_name = "tracker"  # ⚡ Bắt buộc để tránh lỗi NoReverseMatch khi gọi {% url 'tracker:...' %}

urlpatterns = [
    # --- Workouts ---
    path("workouts/", views.workouts_list, name="workouts_list"),
    path("workouts/new/", views.workouts_create, name="workouts_create"),
    path("workouts/<int:pk>/edit/", views.workouts_edit, name="workouts_edit"),
    path("workouts/<int:pk>/delete/", views.workouts_delete, name="workouts_delete"),

    # --- Meals ---
    path("meals/", views.meals_list, name="meals_list"),
    path("meals/new/", views.meals_create, name="meals_create"),
    path("meals/<int:pk>/edit/", views.meals_edit, name="meals_edit"),
    path("meals/<int:pk>/delete/", views.meals_delete, name="meals_delete"),
]
