from django.core.management.base import BaseCommand
from django.core.mail import send_mail

class Command(BaseCommand):
    help = "Gửi email test"

    def add_arguments(self, parser):
        parser.add_argument("to", type=str, help="Email người nhận")

    def handle(self, *args, **opts):
        to = opts["to"]
        send_mail("HealthManager Test", "Thông báo thử nghiệm.", None, [to])
        self.stdout.write(self.style.SUCCESS(f"Đã gửi tới {to}"))
