# accounts/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model

from .models import Profile

User = get_user_model()

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    # Khi tạo user mới, tự tạo Profile đi kèm
    if created:
        Profile.objects.get_or_create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    # Mỗi lần user được save (ví dụ đổi tên/email), đảm bảo Profile tồn tại và đồng bộ
    Profile.objects.get_or_create(user=instance)
    # Gọi save() để chạy recalc() trong model Profile (nếu có dữ liệu đủ)
    instance.profile.save()
