# chatbot/urls.py
from django.urls import path
from .views import health_chat

app_name = "chatbot"

urlpatterns = [
    path("", health_chat, name="health_chat"),
]
