from threading import local

# Thread-local storage to store tenant_id for each request
_thread_locals = local()


def get_current_tenant():
    """Returns the tenant_id for the current request."""
    return getattr(_thread_locals, 'tenant_id', None)


class TenantMiddleware:
    """
    Middleware to set tenant_id for each request.
    You can fetch this from user.profile or request headers, or subdomain.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        tenant_id = None

        # Example: if user is logged in and has tenant info
        if request.user.is_authenticated:
            # Prefer employee_profile.tenant_id
            profile = getattr(request.user, 'employee_profile', None)
            if profile and hasattr(profile, 'tenant_id'):
                tenant_id = profile.tenant_id
            elif hasattr(request.user, 'tenant_id'):
                tenant_id = request.user.tenant_id
            elif hasattr(request.user, 'profile') and hasattr(request.user.profile, 'tenant_id'):
                tenant_id = request.user.profile.tenant_id

        # Store in thread-local
        _thread_locals.tenant_id = tenant_id

        return self.get_response(request)
