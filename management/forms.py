from django import forms
from django.contrib.auth.models import User
from .models import Employee


class EmployeeUserForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ('username', 'password', 'is_superuser')


class EmployeeForm(forms.ModelForm):
    user = forms.ModelChoiceField(queryset=User.objects.all())  # Include the user field

    class Meta:
        model = Employee
        fields = ('user', 'name', 'role', 'department')  # Removed pto_balance
