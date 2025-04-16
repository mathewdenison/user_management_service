from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from management.models import Employee

class FirestoreEmployeeAuth(BaseAuthentication):
    def authenticate(self, request):
        username = request.headers.get("X-Username")

        if not username:
            return None

        employee = Employee.get_by_username(username)
        if not employee:
            raise AuthenticationFailed("Invalid employee or user not found.")

        user = type("User", (object,), {"is_authenticated": True})()
        user.employee = employee
        return (user, None)
