from django.db import models

from apps.addresses.models import Address


# Create your models here.
class Customer(models.Model):
    code = models.CharField(max_length=100)
    name = models.CharField(max_length=100)
    id_number = models.CharField(max_length=20)
    phone = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name="Telefone",
    )
    address = models.ForeignKey(
        Address,
        on_delete=models.CASCADE,
        related_name="customers",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"

    def __str__(self):
        return self.name
