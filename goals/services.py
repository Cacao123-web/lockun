# goals/services.py
from dataclasses import dataclass
from datetime import date
from django.db.models import Sum
from django.utils import timezone
from tracker.models import Workout,Meal
from accounts.models import Profile
from .models import Goal
from datetime import timedelta

def _get_current_weight(user):
    """Lấy cân nặng hiện tại từ Profile (nếu có)."""
    try:
        profile = Profile.objects.get(user=user)
        return float(profile.weight_kg or 0)
    except Profile.DoesNotExist:
        return None
    except Exception:
        return None


def compute_goal_progress(goal: Goal):
    """
    Tính tiến độ mục tiêu dựa trên kcal đốt được trong Workout.

    - Lấy tất cả Workout của user trong khoảng [start_date, deadline]
    - Tổng calories_out / tổng kcal cần đốt (goal.total_required_deficit_kcal)
      => phần trăm tiến độ.
    - Sinh ra text mô tả cho thẻ mục tiêu trong overview.
    """

    today = date.today()

    # ===== 1. Kcal cần cho toàn bộ mục tiêu =====
    total_required_kcal = goal.total_required_deficit_kcal or 0  # vd: 15400 kcal
    total_kcal = 0
    kcal_pct = 0.0

    if (
        total_required_kcal > 0
        and goal.start_date is not None
        and goal.deadline is not None
    ):
        qs = Workout.objects.filter(
            user=goal.user,
            date__gte=goal.start_date,
            date__lte=goal.deadline,
        )
        total_kcal = qs.aggregate(total=Sum("calories_out"))["total"] or 0
        kcal_pct = min(total_kcal / total_required_kcal * 100.0, 100.0)

    # ===== 2. Text mô tả =====
    parts = []

    if total_required_kcal > 0:
        parts.append(
            f"Đã đốt khoảng {int(total_kcal)} / {int(total_required_kcal)} kcal mục tiêu."
        )

    if goal.deadline:
        days_left = (goal.deadline - today).days
        if days_left > 0:
            parts.append(f"Còn {days_left} ngày đến hạn.")
        elif days_left == 0:
            parts.append("Hôm nay là hạn cuối của mục tiêu.")
        else:
            parts.append(f"Đã trễ hạn {abs(days_left)} ngày.")

    text = " ".join(parts) if parts else "Chưa đủ dữ liệu để tính tiến độ."

    # ===== 3. Xác định trạng thái =====
    progress_pct = kcal_pct
    status = "in_progress"

    if progress_pct >= 100:
        status = "completed"
    elif goal.deadline and today > goal.deadline and progress_pct < 80:
        status = "failed"

    return {
        "progress_pct": progress_pct,
        "status": status,
        "text": text,
    }


def goals_kpis(user):
    """
    Trả về các KPI tổng quan trong thời gian của mục tiêu đang hoạt động:
    - calories_in: tổng kcal đã nạp từ Meal
    - calories_out: tổng kcal đã đốt từ Workout
    - sessions: số buổi tập (số record Workout)
    - streak_days: chuỗi ngày có log (Meal hoặc Workout) liên tục gần nhất
    """

    today = timezone.localdate()
    active_goal = Goal.get_active_goal(user)

    # Nếu chưa có mục tiêu thì trả về 0 hết
    if not active_goal:
        return {
            "calories_in": 0.0,
            "calories_out": 0.0,
            "sessions": 0,
            "streak_days": 0,
        }

    start = active_goal.start_date or today
    # Không cho vượt quá deadline; nếu chưa tới deadline thì lấy hôm nay
    end = min(today, active_goal.deadline) if active_goal.deadline else today

    # Lọc meal và workout trong khoảng thời gian mục tiêu
    meals_qs = Meal.objects.filter(user=user, date__range=(start, end))
    workouts_qs = Workout.objects.filter(user=user, date__range=(start, end))

    calories_in = meals_qs.aggregate(total=Sum("calories_in"))["total"] or 0.0
    calories_out = workouts_qs.aggregate(total=Sum("calories_out"))["total"] or 0.0
    sessions = workouts_qs.count()

    # Tính chuỗi ngày có log liên tục (Meal hoặc Workout)
    logged_dates = set(
        list(meals_qs.values_list("date", flat=True))
        + list(workouts_qs.values_list("date", flat=True))
    )

    streak = 0
    d = end
    while d >= start and d in logged_dates:
        streak += 1
        d -= timedelta(days=1)

    return {
        "calories_in": float(calories_in),
        "calories_out": float(calories_out),
        "sessions": sessions,
        "streak_days": streak,
    }
