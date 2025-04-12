# forms.py

import uuid
from django import forms
from passlib.context import CryptContext

# Import your Firestore-based Employee class (not a Django model!)
from .models import Employee

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class EmployeeUserForm(forms.Form):
    """
    A plain Form (not ModelForm), creating a Firestore Employee with username/password.
    """
    username = forms.CharField(max_length=100)
    password = forms.CharField(widget=forms.PasswordInput)
    is_superuser = forms.BooleanField(required=False)

    def save(self, commit=True):
        """
        Creates a new Firestore Employee doc with a hashed password.
        """
        employee_id = str(uuid.uuid4())

        # Hash the password
        raw_password = self.cleaned_data['password']
        hashed_password = pwd_context.hash(raw_password)

        # If you want to treat 'is_superuser' as a special role, or store it in a separate field,
        # you can decide how to handle it. For example, let's store it in the 'role' or a separate field:
        role = "Superuser" if self.cleaned_data.get('is_superuser') else "Employee"

        # Create the Firestore-based Employee
        emp = Employee(
            employee_id=employee_id,
            user_id="",  # optional
            name=self.cleaned_data['username'],  # or a separate name field if needed
            role=role,
            department="",  # or some default / or add a field for it
            manager_id=None,
            username=self.cleaned_data['username'],
            hashed_password=hashed_password,
        )
        if commit:
            emp.save()
        return emp


class EmployeeForm(forms.Form):
    """
    A second plain Form if you need to collect additional data
    for an existing or new employee (e.g., role, department, manager).
    """
    name = forms.CharField(max_length=100)
    role = forms.ChoiceField(choices=[('Employee', 'Employee'), ('Manager', 'Manager'), ('HR', 'HR')])
    department = forms.CharField(max_length=100, required=False)
    manager_id = forms.CharField(required=False)

    def save(self, commit=True):
        """
        Create or update Firestore Employee doc with this data.
        For a brand-new doc, we can generate a new doc ID.
        """
        employee_id = str(uuid.uuid4())

        emp = Employee(
            employee_id=employee_id,
            user_id="",  # optional
            name=self.cleaned_data['name'],
            role=self.cleaned_data['role'],
            department=self.cleaned_data['department'],
            manager_id=self.cleaned_data.get('manager_id'),
            # username, hashed_password, etc. not handled here
        )

        if commit:
            emp.save()
        return emp
