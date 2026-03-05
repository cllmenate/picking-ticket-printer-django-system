import pandas as pd
import numpy as np
import re
from typing import Dict, Any, List, Optional
from decimal import Decimal, InvalidOperation
from django.db import transaction

from .models import Pedido, PedidoItem, PedidoVolume, VolumeItem


class ExcelReader:
    @staticmethod
    def ler(caminho: Any) -> Dict[str, Any]:
        """
        Recebe um path ou file-like object (uploaded file), lê com pandas
        e extrai os dados do Pedido e Itens.
        """
        # Read all sheets into a dictionary of DataFrames
        try:
            dfs = pd.read_excel(caminho, sheet_name=None, header=None)
        except Exception as e:
            raise ValueError(f"Não foi possível ler o arquivo Excel: {e}")

        # Encontra a melhor aba para cabeçalho
        header_df = ExcelReader._find_best_header_df(dfs)
        if header_df is None:
            # Fallback para a primeira aba
            header_df = list(dfs.values())[0]

        pedido_data = {
            "numero_pedido": ExcelReader._normalize_digits(
                ExcelReader._find_after(header_df, "Nº") or ExcelReader._find_after(header_df, "Nr") or ""
            ),
            "picking": ExcelReader._normalize_digits(
                ExcelReader._find_after(header_df, "Picking") or ""
            ),
            "rota": (ExcelReader._find_after(header_df, "Rota") or "").strip(),
            "cliente_codigo": (ExcelReader._find_after(header_df, "Cód. Cliente") or ExcelReader._find_after(header_df, "Cod. Cliente") or "").strip(),
            "cliente_nome": (ExcelReader._find_after(header_df, "Cliente") or "").strip(),
            "endereco_logradouro": (ExcelReader._find_after(header_df, "Endereço") or ExcelReader._find_after(header_df, "Endereco") or "").strip(),
            "endereco_numero": "", # C# não puxa número isolado, mas sim no logradouro?
            "endereco_bairro": (ExcelReader._find_after(header_df, "Bairro") or ExcelReader._find_after(header_df, "Bairro") or "").strip(),
            "endereco_uf": (ExcelReader._find_after(header_df, "Estado") or ExcelReader._find_after(header_df, "Estado") or "").strip(),
            "endereco_cidade": (ExcelReader._find_after(header_df, "Cidade") or "").strip(),
            "endereco_cep": (ExcelReader._find_after(header_df, "Cep") or ExcelReader._find_after(header_df, "CEP") or "").strip(),
            "cpf_cnpj": (ExcelReader._find_after(header_df, "CPF/CNPJ") or ExcelReader._find_after(header_df, "CPF/CNPJ") or "").strip(),
            "total_volumes": ExcelReader._try_parse_int(ExcelReader._find_after(header_df, "Volumes")),
            "itens": []
        }

        # Itens: procura a tabela de itens em QUALQUER aba
        for sheet_name, df in dfs.items():
            itens = ExcelReader._extract_items(df)
            if itens:
                pedido_data["itens"] = itens
                break
                
        return pedido_data

    @staticmethod
    def _find_best_header_df(dfs: Dict[str, pd.DataFrame]) -> Optional[pd.DataFrame]:
        for sheet_name, df in dfs.items():
            if ExcelReader._df_contains(df, "DADOS DO PEDIDO") or \
               ExcelReader._df_contains(df, "DADOS") or \
               ExcelReader._df_contains(df, "PEDIDO"):
                return df
        return None

    @staticmethod
    def _df_contains(df: pd.DataFrame, needle: str) -> bool:
        needle = needle.strip().lower()
        for col in df.columns:
            mask = df[col].astype(str).str.lower().str.contains(needle, na=False)
            if mask.any():
                return True
        return False

    @staticmethod
    def _get_str(df: pd.DataFrame, r: int, c: int) -> str:
        if 0 <= r < len(df.index) and 0 <= c < len(df.columns):
            val = df.iat[r, c]
            if pd.isna(val):
                return ""
            return str(val)
        return ""

    @staticmethod
    def _find_after(df: pd.DataFrame, label: str) -> Optional[str]:
        lbl = label.strip().lower()
        
        rows, cols = df.shape
        for r in range(rows):
            for c in range(cols):
                raw = ExcelReader._get_str(df, r, c)
                if not raw or not raw.strip():
                    continue
                
                s = raw.strip()
                low = s.lower()
                
                # Aceita "Cliente:" ou "Cliente"
                if low.startswith(lbl) or (lbl + ":") in low or (lbl + " :") in low or low == lbl:
                    # 1) "Label: valor" na mesma célula
                    idx = s.find(':')
                    if idx >= 0 and idx < len(s) - 1:
                        after = s[idx + 1:].strip()
                        if after:
                            return after
                    
                    # 2) procura à direita
                    for i in range(1, 21):
                        if c + i >= cols:
                            break
                        v = ExcelReader._get_str(df, r, c + i).strip()
                        if v:
                            return v
                            
                # Caso especial
                if (lbl == "nº" or lbl == "nr") and "nº" in low and ":" in low:
                    idx2 = s.find(':')
                    after2 = s[idx2 + 1:].strip()
                    if after2:
                        return after2
                        
        return None

    @staticmethod
    def _extract_items(df: pd.DataFrame) -> List[Dict[str, Any]]:
        headerRow, colCod, colDesc, colQtd = ExcelReader._find_items_header(df)
        if headerRow < 0:
            return []
            
        itens = []
        rows, cols = df.shape
        
        for r in range(headerRow + 1, rows):
            codigo = ExcelReader._get_str(df, r, colCod).strip()
            desc = ExcelReader._get_str(df, r, colDesc).strip()
            qtd_str = ExcelReader._get_str(df, r, colQtd).strip()
            
            # fim: linha vazia
            if not codigo and not desc:
                break
                
            if not desc:
                continue
                
            itens.append({
                "codigo_produto": codigo if codigo else None,
                "descricao": desc,
                "quantidade": ExcelReader._try_parse_decimal(qtd_str),
                "unidade": "",
                "linha_origem": r + 1
            })
            
        return itens

    @staticmethod
    def _find_items_header(df: pd.DataFrame):
        rows, cols = df.shape
        for r in range(rows):
            colCod = -1
            colDesc = -1
            colQtd = -1
            
            for c in range(cols):
                s = ExcelReader._get_str(df, r, c).strip().lower()
                if not s:
                    continue
                    
                if colCod == -1 and ("cód" in s or "codigo" in s or s == "cod" or "cod." in s):
                    colCod = c
                
                if colDesc == -1 and ("descr" in s or "descricao" in s or "descrição" in s or "produto" in s):
                    colDesc = c
                    
                if colQtd == -1 and (s.startswith("qt") or "qtd" in s or "qtde" in s or "quant" in s):
                    colQtd = c
                    
            if colCod != -1 and colDesc != -1 and colQtd != -1:
                return r, colCod, colDesc, colQtd
                
        return -1, -1, -1, -1

    @staticmethod
    def _try_parse_int(s: Optional[str]) -> int:
        if not s:
            return 0
        try:
            return int(float(s.strip()))
        except ValueError:
            return 0

    @staticmethod
    def _try_parse_decimal(s: str) -> Decimal:
        if not s or not s.strip():
            return Decimal('0')
        s = s.strip()
        if ',' in s and '.' in s:
            s = s.replace('.', '').replace(',', '.')
        elif ',' in s:
            s = s.replace(',', '.')
            
        try:
            return Decimal(s)
        except InvalidOperation:
            return Decimal('0')

    @staticmethod
    def _normalize_digits(s: str) -> str:
        if not s or not s.strip():
            return ""
        digits = "".join(c for c in s if c.isdigit())
        return digits if digits else s.strip()


class DatabaseService:
    @staticmethod
    def salvar_pedido_completo(pedido_data: Dict[str, Any], recriar_volumes: bool = True):
        with transaction.atomic():
            numero_pedido = pedido_data.get("numero_pedido", "")
            picking = pedido_data.get("picking", "")
            
            pedido = Pedido.objects.filter(numero_pedido=numero_pedido, picking=picking).first()
            
            if pedido:
                # Limpa itens e volumes
                PedidoVolume.objects.filter(pedido=pedido).delete()
                PedidoItem.objects.filter(pedido=pedido).delete()
                
                # Atualiza dados do pedido
                pedido.rota = pedido_data.get("rota", "")
                pedido.cliente_codigo = pedido_data.get("cliente_codigo", "")
                pedido.cliente_nome = pedido_data.get("cliente_nome", "")
                pedido.endereco_logradouro = pedido_data.get("endereco_logradouro", "")
                pedido.endereco_numero = pedido_data.get("endereco_numero", "")
                pedido.endereco_bairro = pedido_data.get("endereco_bairro", "")
                pedido.endereco_cidade = pedido_data.get("endereco_cidade", "")
                pedido.endereco_uf = pedido_data.get("endereco_uf", "")
                pedido.endereco_cep = pedido_data.get("endereco_cep", "")
                pedido.cpf_cnpj = pedido_data.get("cpf_cnpj", "")
                pedido.save()
            else:
                pedido = Pedido.objects.create(
                    picking=picking,
                    numero_pedido=numero_pedido,
                    rota=pedido_data.get("rota", ""),
                    cliente_codigo=pedido_data.get("cliente_codigo", ""),
                    cliente_nome=pedido_data.get("cliente_nome", ""),
                    endereco_logradouro=pedido_data.get("endereco_logradouro", ""),
                    endereco_numero=pedido_data.get("endereco_numero", ""),
                    endereco_bairro=pedido_data.get("endereco_bairro", ""),
                    endereco_cidade=pedido_data.get("endereco_cidade", ""),
                    endereco_uf=pedido_data.get("endereco_uf", ""),
                    endereco_cep=pedido_data.get("endereco_cep", ""),
                    cpf_cnpj=pedido_data.get("cpf_cnpj", "")
                )
                
            # Insere itens
            itens_data = pedido_data.get("itens", [])
            for i, item_data in enumerate(itens_data):
                PedidoItem.objects.create(
                    pedido=pedido,
                    codigo_produto=item_data.get("codigo_produto", ""),
                    descricao=item_data.get("descricao", ""),
                    quantidade=item_data.get("quantidade", 0),
                    unidade=item_data.get("unidade", ""),
                    linha_origem=item_data.get("linha_origem", i+1)
                )

            # Insere volumes
            total_volumes = pedido_data.get("total_volumes", 0)
            if recriar_volumes and total_volumes > 0:
                for v in range(1, total_volumes + 1):
                    PedidoVolume.objects.create(
                        pedido=pedido,
                        volume_num=v,
                        total_volumes=total_volumes
                    )
            
            return pedido
