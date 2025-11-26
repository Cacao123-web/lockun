from django.http import HttpResponse
from django.contrib.auth import get_user_model
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView

from .forms import SignUpForm, ProfileForm, PasswordResetRequestForm, PasswordResetVerifyForm
from .models import Profile, PasswordResetOTP
from django.core.mail import send_mail        
from django.conf import settings     

def signup(request):
    """
    Đăng ký tài khoản mới:
    - Lưu User từ SignUpForm
    - Tạo Profile rỗng kèm full_name mặc định = username (nếu chưa có)
    - Đăng nhập và chuyển hướng tới hồ sơ cá nhân
    """
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Tạo hồ sơ nếu chưa có
            Profile.objects.get_or_create(
                user=user,
                defaults={"full_name": user.username},
            )
            login(request, user)
            messages.success(request, "Đăng ký thành công. Vui lòng hoàn thiện hồ sơ sức khỏe.")
            return redirect("accounts:profile")  # chuyển đến hồ sơ cá nhân
        else:
            messages.error(request, "Đăng ký thất bại. Vui lòng kiểm tra lại.")
    else:
        form = SignUpForm()

    return render(request, "accounts/signup.html", {"form": form})


@login_required
def profile(request):
    """
    Trang hồ sơ người dùng:
    - Lấy hoặc tạo Profile
    - Lưu form: Profile.save() sẽ tự recalc() BMI/BMR/TDEE
    """
    prof, _ = Profile.objects.get_or_create(user=request.user)

    if request.method == "POST":
        form = ProfileForm(request.POST, instance=prof)
        if form.is_valid():
            form.save()  # save() của model đã tự recalc()
            messages.success(request, "Đã lưu hồ sơ và tính lại chỉ số sức khỏe.")
            return redirect("accounts:profile")
        else:
            messages.error(request, "Vui lòng kiểm tra lại các trường bị lỗi.")
    else:
        form = ProfileForm(instance=prof)

    return render(request, "accounts/profile.html", {"form": form, "profile": prof})


class DashboardView(TemplateView):
    template_name = "dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["services"] = [
            "BMI",
            "BMR",
            "TDEE",
            "DINH DƯỠNG",
            "TẬP LUYỆN",
            "MỤC TIÊU",
        ]
        return context


@user_passes_test(lambda u: u.is_staff)
def users_list(request):
    q = request.GET.get("q", "")
    qs = User.objects.filter(is_superuser=False)
    if q:
        qs = qs.filter(username__icontains=q)
    return render(request, "accounts/users_list.html", {"users": qs, "q": q})

def delete_user(request, user_id):
    user = get_object_or_404(User, id=user_id)

    # Không cho xóa tài khoản admin
    if user.is_superuser:
        messages.error(request, "Không thể xóa tài khoản quản trị viên.")
        return redirect("accounts:admin_users")

    user.delete()
    messages.success(request, "Đã xóa tài khoản thành công.")
    return redirect("accounts:admin_users")

def logout_view(request):
    logout(request)
    messages.info(request, "Bạn đã đăng xuất.")
    return redirect("accounts:login")

# =======================================
# QUÊN MẬT KHẨU + XÁC THỰC OTP 2 BƯỚC
# =======================================

def password_reset_request(request):
    """
    Bước 1: Nhập username/email -> gửi mã OTP về email.
    """
    if request.method == "POST":
        form = PasswordResetRequestForm(request.POST)
        if form.is_valid():
            user = form.user  # đã gán trong clean_identifier

            # tạo OTP mới
            otp = PasswordResetOTP.create_new(user)

            # gửi email
            subject = "Mã khôi phục mật khẩu Libra Health"
            message = (
                f"Xin chào {user.username},\n\n"
                f"Mã xác thực để đặt lại mật khẩu của bạn là: {otp.code}\n"
                "Mã có hiệu lực trong 10 phút.\n\n"
                "Nếu bạn không yêu cầu đặt lại mật khẩu, hãy bỏ qua email này."
            )
            from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@librahealth.local")
            # fail_silently=True để dev không bị crash nếu cấu hình mail chưa chuẩn
            send_mail(subject, message, from_email, [user.email], fail_silently=True)

            # lưu user id vào session để dùng ở bước 2
            request.session["reset_user_id"] = user.id
            messages.success(request, "Đã gửi mã OTP tới email của bạn.")
            return redirect("accounts:password_reset_verify")
        else:
            messages.error(request, "Vui lòng kiểm tra lại thông tin.")
    else:
        form = PasswordResetRequestForm()

    return render(request, "accounts/password_reset_request.html", {"form": form})


def password_reset_verify(request):
    """
    Bước 2: Nhập OTP + mật khẩu mới -> đổi mật khẩu nếu OTP đúng & còn hạn.
    """
    user_id = request.session.get("reset_user_id")
    if not user_id:
        messages.error(request, "Phiên đặt lại mật khẩu đã hết hạn. Vui lòng thử lại.")
        return redirect("accounts:password_reset_request")

    user = get_object_or_404(User, id=user_id)

    if request.method == "POST":
        form = PasswordResetVerifyForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data["code"]

            # Lấy OTP mới nhất của user với mã này
            try:
                otp_obj = PasswordResetOTP.objects.filter(
                    user=user,
                    code=code,
                    is_used=False,
                ).latest("created_at")
            except PasswordResetOTP.DoesNotExist:
                messages.error(request, "Mã OTP không đúng.")
                return render(
                    request,
                    "accounts/password_reset_verify.html",
                    {"form": form, "user": user},
                )

            # Kiểm tra hết hạn
            if otp_obj.is_expired():
                messages.error(request, "Mã OTP đã hết hạn. Vui lòng yêu cầu mã mới.")
                return redirect("accounts:password_reset_request")

            # Đổi mật khẩu
            new_password = form.cleaned_data["new_password1"]
            user.set_password(new_password)
            user.save()

            # Đánh dấu OTP đã dùng
            otp_obj.is_used = True
            otp_obj.save()

            # Xóa session
            try:
                del request.session["reset_user_id"]
            except KeyError:
                pass

            messages.success(request, "Đặt lại mật khẩu thành công. Hãy đăng nhập bằng mật khẩu mới.")
            return redirect("accounts:login")
        else:
            messages.error(request, "Vui lòng kiểm tra lại thông tin.")
    else:
        form = PasswordResetVerifyForm()

    return render(request, "accounts/password_reset_verify.html", {"form": form, "user": user})


# =======================================
# DEBUG: TẠO / RESET TÀI KHOẢN ADMIN TRÊN RENDER
# =======================================
@csrf_exempt
def debug_create_admin(request):
    User = get_user_model()
    user, created = User.objects.get_or_create(
        username="admin",
        defaults={
            "email": "admin@example.com",
            "is_staff": True,
            "is_superuser": True,
        },
    )
    # luôn đảm bảo quyền + mật khẩu
    user.is_staff = True
    user.is_superuser = True
    user.set_password("Admin123!")
    user.save()

    return HttpResponse(f"OK – admin created/updated. created={created}")
