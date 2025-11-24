from django.urls import path
from django.contrib.auth import views as auth_views
from django.contrib.auth.views import LogoutView
from . import views

app_name = "accounts"

urlpatterns = [
    # Đăng ký / đăng nhập / đăng xuất
    path("signup/", views.signup, name="signup"),
    path(
        "login/",
        auth_views.LoginView.as_view(template_name="accounts/login.html"),
        name="login",
    ),
    path(
        "logout/",
        LogoutView.as_view(next_page="accounts:login"),
        name="logout",
    ),

    # Hồ sơ
    path("profile/", views.profile, name="profile"),

    # Quản trị
    path("admin-users/", views.users_list, name="admin_users"),
    path("admin-users/delete/<int:user_id>/", views.delete_user, name="delete_user"),

    # 🔐 QUÊN MẬT KHẨU + OTP 2 BƯỚC
    path("password-reset/", views.password_reset_request, name="password_reset_request"),
    path("password-reset/xac-thuc/", views.password_reset_verify, name="password_reset_verify"),
]
