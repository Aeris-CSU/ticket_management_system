from django.conf import settings
from django.http import HttpResponse


class CorsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if (
            request.method == 'OPTIONS'
            and 'HTTP_ACCESS_CONTROL_REQUEST_METHOD' in request.META
        ):
            response = HttpResponse()
        else:
            response = self.get_response(request)

        origin = request.META.get('HTTP_ORIGIN')
        allowed_origins = getattr(settings, 'CORS_ALLOWED_ORIGINS', [])

        if origin in allowed_origins:
            response['Access-Control-Allow-Origin'] = origin
            response['Vary'] = 'Origin'
            response['Access-Control-Allow-Methods'] = 'GET, POST, PUT, PATCH, DELETE, OPTIONS'
            response['Access-Control-Allow-Headers'] = 'Authorization, Content-Type'
            response['Access-Control-Allow-Credentials'] = str(
                getattr(settings, 'CORS_ALLOW_CREDENTIALS', False)
            ).lower()

        return response
