# goals/models.py
from datetime import datetime
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

from accounts.models import Profile


class Goal(models.Model):
    # 3 loại chính
    GOAL_TYPE_CHOICES = [
        ('lose_weight', 'Giảm cân'),
        ('gain_weight', 'Tăng cân'),
        ('maintain', 'Duy trì'),
    ]

    STATUS_CHOICES = [
        ('in_progress', 'Đang thực hiện'),
        ('completed', 'Hoàn thành'),
        ('failed', 'Không hoàn thành'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)

    # Loại mục tiêu: giảm / tăng / duy trì
    type = models.CharField(max_length=20, choices=GOAL_TYPE_CHOICES)

    # Cân nặng mục tiêu (kg)
    target_value = models.FloatField(
        help_text="Cân nặng mục tiêu (kg)"
    )

    # Cân nặng lúc bắt đầu (tự lấy từ Profile khi tạo)
    start_weight_kg = models.FloatField(
        help_text="Cân nặng khi bắt đầu mục tiêu (kg)",
        null=True,
        blank=True,
    )

    # Ngày bắt đầu & hạn (đều là DATE, không dùng datetime)
    # dùng timezone.localdate (hàm, không gọi) để luôn là date
    start_date = models.DateField(default=timezone.localdate)
    deadline = models.DateField(blank=True, null=True)

    # Trạng thái
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='in_progress',
    )

    # Gợi ý calo mỗi ngày (tự tính, có thể trống)
    daily_calorie_target_in = models.FloatField(
        null=True, blank=True,
        help_text="Calo nên nạp mỗi ngày để đạt mục tiêu"
    )
    daily_calorie_target_out = models.FloatField(
        null=True, blank=True,
        help_text="Calo nên đốt mỗi ngày để đạt mục tiêu"
    )

    # Ghi chú
    note = models.TextField(blank=True)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    last_reminder_sent = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ['-created']

    def __str__(self):
        return f"{self.user.username} – {self.get_type_display()} tới {self.target_value} kg"

    # ====== TIỆN ÍCH ======

    @property
    def total_days(self):
        """
        Số ngày của mục tiêu (bao gồm cả ngày bắt đầu & ngày kết thúc).
        Ép cả start_date & deadline về date để tránh lỗi date vs datetime.
        """
        if not self.start_date or not self.deadline:
            return 0

        start = self.start_date
        end = self.deadline

        if isinstance(start, datetime):
            start = start.date()
        if isinstance(end, datetime):
            end = end.date()

        return (end - start).days + 1

    @property
    def lost_kg(self):
        """Số kg cần thay đổi (giảm hoặc tăng)."""
        if self.start_weight_kg is None:
            return 0
        if self.type == 'lose_weight':
            return max(self.start_weight_kg - self.target_value, 0)
        elif self.type == 'gain_weight':
            return max(self.target_value - self.start_weight_kg, 0)
        else:
            return 0

    @property
    def total_required_deficit_kcal(self):
        """
        Số kcal thâm hụt (hoặc thặng dư) cần có cho toàn mục tiêu.
        Tạm quy ước 1kg ~ 7700 kcal.
        """
        return self.lost_kg * 7700

    @property
    def required_deficit_per_day(self):
        if self.total_days <= 0:
            return 0
        return self.total_required_deficit_kcal / self.total_days

    @classmethod
    def get_active_goal(cls, user):
        """Mục tiêu đang thực hiện (nếu có)."""
        return (
            cls.objects.filter(user=user, status='in_progress')
            .order_by('-created')
            .first()
        )

    def init_from_profile(self):
        """
        Gọi khi mới tạo mục tiêu: lấy cân nặng từ Profile,
        và tính gợi ý calo mỗi ngày.
        """
        try:
            profile = Profile.objects.get(user=self.user)
        except Profile.DoesNotExist:
            profile = None

        if profile and profile.weight_kg:
            self.start_weight_kg = profile.weight_kg

        # Dùng TDEE trong profile nếu có để gợi ý calo
        if profile and profile.tdee and self.required_deficit_per_day:
            # giảm cân => ăn ít hơn TDEE
            # tăng cân => ăn nhiều hơn TDEE
            if self.type == 'lose_weight':
                self.daily_calorie_target_in = profile.tdee - self.required_deficit_per_day
                self.daily_calorie_target_out = profile.tdee
            elif self.type == 'gain_weight':
                self.daily_calorie_target_in = profile.tdee + self.required_deficit_per_day
                self.daily_calorie_target_out = profile.tdee
            else:  # duy trì
                self.daily_calorie_target_in = profile.tdee
                self.daily_calorie_target_out = profile.tdee

    def mark_completed(self):
        self.status = 'completed'
        self.save(update_fields=['status'])

    def mark_failed(self):
        self.status = 'failed'
        self.save(update_fields=['status'])
