import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from apps.imports.services.file_processors import ExcelProcessor, PDFProcessor
from apps.imports.services.db_importer import DatabaseImporter


def run():
    print("Testing XLS import...")
    try:
        xls_data = ExcelProcessor().read("data/0442739.xls")
        order = DatabaseImporter.save_complete_order(xls_data)
        print(
            f"Success! Saved Order {order.order_number} with {order.items.count()} items."
        )
        print(
            f"Customer: {order.customer.code} - {order.customer.name}, Phone: {order.customer.phone}"
        )
        print(f"Delivery: {order.delivery}")
        print(
            f"Total Price: {order.total_price}, Type Date: {order.typing_date}, Weight: {order.net_weight}"
        )
    except Exception as e:
        print(f"Failed XLS: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    run()
