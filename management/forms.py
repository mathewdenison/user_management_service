from django import forms
from django.contrib.auth.models import User

# Import your Firestore-based Employee class (not a Django model!)
# Adjust the import path as needed:
from .models import Employee

# This form remains a ModelForm, because `User` *is* a Django model
class EmployeeUserForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ('username', 'password', 'is_superuser')

################################################################
# Convert EmployeeForm to a plain Form for Firestore usage
################################################################
class EmployeeForm(forms.Form):
    user = forms.ModelChoiceField(queryset=User.objects.all())
    name = forms.CharField(max_length=100)
    role = forms.ChoiceField(
        choices=[
            ('Employee', 'Employee'),
            ('Manager', 'Manager'),
            ('HR', 'HR'),
        ]
    )
    department = forms.CharField(max_length=100)

    def save(self, commit=True):
        """
        Save form data to Firestore Employee doc.
        """
        # Possibly generate a unique employee_id
        import uuid
        employee_id = str(uuid.uuid4())

        # Convert 'user' (a Django User) to a user_id string
        django_user = self.cleaned_data['user']
        user_id = str(django_user.id)  # or use django_user.username if preferred

        emp = Employee(
            employee_id=employee_id,
            user_id=user_id,
            name=self.cleaned_data['name'],
            role=self.cleaned_data['role'],
            department=self.cleaned_data['department'],
            manager_id=None  # or define a manager field in this form if needed
        )

        if commit:
            emp.save()

        return emp
