from django.db import models


class ERPSyncLog(models.Model):
    """
    Registro de cada execução de sincronização com a API ERP.

    Análogo ao ImportBatch (apps/imports), mas para sincronizações via API.
    Exibido na tela de ingestão junto com os lotes de arquivo.
    """

    class StatusChoices(models.TextChoices):
        RUNNING = "running", "Executando"
        SUCCESS = "success", "Concluído"
        ERROR = "error", "Erro"
        PARTIAL = "partial", "Parcial (com erros)"

    sync_date = models.DateField(
        verbose_name="Data Sincronizada",
        help_text="Data dos pedidos consultados na API.",
    )
    branch_ids = models.CharField(
        max_length=50,
        verbose_name="Filiais",
        help_text="IDs das filiais consultadas (ex: 27,19).",
    )
    orders_fetched = models.IntegerField(
        default=0, verbose_name="Pedidos Recebidos"
    )
    orders_created = models.IntegerField(
        default=0, verbose_name="Pedidos Criados"
    )
    orders_updated = models.IntegerField(
        default=0, verbose_name="Pedidos Atualizados"
    )
    orders_errors = models.IntegerField(
        default=0, verbose_name="Erros"
    )
    status = models.CharField(
        max_length=10,
        choices=StatusChoices.choices,
        default=StatusChoices.RUNNING,
        verbose_name="Status",
    )
    error_detail = models.TextField(
        blank=True,
        verbose_name="Detalhe do Erro",
    )
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name="Iniciado em"
    )
    finished_at = models.DateTimeField(
        null=True, blank=True, verbose_name="Finalizado em"
    )

    class Meta:
        db_table = "erp_sync_logs"
        verbose_name = "Log de Sincronização ERP"
        verbose_name_plural = "Logs de Sincronização ERP"
        ordering = ["-created_at"]

    def __str__(self):
        return (
            f"Sync {self.sync_date} — {self.get_status_display()} "
            f"({self.orders_fetched} pedidos)"
        )
