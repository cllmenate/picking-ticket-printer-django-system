from django.urls import path

from .views import DeliveryDetailView, DeliveryListView

urlpatterns = [
    path(
        "deliveries/list/",
        DeliveryListView.as_view(),
        name="delivery-list",
    ),
    path(
        "deliveries/<int:pk>/detail/",
        DeliveryDetailView.as_view(),
        name="delivery-detail",
    ),
]
