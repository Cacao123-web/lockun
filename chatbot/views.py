# chatbot/views.py
import json
import re
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

# ==============================
# Helpers
# ==============================

def _norm(s: str) -> str:
    return (s or "").strip().lower()

def _extract_numbers(text: str):
    # lấy tất cả số (int/float) trong câu
    nums = re.findall(r"(\d+(?:[.,]\d+)?)", text)
    out = []
    for n in nums:
        out.append(float(n.replace(",", ".")))
    return out

def _extract_weight_height(text: str):
    """
    Bắt các kiểu:
    - "67kg 172cm"
    - "67 172"
    - "nặng 67 cao 172"
    - "67kg, 1m72"
    """
    t = _norm(text)

    # 1m72 / 1.72m
    m = re.search(r"(\d+(?:[.,]\d+)?)\s*m\s*(\d{1,2})", t)
    if m:
        a = float(m.group(1).replace(",", "."))
        b = float(m.group(2))
        height_cm = a * 100 + b
        # cân nặng vẫn phải lấy chỗ khác
        w = re.search(r"(\d+(?:[.,]\d+)?)\s*kg", t)
        if w:
            weight = float(w.group(1).replace(",", "."))
            return weight, height_cm

    # dạng kg/cm
    w = re.search(r"(\d+(?:[.,]\d+)?)\s*kg", t)
    h = re.search(r"(\d+(?:[.,]\d+)?)\s*cm", t)
    if w and h:
        weight = float(w.group(1).replace(",", "."))
        height = float(h.group(1).replace(",", "."))
        return weight, height

    # nếu chỉ có 2 số -> hiểu là (kg, cm) theo thứ tự
    nums = _extract_numbers(t)
    if len(nums) >= 2:
        weight, height = nums[0], nums[1]
        # nếu chiều cao nhập dạng mét (<=3) thì đổi sang cm
        if height <= 3:
            height = height * 100
        return weight, height

    return None, None

def _bmi(weight_kg: float, height_cm: float) -> float:
    h_m = height_cm / 100.0
    return weight_kg / (h_m * h_m)

def _bmi_asian_category(bmi: float) -> str:
    # chuẩn châu Á (tham khảo phổ biến)
    if bmi < 18.5:
        return "Gầy"
    if bmi < 23:
        return "Bình thường"
    if bmi < 25:
        return "Thừa cân (tiền béo phì)"
    if bmi < 30:
        return "Béo phì độ I"
    return "Béo phì độ II"

def _bmr_mifflin(weight_kg: float, height_cm: float, age: int, sex: str) -> float:
    # Mifflin-St Jeor: Nam = 10w + 6.25h - 5a + 5 ; Nữ = ... -161
    base = 10 * weight_kg + 6.25 * height_cm - 5 * age
    if sex == "female":
        return base - 161
    return base + 5

def _tdee_multiplier(activity: str) -> float:
    # mức vận động phổ biến
    mapping = {
        "ít": 1.2, "it": 1.2, "sedentary": 1.2,
        "nhẹ": 1.375, "nhe": 1.375, "light": 1.375,
        "vừa": 1.55, "vua": 1.55, "moderate": 1.55,
        "nặng": 1.725, "nang": 1.725, "active": 1.725,
        "rất nặng": 1.9, "rat nang": 1.9, "very active": 1.9,
    }
    a = _norm(activity)
    for k, v in mapping.items():
        if k in a:
            return v
    # mặc định
    return 1.55

def _reply_rule_based(user_text: str) -> str:
    t = _norm(user_text)

    # 0) chào hỏi / xã giao
    if re.fullmatch(r"(hi|hello|hey|xin chào|chào|chao|alo|lô|lo)\b.*", t):
        return (
            "Chào bạn 👋 Mình là Trợ lý sức khỏe của Libra Health.\n"
            "Bạn có thể hỏi về **BMI, BMR, TDEE**, dinh dưỡng, tập luyện hoặc cách dùng web.\n"
            "Ví dụ:\n"
            "- `BMI 67kg 172cm`\n"
            "- `BMR là gì?`\n"
            "- `TDEE 67kg 172cm 21 tuổi nam vận động vừa`"
        )

    if "cảm ơn" in t or "cam on" in t or "thanks" in t:
        return "Không có gì 😊 Nếu cần tính BMI/BMR/TDEE hoặc gợi ý ăn uống/tập luyện, bạn cứ nhắn nhé!"

    # 1) hỏi định nghĩa
    if "bmi là gì" in t or re.search(r"\bbmi\b.*là gì", t):
        return (
            "✅ **BMI (Body Mass Index)** là chỉ số khối cơ thể, dùng để ước lượng mức gầy/bình thường/thừa cân.\n"
            "Công thức: **BMI = cân nặng(kg) / (chiều cao(m)²)**.\n"
            "Bạn có thể gửi: `BMI 67kg 172cm` để mình tính."
        )

    if "bmr là gì" in t or re.search(r"\bbmr\b.*là gì", t):
        return (
            "✅ **BMR (Basal Metabolic Rate)** là lượng calo cơ thể tiêu thụ khi nghỉ ngơi hoàn toàn (duy trì sống).\n"
            "BMR phụ thuộc vào **giới tính, tuổi, chiều cao, cân nặng**.\n"
            "Ví dụ bạn gửi: `BMR 67kg 172cm 21 tuổi nam`."
        )

    if "tdee là gì" in t or re.search(r"\btdee\b.*là gì", t):
        return (
            "✅ **TDEE (Total Daily Energy Expenditure)** là tổng calo bạn tiêu thụ mỗi ngày (BMR × mức vận động).\n"
            "Dùng để đặt mục tiêu **giảm cân / tăng cân / duy trì**.\n"
            "Ví dụ: `TDEE 67kg 172cm 21 tuổi nam vận động vừa`."
        )

    # 2) tính BMI
    if "bmi" in t:
        w, h = _extract_weight_height(t)
        if w and h:
            bmi = _bmi(w, h)
            cat = _bmi_asian_category(bmi)
            return f"✅ BMI của bạn là **{bmi:.2f}** (**{cat}** theo chuẩn châu Á)."
        return "Bạn gửi giúp mình **cân nặng + chiều cao** nha. Ví dụ: `BMI 67kg 172cm`."

    # 3) tính BMR
    if "bmr" in t:
        # bắt weight/height + age + sex
        w, h = _extract_weight_height(t)
        age = None
        m_age = re.search(r"(\d{1,2})\s*(tuổi|tuoi)", t)
        if m_age:
            age = int(m_age.group(1))

        sex = None
        if "nữ" in t or "nu" in t or "female" in t:
            sex = "female"
        if "nam" in t or "male" in t:
            sex = "male"

        if not (w and h and age and sex):
            return (
                "Để tính **BMR**, bạn cần cho mình đủ: **cân nặng, chiều cao, tuổi, giới tính**.\n"
                "Ví dụ: `BMR 67kg 172cm 21 tuổi nam`"
            )

        bmr = _bmr_mifflin(w, h, age, sex)
        return f"✅ BMR ước tính của bạn là **{bmr:.0f} kcal/ngày** (công thức Mifflin–St Jeor)."

    # 4) tính TDEE
    if "tdee" in t:
        w, h = _extract_weight_height(t)
        age = None
        m_age = re.search(r"(\d{1,2})\s*(tuổi|tuoi)", t)
        if m_age:
            age = int(m_age.group(1))

        sex = None
        if "nữ" in t or "nu" in t or "female" in t:
            sex = "female"
        if "nam" in t or "male" in t:
            sex = "male"

        # mức vận động (ít/nhẹ/vừa/nặng/rất nặng)
        activity = "vừa"
        for key in ["ít", "it", "nhẹ", "nhe", "vừa", "vua", "nặng", "nang", "rất nặng", "rat nang", "sedentary", "light", "moderate", "active", "very active"]:
            if key in t:
                activity = key
                break

        if not (w and h and age and sex):
            return (
                "Để tính **TDEE**, bạn cần: **cân nặng, chiều cao, tuổi, giới tính, mức vận động**.\n"
                "Ví dụ: `TDEE 67kg 172cm 21 tuổi nam vận động vừa`"
            )

        bmr = _bmr_mifflin(w, h, age, sex)
        mul = _tdee_multiplier(activity)
        tdee = bmr * mul

        return (
            f"✅ TDEE ước tính của bạn là **{tdee:.0f} kcal/ngày**.\n"
            f"(BMR ≈ {bmr:.0f} × hệ số vận động {mul})\n"
            "Gợi ý nhanh:\n"
            "- **Giảm cân**: ăn thấp hơn TDEE ~ 300–500 kcal/ngày\n"
            "- **Tăng cân**: ăn cao hơn TDEE ~ 200–400 kcal/ngày\n"
            "- **Duy trì**: ăn gần bằng TDEE"
        )

    # 5) dinh dưỡng / tập luyện chung
    if "giảm cân" in t or "giam can" in t:
        return (
            "Giảm cân bền vững: ưu tiên **thâm hụt 300–500 kcal/ngày**, tăng **protein**, ăn nhiều rau, ngủ đủ.\n"
            "Bạn muốn mình tính **TDEE** để đặt mục tiêu không? Gửi: `TDEE 67kg 172cm 21 tuổi nam vận động vừa`."
        )

    if "tăng cân" in t or "tang can" in t:
        return (
            "Tăng cân khỏe: tăng **200–400 kcal/ngày** so với TDEE, ưu tiên protein + tinh bột tốt, tập kháng lực.\n"
            "Bạn gửi mình `TDEE ...` để mình ước tính mức calo mục tiêu nhé."
        )

    if "ăn" in t or "dinh dưỡng" in t or "dinh duong" in t:
        return (
            "Về dinh dưỡng: bạn có thể theo dõi bữa ăn trong mục **Dinh dưỡng** để cộng tổng kcal trong ngày.\n"
            "Nếu bạn cho mình mục tiêu (giảm/tăng/duy trì) + TDEE, mình gợi ý mức kcal/ngày phù hợp."
        )

    if "tập" in t or "tap" in t or "gym" in t:
        return (
            "Về tập luyện: bạn có thể nhập bài tập và thời lượng trong mục **Tập luyện** để ước tính calo tiêu hao.\n"
            "Bạn đang muốn **giảm mỡ** hay **tăng cơ**? Mình gợi ý lịch tập đơn giản cho bạn."
        )

    # 6) fallback
    return (
        "Mình hỗ trợ các vấn đề về **BMI, BMR, TDEE, dinh dưỡng, tập luyện** và cách dùng Libra Health.\n"
        "Bạn thử gửi:\n"
        "- `BMI 67kg 172cm`\n"
        "- `BMR là gì?`\n"
        "- `TDEE 67kg 172cm 21 tuổi nam vận động vừa`"
    )

# ==============================
# API View
# ==============================

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

    reply = _reply_rule_based(user_message)
    return JsonResponse({"reply": reply})
