from django.contrib import admin
from unfold.admin import ModelAdmin

from apps.products import models


# Register your models here.
class ProductAdmin(ModelAdmin):
    list_display = (
        "sku_code",
        "description",
        "price",
        "created_at",
        "updated_at",
    )
    search_fields = ("sku_code", "description")
    list_filter = ("created_at", "updated_at")


admin.site.register(models.Product, ProductAdmin)
