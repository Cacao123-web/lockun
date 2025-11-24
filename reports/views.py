# reports/views.py
from datetime import date, timedelta, datetime
import io, csv
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render
from django.utils import timezone
from django.db.models import Sum
from goals.models import Goal 
from tracker.models import Workout, Meal
from accounts.models import Profile

# ================== helpers ==================
def _parse_ymd(s: str, default: date):
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except Exception:
        return default

def _daterange(d0: date, d1: date):
    cur = d0
    while cur <= d1:
        yield cur
        cur += timedelta(days=1)

def _get_tdee(user) -> float:
    """Ưu tiên dùng TDEE từ Profile; fallback 2000."""
    try:
        prof = Profile.objects.get(user=user)
        if prof.tdee and prof.tdee > 0:
            return float(prof.tdee)
        # fallback nhẹ nếu tdee rỗng: bmr*1.375 hoặc 2000
        if getattr(prof, "bmr", 0) and prof.bmr > 0:
            return round(prof.bmr * 1.375, 0)
    except Profile.DoesNotExist:
        pass
    return 2000.0

# ================== views ==================
@login_required
def reports_dashboard(request):
    """
    Báo cáo tổng hợp:
    - Calories In / Out theo ngày
    - Chênh lệch năng lượng (net)
    - So sánh với mục tiêu (nếu có)
    - Biểu đồ IN – OUT – NET
    """
    user = request.user

    today = timezone.localdate()
    default_start = today - timedelta(days=13)

    start = _parse_ymd(request.GET.get("start", ""), default_start)
    end   = _parse_ymd(request.GET.get("end", ""), today)

    if start > end:
        start, end = end, start

    # ---- Lấy dữ liệu theo ngày ----
    meals = (
        Meal.objects.filter(user=user, date__range=(start, end))
        .values("date")
        .annotate(kcal_in=Sum("calories_in"))
    )
    workouts = (
        Workout.objects.filter(user=user, date__range=(start, end))
        .values("date")
        .annotate(kcal_out=Sum("calories_out"))
    )

    kcal_in_by_day  = {m["date"]: float(m["kcal_in"] or 0) for m in meals}
    kcal_out_by_day = {w["date"]: float(w["kcal_out"] or 0) for w in workouts}

    # ---- Profile & mục tiêu ----
    try:
        prof = Profile.objects.get(user=user)
        tdee = prof.tdee or 2000
    except:
        prof = None
        tdee = 2000

    # ---- Duyệt từng ngày ----
    labels, cal_in, cal_out, net_arr = [], [], [], []
    total_in, total_out = 0, 0

    for d in _daterange(start, end):
        labels.append(d.strftime("%d/%m"))

        ki = round(kcal_in_by_day.get(d, 0.0), 1)
        ko = round(kcal_out_by_day.get(d, 0.0), 1)
        net = ki - ko  # dương = dư calo, âm = thâm hụt

        cal_in.append(ki)
        cal_out.append(ko)
        net_arr.append(net)

        total_in  += ki
        total_out += ko

    # ---- KPI tổng hợp ----
    days_logged = len(labels)
    net_total = total_in - total_out
    net_avg = net_total / days_logged if days_logged > 0 else 0

    # ---- Mục tiêu (nếu có) ----
    try:
        active_goal = user.goal_set.get(status="in_progress")
        goal_text = active_goal.get_type_display()
        deficit_per_day = active_goal.required_kcal_deficit_per_day()  # nếu bạn có hàm này
    except:
        active_goal = None
        goal_text = None
        deficit_per_day = None

    return render(
        request,
        "reports/dashboard.html",
        {
            "start": start,
            "end": end,
            "labels": labels,
            "cal_in": cal_in,
            "cal_out": cal_out,
            "net_arr": net_arr,

            # KPI
            "total_in": total_in,
            "total_out": total_out,
            "net_total": net_total,
            "net_avg": net_avg,

            "profile": prof,
            "active_goal": active_goal,
            "goal_text": goal_text,
            "deficit_per_day": deficit_per_day,
        },
    )


@login_required
def export_csv(request):
    """
    Xuất CSV theo đúng khoảng ngày đang lọc (?start, ?end)
    Gồm 2 phần: Workouts và Meals, mỗi phần có header riêng.
    """
    user = request.user
    today = timezone.localdate()
    default_start = today - timedelta(days=13)
    start = _parse_ymd(request.GET.get("start", ""), default_start)
    end = _parse_ymd(request.GET.get("end", ""), today)
    if start > end:
        start, end = end, start

    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="report_{start}_{end}.csv"'
    writer = csv.writer(response)

    # Workouts
    writer.writerow([f"Workouts từ {start} đến {end}"])
    writer.writerow(["Date","Type","Duration(min)","Distance(km)","Steps","Calories OUT"])
    for w in Workout.objects.filter(user=user, date__range=(start, end)).order_by("date","id"):
        writer.writerow([w.date, w.type, w.duration_min, w.distance_km, w.steps, w.calories_out])

    writer.writerow([])

    # Meals
    writer.writerow([f"Meals từ {start} đến {end}"])
    writer.writerow(["Date","Meal","Food","Portion","Calories IN"])
    for m in Meal.objects.filter(user=user, date__range=(start, end)).order_by("date","id"):
        writer.writerow([m.date, m.meal_type, m.food, m.portion, m.calories_in])

    return response

# ============= PDF (tùy chọn, giống lọc ngày ở trên) =============
try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
except Exception:
    canvas = None
    A4 = None

@login_required
def export_pdf(request):
    """
    Xuất PDF theo đúng khoảng ngày đang lọc (?start, ?end).
    Nếu chưa cài reportlab: pip install reportlab
    """
    if canvas is None:
        return HttpResponse("reportlab chưa được cài. Chạy: pip install reportlab", status=501)

    user = request.user
    today = timezone.localdate()
    default_start = today - timedelta(days=13)
    start = _parse_ymd(request.GET.get("start", ""), default_start)
    end = _parse_ymd(request.GET.get("end", ""), today)
    if start > end:
        start, end = end, start

    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    w, h = A4

    p.setTitle("Health Report")
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, h - 40, f"Health Report - User: {user.username}")
    p.setFont("Helvetica", 10)
    p.drawString(50, h - 58, f"Khoảng ngày: {start}  đến  {end}")

    y = h - 80
    p.setFont("Helvetica-Bold", 11)
    p.drawString(50, y, "Workouts")
    y -= 18
    p.setFont("Helvetica", 10)

    for wkt in Workout.objects.filter(user=user, date__range=(start, end)).order_by("date", "id"):
        line = f"{wkt.date}  -  {wkt.get_type_display()}  -  {wkt.duration_min} phút  -  {wkt.calories_out} kcal"
        p.drawString(60, y, line)
        y -= 14
        if y < 60:
            p.showPage()
            y = h - 40

    y -= 10
    if y < 60:
        p.showPage()
        y = h - 40

    p.setFont("Helvetica-Bold", 11)
    p.drawString(50, y, "Meals")
    y -= 18
    p.setFont("Helvetica", 10)

    for m in Meal.objects.filter(user=user, date__range=(start, end)).order_by("date", "id"):
        line = f"{m.date}  -  {m.get_meal_type_display()}  -  {m.food}  -  {m.calories_in} kcal"
        p.drawString(60, y, line)
        y -= 14
        if y < 60:
            p.showPage()
            y = h - 40

    p.showPage()
    p.save()

    pdf = buffer.getvalue()
    buffer.close()

    resp = HttpResponse(content_type="application/pdf")
    resp["Content-Disposition"] = f'attachment; filename="report_{start}_{end}.pdf"'
    resp.write(pdf)
    return resp

@login_required
def health_overview(request):
    """
    Trang QUẢN LÝ SỨC KHỎE CÁ NHÂN:
    - Hiển thị hồ sơ sức khỏe (BMI, BMR, TDEE...)
    - Tình hình ăn uống & tập luyện HÔM NAY
    - Mục tiêu cân nặng đang theo đuổi
    """
    user = request.user
    today = timezone.localdate()

    # Hồ sơ sức khỏe
    profile = Profile.objects.filter(user=user).first()

    # Tổng calo IN/OUT hôm nay
    meals_today = (
        Meal.objects.filter(user=user, date=today)
        .aggregate(total_in=Sum("calories_in"))
    )
    workouts_today = (
        Workout.objects.filter(user=user, date=today)
        .aggregate(total_out=Sum("calories_out"))
    )

    cal_in_today = float(meals_today.get("total_in") or 0)
    cal_out_today = float(workouts_today.get("total_out") or 0)

    # TDEE (dùng lại helper ở trên nếu muốn, ở đây mình viết đơn giản)
    tdee = 2000.0
    if profile and profile.tdee:
        tdee = float(profile.tdee)

    # Net calories = ăn vào - TDEE + đốt
    # Nếu net < 0 => đang thâm hụt (giảm cân)
    net_cal_today = cal_in_today - tdee + cal_out_today

    # Mục tiêu đang thực hiện (nếu có)
    active_goal = None
    if hasattr(Goal, "get_active_goal"):
        active_goal = Goal.get_active_goal(user)

    # Tính BMI text đơn giản
    bmi_text = ""
    if profile and profile.bmi:
        bmi = float(profile.bmi)
        if bmi < 18.5:
            bmi_text = "Gầy"
        elif bmi < 23:
            bmi_text = "Bình thường"
        elif bmi < 25:
            bmi_text = "Thừa cân"
        else:
            bmi_text = "Béo phì"

    context = {
        "today": today,
        "profile": profile,
        "tdee": tdee,
        "cal_in_today": cal_in_today,
        "cal_out_today": cal_out_today,
        "net_cal_today": net_cal_today,
        "active_goal": active_goal,
        "bmi_text": bmi_text,
    }
    return render(request, "health/overview.html", context)