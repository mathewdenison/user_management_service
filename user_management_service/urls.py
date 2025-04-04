from django.contrib import admin
from django.urls import path

urlpatterns = [
    path('/api/user/admin', admin.site.urls),
]
