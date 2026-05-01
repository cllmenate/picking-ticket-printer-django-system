"""
Celery tasks para sincronização periódica com a API ERP.

Task principal:
    sync_erp_orders_task()
    - Busca pedidos do dia corrente para todas as filiais configuradas
    - Salva/atualiza os dados no banco via ERPOrderImporter
    - Registra o resultado em ERPSyncLog
    - Roda a cada ERP_SYNC_INTERVAL_MINUTES minutos (padrão: 10)

O agendamento é configurado em core/settings.py via CELERY_BEAT_SCHEDULE.
"""

import logging
from datetime import date, datetime, timezone

from celery import shared_task
from django.conf import settings

from apps.erp_sync.services.erp_importer import ERPOrderImporter
from apps.erp_sync.services.order_service import ERPOrderService

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    name="erp_sync.sync_erp_orders",
    max_retries=3,
    default_retry_delay=60,  # espera 60s antes de cada retry
    acks_late=True,
)
def sync_erp_orders_task(self, manual_log_id: int | None = None):  # type: ignore[override]
    """
    Sincroniza os pedidos do dia atual com a API ERP.

    Busca pedidos para cada filial em ERP_BRANCH_IDS (padrão: RJ=27, ES=19),
    insere novos e atualiza os existentes no banco de dados.
    Registra o resultado em ERPSyncLog para auditoria.

    Args:
        manual_log_id: quando disparada manualmente via botão Resync, recebe
                       o ID do log já criado pela view; caso contrário (Beat),
                       cria um novo log.
    """
    # Import aqui para evitar circular import no carregamento do Celery
    from apps.erp_sync.models import ERPSyncLog

    today = date.today()
    today_str = today.strftime("%Y-%m-%d")
    branch_ids: list[int] = getattr(settings, "ERP_BRANCH_IDS", [27, 19])
    branch_ids_str = ",".join(str(b) for b in branch_ids)

    logger.info(
        "ERP Sync: iniciando sincronização para data=%s filiais=%s (manual=%s)",
        today_str,
        branch_ids,
        manual_log_id is not None,
    )

    # Reutiliza o log criado pela view (resync manual) ou cria um novo (Beat)
    if manual_log_id:
        try:
            sync_log = ERPSyncLog.objects.get(id=manual_log_id)
            sync_log.status = ERPSyncLog.StatusChoices.RUNNING
            sync_log.save(update_fields=["status"])
        except ERPSyncLog.DoesNotExist:
            sync_log = ERPSyncLog.objects.create(
                sync_date=today,
                branch_ids=branch_ids_str,
                status=ERPSyncLog.StatusChoices.RUNNING,
            )
    else:
        sync_log = ERPSyncLog.objects.create(
            sync_date=today,
            branch_ids=branch_ids_str,
            status=ERPSyncLog.StatusChoices.RUNNING,
        )

    try:
        orders = ERPOrderService.fetch_orders_for_all_branches(today_str)
    except Exception as exc:
        logger.exception("ERP Sync: falha ao buscar pedidos da API: %s", exc)
        sync_log.status = ERPSyncLog.StatusChoices.ERROR
        sync_log.error_detail = str(exc)
        sync_log.finished_at = datetime.now(timezone.utc)
        sync_log.save(update_fields=["status", "error_detail", "finished_at"])
        raise self.retry(exc=exc)

    if not orders:
        logger.info("ERP Sync: nenhum pedido retornado para %s.", today_str)
        sync_log.status = ERPSyncLog.StatusChoices.SUCCESS
        sync_log.orders_fetched = 0
        sync_log.finished_at = datetime.now(timezone.utc)
        sync_log.save(
            update_fields=[
                "status", "orders_fetched", "finished_at"
            ]
        )
        return {"status": "ok", "orders_fetched": 0}

    importer = ERPOrderImporter()
    stats = importer.import_orders(orders)

    # Determina o status final
    if stats["errors"] == 0:
        final_status = ERPSyncLog.StatusChoices.SUCCESS
    elif stats["errors"] < len(orders):
        final_status = ERPSyncLog.StatusChoices.PARTIAL
    else:
        final_status = ERPSyncLog.StatusChoices.ERROR

    sync_log.status = final_status
    sync_log.orders_fetched = len(orders)
    sync_log.orders_created = stats["created"]
    sync_log.orders_updated = stats["updated"]
    sync_log.orders_errors = stats["errors"]
    sync_log.finished_at = datetime.now(timezone.utc)
    sync_log.save(
        update_fields=[
            "status",
            "orders_fetched",
            "orders_created",
            "orders_updated",
            "orders_errors",
            "finished_at",
        ]
    )

    logger.info(
        "ERP Sync: concluído — data=%s pedidos=%d criados=%d atualizados=%d erros=%d",
        today_str,
        len(orders),
        stats["created"],
        stats["updated"],
        stats["errors"],
    )
    return {
        "status": "ok",
        "date": today_str,
        "orders_fetched": len(orders),
        **stats,
    }
