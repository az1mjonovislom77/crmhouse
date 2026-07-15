from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsProjectMemberOrAdmin(BasePermission):

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        user = request.user

        if request.method in SAFE_METHODS:
            return True

        if user.role in ['a', 'sa']:
            return True

        return user in obj.users.all()
