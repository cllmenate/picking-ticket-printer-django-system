from django.contrib.auth.mixins import (
    LoginRequiredMixin,
    PermissionRequiredMixin,
)
from django.views.generic import DetailView, ListView

from .models import Customer


# Create your views here.
class CustomerListView(
    LoginRequiredMixin,
    PermissionRequiredMixin,
    ListView,
):
    model = Customer
    template_name = "customer_list.html"
    context_object_name = "customers"
    permission_required = "customers.view_customer"

    def get_queryset(self):
        return Customer.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Customers"
        return context


class CustomerDetailView(
    LoginRequiredMixin,
    PermissionRequiredMixin,
    DetailView,
):
    model = Customer
    template_name = "customer_detail.html"
    context_object_name = "customer"
    permission_required = "customers.view_customer"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Customer"
        return context
