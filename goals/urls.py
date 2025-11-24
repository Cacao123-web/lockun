# goals/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path("", views.goals_overview, name="goals_overview"),
    path("list/", views.goals_list, name="goals_list"),
    path("new/", views.goals_create, name="goals_create"),
    path("<int:pk>/delete/", views.goals_delete, name="goals_delete"),
    path('<int:pk>/finish/<str:result>/', views.goals_finish, name='goals_finish'),
    path('history/', views.goals_history, name='goals_history'),

]
