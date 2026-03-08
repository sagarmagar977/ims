class LegacyApiDeprecationMiddleware:
    """
    Adds RFC-style deprecation metadata for legacy /api/* routes while /api/v1/* is active.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        from django.conf import settings

        response = self.get_response(request)
        path = request.path or ""
        if (
            getattr(settings, "LEGACY_API_DEPRECATION_ENABLED", True)
            and path.startswith(getattr(settings, "LEGACY_API_PREFIX", "/api/"))
            and not path.startswith(getattr(settings, "LEGACY_API_SUCCESSOR_PREFIX", "/api/v1/"))
        ):
            response["Deprecation"] = "true"
            successor = getattr(settings, "LEGACY_API_SUCCESSOR_PREFIX", "/api/v1/")
            response["Sunset"] = getattr(settings, "LEGACY_API_SUNSET_HTTP_DATE", "Thu, 31 Dec 2026 23:59:59 GMT")
            response["Link"] = f'<{successor}>; rel="successor-version"'
        return response
