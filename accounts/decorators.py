from functools import wraps
from django.shortcuts import redirect


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
    
    Usage:
        @role_required('doctor')
        @role_required('secretary')
        @role_required('doctor', 'secretary')
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            user_role = getattr(request.user, 'role', None)
            
            if user_role not in allowed_roles:
                return redirect_by_role(request.user)
            
            return view_func(request, *args, **kwargs)
        
        return wrapper
    return decorator


def doctor_required(view_func):
    """
    Decorator to restrict access to doctors only.
    
    Usage:
        @login_required
        @doctor_required
        def my_view(request):
            ...
    """
    return role_required('doctor')(view_func)


def secretary_required(view_func):
    """
    Decorator to restrict access to secretaries only.
    
    Usage:
        @login_required
        @secretary_required
        def my_view(request):
            ...
    """
    return role_required('secretary')(view_func)
