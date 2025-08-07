from django.shortcuts import redirect
from django.http import HttpResponseForbidden
from django.utils.deprecation import MiddlewareMixin

class SecurityMiddleware(MiddlewareMixin):
    def process_request(self, request):
        # 🔹 Define restricted URLs for normal users
        protected_urls = [
            "/user/dashboard/",  # User home
            "/center/home/",     # Center dashboard
        ]

        # 🔹 Restrict non-authenticated users
        if request.path in protected_urls and not request.user.is_authenticated:
            return redirect("login")  # Redirect to login page

        # 🔹 Block non-admin users from accessing /admin/
        if request.path.startswith("/admin/") and not request.user.is_superuser:
            return HttpResponseForbidden("403 Forbidden: Access Denied")  # Instead of 404

    def process_response(self, request, response):
        # 🔹 Prevent users from using the "Back" button after logout
        if not request.user.is_authenticated:
            response["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
            response["Pragma"] = "no-cache"
            response["Expires"] = "0"

        return response
