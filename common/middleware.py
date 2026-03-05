class LegacyApiDeprecationMiddleware:
    """
    Adds RFC-style deprecation metadata for legacy /api/* routes while /api/v1/* is active.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        path = request.path or ""
        if path.startswith("/api/") and not path.startswith("/api/v1/"):
            response["Deprecation"] = "true"
            response["Sunset"] = "Wed, 31 Dec 2026 23:59:59 GMT"
            response["Link"] = '</api/v1/>; rel="successor-version"'
        return response
