from django.urls import path

from .views import CustomerDetailView, CustomerListView

urlpatterns = [
    path(
        "customers/list/",
        CustomerListView.as_view(),
        name="customer-list",
    ),
    path(
        "customers/<int:pk>/detail/",
        CustomerDetailView.as_view(),
        name="customer-detail",
    ),
]
