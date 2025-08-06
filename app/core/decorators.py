from django.http import HttpResponseForbidden


def role_required(allowed_roles=None):
    if allowed_roles is None:
        allowed_roles = []

    def decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):
            if request.user.is_authenticated:
                profile = getattr(request.user, 'employee_profile', None)
                if profile and profile.role in allowed_roles:
                    return view_func(request, *args, **kwargs)
            return HttpResponseForbidden("You do not have permission to access this page.")
        return _wrapped_view
    return decorator
