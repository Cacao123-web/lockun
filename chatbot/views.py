# chatbot/views.py
import json
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from openai import OpenAI

HEALTH_CONTEXT = """
Libra Health là website quản lý sức khỏe cá nhân với các chức năng chính:
- Tính BMI, phân loại theo chuẩn châu Á.
- Tính BMR (Mifflin-St Jeor) và TDEE dựa trên chiều cao, cân nặng, tuổi, giới tính và mức độ vận động.
- Quản lý hồ sơ sức khỏe: chiều cao, cân nặng, giới tính, tuổi, mức vận động.
- Theo dõi bữa ăn: nhập món ăn, khẩu phần, khối lượng (gram), tính tổng kcal trong ngày.
- Theo dõi tập luyện: nhập bài tập, thời lượng, ước tính calo tiêu hao.
- Đặt mục tiêu sức khỏe (giảm cân, tăng cân, duy trì) dựa trên TDEE.
- Các gợi ý chăm sóc sức khỏe chung: ăn đủ chất, tập luyện thường xuyên, ngủ đủ giấc.

Nguyên tắc trả lời:
- Chỉ trả lời các câu hỏi liên quan đến: BMI, BMR, TDEE, dinh dưỡng, luyện tập, kiểm soát cân nặng,
  và cách sử dụng các chức năng trên website Libra Health.
- Không được trả lời các chủ đề khác (code, game, tài chính, tình cảm, lịch sử, chính trị, v.v.).
- Không chẩn đoán bệnh, không kê đơn thuốc, chỉ đưa ra lời khuyên chung và luôn nhắc người dùng
  hỏi ý kiến bác sĩ khi có vấn đề sức khỏe nghiêm trọng.
- Nếu câu hỏi nằm ngoài phạm vi trên, hãy trả lời ngắn gọn rằng bạn chỉ hỗ trợ về sức khỏe
  và các chức năng của Libra Health.
"""

@csrf_exempt
@require_POST
def health_chat(request):
    # 1) Check API key trước để khỏi “mất kết nối” mù
    if not getattr(settings, "OPENAI_API_KEY", ""):
        return JsonResponse({"error": "Missing OPENAI_API_KEY on server"}, status=500)

    # 2) Parse JSON an toàn (tránh lỗi khi body rỗng / JSON sai)
    try:
        raw = request.body.decode("utf-8") if request.body else ""
        data = json.loads(raw or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    user_message = (data.get("message") or "").strip()
    if not user_message:
        return JsonResponse({"error": "empty message"}, status=400)

    # 3) Tạo client sau khi chắc chắn có key (tránh client bị init với key rỗng)
    client = OpenAI(api_key=settings.OPENAI_API_KEY)

    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Bạn là trợ lý sức khỏe của website Libra Health. "
                        "Giữ câu trả lời ngắn gọn, dễ hiểu, tiếng Việt, giọng thân thiện. "
                        "Dưới đây là thông tin về hệ thống và phạm vi hỗ trợ:\n\n"
                        + HEALTH_CONTEXT
                    ),
                },
                {"role": "user", "content": user_message},
            ],
            temperature=0.5,
            max_tokens=300,
        )

        reply = (completion.choices[0].message.content or "").strip()
        return JsonResponse({"reply": reply})

    except Exception:
        return JsonResponse(
            {"error": "Đã có lỗi khi gọi trợ lý sức khỏe, vui lòng thử lại sau."},
            status=500,
        )
