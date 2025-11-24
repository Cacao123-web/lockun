# goals/views.py
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from .forms import GoalForm
from .models import Goal
from .services import goals_kpis, compute_goal_progress  # nếu không dùng có thể xoá
from tracker.models import Workout, Meal


# ====== HÀM PHỤ: TÍNH TIẾN ĐỘ CHO 1 MỤC TIÊU ======
def _calc_goal_progress(goal: Goal, user, today):
    """
    Trả về: (progress_pct, burned_kcal, total_required_kcal, days_left)
    """
    g_start = goal.start_date
    g_deadline = goal.deadline or today

    if not g_start or g_start > g_deadline:
        return 0.0, 0.0, goal.total_required_deficit_kcal, 0

    # chỉ tính tới hôm nay hoặc tới deadline (lấy mốc nhỏ hơn)
    calc_end = min(today, g_deadline)

    total_kcal = goal.total_required_deficit_kcal or 0.0

    burned = (
        Workout.objects.filter(
            user=user,
            date__range=(g_start, calc_end),
        ).aggregate(s=Sum("calories_out"))["s"]
        or 0.0
    )

    if total_kcal > 0:
        progress_pct = min(burned / total_kcal * 100.0, 100.0)
    else:
        progress_pct = 0.0

    days_left = max((g_deadline - today).days, 0)

    return progress_pct, burned, total_kcal, days_left


@login_required
def goals_overview(request):
    user = request.user
    today = timezone.localdate()

    # ==== 0. TỰ ĐỘNG CẬP NHẬT TRẠNG THÁI CHO CÁC MỤC TIÊU ĐÃ TỚI HẠN ====
    in_progress_goals = Goal.objects.filter(user=user, status="in_progress")
    for g in in_progress_goals:
        progress_pct, burned, total_kcal, _ = _calc_goal_progress(g, user, today)

        # Nếu có deadline và đã quá hạn
        if g.deadline and today > g.deadline:
            # Nếu đã đạt >= 99% kcal yêu cầu => xem như hoàn thành
            if total_kcal > 0 and burned >= total_kcal * 0.99:
                g.mark_completed()
            else:
                # chưa đủ tiến độ mà đã quá hạn => thất bại
                g.mark_failed()

    # ==== 1. Lấy active goal (mục tiêu đang thực hiện) sau khi đã auto-update ====
    active_goal = Goal.get_active_goal(user)

    # ==== 2. Xác định khoảng ngày để tính KPI ====
    if active_goal and active_goal.start_date:
        kpi_start = active_goal.start_date
        kpi_end = min(active_goal.deadline or today, today)
    else:
        # nếu chưa có mục tiêu -> thống kê 7 ngày gần nhất
        kpi_end = today
        kpi_start = kpi_end - timedelta(days=6)

    # đảm bảo start <= end
    if kpi_start > kpi_end:
        kpi_start, kpi_end = kpi_end, kpi_start

    meals_qs = Meal.objects.filter(
        user=user,
        date__range=(kpi_start, kpi_end),
    )
    workouts_qs = Workout.objects.filter(
        user=user,
        date__range=(kpi_start, kpi_end),
    )

    # ==== 3. Tính KPI tổng quan ====
    total_in = meals_qs.aggregate(s=Sum("calories_in"))["s"] or 0
    total_out = workouts_qs.aggregate(s=Sum("calories_out"))["s"] or 0
    sessions = workouts_qs.count()

    # Chuỗi ngày log liên tục (có meal hoặc workout)
    streak = 0
    d = kpi_end
    while d >= kpi_start:
        has_log = (
            meals_qs.filter(date=d).exists()
            or workouts_qs.filter(date=d).exists()
        )
        if not has_log:
            break
        streak += 1
        d -= timedelta(days=1)

    kpis = {
        "calories_in": total_in,
        "calories_out": total_out,
        "sessions": sessions,
        "streak_days": streak,
    }

    # ==== 4. Tính tiến độ mục tiêu theo kcal đã đốt (chỉ cho goal đang in_progress) ====
    if active_goal:
        progress_pct, burned, total_kcal, days_left = _calc_goal_progress(
            active_goal, user, today
        )
        active_goal.progress_pct = progress_pct

        if total_kcal > 0:
            active_goal.progress_text = (
                f"Đã đốt khoảng {int(burned)} / {int(total_kcal)} kcal mục tiêu. "
                f"Còn {days_left} ngày đến hạn."
            )
        else:
            active_goal.progress_text = ""
    # nếu không có active_goal thì cứ để None

    # ==== 5. Lấy danh sách tất cả mục tiêu (lịch sử) ====
    items = Goal.objects.filter(user=user).order_by("-created")

    return render(
        request,
        "goals/overview.html",
        {
            "kpis": kpis,
            "active_goal": active_goal,
            "items": items,
        },
    )


@login_required
def goals_list(request):
    """Trang list đơn giản (nếu bạn vẫn muốn giữ)."""
    qs = Goal.objects.filter(user=request.user).order_by("-created")
    return render(request, "goals/goals_list.html", {"items": qs})


@login_required
def goals_create(request):
    """
    Tạo mục tiêu mới.
    - Nếu đã có goal status='in_progress' thì cảnh báo (tránh trùng mục tiêu tổng).
    - Khi lưu, tự gán user.
    - start_date đã có default trong model (timezone.localdate) nên không cần set lại.
    - init_from_profile() để lấy cân nặng + TDEE nếu có.
    """

    active = Goal.get_active_goal(request.user)
    if active:
        messages.warning(
            request,
            "Bạn đang có một mục tiêu đang thực hiện. "
            "Hãy hoàn thành hoặc kết thúc mục tiêu đó trước khi tạo mục tiêu mới.",
        )
        return redirect("goals_overview")

    if request.method == "POST":
        form = GoalForm(request.POST)
        if form.is_valid():
            obj: Goal = form.save(commit=False)
            obj.user = request.user

            # status mặc định 'in_progress', start_date default = hôm nay (trong model)
            # Khởi tạo từ profile (lấy cân nặng hiện tại, TDEE,...)
            obj.init_from_profile()
            obj.save()

            messages.success(request, "Đã tạo mục tiêu sức khỏe mới.")
            return redirect("goals_overview")
    else:
        form = GoalForm()

    return render(request, "goals/goals_form.html", {"form": form})


@login_required
def goals_delete(request, pk):
    """
    Xóa mục tiêu (đang thực hiện hoặc trong lịch sử đều được).
    Nếu không muốn cho xóa mục tiêu đã hoàn thành thì có thể check thêm tại đây.
    """
    obj = get_object_or_404(Goal, pk=pk, user=request.user)
    if request.method == "POST":
        obj.delete()
        messages.info(request, "Đã xóa mục tiêu.")
        return redirect("goals_overview")
    return render(request, "confirm_delete.html", {"obj": obj})


@login_required
def goals_finish(request, pk, result):
    """
    Kết thúc một mục tiêu:
    - result = 'success'  -> đánh dấu hoàn thành
    - result = 'fail'     -> đánh dấu không hoàn thành
    """
    goal = get_object_or_404(Goal, pk=pk, user=request.user)

    if result == "success":
        goal.mark_completed()
        messages.success(request, "Chúc mừng! Bạn đã hoàn thành mục tiêu này.")
    elif result == "fail":
        goal.mark_failed()
        messages.info(request, "Mục tiêu đã được kết thúc và lưu lại trong lịch sử.")
    else:
        messages.warning(request, "Trạng thái không hợp lệ.")

    return redirect("goals_overview")


@login_required
def goals_history(request):
    """
    Lịch sử các mục tiêu đã kết thúc (completed / failed).
    """
    qs = (
        Goal.objects.filter(user=request.user)
        .exclude(status="in_progress")
        .order_by("-created")
    )
    return render(request, "goals/history.html", {"items": qs})
