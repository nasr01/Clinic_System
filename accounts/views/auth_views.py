"""
Authentication Views
Views for login and logout functionality
"""
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.cache import never_cache

from accounts.decorators import redirect_by_role
from tenants.routers import set_current_tenant_db, clear_current_tenant_db


@csrf_protect
@never_cache
def login_view(request):
    """
    Login view for tenant users
    """
    # Redirect authenticated users
    if request.user.is_authenticated:
        return redirect_by_role(request.user)
    
    tenant = request.tenant
    
    # SECURITY: Ensure tenant context exists
    if not tenant:
        return HttpResponse(
            "<!DOCTYPE html><html><body><h1>Error: No tenant context</h1></body></html>",
            status=400
        )

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")

        context = {
            "username": username,
        }

        if not username or not password:
            context["error"] = "يرجى إدخال اسم المستخدم وكلمة المرور."
            return render(request, "accounts/login.html", context)

        set_current_tenant_db("tenant")

        user = authenticate(request, username=username, password=password)

        if user is None:
            clear_current_tenant_db()
            context["error"] = "اسم المستخدم أو كلمة المرور غير صحيحة."
            return render(request, "accounts/login.html", context)

        # Check if user is active
        if not user.is_active:
            clear_current_tenant_db()
            context["error"] = "هذا الحساب غير نشط."
            return render(request, "accounts/login.html", context)

        # SECURITY: Store current tenant ID in session
        # This binds the session to this specific tenant
        request.session["tenant_id"] = tenant.id
        request.session["tenant_slug"] = tenant.slug

        try:
            login(request, user)
        finally:
            clear_current_tenant_db()

        return redirect_by_role(user)

    return render(
        request,
        "accounts/login.html",
        {
            "clinic_name": tenant.clinic_name if tenant else "",
        },
    )


@login_required
def logout_view(request):
    """
    Logout view for all users
    """
    logout(request)
    return redirect("login")
