from django import forms
from django.contrib.auth.models import User
from .models import Employee


class EmployeeUserForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ('username', 'password', 'is_superuser')


class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = ('name', 'role', 'department', 'pto_balance')
