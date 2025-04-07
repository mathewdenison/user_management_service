from django.urls import path
from .views import (
    EmployeeListView, login_view, logout_view, csrf_setup, SubmitTimeLogView,
    EmployeeTimeLogsView, PTOUpdateView, TimeLogListView, create_employee_page,
    GetPTOView, CurrentWeekView, verify_token, BulkPTOView, TimeLogUpdateView
)

urlpatterns = [
    path('login/', login_view, name='login'),  # Login route
    path('logout/', logout_view, name='logout'),  # Logout route
    path('employees/', EmployeeListView.as_view(), name='employee-list'),
    path('csrf/', csrf_setup, name='csrf'),
    path('csrf_setup/', csrf_setup, name='csrf_setup'),
    path('create_employee/', create_employee_page, name='create_employee'),
    path('employees/<int:employee_id>/submit_timesheet/', SubmitTimeLogView.as_view(), name='submit-timelog'),
    path('employees/timelogs/', EmployeeTimeLogsView.as_view(), name='employee-timelogs'),
    path('employees/<int:employee_id>/pto/', PTOUpdateView.as_view(), name='update-pto'),
    path('employees/<int:employee_id>/get_timesheet/', TimeLogListView.as_view(), name='get-timelog'),
    path('ptoBalance/', GetPTOView.as_view(), name='get-pto'),
    path('payPeriod/', CurrentWeekView.as_view(), name='get-payperiod'),
    path('timelogs/<int:pk>/', TimeLogListView.as_view(), name='update-timelog'),
    path('verify-token/', verify_token, name='verify_token'),
    path('bulk_pto/', BulkPTOView.as_view(), name='bulk-pto'),
    path('timelogs/<int:pk>/', TimeLogUpdateView.as_view(), name='update-timelog'),
]
