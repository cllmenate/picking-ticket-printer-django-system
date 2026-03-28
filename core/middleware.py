from django.http import JsonResponse


class HealthCheckMiddleware:
    """
    Middleware que permite requisições de healthcheck sem validação de Host.
    Isso é necessário porque Railway's healthcheck probe pode enviar um Host header
    que não passa na validação do CommonMiddleware.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Se for healthcheck, retorna direto sem passar pelos outros middlewares
        if request.path == "/health/":
            return JsonResponse({"status": "ok"})

        return self.get_response(request)
