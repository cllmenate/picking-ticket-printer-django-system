from abc import ABC, abstractmethod
from decimal import Decimal, InvalidOperation
from typing import Any

import docx
import pandas as pd
import pdfplumber


class ProcessingError(Exception):
    pass


class FileProcessor(ABC):
    @abstractmethod
    def read(self, path: Any) -> dict[str, Any]:
        """Reads a file and returns the standardized order data dictionary."""
        pass


class ExcelProcessor(FileProcessor):
    def read(self, path: Any) -> dict[str, Any]:
        try:
            xl = pd.ExcelFile(path)
        except Exception as e:
            msg = f"Could not read the Excel file: {e}"
            raise ProcessingError(msg) from e

        header_df = None
        for sheet_name in xl.sheet_names:
            df = xl.parse(sheet_name, header=None)
            if (
                self._df_contains(df, "DADOS DO PEDIDO")
                or self._df_contains(df, "DADOS")
                or self._df_contains(df, "PEDIDO")
            ):
                header_df = df
                break

        if header_df is None:
            header_df = xl.parse(xl.sheet_names[0], header=None)

        order_data = self._extract_order_data(header_df)

        products = self._extract_products(header_df)
        if products:
            order_data["products"] = products
        else:
            for sheet_name in xl.sheet_names:
                df = xl.parse(sheet_name, header=None)
                products = self._extract_products(df)
                if products:
                    order_data["products"] = products
                    break

        xl.close()
        return order_data

    def _extract_order_data(self, header_df: pd.DataFrame) -> dict[str, Any]:
        cliente_full = (self._find_after(header_df, "Cliente") or "").strip()
        customer_code = (
            self._find_after(header_df, "Cód. Cliente")
            or self._find_after(header_df, "Cod. Cliente")
            or ""
        ).strip()
        customer_name = cliente_full

        if not customer_code and " - " in cliente_full:
            parts = cliente_full.split(" - ", 1)
            customer_code = parts[0].strip()
            customer_name = parts[1].strip()

        return {
            "order_number": self._normalize_digits(
                self._find_after(header_df, "Nº")
                or self._find_after(header_df, "Nr")
                or ""
            ),
            "picking": self._normalize_digits(
                self._find_after(header_df, "Picking") or ""
            ),
            "route": (self._find_after(header_df, "Rota") or "").strip(),
            "customer_code": customer_code,
            "customer_name": customer_name,
            "address_street": (
                self._find_after(header_df, "Endereço")
                or self._find_after(header_df, "Endereco")
                or ""
            ).strip(),
            "address_number": "",
            "address_district": (
                self._find_after(header_df, "Bairro")
                or self._find_after(header_df, "Bairro")
                or ""
            ).strip(),
            "address_state": (
                self._find_after(header_df, "Estado")
                or self._find_after(header_df, "Estado")
                or ""
            ).strip(),
            "address_city": (
                self._find_after(header_df, "Cidade") or ""
            ).strip(),
            "address_zip_code": (
                self._find_after(header_df, "Cep")
                or self._find_after(header_df, "CEP")
                or ""
            ).strip(),
            "id_number": (
                self._find_after(header_df, "CPF/CNPJ")
                or self._find_after(header_df, "CPF/CNPJ")
                or ""
            ).strip(),
            "total_volumes": self._try_parse_int(
                self._find_after(header_df, "Volumes")
            ),
            "typing_date": self._find_after(header_df, "Digitação"),
            "release_date": self._find_after(header_df, "Liberação"),
            "pre_invoice_date": self._find_after(header_df, "Pré - Nota"),
            "invoice_number": self._find_after(header_df, "NF"),
            "scheduled_date": self._find_after(header_df, "Data Programada"),
            "condition": self._find_after(header_df, "Condição"),
            "operation": self._find_after(header_df, "Operação"),
            "origin": self._find_after(header_df, "Origem"),
            "typist": self._find_after(header_df, "Digitador"),
            "salesperson": self._find_after(header_df, "Vendedor"),
            "releaser": self._find_after(header_df, "Liberador"),
            "situation": self._find_after(header_df, "Situação"),
            "pending_payment": self._find_after(header_df, "Pendência"),
            "net_weight": self._find_after(header_df, "Peso Líquido"),
            "phone": self._find_after(header_df, "Telefone"),
            "customer_reference": self._find_after(header_df, "Ref."),
            "products": [],
        }

    def _df_contains(self, df: pd.DataFrame, needle: str) -> bool:
        needle = needle.strip().lower()
        for col in df.columns:
            mask = (
                df[col].astype(str).str.lower().str.contains(needle, na=False)
            )
            if mask.any():
                return True
        return False

    def _get_str(self, df: pd.DataFrame, r: int, c: int) -> str:
        if 0 <= r < len(df.index) and 0 <= c < len(df.columns):
            val = df.iat[r, c]
            if pd.isna(val):
                return ""
            return str(val)
        return ""

    def _find_after(self, df: pd.DataFrame, label: str) -> str | None:
        lbl = label.strip().lower()
        rows, cols = df.shape
        for r in range(rows):
            for c in range(cols):
                res = self._check_cell_for_label(df, r, c, lbl, cols)
                if res:
                    return res
        return None

    def _check_cell_for_label(
        self, df: pd.DataFrame, r: int, c: int, lbl: str, cols: int
    ) -> str | None:
        raw = self._get_str(df, r, c)
        if not raw or not raw.strip():
            return None

        s = raw.strip()
        low = s.lower()

        if (lbl in ("nº", "nr")) and "nº" in low and ":" in low:
            return self._extract_after_colon(s)

        if self._matches_label(low, lbl):
            after = self._extract_after_colon(s)
            if after:
                return after

            return self._search_adjacent_cells(df, r, c, cols)

        return None

    def _matches_label(self, low: str, lbl: str) -> bool:
        return (
            low.startswith(lbl)
            or (lbl + ":") in low
            or (lbl + " :") in low
            or low == lbl
        )

    def _extract_after_colon(self, s: str) -> str | None:
        idx = s.find(":")
        if 0 <= idx < len(s) - 1:
            after = s[idx + 1 :].strip()
            if after:
                return after
        return None

    def _search_adjacent_cells(
        self, df: pd.DataFrame, r: int, c: int, cols: int
    ) -> str | None:
        for i in range(1, 21):
            if c + i >= cols:
                break
            v = self._get_str(df, r, c + i).strip()
            if v:
                return v
        return None

    def _extract_products(self, df: pd.DataFrame) -> list[dict[str, Any]]:
        header_row, col_cod, col_desc, col_qtd, col_preco = (
            self._find_items_header(df)
        )
        if header_row < 0:
            return []

        items = []
        rows, _ = df.shape
        for r in range(header_row + 1, rows):
            product_code = self._get_str(df, r, col_cod).strip()
            description = self._get_str(df, r, col_desc).strip()
            quantity_str = self._get_str(df, r, col_qtd).strip()

            if not product_code and not description:
                break
            if not description:
                continue

            items.append({
                "product_code": product_code if product_code else None,
                "description": description,
                "quantity": self._try_parse_decimal(quantity_str),
                "price": self._try_parse_decimal(
                    self._get_str(df, r, col_preco).strip()
                )
                if col_preco != -1
                else Decimal("0"),
                "unit": "",
                "source_line": r + 1,
            })
        return items

    def _find_items_header(self, df: pd.DataFrame):
        rows, cols = df.shape
        for r in range(rows):
            header_info = self._analyze_header_row(df, r, cols)
            if header_info:
                return header_info
        return -1, -1, -1, -1, -1

    def _analyze_header_row(self, df: pd.DataFrame, r: int, cols: int):
        col_cod, col_desc, col_qtd, col_preco = -1, -1, -1, -1
        for c in range(cols):
            s = self._get_str(df, r, c).strip().lower()
            if not s:
                continue
            if col_cod == -1 and self._is_code_column(s):
                col_cod = c
            if col_desc == -1 and self._is_desc_column(s):
                col_desc = c
            if col_qtd == -1 and self._is_qtd_column(s):
                col_qtd = c
            if col_preco == -1 and self._is_price_column(s):
                col_preco = c
        if col_cod != -1 and col_desc != -1 and col_qtd != -1:
            return r, col_cod, col_desc, col_qtd, col_preco
        return None

    def _is_code_column(self, s: str) -> bool:
        return "cód" in s or "codigo" in s or s == "cod" or "cod." in s

    def _is_desc_column(self, s: str) -> bool:
        return (
            "descr" in s
            or "descricao" in s
            or "descrição" in s
            or "produto" in s
        )

    def _is_qtd_column(self, s: str) -> bool:
        return s.startswith("qt") or "qtd" in s or "qtde" in s or "quant" in s

    def _is_price_column(self, s: str) -> bool:
        return "preço" in s or "preco" in s

    def _try_parse_int(self, s: str | None) -> int:
        if not s:
            return 0
        try:
            return int(float(s.strip()))
        except ValueError:
            return 0

    def _try_parse_decimal(self, s: str) -> Decimal:
        if not s or not s.strip():
            return Decimal("0")
        s = s.strip()
        if "," in s and "." in s:
            s = s.replace(".", "").replace(",", ".")
        elif "," in s:
            s = s.replace(",", ".")
        try:
            return Decimal(s)
        except InvalidOperation:
            return Decimal("0")

    def _normalize_digits(self, s: str) -> str:
        if not s or not s.strip():
            return ""
        digits = "".join(c for c in s if c.isdigit())
        return digits if digits else s.strip()


class PDFProcessor(FileProcessor):
    def read(self, path: Any) -> dict[str, Any]:
        """Reads PDF file and extracts basic order info.

        To be expanded based on PDF layout.
        """
        text = ""
        try:
            with pdfplumber.open(path) as pdf:
                for page in pdf.pages:
                    text += (page.extract_text() or "") + "\n"

            import re

            def extract_regex(pattern, t, default=""):
                match = re.search(pattern, t, re.IGNORECASE)
                return match.group(1).strip() if match else default

            order_data = {
                "order_number": extract_regex(r"N[º°]?:\s*([^\s]+)", text),
                "picking": extract_regex(r"Picking:\s*([^\s]+)", text),
                "route": extract_regex(r"Rota:\s*([^\n]+)", text),
                "customer_code": extract_regex(r"Cliente:\s*(\d+)", text),
                "customer_name": extract_regex(
                    r"Cliente:\s*\d+\s*-\s*([^\n]+)", text
                ),
                "address_street": extract_regex(
                    r"Endereço:\s*([^\nBairro:]+)", text
                ),
                "address_district": extract_regex(r"Bairro:\s*([^\n]+)", text),
                "address_state": extract_regex(r"Estado:\s*([A-Za-z]+)", text),
                "address_city": extract_regex(
                    r"Cidade:\s*([^\nEstado:]+)", text
                ),
                "address_zip_code": extract_regex(r"Cep:\s*([\d-]+)", text),
                "id_number": extract_regex(r"CPF/CNPJ:\s*([\d./-]+)", text),
                "phone": extract_regex(r"Telefone:\s*([\d\s-]+)", text),
                "customer_reference": extract_regex(
                    r"Ref\.:\s*([^\n]*)", text
                ),
                "total_volumes": 0,
                "typing_date": extract_regex(
                    r"Digitação:\s*([\d/]+ - [\d:]+)", text
                ),
                "release_date": extract_regex(
                    r"Liberação:\s*([\d/]+ - [\d:]+)", text
                ),
                "pre_invoice_date": extract_regex(
                    r"Pré - Nota:\s*([\d/]+ - [\d:]+)", text
                ),
                "invoice_number": extract_regex(r"NF:\s*([^\n]*)", text),
                "scheduled_date": extract_regex(
                    r"Data Programada:\s*([^\n]*)", text
                ),
                "condition": extract_regex(r"Condição:\s*([^\n]+)", text),
                "operation": extract_regex(r"Operação:\s*([^\n]+)", text),
                "origin": extract_regex(
                    r"Origem:\s*([^\n]+(?:(?:\r?\n\s+)(?!Liberador:)[^\n]+)*)",
                    text,
                )
                .split("Digitador:")[0]
                .strip(),
                "typist": extract_regex(r"Digitador:\s*([^\n]+)", text),
                "salesperson": extract_regex(r"Vendedor:\s*([^\n]+)", text),
                "releaser": extract_regex(
                    r"Liberador:\s*([^\n]+(?:(?:\r?\n\s+)(?!Volumes:)[^\n]+)*)",
                    text,
                )
                .split("Vendedor:")[0]
                .strip(),
                "situation": extract_regex(r"Situação:\s*([^\s]+)", text),
                "pending_payment": extract_regex(
                    r"Pendência:\s*([^\n]+)", text
                ),
                "net_weight": extract_regex(
                    r"Peso Líquido:\s*([\d,.]+)", text
                ),
                "carrier": extract_regex(r"Transportadora:\s*([^\n]*)", text)
                .split("Entrega:")[0]
                .strip(),
                "delivery": extract_regex(r"Entrega:\s*([^\n]*)", text)
                .split("Romaneio:")[0]
                .strip(),
                "manifest": extract_regex(r"Romaneio:\s*([^\n]*)", text),
                "vehicle": extract_regex(r"Veículo:\s*([^\n]+)", text)
                .split("Motorista:")[0]
                .strip(),
                "driver": extract_regex(r"Motorista:\s*([^\n]+)", text)
                .split("Ajudante:")[0]
                .strip(),
                "helper": extract_regex(r"Ajudante:\s*([^\n]*)", text),
                "products": [],
            }

            volumes_str = extract_regex(r"Volumes:\s*(\d+)", text)
            if volumes_str:
                order_data["total_volumes"] = int(volumes_str)

            # Basic products extraction using tabular structure if possible
            # Simplified for PDF due to OCR alignment. Recommend using XLS.

        except Exception as e:
            raise ProcessingError(f"Error processing PDF: {e}") from e
        return order_data


class DocxProcessor(FileProcessor):
    def read(self, path: Any) -> dict[str, Any]:
        """Reads Docx file and extracts basic order info."""
        order_data: dict[str, Any] = {
            "order_number": "",
            "picking": "",
            "route": "",
            "customer_code": "",
            "customer_name": "",
            "address_street": "",
            "address_district": "",
            "address_state": "",
            "address_city": "",
            "address_zip_code": "",
            "id_number": "",
            "phone": "",
            "customer_reference": "",
            "total_volumes": 0,
            "typing_date": None,
            "release_date": None,
            "pre_invoice_date": None,
            "invoice_number": "",
            "scheduled_date": "",
            "condition": "",
            "operation": "",
            "origin": "",
            "typist": "",
            "salesperson": "",
            "releaser": "",
            "situation": "",
            "pending_payment": "",
            "net_weight": 0,
            "carrier": "",
            "delivery": "",
            "manifest": "",
            "vehicle": "",
            "driver": "",
            "helper": "",
            "products": [],
        }
        try:
            doc = docx.Document(path)
            full_text = []
            for para in doc.paragraphs:
                full_text.append(para.text)
            # Add parsing logic...
        except Exception as e:
            raise ProcessingError(f"Error processing DOCX: {e}") from e
        return order_data
