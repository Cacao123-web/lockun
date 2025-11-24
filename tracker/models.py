from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


# ============================
#   WORKOUT (GIỮ NGUYÊN)
# ============================
class Workout(models.Model):
    TYPE_CHOICES = [
        ("run", "Chạy bộ"),
        ("walk", "Đi bộ"),
        ("bike", "Đạp xe"),
        ("gym", "Gym"),
        ("yoga", "Yoga"),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField(default=timezone.now)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    duration_min = models.PositiveIntegerField(default=30)
    distance_km = models.FloatField(default=0.0)
    steps = models.IntegerField(default=0)
    calories_out = models.FloatField(default=0.0)
    note = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"{self.get_type_display()} - {self.date} - {self.duration_min} phút"

    def _get_weight(self) -> float:
        try:
            prof = self.user.profile
            w = float(prof.weight_kg or 0)
            if w > 0:
                return w
        except Exception:
            pass
        return 70.0

    def _base_kcal_by_met(self) -> float:
        met = {"run": 9.8, "walk": 3.5, "bike": 7.5, "gym": 6.0, "yoga": 3.0}.get(self.type, 4.0)
        weight = self._get_weight()
        minutes = float(self.duration_min or 0)
        return met * 3.5 * weight / 200.0 * minutes

    def _bonus_distance_steps(self, base: float) -> float:
        bonus = 0.0
        weight = self._get_weight()
        if self.type in ("run", "walk") and self.distance_km > 0:
            bonus += weight * float(self.distance_km)
        if self.steps and self.steps > 0:
            bonus += 0.05 * float(self.steps)
        return min(bonus, base * 0.3) if base > 0 else bonus

    def save(self, *args, **kwargs):
        base = self._base_kcal_by_met()
        bonus = self._bonus_distance_steps(base)
        self.calories_out = round(base + bonus, 1)
        super().save(*args, **kwargs)


# ============================
#   FOOD MODEL (MỚI)
# ============================
class Food(models.Model):
    name = models.CharField(max_length=200, unique=True)
    calories_per_100g = models.FloatField(help_text="kcal trên 100g")

    def __str__(self):
        return f"{self.name} ({self.calories_per_100g} kcal/100g)"


# ============================
#   MEAL (TỰ TÍNH CALO)
# ============================
class Meal(models.Model):
    MEAL_CHOICES = [
        ("breakfast", "Sáng"),
        ("lunch", "Trưa"),
        ("dinner", "Tối"),
        ("snack", "Ăn nhẹ"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField(default=timezone.now)
    meal_type = models.CharField(max_length=20, choices=MEAL_CHOICES)

    food = models.ForeignKey(Food, on_delete=models.CASCADE)
    portion = models.CharField(max_length=100, blank=True)

    # người dùng chỉ nhập gram
    quantity_gram = models.FloatField(default=100.0)

    # kcal auto tính – không cho nhập form
    calories_in = models.FloatField(default=0.0, editable=False)

    def __str__(self):
        return f"{self.get_meal_type_display()} - {self.food} - {self.calories_in} kcal"

    def save(self, *args, **kwargs):
        if self.food and self.quantity_gram:
            self.calories_in = round(
                self.food.calories_per_100g * (self.quantity_gram / 100.0), 1
            )
        else:
            self.calories_in = 0.0

        super().save(*args, **kwargs)
