import os
from pathlib import Path
from dotenv import load_dotenv
import dj_database_url
# ==============================
# Cấu hình cơ bản
# ==============================
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "unsafe-dev")

# Trên Render nên set biến môi trường DEBUG=False
DEBUG = os.getenv("DEBUG", "True") == "True"

ALLOWED_HOSTS = [
    "127.0.0.1",
    "localhost",
    "lockun.onrender.com",
]

CSRF_TRUSTED_ORIGINS = [
    "https://lockun.onrender.com",
    # nếu sau này có domain riêng:
    # "https://tenmiencuaban.com",
    # "https://www.tenmiencuaban.com",
]

# Nếu deploy sau reverse proxy (Render) – giúp nhận https đúng
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# ==============================
# Ứng dụng (Apps)
# ==============================
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Các app của project
    "accounts.apps.AccountsConfig",
    "tracker",
    "goals",
    "reports",
    "chatbot",

    # App cron
    "django_crontab",
]

# ==============================
# Middleware
# ==============================
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    # Whitenoise để serve static trên Render / production
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "healthmanager.urls"

# ==============================
# Templates
# ==============================
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "healthmanager.wsgi.application"

# ==============================
# Database (PostgreSQL)
# ==============================
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("DB_NAME", "healthdb"),
        "USER": os.getenv("DB_USER", "postgres"),
        "PASSWORD": os.getenv("DB_PASSWORD", "123456789"),
        "HOST": os.getenv("DB_HOST", "127.0.0.1"),
        "PORT": os.getenv("DB_PORT", "5432"),
    }
}
DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL:
    DATABASES["default"] = dj_database_url.config(
        default=DATABASE_URL,
        conn_max_age=600,              # giữ kết nối pool, đỡ tốn tài nguyên
        ssl_require=not DEBUG,         # Render thường dùng SSL
    )
# ==============================
# Mật khẩu & Bảo mật
# ==============================
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ==============================
# Ngôn ngữ & Múi giờ
# ==============================
LANGUAGE_CODE = "vi"
TIME_ZONE = "Asia/Ho_Chi_Minh"
USE_I18N = True
USE_TZ = True

# ==============================
# Static & Media
# ==============================
# URL cho static
STATIC_URL = "/static/"

# Thư mục chứa static trong source (css, js, img...)
STATICFILES_DIRS = [BASE_DIR / "static"]

# Nơi collectstatic gom file vào (Render sẽ serve thư mục này)
STATIC_ROOT = BASE_DIR / "staticfiles"

# Whitenoise storage: nén + hash tên file static
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# ==============================
# Login / Logout Redirect
# ==============================
LOGIN_REDIRECT_URL = "dashboard"
LOGOUT_REDIRECT_URL = "login"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ==============================
# Email (gửi nhắc nhở)
# ==============================
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "True") == "True"
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
SERVER_EMAIL = "no-reply@librahealth.local"

# ==============================
# API (Chatbot / OpenAI)
# ==============================
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# ==============================
# Cronjob (Tự động gửi nhắc nhở)
# ==============================
CRONJOBS = [
    # Gửi nhắc nhở lúc 7 giờ sáng mỗi ngày
    ("0 7 * * *", "django.core.management.call_command", ["send_reminder"]),
]
