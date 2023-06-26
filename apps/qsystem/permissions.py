from rest_framework.permissions import BasePermission

class IsOperator(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.profile.position == 'operator' and request.user.profile.banned != True  and request.user.window.is_online == True


class IsOperatorOfCustomer(BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.user == obj.operator