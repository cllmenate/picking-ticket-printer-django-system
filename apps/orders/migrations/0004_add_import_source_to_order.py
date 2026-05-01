from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("orders", "0003_refactor_order_route"),
    ]

    operations = [
        migrations.AddField(
            model_name="order",
            name="import_source",
            field=models.CharField(
                choices=[
                    ("xlsx", "Planilha (XLSX/XLS/PDF)"),
                    ("api", "API ERP"),
                ],
                db_index=True,
                default="xlsx",
                max_length=10,
                verbose_name="Origem da Importação",
            ),
        ),
    ]
