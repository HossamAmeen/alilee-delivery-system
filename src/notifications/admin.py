from django.contrib import admin

from notifications.models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("user_account", "title", "is_read", "created")
    list_filter = ("is_read", "created")
    search_fields = ("title", "message", "user_account__full_name")
    ordering = ("-id",)
