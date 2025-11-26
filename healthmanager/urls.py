from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from accounts.views import DashboardView
from healthmanager import views
from reports import views as reports_views

urlpatterns = [
    path("admin/", admin.site.urls),

    # Apps con
    path("accounts/", include("accounts.urls")),
    path("tracker/", include("tracker.urls")),
    path("reports/", include("reports.urls")),
    path("goals/", include("goals.urls")),
    path("health/", reports_views.health_overview, name="health_overview"),

    # ✅ API chatbot: /api/chat/
    path("api/chat/", include("chatbot.urls")),

    # Trang chính & tĩnh
    path("", DashboardView.as_view(), name="dashboard"),
    path("search/", views.search, name="search"),
    path("about/", TemplateView.as_view(template_name="pages/about.html"), name="about"),
    path(
        "services/",
        TemplateView.as_view(
            template_name="pages/services.html",
            extra_context={
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
