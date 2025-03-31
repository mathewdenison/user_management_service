from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User

class Employee(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    role = models.CharField(max_length=50, choices=[
        ('Employee', 'Employee'),
        ('Manager', 'Manager'),
        ('HR', 'HR'),
    ])
    department = models.CharField(max_length=100)
    manager = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.name
