
from django.contrib import admin

from .models import Driver, Trader, UserAccount


@admin.register(UserAccount)
class UserAccountAdmin(admin.ModelAdmin):
    list_display = ("email", "full_name", "role")
    list_filter = ("role",)
    search_fields = ("email", "full_name")


@admin.register(Trader)
class TraderAdmin(admin.ModelAdmin):
    list_display = ("email", "full_name", "role", "balance")
    list_filter = ("role",)
    search_fields = ("email", "full_name")


@admin.register(Driver)
class DriverAdmin(admin.ModelAdmin):
    list_display = (
        "email",
        "full_name",
        "role",
        "vehicle_number",
        "license_number",
        "balance",
    )
    list_filter = ("role", "vehicle_number", "license_number")
    search_fields = ("email", "full_name")
