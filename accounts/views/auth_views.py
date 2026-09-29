"""
Authentication Views
Views for login and logout functionality
"""
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from accounts.decorators import redirect_by_role
from tenants.routers import set_current_tenant_db, clear_current_tenant_db


def login_view(request):
    """
    Login view for tenant users
    """
    tenant = request.tenant

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
