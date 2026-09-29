from django.http import HttpResponse


def service_worker(request):
    js = """
self.addEventListener("install", () => {
    self.skipWaiting();
});

self.addEventListener("activate", (event) => {
    event.waitUntil(self.clients.claim());
});

// لا نعمل Cache لصفحات Django أو بيانات المرضى
self.addEventListener("fetch", (event) => {
    // Network only
});
"""

    return HttpResponse(
        js,
        content_type="application/javascript"
    )