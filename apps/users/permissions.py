from rest_framework.permissions import BasePermission

class IsOperatorOnline(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.profile.position == 'operator'
    
class OperatorIsNotBusy(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.profile.position == 'operator' and request.user.window.is_busy != True
    
class IsRegistrator(BasePermission):
    def has_permission(self, request, view):
        return request.user.profile.position == 'registrator' and request.user.profile.is_banned != True