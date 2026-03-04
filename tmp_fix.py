import os
import re

base_path = r"c:\Users\sm70p\OneDrive\Documents\Projects\AVANCE\WEB\picking-ticket-printer-django-system\ticket_printer\migrations"
in_path = os.path.join(base_path, "init.sql")

with open(in_path, "r", encoding="utf-8") as f:
    lines = f.read().splitlines()

statements = []
in_copy = False
table = ""
cols = ""
for line in lines:
    if line.startswith("COPY "):
        in_copy = True
        table = line.split(" ")[1]
        cols = line[line.find("("):line.find(")")+1]
        continue
    if in_copy:
        if line == "\\.":
            in_copy = False
            continue
        vals = line.split("\t")
        def format_val(v):
            if v == "\\N" or v == "": return "NULL"
            v = v.replace("'", "''")
            return f"'{v}'"
        formatted_vals = ", ".join(format_val(v) for v in vals)
        statements.append(f"INSERT INTO {table} {cols} VALUES ({formatted_vals});")
        continue

    if line.startswith("SELECT pg_catalog.setval"):
        statements.append(line)

with open(in_path, "w", encoding="utf-8") as f:
    f.write("-- Seed data inserts\n")
    f.write("\n".join(statements) + "\n")

print(f"Rewrote init.sql to {len(statements)} statements.")
