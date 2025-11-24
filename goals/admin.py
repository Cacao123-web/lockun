from django.contrib import admin
from .models import Goal
admin.site.register(Goal)
class GoalAdmin(admin.ModelAdmin):
    list_display = ("user", "goal_type", "target_value", "deadline", "created")
    search_fields = ("user__username",)
    list_filter = ("goal_type", "deadline")