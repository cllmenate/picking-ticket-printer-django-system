from customers import views
from django.urls import path

urlpatterns = [
    path(
        "customers/list/",
        views.CustomerListView.as_view(),
        name="customer-list",
    ),
    path(
        "customers/<int:pk>/detail/",
        views.CustomerDetailView.as_view(),
        name="customer-detail",
    ),
]
