from rest_framework.permissions import BasePermission

# Permission - проверяющий что пользователь является оператором, не заблокирован ли он и то что он на месте
class IsOperator(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.profile.position == 'operator' and request.user.profile.banned != True  and request.user.window.is_online == True

# Permission - проверяющий что пользователь является оператором данного талона
class IsOperatorOfCustomer(BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.user == obj.operator