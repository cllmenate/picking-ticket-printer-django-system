from django.apps import AppConfig


class TicketPrinterConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.ticket_printer"
    verbose_name = "Impressão de Etiquetas"
