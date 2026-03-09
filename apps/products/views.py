from django.core.cache import cache
from django.views.generic import DetailView, ListView
from products import models


class ProductListView(ListView):
    model = models.Product
    template_name = "product_list.html"
    context_object_name = "products"
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()
        sku = self.request.GET.get("sku")
        description = self.request.GET.get("description")

        if sku:
            queryset = queryset.filter(sku__icontains=sku)

        if description:
            queryset = queryset.filter(description__icontains=description)

        key = "product_list_queryset"
        cached_qs = cache.get(key)

        if cached_qs:
            return cached_qs

        # Force evaluation to cache the result
        qs_list = list(queryset)
        cache.set(key, qs_list, 60 * 15)

        return qs_list

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class ProductDetailView(DetailView):
    model = models.Product
    template_name = "product_detail.html"
    context_object_name = "product"
