from django.db import models


class ImportBatch(models.Model):
    total_files = models.IntegerField(default=0)
    processed_files = models.IntegerField(default=0)
    status = models.CharField(
        max_length=20, default="processing"
    )  # processing, completed, error
    errors = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return f"Lote {self.id} - {self.status} ({self.processed_files}/{self.total_files})"  # noqa: E501
