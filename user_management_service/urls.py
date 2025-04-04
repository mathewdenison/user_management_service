from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('api/user/admin/', admin.site.urls),
    path('api/user/', include('management.urls')),
]
