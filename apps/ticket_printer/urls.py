from django.urls import path

from .views import QzCertificateView, QzSignView

urlpatterns = [
    path(
        "qz-certificate/", QzCertificateView.as_view(), name="qz-certificate"
    ),
    path("qz-sign/", QzSignView.as_view(), name="qz-sign"),
]
