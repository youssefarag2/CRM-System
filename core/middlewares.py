from django.utils.deprecation import MiddlewareMixin
from django.http import HttpResponseForbidden
from .models import ServerSetting
from django.shortcuts import redirect


class MediaAccessMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if request.path.startswith('/media/'):
            return HttpResponseForbidden('Access denied to media files')
        return None
    


admin_users = ['admin','ezzat','ahmedezzat']

class MaintenanceMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Exclude the maintenance page and crm-admin from the check to avoid a redirect loop
        if not request.path.startswith('/maintenance') and not request.path.startswith('/crm-admin'):
            maintenance_mode = ServerSetting.objects.first().maintenance
            if maintenance_mode and str(request.user) not in admin_users:
                return redirect('/maintenance')

        return self.get_response(request)