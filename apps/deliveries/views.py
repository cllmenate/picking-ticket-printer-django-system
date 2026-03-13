from django.contrib.auth.mixins import (
    LoginRequiredMixin,
    PermissionRequiredMixin,
)
from django.views.generic import DetailView, ListView

from .models import Delivery


# Create your views here.
class DeliveryListView(
    LoginRequiredMixin,
    PermissionRequiredMixin,
    ListView,
):
    model = Delivery
    template_name = "delivery_list.html"
    context_object_name = "deliveries"
    permission_required = "deliveries.view_delivery"

    def get_queryset(self):
        return Delivery.objects.all()


class DeliveryDetailView(
    LoginRequiredMixin,
    PermissionRequiredMixin,
    DetailView,
):
    model = Delivery
    template_name = "delivery_detail.html"
    context_object_name = "delivery"
    permission_required = "deliveries.view_delivery"
