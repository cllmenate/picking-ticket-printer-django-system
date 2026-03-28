from django.urls import path

from .views import ProductDetailView, ProductListView

urlpatterns = [
    path(
        "products/list/", ProductListView.as_view(), name="product_list"
    ),
    path(
        "products/<int:pk>/detail/",
        ProductDetailView.as_view(),
        name="product_detail",
    ),
]
