from functools import wraps
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import redirect


def require_tenant(view_func):
    """
    Decorator to ensure tenant context exists.
    Use for views that require tenant isolation.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not hasattr(request, 'tenant') or request.tenant is None:
            return HttpResponse(
                "<!DOCTYPE html><html><body><h1>Error: No tenant context</h1></body></html>",
                status=400
            )
        return view_func(request, *args, **kwargs)
    return wrapper


def redirect_by_role(user):
    """
    Redirect user to their role-specific dashboard
    """
    from accounts.models import User
    
    user_role = getattr(user, 'role', None)

    if user_role == User.Role.DOCTOR:
        return redirect("doctor_dashboard")

    if user_role == User.Role.SECRETARY:
        return redirect("secretary_dashboard")

    return redirect("login")


def role_required(*allowed_roles):
    """
    Decorator to restrict access to specific user roles.
    MUST be used with @login_required decorator.
    
    Usage:
        @login_required
        @role_required('doctor')
        def my_view(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Check if user is authenticated (should be guaranteed by @login_required)
            if not request.user.is_authenticated:
                return redirect("login")
            
            user_role = getattr(request.user, 'role', None)
            
            # If user has no role or wrong role, redirect appropriately
            if user_role not in allowed_roles:
                return redirect_by_role(request.user)
            
            return view_func(request, *args, **kwargs)
        
        return wrapper
    return decorator


def doctor_required(view_func):
    """
    Decorator to restrict access to doctors only.
    Combines @require_tenant, @login_required with role check.
    
    Usage:
        @doctor_required
        def my_view(request):
            ...
    """
    @wraps(view_func)
    @require_tenant
    @login_required
    @role_required('doctor')
    def wrapper(request, *args, **kwargs):
        return view_func(request, *args, **kwargs)
    return wrapper


def secretary_required(view_func):
    """
    Decorator to restrict access to secretaries only.
    Combines @require_tenant, @login_required with role check.
    
    Usage:
        @secretary_required
        def my_view(request):
            ...
    """
    @wraps(view_func)
    @require_tenant
    @login_required
    @role_required('secretary')
    def wrapper(request, *args, **kwargs):
        return view_func(request, *args, **kwargs)
    return wrapper
