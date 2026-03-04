import base64
import json
import os

from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST
from django.db import transaction
from django.db.models import Q

from .models import Pedido, PedidoVolume, VolumeItem

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
    Sign the challenge string sent by QZ Tray using the private key.
    QZ Tray sends the raw string to sign; we return the base64 SHA-512 signature.
    """
    try:
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import padding
    except ImportError:
        return HttpResponse("cryptography package not installed", status=500)

    to_sign = request.body  # raw bytes from QZ Tray
    key_path = os.path.join(CERTS_DIR, "private-key.pem")
    try:
        with open(key_path, "rb") as f:
            private_key = serialization.load_pem_private_key(f.read(), password=None)
    except FileNotFoundError:
        return HttpResponse("Private key not found", status=404)

    signature = private_key.sign(to_sign, padding.PKCS1v15(), hashes.SHA1())
    return HttpResponse(base64.b64encode(signature).decode("ascii"), content_type="text/plain")


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
