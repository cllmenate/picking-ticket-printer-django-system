"""
Adds cpf_cnpj column to pedidos and backfills data from init.sql.

The seed migration (0002) could not populate cpf_cnpj because the column
did not exist yet. This migration adds the column and then reads the same
init.sql to update each row with the correct value.
"""
import os
import re

from django.db import migrations, models


def _extract_cpf_cnpj_map(sql_path):
    """
    Parses init.sql and returns a dict of {pedido_id: cpf_cnpj} from the
    COPY public.pedidos (...) FROM stdin block.
    """
    with open(sql_path, encoding="utf-8") as f:
        sql_text = f.read()

    pattern = re.compile(
        r"COPY\s+\S*pedidos\S*\s*\(([^)]+)\)\s+FROM\s+stdin\s*;\n(.*?)\n\\\.(?:\n|$)",
        re.IGNORECASE | re.DOTALL,
    )
    m = pattern.search(sql_text)
    if not m:
        return {}

    columns = [c.strip() for c in m.group(1).split(",")]
    data_lines = [line for line in m.group(2).splitlines() if line.strip()]

    try:
        id_idx = columns.index("id")
        cnpj_idx = columns.index("cpf_cnpj")
    except ValueError:
        return {}

    result = {}
    for line in data_lines:
        parts = line.split("\t")
        if len(parts) > max(id_idx, cnpj_idx):
            row_id = int(parts[id_idx])
            cpf_cnpj = parts[cnpj_idx] if parts[cnpj_idx] != "\\N" else None
            result[row_id] = cpf_cnpj
    return result


def backfill_cpf_cnpj(apps, schema_editor):
    sql_path = os.path.join(os.path.dirname(__file__), "init.sql")
    cnpj_map = _extract_cpf_cnpj_map(sql_path)
    if not cnpj_map:
        return

    with schema_editor.connection.cursor() as cursor:
        for pedido_id, cpf_cnpj in cnpj_map.items():
            if cpf_cnpj:
                cursor.execute(
                    "UPDATE pedidos SET cpf_cnpj = %s WHERE id = %s",
                    [cpf_cnpj, pedido_id],
                )


class Migration(migrations.Migration):

    dependencies = [
        ("ticket_printer", "0002_seed_data"),
    ]

    operations = [
        migrations.AddField(
            model_name="pedido",
            name="cpf_cnpj",
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.RunPython(backfill_cpf_cnpj, reverse_code=migrations.RunPython.noop),
    ]
