# chatbot/views.py
import json
import re
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods


# =========================
# HÀM TÍNH TOÁN CƠ BẢN
# =========================
def calc_bmi(weight, height_cm):
    h = height_cm / 100
    bmi = weight / (h * h)
    return round(bmi, 2)


def bmi_category_asia(bmi):
    if bmi < 18.5:
        return "Gầy"
    elif bmi < 23:
        return "Bình thường"
    elif bmi < 25:
        return "Thừa cân"
    else:
        return "Béo phì"


def calc_bmr(weight, height, age, gender):
    # Mifflin-St Jeor
    if gender == "male":
        return round(10 * weight + 6.25 * height - 5 * age + 5)
    else:
        return round(10 * weight + 6.25 * height - 5 * age - 161)


def calc_tdee(bmr, activity):
    factors = {
        "ít": 1.2,
        "nhẹ": 1.375,
        "vừa": 1.55,
        "nhiều": 1.725,
    }
    return round(bmr * factors.get(activity, 1.2))


# =========================
# TRẢ LỜI THEO RULE
# =========================
def reply_rule_based(message: str) -> str:
    msg = message.lower()

    # ---- BMI ----
    m = re.search(r"bmi\s*(\d+)\s*kg\s*(\d+)\s*cm", msg)
    if m:
        w = float(m.group(1))
        h = float(m.group(2))
        bmi = calc_bmi(w, h)
        cate = bmi_category_asia(bmi)
        return f"BMI của bạn là {bmi} ({cate} theo chuẩn châu Á)."

    # ---- BMR ----
    if "bmr" in msg:
        return (
            "BMR là năng lượng cơ thể cần để duy trì sự sống khi nghỉ ngơi.\n"
            "Công thức: Mifflin-St Jeor.\n"
            "Ví dụ: BMR = 10×cân nặng + 6.25×chiều cao − 5×tuổi ± giới tính."
        )

    # ---- TDEE ----
    if "tdee" in msg:
        return (
            "TDEE là tổng năng lượng bạn tiêu thụ mỗi ngày.\n"
            "TDEE = BMR × mức độ vận động.\n"
            "Dùng để giảm cân, tăng cân hoặc duy trì cân nặng."
        )

    # ---- GIẢM CÂN ----
    if "giảm cân" in msg:
        return (
            "Để giảm cân an toàn:\n"
            "- Thâm hụt 300–500 kcal/ngày\n"
            "- Ăn đủ protein\n"
            "- Tập luyện đều đặn\n"
            "- Ngủ đủ giấc"
        )

    # ---- TĂNG CÂN ----
    if "tăng cân" in msg:
        return (
            "Để tăng cân:\n"
            "- Dư năng lượng 300–500 kcal/ngày\n"
            "- Ăn đủ đạm và tinh bột\n"
            "- Tập kháng lực\n"
            "- Nghỉ ngơi hợp lý"
        )

    # ---- HELP ----
    if msg in ["help", "trợ giúp", "hướng dẫn"]:
        return (
            "Mình có thể hỗ trợ:\n"
            "- BMI (ví dụ: BMI 65kg 170cm)\n"
            "- BMR, TDEE\n"
            "- Giảm cân, tăng cân\n"
            "- Cách dùng website Libra Health"
        )

    # ---- MẶC ĐỊNH ----
    return (
        "Mình chỉ hỗ trợ các vấn đề về sức khỏe như BMI, BMR, TDEE, "
        "dinh dưỡng, tập luyện và cách dùng Libra Health."
    )


# =========================
# API CHAT
# =========================
@csrf_exempt
@require_http_methods(["GET", "POST"])
def health_chat(request):
    # GET để test API sống
    if request.method == "GET":
        return JsonResponse({"ok": True, "message": "Chat API is running (FREE mode)."})

    # POST
    try:
        data = json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    user_message = (data.get("message") or "").strip()
    if not user_message:
        return JsonResponse({"error": "empty message"}, status=400)

    reply = reply_rule_based(user_message)
    return JsonResponse({"reply": reply})
