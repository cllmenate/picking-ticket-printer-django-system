from addresses import views
from django.urls import path

urlpatterns = [
    path(
        "addresses/list/",
        views.AddressListView.as_view(),
        name="address-list",
    ),
    path(
        "addresses/detail/<int:pk>/",
        views.AddressDetailView.as_view(),
        name="address-detail",
    ),
]
