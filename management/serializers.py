# new_serializer.py
from rest_framework import serializers

class EmployeeSerializer(serializers.Serializer):
    employee_id = serializers.CharField(required=False)
    user_id = serializers.CharField()
    name = serializers.CharField()
    role = serializers.CharField()
    department = serializers.CharField()
    manager_id = serializers.CharField(required=False, allow_null=True, allow_blank=True)

    # Create a new EmployeeFS from validated data
    def create(self, validated_data):
        from .models import Employee
        # If there's no employee_id, we can have Firestore generate one, or we do random uuid
        employee_id = validated_data.pop('employee_id', None)
        if not employee_id:
            # Firestore can auto-generate ID if you call `db.collection(...).document()`
            # without an ID, or you can generate your own:
            import uuid
            employee_id = str(uuid.uuid4())

        emp = Employee(
            employee_id=employee_id,
            user_id=validated_data['user_id'],
            name=validated_data['name'],
            role=validated_data['role'],
            department=validated_data['department'],
            manager_id=validated_data.get('manager_id')
        )
        emp.save()
        return emp

    # Update existing EmployeeFS
    def update(self, instance, validated_data):
        # 'instance' is an EmployeeFS object
        instance.user_id = validated_data.get('user_id', instance.user_id)
        instance.name = validated_data.get('name', instance.name)
        instance.role = validated_data.get('role', instance.role)
        instance.department = validated_data.get('department', instance.department)
        instance.manager_id = validated_data.get('manager_id', instance.manager_id)
        instance.save()
        return instance
