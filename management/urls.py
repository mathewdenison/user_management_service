from django.urls import path
from .views import EmployeeListView, login_view, logout_view, csrf_setup, SubmitTimeLogView, EmployeeTimeLogsView, PTOUpdateView, TimeLogListView, create_employee_page, GetPTOView, CurrentWeekView, verify_token
from . import views

urlpatterns = [
    path('api/login/', login_view, name='login'),  # Login route
    path('api/logout/', logout_view, name='logout'),  # Logout route
    path('api/employees/', EmployeeListView.as_view(), name='employee-list'),
    path("api/csrf/", views.csrf, name="csrf"),
    path("api/csrf_setup/", csrf_setup, name="csrf_setup"),
    path('api/create_employee/', create_employee_page, name='create_employee'),
]

urlpatterns += [
    path('api/employees/<int:employee_id>/submit_timesheet/', SubmitTimeLogView.as_view(), name='submit-timelog'),
]

urlpatterns += [
    path('api/employees/timelogs/', EmployeeTimeLogsView.as_view(), name='employee-timelogs'),
]

urlpatterns += [
    path('api/employees/<int:employee_id>/pto/', PTOUpdateView.as_view(), name='update-pto'),
]

urlpatterns += [
    path('api/employees/<int:employee_id>/get_timesheet/', TimeLogListView.as_view(), name='get-timelog'),
]

urlpatterns += [
    path('api/ptoBalance/', GetPTOView.as_view(), name='get-pto'),
]

urlpatterns += [
    path('api/payPeriod/', CurrentWeekView.as_view(), name='get-payperiod'),
]

urlpatterns += [
    path('api/timelogs/<int:pk>/', views.TimeLogUpdateView.as_view(), name='update-timelog'),
]

urlpatterns = [
    path('api/verify-token/', verify_token, name='verify_token'),  # Add this line
]