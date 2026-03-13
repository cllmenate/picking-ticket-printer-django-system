from django.contrib import admin

from .models import Delivery


# Register your models here.
@admin.register(Delivery)
class DeliveryAdmin(admin.ModelAdmin):
    list_display = (
        "carrier",
        "delivery",
        "route",
        "manifest",
        "vehicle",
        "driver",
        "helper",
        "created_at",
        "updated_at",
    )
    list_filter = (
        "carrier",
        "delivery",
        "route",
        "manifest",
        "vehicle",
        "driver",
        "helper",
        "created_at",
        "updated_at",
    )
    search_fields = (
        "carrier",
        "delivery",
        "route",
        "manifest",
        "vehicle",
        "driver",
        "helper",
    )
    ordering = (
        "-created_at",
    )
