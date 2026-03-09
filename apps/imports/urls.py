from django.urls import path

from .views import ImportProgressAPIView, UploadImportView

urlpatterns = [
    path("upload/", UploadImportView.as_view(), name="upload-import"),
    path(
        "api/v1/imports/progress/",
        ImportProgressAPIView.as_view(),
        name="api-import-progress",
    ),
]
