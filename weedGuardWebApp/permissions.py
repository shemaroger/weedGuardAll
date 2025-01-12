from rest_framework.permissions import BasePermission

class IsAdminOrReadOnly(BasePermission):
    """
    Custom permission to only allow admins to edit an object.
    """
    def has_permission(self, request, view):
        # Allow any request if the request method is a safe method (GET, HEAD, OPTIONS)
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return True
        # Only allow editing for admin users
        return request.user and request.user.is_staff
