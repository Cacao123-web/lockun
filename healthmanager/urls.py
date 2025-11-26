# healthmanager/urls.py
from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from accounts.views import DashboardView
from healthmanager import views  # nếu bạn có views.search trong đây
from reports import views as reports_views 
urlpatterns = [
    path("admin/", admin.site.urls),

    # Apps con
    path("accounts/", include("accounts.urls")),
    path("tracker/", include("tracker.urls")),
    path("reports/", include("reports.urls")),
    path("goals/", include("goals.urls")),           # ✅ chỉ include, KHÔNG gọi trực tiếp goals_overview
    path("health/", reports_views.health_overview, name="health_overview"),
    # API chatbot (JS đang gọi /api/chat/)
    path("api/", include("chatbot.urls")),
    path("chatbot/", include("chatbot.urls", namespace="chatbot")),
    # Trang chính & tĩnh
    path("", DashboardView.as_view(), name="dashboard"),
    path("search/", views.search, name="search"),    # nếu search nằm trong healthmanager/views.py
    path("about/", TemplateView.as_view(template_name="pages/about.html"), name="about"),
    path(
        "services/",
        TemplateView.as_view(
            template_name="pages/services.html",
            extra_context={
                # TODO: thay nội dung services nếu bạn đã sửa sang các dịch vụ "sức khỏe cá nhân"
                "departments": [
                    "Khoa tai mũi họng",
                    "Khoa xương cơ khớp",
                    "Phẫu thuật tim mạch",
                    "Tiêu hóa",
                    "Thẩm mỹ",
                    "Cấp cứu ngoại khoa",
                ]
            },
        ),
        name="services",
    ),
]
