from rest_framework import serializers
from management.models import Employee

class EmployeeSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)  # Include user's username

    class Meta:
        model = Employee
        fields = ['id', 'user', 'name', 'role', 'department']  # Removed pto_balance
