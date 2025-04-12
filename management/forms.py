# forms.py

import uuid
from django import forms
from passlib.context import CryptContext

# Import your Firestore-based Employee class (not a Django model!)
from .models import Employee

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class EmployeeForm(forms.Form):
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)
    name = forms.CharField(max_length=100)
    role = forms.ChoiceField(
        choices=[('Employee', 'Employee'), ('Manager', 'Manager'), ('HR', 'HR')]
    )
    department = forms.CharField(max_length=100)
    manager_id = forms.CharField(required=False)

    def save(self, commit=True):
        import uuid
        from passlib.context import CryptContext
        from .models import Employee

        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        hashed_password = pwd_context.hash(self.cleaned_data['password'])

        emp = Employee(
            employee_id=str(uuid.uuid4()),
            user_id="",  # optional
            username=self.cleaned_data['username'],
            hashed_password=hashed_password,
            name=self.cleaned_data['name'],
            role=self.cleaned_data['role'],
            department=self.cleaned_data['department'],
            manager_id=self.cleaned_data.get('manager_id'),
        )

        if commit:
            emp.save()

        return emp

