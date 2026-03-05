import base64
import json
import os

from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST
from django.db import transaction
from django.db.models import Q
import json
import os
import threading
from django.core.files.storage import FileSystemStorage

from .models import Pedido, PedidoVolume, VolumeItem, ImportBatch
from .services import ExcelReader, DatabaseService

CERTS_DIR = os.path.join(settings.BASE_DIR, "certs")


def qz_certificate(request):
    """Serve the public digital certificate for QZ Tray."""
    cert_path = os.path.join(CERTS_DIR, "digital-certificate.txt")
    try:
        with open(cert_path) as f:
            return HttpResponse(f.read(), content_type="text/plain")
    except FileNotFoundError:
        return HttpResponse("", content_type="text/plain", status=404)


@csrf_exempt
def qz_sign(request):
    """
    Sign the challenge string sent by QZ Tray using the private key (SHA1/RSA).
    Tries the 'cryptography' package first; falls back to the system 'openssl'
    binary (always available in the Docker base image) if not installed.
    """
    to_sign = request.body  # raw bytes sent by QZ Tray
    key_path = os.path.join(CERTS_DIR, "private-key.pem")

    if not os.path.exists(key_path):
        return HttpResponse("Private key not found", status=404)

    # ── Strategy 1: cryptography package ────────────────────────────────────
    try:
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import padding as asym_padding

        with open(key_path, "rb") as f:
            private_key = serialization.load_pem_private_key(f.read(), password=None)

        sig = private_key.sign(to_sign, asym_padding.PKCS1v15(), hashes.SHA1())
        return HttpResponse(base64.b64encode(sig).decode("ascii"), content_type="text/plain")

    except ImportError:
        pass  # fall through to openssl

    # ── Strategy 2: openssl subprocess (always available on Debian/Alpine) ──
    import subprocess
    import tempfile

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".bin") as tmp:
            tmp.write(to_sign)
            tmp_path = tmp.name

        result = subprocess.run(
            ["openssl", "dgst", "-sha1", "-sign", key_path, "-out", "-", tmp_path],
            capture_output=True,
        )
        os.unlink(tmp_path)

        if result.returncode != 0:
            return HttpResponse(
                "openssl error: " + result.stderr.decode(), status=500
            )
        return HttpResponse(
            base64.b64encode(result.stdout).decode("ascii"),
            content_type="text/plain",
        )

    except FileNotFoundError:
        return HttpResponse("Neither cryptography nor openssl is available", status=500)


def search_order_view(request):
    pedido = None
    search_query = request.GET.get("numero_pedido")

    if search_query:
        pedido = Pedido.objects.filter(Q(numero_pedido=search_query) | Q(picking=search_query)).first()

    context = {"pedido": pedido, "search_query": search_query}
    return render(request, "ticket_printer/index.html", context)


@require_POST
def process_volumes_view(request):
    try:
        data = json.loads(request.body)
        search_query = data.get("numero_pedido")
        total_volumes = int(data.get("total_volumes", 1))

        if not search_query or total_volumes < 1:
            return JsonResponse({"error": "Parâmetros inválidos."}, status=400)

        pedido = Pedido.objects.filter(Q(numero_pedido=search_query) | Q(picking=search_query)).first()
        if not pedido:
            return JsonResponse({"error": "Pedido não encontrado."}, status=404)

        zpl_commands = []
        # Endereço formatado em duas partes para melhor legibilidade
        addr_main = []
        if pedido.endereco_logradouro: addr_main.append(pedido.endereco_logradouro)
        if pedido.endereco_numero: addr_main.append(f"{pedido.endereco_numero}")
        if pedido.endereco_bairro: addr_main.append(f"- {pedido.endereco_bairro}")
        endereco_completo = " ".join(addr_main)

        addr_sub = []
        city_uf = []
        if pedido.endereco_cidade: city_uf.append(pedido.endereco_cidade)
        if pedido.endereco_uf: city_uf.append(pedido.endereco_uf)
        if city_uf: addr_sub.append(" / ".join(city_uf))
        if pedido.endereco_cep: addr_sub.append(f"CEP: {pedido.endereco_cep}")
        endereco_uf_cep = " - ".join(addr_sub)
        
        with transaction.atomic():
            # Limpar volumes antigos para regerar caso o operador processe novamente para o mesmo pedido no MVP
            PedidoVolume.objects.filter(pedido=pedido).delete()

            itens = list(pedido.itens.all())

            for i in range(1, total_volumes + 1):
                # Opcional: deletar e recriar ou apenas criar volumes incrementais
                volume_obj = PedidoVolume.objects.create(
                    pedido=pedido, volume_num=i, total_volumes=total_volumes
                )

                # Rateio simplificado para o MVP (distribuindo homogeneamente ou registrando as partes)
                for item in itens:
                    qtd_por_volume = max(1, item.quantidade // total_volumes)
                    VolumeItem.objects.create(
                        volume=volume_obj,
                        item=item,
                        quantidade=qtd_por_volume,
                    )

                # Geração do código ZPL seguindo o padrão solicitado
                zpl = f"""^XA
                    ^CI28

                    ^CF0,60,60
                    ^FO40,25^FDPicking: {pedido.picking}^FS

                    ^FO40,85^GB720,3,3^FS

                    ^CF0,35,35
                    ^FO40,110^FD{pedido.cliente_nome}^FS

                    ^CF0,35,35
                    ^FO40,160^FD{pedido.endereco_logradouro or ''}, {pedido.endereco_numero or ''}^FS

                    ^CF0,60,60
                    ^FO40,200^FD{pedido.endereco_bairro or ''}^FS

                    ^CF0,35,35
                    ^FO40,270^FD{pedido.endereco_cidade or ''}/{pedido.endereco_uf or ''} - {pedido.endereco_cep or ''}^FS

                    ^FO40,325^GB720,3,3^FS

                    ^CF0,60,60
                    ^FO0,350^FB800,1,0,C^FDVol: {i}/{total_volumes}^FS

                    ^XZ"""
                zpl_commands.append(zpl)

        return JsonResponse({"success": True, "zpl_commands": zpl_commands})

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


def process_import_batch_thread(batch_id, file_paths):
    batch = ImportBatch.objects.get(id=batch_id)
    erros = []
    
    for path, filename in file_paths:
        try:
            with open(path, 'rb') as f:
                pedido_data = ExcelReader.ler(f)
                
            if not pedido_data.get("itens"):
                erros.append(f"{filename}: Nenhum item encontrado.")
            else:
                DatabaseService.salvar_pedido_completo(pedido_data)
                
            batch.processed_files += 1
            batch.save(update_fields=['processed_files'])
            
        except Exception as e:
            erros.append(f"{filename}: {str(e)}")
            batch.processed_files += 1
            batch.save(update_fields=['processed_files'])
        finally:
            # Clean up temp file
            if os.path.exists(path):
                try:
                    os.remove(path)
                except:
                    pass
                    
    batch.status = 'completed' if not erros else 'error'
    if erros:
        batch.errors = json.dumps(erros)
    batch.save(update_fields=['status', 'errors'])


def upload_excel_view(request):
    if request.method == "POST":
        excel_files = request.FILES.getlist("excel_files")
        if not excel_files:
            return JsonResponse({"error": "Nenhum arquivo de planilha foi enviado."}, status=400)
            
        # Create temp files safely
        fs = FileSystemStorage(location=os.path.join(settings.BASE_DIR, 'tmp', 'uploads'))
        
        file_paths = []
        for f in excel_files:
            try:
                # save returns the actual name, append to paths
                saved_name = fs.save(f.name, f)
                full_path = fs.path(saved_name)
                file_paths.append((full_path, f.name))
            except Exception as e:
                pass
                
        if not file_paths:
            return JsonResponse({"error": "Falha ao alocar os arquivos temporários no servidor."}, status=500)
            
        batch = ImportBatch.objects.create(
            total_files=len(file_paths),
            processed_files=0,
            status='processing'
        )
        
        # Inicia a Thread
        thread = threading.Thread(target=process_import_batch_thread, args=(batch.id, file_paths))
        thread.start()
        
        return JsonResponse({"success": True, "batch_id": batch.id})
        
    recent_batches = ImportBatch.objects.order_by('-created_at')[:10]
    recent_pedidos = Pedido.objects.order_by('-criado_em')[:10]
    return render(request, "ticket_printer/upload_excel.html", {
        "recent_batches": recent_batches,
        "recent_pedidos": recent_pedidos
    })


def check_import_progress(request):
    batch_id = request.GET.get('batch_id')
    if not batch_id:
        return JsonResponse({"error": "batch_id não fornecido"}, status=400)
        
    try:
        batch = ImportBatch.objects.get(id=batch_id)
        errors = json.loads(batch.errors) if batch.errors else []
        
        return JsonResponse({
            "status": batch.status,
            "processed": batch.processed_files,
            "total": batch.total_files,
            "errors": errors
        })
    except ImportBatch.DoesNotExist:
        return JsonResponse({"error": "Batch não encontrado"}, status=404)
