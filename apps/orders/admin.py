from django.contrib import admin
from unfold.admin import ModelAdmin

from apps.orders.models import Order, OrderItem


class OrderAdmin(ModelAdmin):
    list_display = (
        "picking",
        "order_number",
        "order_route",
        "customer__name",
        "status",
        "created_at",
        "updated_at",
    )
    search_fields = (
        "picking",
        "order_number",
        "order_route",
        "customer__name",
        "status",
        "created_at",
        "updated_at",
    )
    list_filter = (
        "picking",
        "order_number",
        "order_route",
        "customer__name",
        "status",
        "created_at",
        "updated_at",
    )


admin.site.register(Order, OrderAdmin)


class OrderItemAdmin(ModelAdmin):
    list_display = (
        "order",
        "product__description",
        "quantity",
        "created_at",
        "updated_at",
    )
    search_fields = (
        "order",
        "product__description",
        "quantity",
        "created_at",
        "updated_at",
    )
    list_filter = (
        "order",
        "product__description",
        "quantity",
        "created_at",
        "updated_at",
    )


admin.site.register(OrderItem, OrderItemAdmin)
