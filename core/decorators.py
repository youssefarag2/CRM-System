# core/decorators.py

from django.http import HttpResponseForbidden
from django.shortcuts import redirect
from functools import wraps
from .models import Role, Profile
from django.utils import timezone as tz

def permission_required(permission_name):
    """
    Decorator to check if the user has the specified permission.
    :param permission_name: Name of the permission to check.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            
            if not request.user.is_authenticated:  # Check if the user is logged in
                return redirect('/login')
            
            
            profile = Profile.objects.get(user=request.user)
            user_role = profile.role  # Modify as necessary            
            try:
                role_permission = Role.objects.get(role_name=user_role)
            except Role.DoesNotExist:
                return redirect('/')

            
            if getattr(role_permission, permission_name, False):
                return view_func(request, *args, **kwargs)
            else:
                if str(role_permission) == "Affiliate":
                    now = tz.now()
                    current_year = now.year
                    current_month = now.month
                    return redirect(f'/affiliate-dashboard/{current_month}-{current_year}')
                else:
                    return redirect('/')
        
        return _wrapped_view
    return decorator

def permissions_required(*permission_names):


    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):

            profile = Profile.objects.get(user=request.user)
            user_role = profile.role  # Modify as necessary
            try:
                role_permission = Role.objects.get(role_name=user_role)
            except Role.DoesNotExist:
                return redirect('/')

            for permission_name in permission_names:
                if not getattr(role_permission, permission_name, False):
                    return redirect('/')
                    
            return view_func(request, *args, **kwargs)
        
        return _wrapped_view
    return decorator
