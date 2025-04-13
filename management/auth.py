from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from management.models import Employee  # Your Firestore Employee model

class FirestoreEmployeeAuth(BaseAuthentication):
    def authenticate(self, request):
        username = request.headers.get("X-Username")

        if not username:
            return None  # Let other authenticators try (or treat as unauthenticated)

        employee = Employee.get_by_username(username)
        if not employee:
            raise AuthenticationFailed("Invalid employee or user not found.")

        # Use a dummy user object or AnonymousUser if you aren't using Django's auth system
        user = type("User", (object,), {"is_authenticated": True})()
        user.employee = employee
        return (user, None)
