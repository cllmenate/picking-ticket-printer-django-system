from django.urls import path

from .views import AddressDetailView, AddressListView

urlpatterns = [
    path(
        "addresses/list/",
        AddressListView.as_view(),
        name="address-list",
    ),
    path(
        "addresses/<int:pk>/detail/",
        AddressDetailView.as_view(),
        name="address-detail",
    ),
]
