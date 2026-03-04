"""
Adds cliente_codigo column to pedidos and backfills it by splitting the
existing cliente_nome field.

Pattern: "{codigo}  -  {rest of name}"
Example: "28010  -  FARM REAL DE TRINDADE LTDA  -  INDEPENDENTE"
  → cliente_codigo = "28010"
  → cliente_nome   = "FARM REAL DE TRINDADE LTDA  -  INDEPENDENTE"
"""
import re

from django.db import migrations, models


def split_cliente_nome(apps, schema_editor):
    """
    Parses every pedido's cliente_nome and extracts the leading numeric code.
    Updates cliente_codigo and strips the code from cliente_nome.
    """
    Pedido = apps.get_model("ticket_printer", "Pedido")
    # Pattern: optional leading digits, then "  -  " separator
    pattern = re.compile(r"^(\d+)\s+-\s+(.+)$", re.DOTALL)

    to_update = []
    for pedido in Pedido.objects.all():
        if not pedido.cliente_nome:
            continue
        m = pattern.match(pedido.cliente_nome.strip())
        if m:
            pedido.cliente_codigo = m.group(1).strip()
            pedido.cliente_nome = m.group(2).strip()
            to_update.append(pedido)

    if to_update:
        Pedido.objects.bulk_update(to_update, ["cliente_codigo", "cliente_nome"])


def reverse_split(apps, schema_editor):
    """Re-concatenates cliente_codigo back into cliente_nome."""
    Pedido = apps.get_model("ticket_printer", "Pedido")
    to_update = []
    for pedido in Pedido.objects.all():
        if pedido.cliente_codigo and pedido.cliente_nome:
            pedido.cliente_nome = f"{pedido.cliente_codigo}  -  {pedido.cliente_nome}"
            pedido.cliente_codigo = None
            to_update.append(pedido)
    if to_update:
        Pedido.objects.bulk_update(to_update, ["cliente_codigo", "cliente_nome"])


class Migration(migrations.Migration):

    dependencies = [
        ("ticket_printer", "0003_pedido_cliente_cnpj"),
    ]

    operations = [
        migrations.AddField(
            model_name="pedido",
            name="cliente_codigo",
            field=models.CharField(blank=True, max_length=30, null=True),
        ),
        migrations.RunPython(split_cliente_nome, reverse_code=reverse_split),
    ]
