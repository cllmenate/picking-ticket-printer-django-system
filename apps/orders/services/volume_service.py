import logging

from apps.orders.models import Order
from apps.ticket_printer.services.zpl_service import ZPLGenerator

logger = logging.getLogger(__name__)


class VolumeService:
    """
    Serviço responsável por confirmar volumes e gerar ZPL para impressão.

    O campo `total_volumes` é persistido no Order para consulta em relatórios.
    """

    @staticmethod
    def confirm_volumes(order: Order, total_volumes: int) -> None:
        """
        Confirma a quantidade de volumes de um pedido sem gerar ZPL.
        Status: pending → confirmed.
        """
        order.total_volumes = total_volumes
        order.status = Order.StatusChoices.CONFIRMED
        order.save(update_fields=["total_volumes", "status", "updated_at"])

    @staticmethod
    def process_and_print(order: Order, total_volumes: int) -> list[str]:
        """
        Gera os comandos ZPL para todos os volumes de um pedido e marca
        o pedido como 'in_progress' (em processo de impressão).

        O status final (shipped / failed) é confirmado pelo cliente
        via endpoint separado após o QZ Tray terminar.

        Returns:
            Lista de strings ZPL, uma por volume.
        """
        zpl_commands: list[str] = []
        for i in range(1, total_volumes + 1):
            zpl = ZPLGenerator.generate_label(order, i, total_volumes)
            zpl_commands.append(zpl)

        order.total_volumes = total_volumes
        order.status = Order.StatusChoices.IN_PROGRESS
        order.save(update_fields=["total_volumes", "status", "updated_at"])

        logger.info(
            "Order %s ZPL generated (%d volumes), status=in_progress.",
            order.order_number,
            total_volumes,
        )
        return zpl_commands

    @staticmethod
    def mark_shipped(order: Order) -> None:
        """Confirma que a impressão foi concluída com sucesso."""
        order.status = Order.StatusChoices.SHIPPED
        order.save(update_fields=["status", "updated_at"])
        logger.info("Order %s marked as shipped.", order.order_number)

    @staticmethod
    def mark_failed(order: Order) -> None:
        """Registra falha na impressão. Retorna status para 'failed'."""
        order.status = Order.StatusChoices.FAILED
        order.save(update_fields=["status", "updated_at"])
        logger.warning("Order %s marked as failed.", order.order_number)
