from django.urls import path
from . import views

urlpatterns = [
    path("", views.reports_dashboard, name="reports_dashboard"),
    path("csv/", views.export_csv, name="export_csv"),
    path("pdf/", views.export_pdf, name="export_pdf"),
]
