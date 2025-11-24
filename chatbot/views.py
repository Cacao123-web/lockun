import json, requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

# ======== Cấu hình Ollama local ========
OLLAMA_URL = "http://127.0.0.1:11434/api/chat"
OLLAMA_MODEL = "gemma2:2b"  # model bạn vừa tải về

DISCLAIMER = (
    "⚠️ Thông tin chỉ mang tính tham khảo, không thay thế chẩn đoán hoặc y lệnh bác sĩ."
)

# Từ khóa sơ bộ để nhận diện câu hỏi liên quan sức khỏe / Libra Health
HEALTH_KEYWORDS = [
    "sức khỏe", "sức khoẻ", "tập luyện", "tập thể dục", "dinh dưỡng",
    "ăn uống", "giảm cân", "tăng cân", "bmi", "bmr", "tdee",
    "calo", "kcal", "cân nặng", "chiều cao", "mục tiêu", "libra health",
    "hồ sơ sức khỏe", "chỉ số", "đặt mục tiêu", "báo cáo sức khỏe",
]

# ======== SYSTEM PROMPT CHUYÊN LIBRA HEALTH ========
SYSTEM_PROMPT = """
Bạn là trợ lý ảo của website Libra Health – hệ thống quản lý sức khỏe cá nhân.

NHIỆM VỤ CHÍNH:
- Giải thích các chỉ số sức khỏe trong hệ thống: BMI, BMR, TDEE, mục tiêu calo, cân nặng.
- Hướng dẫn người dùng cách sử dụng website Libra Health (đăng ký, đăng nhập, nhập hồ sơ, xem báo cáo, đặt mục tiêu…).
- Gợi ý mức độ vận động, thói quen ăn uống lành mạnh ở mức cơ bản.

GIỚI HẠN:
- CHỈ trả lời các câu hỏi liên quan đến sức khỏe tổng quát, dinh dưỡng, tập luyện nhẹ và cách dùng Libra Health.
- KHÔNG được chẩn đoán bệnh, kê thuốc, đưa ra phác đồ điều trị.
- Nếu người dùng hỏi về chủ đề khác (lập trình, game, tiền ảo, chính trị, …) bạn PHẢI từ chối và nhắc họ hỏi về sức khỏe hoặc Libra Health.
- Nếu người dùng hỏi về bệnh nặng, thuốc, xét nghiệm, phẫu thuật… hãy trả lời:
  “Mình chỉ hỗ trợ giải thích chỉ số sức khỏe cơ bản và hướng dẫn dùng Libra Health. 
   Với vấn đề y khoa chuyên sâu hoặc khẩn cấp, bạn nên hỏi trực tiếp bác sĩ.”

THÔNG TIN VỀ WEBSITE:
- Libra Health cho phép người dùng tạo tài khoản, nhập tuổi, giới tính, chiều cao, cân nặng, mức độ vận động.
- Hệ thống tính các chỉ số:
  + BMI = cân nặng / (chiều cao_m)^2 và phân loại: Gầy, Bình thường, Thừa cân, Béo phì.
  + BMR: tính theo công thức Mifflin–St Jeor (nam/nữ khác nhau).
  + TDEE = BMR * hệ số vận động (ít vận động, nhẹ, vừa, nhiều, rất nhiều).
- Người dùng có thể vào trang Hồ sơ để cập nhật dữ liệu, xem kết quả và biểu đồ.
- Ngoài ra có các mục: Dinh dưỡng, Tập luyện, Mục tiêu, Báo cáo.

CÁCH TRẢ LỜI:
- Dùng tiếng Việt, ngắn gọn, dễ hiểu, thân thiện, có thể dùng gạch đầu dòng.
- Ưu tiên giải thích theo số liệu đã có trên web (BMI, BMR, TDEE).
- Khi hướng dẫn, hãy nói cụ thể nút, menu: “Vào menu Mục tiêu → chọn Thêm mục tiêu…”.
- Nếu câu hỏi không liên quan đến sức khỏe tổng quát hoặc Libra Health, hãy từ chối trả lời và nhắc người dùng hỏi đúng chủ đề.
"""

@csrf_exempt
def chat_api(request):
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "POST only"}, status=405)

    try:
        data = json.loads(request.body.decode("utf-8"))
        user_msg = (data.get("message") or "").strip()
        if not user_msg:
            return JsonResponse({"ok": False, "error": "empty"}, status=400)
    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=400)

    # ===== LỚP CHẶN BÊN NGOÀI: nếu câu hỏi không liên quan sức khỏe/web thì từ chối luôn =====
    lower_msg = user_msg.lower()
    if not any(kw in lower_msg for kw in HEALTH_KEYWORDS):
        reply = (
            "Mình chỉ hỗ trợ các câu hỏi về sức khỏe tổng quát, dinh dưỡng, tập luyện "
            "và cách sử dụng website Libra Health (BMI, BMR, TDEE, mục tiêu, báo cáo...).\n"
            "Bạn hãy hỏi về các chủ đề đó nhé."
        )
        return JsonResponse({"ok": True, "reply": f"{reply}\n\n{DISCLAIMER}"})

    # ===== Nếu câu hỏi hợp lệ → gọi AI qua Ollama =====
    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_msg},
                ],
                "stream": False,
            },
            timeout=60,
        )
        response.raise_for_status()
        data = response.json()
        reply = data.get("message", {}).get("content", "").strip()
        if not reply:
            reply = "Mình chưa rõ, bạn có thể hỏi lại cụ thể hơn nhé."
    except Exception as e:
        print("Ollama error:", e)
        reply = "Máy chủ AI đang không phản hồi, hãy đảm bảo Ollama đang chạy."

    return JsonResponse({"ok": True, "reply": f"{reply}\n\n{DISCLAIMER}"})
