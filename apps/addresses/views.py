from django.contrib.auth.mixins import (
    LoginRequiredMixin,
    PermissionRequiredMixin,
)
from django.core.cache import cache
from django.views.generic import DetailView, ListView

from .models import Address


# Create your views here.
class AddressListView(
    LoginRequiredMixin,
    PermissionRequiredMixin,
    ListView,
):
    model = Address
    template_name = "address_list.html"
    context_object_name = "addresses"
    paginate_by = 10
    permission_required = "addresses.view_address"

    def get_queryset(self):
        queryset = super().get_queryset()

        key = "addresses_list"
        cached_qs = cache.get(key)

        if cached_qs:
            return cached_qs

        # Force evaluation to cache the result
        qs_list = list(queryset)
        cache.set(key, qs_list, 60 * 15)

        return qs_list

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["addresses"] = self.get_queryset()
        return context


class AddressDetailView(
    LoginRequiredMixin,
    PermissionRequiredMixin,
    DetailView,
):
    model = Address
    template_name = "address_detail.html"
    context_object_name = "address"
    permission_required = "addresses.view_address"
