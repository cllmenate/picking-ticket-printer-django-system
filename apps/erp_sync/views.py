"""
Views da app erp_sync.

ERPSyncTriggerView  — POST: dispara a task de sincronização manualmente
                      Retorna {log_id} para polling de status.

ERPSyncStatusView   — GET: retorna o status atual de um ERPSyncLog pelo ID.
                      Usado pelo frontend para fazer polling e atualizar o botão.
"""

import logging

from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.erp_sync.models import ERPSyncLog

logger = logging.getLogger(__name__)


class ERPSyncTriggerView(LoginRequiredMixin, APIView):
    """
    POST /api/v1/erp-sync/trigger/

    Dispara a sincronização ERP imediatamente (para uso manual via botão).
    Cria um ERPSyncLog com status 'running' e enfileira a Celery task.

    Permissão: usuário logado (mesma permissão da tela de ingestão).
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        from datetime import date

        from django.conf import settings

        from apps.erp_sync.tasks import sync_erp_orders_task

        # request.data é o body já parseado pelo DRF (funciona com JSON e form-data)
        raw_date = (request.data.get("date") or "").strip()
        if raw_date:
            try:
                target_date = date.fromisoformat(raw_date)
            except ValueError:
                return Response(
                    {"error": f"Data inválida: '{raw_date}'. Use o formato YYYY-MM-DD."},
                    status=400,
                )
        else:
            target_date = date.today()

        branch_ids = getattr(settings, "ERP_BRANCH_IDS", [27, 19])
        branch_ids_str = ",".join(str(b) for b in branch_ids)

        log = ERPSyncLog.objects.create(
            sync_date=target_date,
            branch_ids=branch_ids_str,
            status=ERPSyncLog.StatusChoices.RUNNING,
        )

        sync_erp_orders_task.apply_async(kwargs={
            "manual_log_id": log.id,
            "sync_date": target_date.strftime("%Y-%m-%d"),
        })

        logger.info(
            "ERP Sync: manual pelo usuário %s — data=%s log_id=%s",
            request.user,
            target_date,
            log.id,
        )

        return Response({
            "status": "queued",
            "log_id": log.id,
            "sync_date": target_date.strftime("%d/%m/%Y"),
            "message": f"Sincronização de {target_date.strftime('%d/%m/%Y')} iniciada.",
        }, status=202)



class ERPSyncStatusView(APIView):
    """
    GET /api/v1/erp-sync/status/<log_id>/

    Retorna o status atual de um ERPSyncLog.
    Usado pelo frontend para fazer polling após disparar o trigger.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, log_id, *args, **kwargs):
        try:
            log = ERPSyncLog.objects.get(id=log_id)
        except ERPSyncLog.DoesNotExist:
            return Response({"error": "Log não encontrado."}, status=404)

        return Response({
            "log_id": log.id,
            "status": log.status,
            "status_display": log.get_status_display(),
            "sync_date": log.sync_date.strftime("%d/%m/%Y"),
            "branch_ids": log.branch_ids,
            "orders_fetched": log.orders_fetched,
            "orders_created": log.orders_created,
            "orders_updated": log.orders_updated,
            "orders_errors": log.orders_errors,
            "error_detail": log.error_detail,
            "created_at": log.created_at.strftime("%d/%m/%Y %H:%M:%S"),
            "finished_at": (
                log.finished_at.strftime("%d/%m/%Y %H:%M:%S")
                if log.finished_at else None
            ),
            "is_done": log.status in (
                ERPSyncLog.StatusChoices.SUCCESS,
                ERPSyncLog.StatusChoices.ERROR,
                ERPSyncLog.StatusChoices.PARTIAL,
            ),
        })
