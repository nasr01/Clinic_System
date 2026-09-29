from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from .views import service_worker



urlpatterns = [
path("",RedirectView.as_view(pattern_name="login", permanent=False),),


path("admin/", admin.site.urls),

path("", include("accounts.urls")),
path("", include("patients.urls")),

    path("sw.js", service_worker, name="service-worker"),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
