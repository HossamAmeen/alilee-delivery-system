
from django.contrib import admin

from users.models import Driver, Trader, UserAccount, FirebaseDevice


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

@admin.register(FirebaseDevice)
class FirebaseDeviceAdmin(admin.ModelAdmin):
    list_display = ("user", "token", "last_seen", "created_at")
    list_filter = ("user", "last_seen")
    search_fields = ("user", "token")
    