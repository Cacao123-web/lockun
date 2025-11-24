from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.contrib.auth import get_user_model
from goals.models import Goal

User = get_user_model()

class Command(BaseCommand):
    help = "Gửi email nhắc nhở tập luyện / dinh dưỡng cho các mục tiêu đang thực hiện"

    def handle(self, *args, **kwargs):
        # Chỉ lấy user có email
        users = User.objects.filter(is_active=True).exclude(email="").exclude(email__isnull=True)

        if not users.exists():
            self.stdout.write("Không có user nào có email để gửi.")
            return

        for user in users:
            # Lấy các Goal đang ở trạng thái 'in_progress'
            goals = Goal.objects.filter(user=user, status="in_progress")
            if not goals.exists():
                continue

            lines = []
            for g in goals:
                type_label = dict(Goal.GOAL_TYPES).get(g.type, g.type)
                lines.append(
                    f"- Mục tiêu: {type_label}, mục tiêu: {g.target_value}, tiến độ: {g.progress_pct}%"
                )

            message = (
                f"Chào {user.username},\n\n"
                "Đây là nhắc nhở sức khỏe / tập luyện hôm nay của bạn:\n\n"
                + "\n".join(lines)
                + "\n\nCố gắng duy trì thói quen tốt nhé!"
            )

            send_mail(
                subject="Nhắc nhở sức khỏe hôm nay",
                message=message,
                from_email=None,  # sẽ dùng DEFAULT_FROM_EMAIL trong settings
                recipient_list=[user.email],
                fail_silently=False,
            )

        self.stdout.write(self.style.SUCCESS("Đã gửi email nhắc nhở cho các user có mục tiêu đang thực hiện."))
