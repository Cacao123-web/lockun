# accounts/models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
import random
# Hệ số hoạt động để tính TDEE
ACTIVITY_CHOICES = (
    ("sedentary", "Ít vận động (x1.2)"),
    ("light",     "Nhẹ (x1.375)"),
    ("moderate",  "Vừa (x1.55)"),
    ("active",    "Nhiều (x1.725)"),
    ("very",      "Rất nhiều (x1.9)"),
)
ACTIVITY_FACTOR = {
    "sedentary": 1.2,
    "light": 1.375,
    "moderate": 1.55,
    "active": 1.725,
    "very": 1.9,
}


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=120, blank=True)

    # Dữ liệu nhân trắc
    age = models.PositiveIntegerField(default=18)  # tuổi (năm)
    gender = models.CharField(
        max_length=10,
        choices=[("M", "Nam"), ("F", "Nữ")],
        default="M",
    )
    height_cm = models.FloatField(default=170)  # chiều cao (cm)
    weight_kg = models.FloatField(default=65)   # cân nặng (kg)

    # Mức độ vận động để tính TDEE
    activity_level = models.CharField(
        max_length=10, choices=ACTIVITY_CHOICES, default="light"
    )

    # Các chỉ số được lưu lại sau khi tính (để dễ query/report)
    bmr = models.FloatField(default=0)   # kcal/ngày
    bmi = models.FloatField(default=0)   # kg/m^2
    tdee = models.FloatField(default=0)  # kcal/ngày

    def __str__(self):
        return self.full_name or self.user.username

    # Phân loại BMI – tiện hiển thị
    @property
    def bmi_class(self):
        v = float(self.bmi or 0)
        if v <= 0:
            return ""
        if v < 18.5:
            return "Gầy"
        if v < 25:
            return "Bình thường"
        if v < 30:
            return "Thừa cân"
        return "Béo phì"

    def recalc(self):
        """
        Tính lại BMI, BMR (Mifflin–St Jeor) và TDEE dựa vào dữ liệu hiện có.
        Hàm này an toàn với dữ liệu trống/0 để tránh ZeroDivisionError.
        """
        # Chuẩn hóa dữ liệu đầu vào
        try:
            h_cm = float(self.height_cm or 0)
            w_kg = float(self.weight_kg or 0)
            age = int(self.age or 0)
        except Exception:
            h_cm, w_kg, age = 0.0, 0.0, 0

        # BMI
        if h_cm > 0 and w_kg > 0:
            h_m = h_cm / 100.0
            try:
                self.bmi = round(w_kg / (h_m * h_m), 2)
            except ZeroDivisionError:
                self.bmi = 0
        else:
            self.bmi = 0

        # BMR (Mifflin–St Jeor)
        if w_kg > 0 and h_cm > 0 and age > 0 and self.gender in ("M", "F"):
            base = 10 * w_kg + 6.25 * h_cm - 5 * age
            if self.gender == "M":
                self.bmr = round(base + 5, 0)
            else:
                self.bmr = round(base - 161, 0)
        else:
            self.bmr = 0

        # TDEE
        factor = ACTIVITY_FACTOR.get(self.activity_level, ACTIVITY_FACTOR["light"])
        self.tdee = round(self.bmr * factor, 0) if self.bmr > 0 else 0

    def save(self, *args, **kwargs):
        # Luôn tính lại trước khi lưu để dữ liệu nhất quán
        self.recalc()
        return super().save(*args, **kwargs)

class PasswordResetOTP(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reset_otps')
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    def __str__(self):
        return f"OTP reset for {self.user.username} - {self.code}"

    @classmethod
    def create_new(cls, user):
        # tạo mã 6 số
        code = f"{random.randint(0, 999999):06d}"
        return cls.objects.create(user=user, code=code)

    def is_expired(self, minutes=10):
        return self.created_at + timedelta(minutes=minutes) < timezone.now()