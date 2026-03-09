from django.db import models


# Create your models here.
class Product(models.Model):
    description = models.CharField(max_length=100)
    sku_code = models.CharField(max_length=50, verbose_name="Código SKU")
    price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "produtos"
        verbose_name = "Produto"
        verbose_name_plural = "Produtos"

    def __str__(self):
        return self.sku_code + " - " + self.description
