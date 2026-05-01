"""
ERPOrderService — consulta o endpoint de pedidos da API ERP.

Endpoint: GET /api/Avance/PrenoteOrder
Parâmetros utilizados:
  - relationalBranchId : ID da filial (RJ=27, ES=19)
  - beginDate          : data de início no formato YYYY-MM-DD
  - endDate            : data de fim no formato YYYY-MM-DD
  - dateType           : 1 = pedido | 2 = prenota  (sempre usamos 1)
"""

import logging

import requests
from django.conf import settings

from apps.erp_sync.services.auth_service import ERPAuthService

logger = logging.getLogger(__name__)

DATE_TYPE_ORDER = 1  # Pedido (não prenota)


class ERPOrderService:
    """
    Serviço stateless para buscar pedidos da API ERP.
    Em caso de 401, invalida o cache e tenta novamente com novo login.
    """

    @classmethod
    def _base_url(cls) -> str:
        return getattr(settings, "ERP_API_BASE_URL", "http://187.117.44.93:55050")

    @classmethod
    def fetch_orders(cls, branch_id: int, date_str: str) -> list[dict]:
        """
        Busca pedidos de uma filial para a data informada.

        Args:
            branch_id : relationalBranchId (ex: 27 para RJ, 19 para ES)
            date_str  : data no formato "YYYY-MM-DD"

        Returns:
            Lista de dicts conforme o JSON da API.
        """
        url = f"{cls._base_url()}/api/Avance/PrenoteOrder"
        params = {
            "relationalBranchId": branch_id,
            "beginDate": date_str,
            "endDate": date_str,
            "dateType": DATE_TYPE_ORDER,
        }

        token = ERPAuthService.get_valid_token()
        headers = {
            "accept": "text/plain",
            "Authorization": f"Bearer {token}",
        }

        logger.info(
            "ERP Orders: buscando filial=%s data=%s...", branch_id, date_str
        )

        try:
            resp = requests.get(url, params=params, headers=headers, timeout=60)

            # Token expirado inesperadamente → invalida cache e retenta
            if resp.status_code == 401:
                logger.warning(
                    "ERP Orders: 401 na filial=%s — invalidando cache e "
                    "retentando login.",
                    branch_id,
                )
                ERPAuthService.invalidate_cache()
                token = ERPAuthService.get_valid_token()
                headers["Authorization"] = f"Bearer {token}"
                resp = requests.get(url, params=params, headers=headers, timeout=60)

            resp.raise_for_status()

        except requests.RequestException as exc:
            logger.error(
                "ERP Orders: erro de rede ao buscar filial=%s data=%s: %s",
                branch_id,
                date_str,
                exc,
            )
            return []

        try:
            data = resp.json()
        except ValueError:
            logger.error(
                "ERP Orders: resposta inválida (não-JSON) para filial=%s data=%s",
                branch_id,
                date_str,
            )
            return []

        if not isinstance(data, list):
            logger.warning(
                "ERP Orders: resposta inesperada (não é lista) para filial=%s: %r",
                branch_id,
                data,
            )
            return []

        logger.info(
            "ERP Orders: %d pedido(s) recebido(s) — filial=%s data=%s",
            len(data),
            branch_id,
            date_str,
        )
        return data

    @classmethod
    def fetch_orders_for_all_branches(cls, date_str: str) -> list[dict]:
        """
        Busca pedidos de todas as filiais configuradas em ERP_BRANCH_IDS.

        Args:
            date_str : data no formato "YYYY-MM-DD"

        Returns:
            Lista consolidada de todos os pedidos de todas as filiais.
        """
        branch_ids: list[int] = getattr(settings, "ERP_BRANCH_IDS", [27, 19])
        all_orders: list[dict] = []

        for branch_id in branch_ids:
            orders = cls.fetch_orders(branch_id, date_str)
            all_orders.extend(orders)

        return all_orders
