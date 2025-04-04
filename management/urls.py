from django.urls import path
from .views import EmployeeListView, login_view, logout_view, csrf_setup, SubmitTimeLogView, EmployeeTimeLogsView, PTOUpdateView, TimeLogListView, create_employee_page, GetPTOView, CurrentWeekView, verify_token
from . import views

urlpatterns = [
    path('login/', login_view, name='login'),  # Login route
    path('logout/', logout_view, name='logout'),  # Logout route
    path('employees/', EmployeeListView.as_view(), name='employee-list'),
    path("csrf/", views.csrf, name="csrf"),
    path("csrf_setup/", csrf_setup, name="csrf_setup"),
    path('create_employee/', create_employee_page, name='create_employee'),
]

urlpatterns += [
    path('employees/<int:employee_id>/submit_timesheet/', SubmitTimeLogView.as_view(), name='submit-timelog'),
]

urlpatterns += [
    path('employees/timelogs/', EmployeeTimeLogsView.as_view(), name='employee-timelogs'),
]

urlpatterns += [
    path('employees/<int:employee_id>/pto/', PTOUpdateView.as_view(), name='update-pto'),
]

urlpatterns += [
    path('employees/<int:employee_id>/get_timesheet/', TimeLogListView.as_view(), name='get-timelog'),
]

urlpatterns += [
    path('ptoBalance/', GetPTOView.as_view(), name='get-pto'),
]

urlpatterns += [
    path('payPeriod/', CurrentWeekView.as_view(), name='get-payperiod'),
]

urlpatterns += [
    path('timelogs/<int:pk>/', views.TimeLogUpdateView.as_view(), name='update-timelog'),
]

urlpatterns = [
    path('verify-token/', verify_token, name='verify_token'),  # Add this line
]