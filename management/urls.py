from django.urls import path
from .views import EmployeeListView, login_view, logout_view, csrf_setup, SubmitTimeLogView, EmployeeTimeLogsView, PTOUpdateView, TimeLogListView, create_employee_page, GetPTOView, CurrentWeekView, verify_token
from . import views

urlpatterns = [
    path('api/user/user/login/', login_view, name='login'),  # Login route
    path('api/user/user/logout/', logout_view, name='logout'),  # Logout route
    path('api/user/user/employees/', EmployeeListView.as_view(), name='employee-list'),
    path("api/user/user/csrf/", views.csrf, name="csrf"),
    path("api/user/user/csrf_setup/", csrf_setup, name="csrf_setup"),
    path('api/user/user/create_employee/', create_employee_page, name='create_employee'),
]

urlpatterns += [
    path('api/user/user/employees/<int:employee_id>/submit_timesheet/', SubmitTimeLogView.as_view(), name='submit-timelog'),
]

urlpatterns += [
    path('api/user/user/employees/timelogs/', EmployeeTimeLogsView.as_view(), name='employee-timelogs'),
]

urlpatterns += [
    path('api/user/user/employees/<int:employee_id>/pto/', PTOUpdateView.as_view(), name='update-pto'),
]

urlpatterns += [
    path('api/user/user/employees/<int:employee_id>/get_timesheet/', TimeLogListView.as_view(), name='get-timelog'),
]

urlpatterns += [
    path('api/user/user/ptoBalance/', GetPTOView.as_view(), name='get-pto'),
]

urlpatterns += [
    path('api/user/user/payPeriod/', CurrentWeekView.as_view(), name='get-payperiod'),
]

urlpatterns += [
    path('api/user/user/timelogs/<int:pk>/', views.TimeLogUpdateView.as_view(), name='update-timelog'),
]

urlpatterns = [
    path('api/user/user/verify-token/', verify_token, name='verify_token'),  # Add this line
]