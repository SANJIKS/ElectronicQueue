from rest_framework.permissions import BasePermission

class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.profile.position == 'admin'

# class IsAdminOfHisBranch(BasePermission):
#     def has_object_permission(self, request, view, obj):