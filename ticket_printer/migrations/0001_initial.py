import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Pedido",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("picking", models.CharField(max_length=20)),
                ("numero_pedido", models.CharField(max_length=30)),
                ("rota", models.CharField(blank=True, max_length=50, null=True)),
                ("cliente_nome", models.TextField(blank=True, null=True)),
                ("endereco_logradouro", models.TextField(blank=True, null=True)),
                ("endereco_numero", models.TextField(blank=True, null=True)),
                ("endereco_bairro", models.TextField(blank=True, null=True)),
                ("endereco_cidade", models.TextField(blank=True, null=True)),
                ("endereco_uf", models.CharField(blank=True, max_length=2, null=True)),
                (
                    "endereco_cep",
                    models.CharField(blank=True, max_length=15, null=True),
                ),
                (
                    "criado_em",
                    models.DateTimeField(default=django.utils.timezone.now),
                ),
            ],
            options={
                "db_table": "pedidos",
            },
        ),
        migrations.CreateModel(
            name="PedidoItem",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "codigo_produto",
                    models.CharField(blank=True, max_length=50, null=True),
                ),
                ("descricao", models.TextField(blank=True, null=True)),
                (
                    "quantidade",
                    models.DecimalField(decimal_places=3, default=0, max_digits=18),
                ),
                ("unidade", models.CharField(blank=True, max_length=20, null=True)),
                ("linha_origem", models.IntegerField(blank=True, null=True)),
                (
                    "pedido",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="itens",
                        to="ticket_printer.pedido",
                    ),
                ),
            ],
            options={
                "db_table": "pedido_itens",
            },
        ),
        migrations.CreateModel(
            name="PedidoVolume",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("volume_num", models.IntegerField()),
                ("total_volumes", models.IntegerField()),
                (
                    "criado_em",
                    models.DateTimeField(default=django.utils.timezone.now),
                ),
                (
                    "pedido",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="volumes",
                        to="ticket_printer.pedido",
                    ),
                ),
            ],
            options={
                "db_table": "pedido_volumes",
            },
        ),
        migrations.CreateModel(
            name="VolumeItem",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "quantidade",
                    models.DecimalField(decimal_places=3, default=0, max_digits=18),
                ),
                (
                    "item",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="ticket_printer.pedidoitem",
                    ),
                ),
                (
                    "volume",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="itens_rateados",
                        to="ticket_printer.pedidovolume",
                    ),
                ),
            ],
            options={
                "db_table": "volume_itens",
            },
        ),
        migrations.AddConstraint(
            model_name="pedido",
            constraint=models.UniqueConstraint(
                fields=("picking", "numero_pedido"), name="pedidos_picking_numero_pedido_key"
            ),
        ),
        migrations.AddIndex(
            model_name="pedido",
            index=models.Index(fields=["picking"], name="ix_pedidos_picking"),
        ),
        migrations.AddIndex(
            model_name="pedido",
            index=models.Index(fields=["numero_pedido"], name="ix_pedidos_pedido"),
        ),
        migrations.AddConstraint(
            model_name="pedidoitem",
            constraint=models.UniqueConstraint(
                fields=("pedido", "codigo_produto", "descricao", "linha_origem"),
                name="pedido_itens_pedido_id_codigo_produto_descricao_linha_orige_key",
            ),
        ),
        migrations.AddIndex(
            model_name="pedidoitem",
            index=models.Index(fields=["pedido"], name="ix_itens_pedido"),
        ),
        migrations.AddConstraint(
            model_name="pedidovolume",
            constraint=models.UniqueConstraint(
                fields=("pedido", "volume_num"), name="pedido_volumes_pedido_id_volume_num_key"
            ),
        ),
        migrations.AddIndex(
            model_name="pedidovolume",
            index=models.Index(fields=["pedido"], name="ix_volumes_pedido"),
        ),
        migrations.AddConstraint(
            model_name="volumeitem",
            constraint=models.UniqueConstraint(
                fields=("volume", "item"), name="volume_itens_volume_id_item_id_key"
            ),
        ),
        migrations.AddIndex(
            model_name="volumeitem",
            index=models.Index(fields=["volume"], name="ix_volume_itens_volume"),
        ),
    ]
