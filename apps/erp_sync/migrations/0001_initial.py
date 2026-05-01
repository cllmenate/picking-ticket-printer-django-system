from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="ERPSyncLog",
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
                    "sync_date",
                    models.DateField(
                        help_text="Data dos pedidos consultados na API.",
                        verbose_name="Data Sincronizada",
                    ),
                ),
                (
                    "branch_ids",
                    models.CharField(
                        help_text="IDs das filiais consultadas (ex: 27,19).",
                        max_length=50,
                        verbose_name="Filiais",
                    ),
                ),
                (
                    "orders_fetched",
                    models.IntegerField(
                        default=0, verbose_name="Pedidos Recebidos"
                    ),
                ),
                (
                    "orders_created",
                    models.IntegerField(
                        default=0, verbose_name="Pedidos Criados"
                    ),
                ),
                (
                    "orders_updated",
                    models.IntegerField(
                        default=0, verbose_name="Pedidos Atualizados"
                    ),
                ),
                (
                    "orders_errors",
                    models.IntegerField(default=0, verbose_name="Erros"),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("running", "Executando"),
                            ("success", "Concluído"),
                            ("error", "Erro"),
                            ("partial", "Parcial (com erros)"),
                        ],
                        default="running",
                        max_length=10,
                        verbose_name="Status",
                    ),
                ),
                (
                    "error_detail",
                    models.TextField(blank=True, verbose_name="Detalhe do Erro"),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True, verbose_name="Iniciado em"
                    ),
                ),
                (
                    "finished_at",
                    models.DateTimeField(
                        blank=True, null=True, verbose_name="Finalizado em"
                    ),
                ),
            ],
            options={
                "verbose_name": "Log de Sincronização ERP",
                "verbose_name_plural": "Logs de Sincronização ERP",
                "db_table": "erp_sync_logs",
                "ordering": ["-created_at"],
            },
        ),
    ]
