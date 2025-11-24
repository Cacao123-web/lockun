# tracker/services.py
from django.db.models import Sum, Count
from datetime import timedelta, date
from goals.models import Goal
from .models import Workout, Meal
from django.utils import timezone
import json 
from accounts.models import Profile
def workouts_summary(user):
    """
    Tổng hợp dữ liệu tập luyện:
    - Nếu có Goal đang 'in_progress' → chỉ tính trong khoảng start_date → deadline
    - Nếu không có Goal → tính toàn bộ
    Đồng thời trả thêm thông tin về kcal cần đốt cho mục tiêu.
    """
    qs = Workout.objects.filter(user=user)
    active_goal = Goal.get_active_goal(user)
    goal_range_text = None

    if active_goal and active_goal.start_date and active_goal.deadline:
        qs = qs.filter(date__range=[active_goal.start_date, active_goal.deadline])
        goal_range_text = (
            f"Tính trong mục tiêu từ {active_goal.start_date.strftime('%d/%m/%Y')} "
            f"đến {active_goal.deadline.strftime('%d/%m/%Y')}"
        )

    agg = qs.aggregate(
        total_minutes=Sum("duration_min"),
        total_kcal=Sum("calories_out"),
        total_steps=Sum("steps"),
        total_distance=Sum("distance_km"),
    )

    total_kcal = agg["total_kcal"] or 0

    # Thông tin kcal cần đốt theo mục tiêu (nếu có)
    goal_total_required = 0
    goal_daily_required = 0
    goal_kcal_progress_pct = 0

    if active_goal:
        goal_total_required = active_goal.total_required_deficit_kcal or 0
        goal_daily_required = active_goal.required_deficit_per_day or 0
        if goal_total_required > 0:
            goal_kcal_progress_pct = min(
                100, round(total_kcal / goal_total_required * 100, 1)
            )

    return {
        "total_minutes": agg["total_minutes"] or 0,
        "total_kcal": total_kcal,
        "total_steps": agg["total_steps"] or 0,
        "total_distance": agg["total_distance"] or 0,
        "active_goal": active_goal,
        "goal_range_text": goal_range_text,
        "goal_total_required": goal_total_required,
        "goal_daily_required": goal_daily_required,
        "goal_kcal_progress_pct": goal_kcal_progress_pct,
    }


def meals_summary(user):
    today = date.today()

    # ----- Hồ sơ / TDEE -----
    profile = getattr(user, "profile", None)
    tdee = float(profile.tdee) if (profile and profile.tdee) else 0.0

    # ----- Mục tiêu đang thực hiện -----
    active_goal = Goal.get_active_goal(user)
    goal_text = ""
    goal_daily_target = None
    goal_start = None
    goal_end = None

    if active_goal:
        goal_start = active_goal.start_date
        goal_end = active_goal.deadline or today
        goal_daily_target = active_goal.daily_calorie_target_in or tdee

        goal_text = (
            f"Tính trong mục tiêu từ {goal_start.strftime('%d/%m/%Y')} "
            f"đến {goal_end.strftime('%d/%m/%Y')}."
        )
    else:
        # không có goal => dùng TDEE để so sánh
        goal_start = today - timedelta(days=6)
        goal_end = today
        goal_daily_target = tdee
        if tdee:
            goal_text = "Đang so sánh ăn vào với TDEE ước tính từ hồ sơ."
        else:
            goal_text = "Chưa có mục tiêu cụ thể hoặc TDEE."

    # ----- Lọc Meal trong khoảng ngày -----
    qs = (
        Meal.objects.filter(user=user, date__range=(goal_start, goal_end))
        .order_by("date")
    )

    # Tổng calo
    total_kcal = qs.aggregate(total=Sum("calories_in"))["total"] or 0.0

    # Gom theo ngày
    per_day = {}
    for m in qs:
        per_day.setdefault(m.date, 0.0)
        per_day[m.date] += float(m.calories_in or 0)

    days_count = len(per_day)
    avg_kcal_per_day = total_kcal / days_count if days_count > 0 else 0.0

    # ----- Chuẩn bị dữ liệu cho Chart.js -----
    labels = []
    calories_series = []
    tdee_series = []

    d = goal_start
    while d <= goal_end:
        labels.append(d.strftime("%d/%m"))
        calories_series.append(per_day.get(d, 0.0))
        tdee_series.append(goal_daily_target or tdee or 0.0)
        d += timedelta(days=1)

    return {
        "active_goal": active_goal,
        "goal_text": goal_text,

        "total_kcal": total_kcal,
        "days_count": days_count,
        "avg_kcal_per_day": avg_kcal_per_day,
        "goal_daily_target": goal_daily_target,

        "chart_labels_json": json.dumps(labels, ensure_ascii=False),
        "chart_calories_json": json.dumps(calories_series),
        "chart_tdee_json": json.dumps(tdee_series),
    }

def nutrition_summary_for_user(user, today=None, days_back=7):
    """
    Tổng hợp dinh dưỡng cho user:
    - Tổng kcal hôm nay
    - So sánh với TDEE và mục tiêu (Goal)
    - Lịch sử 7 ngày để vẽ biểu đồ
    - Top món ăn trong 7 ngày gần nhất
    """
    if today is None:
        today = timezone.localdate()

    # ===== HÔM NAY =====
    today_qs = Meal.objects.filter(user=user, date=today)

    total_today = (
        today_qs.aggregate(total=Sum("calories_in"))["total"] or 0
    )

    # phân theo bữa
    by_meal_type = list(
        today_qs.values("meal_type")
        .annotate(total=Sum("calories_in"))
        .order_by()
    )

    # ===== TDEE TỪ PROFILE =====
    profile = getattr(user, "profile", None)
    tdee = float(getattr(profile, "tdee", 0) or 0)

    diff = total_today - tdee if tdee > 0 else 0
    diff_status = ""
    advice_text = ""

    if tdee > 0:
        if diff < -150:
            diff_status = "under"
            advice_text = (
                "Bạn đang ăn thấp hơn nhu cầu duy trì. "
                "Nếu mục tiêu tăng cân, hãy ăn thêm một chút."
            )
        elif diff > 150:
            diff_status = "over"
            advice_text = (
                "Bạn đang ăn nhiều hơn nhu cầu duy trì. "
                "Nếu mục tiêu giảm cân, nên giảm bớt khẩu phần."
            )
        else:
            diff_status = "balanced"
            advice_text = "Lượng calo hôm nay khá cân bằng so với TDEE."
    else:
        advice_text = (
            "Bạn chưa có TDEE trong hồ sơ, hãy cập nhật chiều cao/cân nặng "
            "để hệ thống gợi ý calo chính xác hơn."
        )

    # ===== MỤC TIÊU ĐANG HOẠT ĐỘNG =====
    active_goal = Goal.get_active_goal(user)
    daily_goal_in = 0
    goal_text = ""

    if active_goal and active_goal.daily_calorie_target_in:
        daily_goal_in = float(active_goal.daily_calorie_target_in or 0)
        goal_text = (
            f"Mục tiêu hiện tại: {active_goal.get_type_display()} tới "
            f"{active_goal.target_value} kg. "
            f"Gợi ý calo nạp mỗi ngày ~ {daily_goal_in:.0f} kcal."
        )

    # ===== LỊCH SỬ NHIỀU NGÀY (VẼ BIỂU ĐỒ) =====
    start_date = today - timedelta(days=days_back - 1)
    history_qs = (
        Meal.objects.filter(user=user, date__range=(start_date, today))
        .values("date")
        .annotate(total=Sum("calories_in"))
        .order_by("date")
    )

    chart_labels = []
    chart_calories = []
    chart_tdee = []

    for row in history_qs:
        d = row["date"]
        chart_labels.append(d.strftime("%d/%m"))
        chart_calories.append(float(row["total"] or 0))
        chart_tdee.append(tdee)

    # ===== TOP MÓN ĂN 7 NGÀY =====
    top_foods_qs = (
        Meal.objects.filter(user=user, date__range=(start_date, today))
        .values("food__name")
        .annotate(
            times=Count("id"),
            total_gram=Sum("quantity_gram"),
            total_kcal=Sum("calories_in"),
        )
        .order_by("-total_kcal")[:5]
    )

    top_foods = [
        {
            "name": row["food__name"],
            "times": row["times"],
            "total_gram": float(row["total_gram"] or 0),
            "total_kcal": float(row["total_kcal"] or 0),
        }
        for row in top_foods_qs
    ]

    return {
        "today": today,
        "total_today": float(total_today),
        "by_meal_type": by_meal_type,
        "tdee": tdee,
        "diff": diff,
        "diff_status": diff_status,
        "advice_text": advice_text,
        "active_goal": active_goal,
        "daily_goal_in": daily_goal_in,
        "goal_text": goal_text,
        "chart_labels": chart_labels,
        "chart_calories": chart_calories,
        "chart_tdee": chart_tdee,
        "top_foods": top_foods,
    }