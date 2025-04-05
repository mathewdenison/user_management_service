import json
from django.utils import timezone
from rest_framework import generics, permissions
from rest_framework.permissions import BasePermission
from rest_framework.views import APIView
from management.models import Employee
from management.serializers import EmployeeSerializer
from rest_framework.decorators import api_view
from django.contrib.auth import authenticate, login, logout
from django.views.decorators.csrf import csrf_exempt
from rest_framework.permissions import AllowAny
from .utils import send_message_to_topic
from django.middleware.csrf import get_token
from django.http import JsonResponse
from django.shortcuts import render, redirect
from .forms import EmployeeUserForm, EmployeeForm
from django.contrib.auth.decorators import login_required
from datetime import timedelta
import logging
from google.cloud import logging as cloud_logging
from rest_framework import status
from dotenv import load_dotenv
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
import os

load_dotenv()

log_group = os.getenv('LOG_GROUP_MAIN')
stream_name = os.getenv('STREAM_NAME_MAIN')

client = cloud_logging.Client()
client.setup_logging()

# Logger setup
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.propagate = False


@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
@csrf_exempt
def login_view(request):
    if request.method == 'POST':
        logger.info("LOGIN VIEW REACHED")
        username = request.data.get('username')
        password = request.data.get('password')

        logger.info(f"Username: {username}, Password: {password}")

        user = authenticate(request, username=username, password=password)
        logger.info(f"User authenticated")
        if user is not None:  # Check if the user exists
            logger.info(f"User is not none")
            token, _ = Token.objects.get_or_create(
                user=user)
            if user.is_superuser:  # The user is a superuser
                logger.info(f"User is a superuser")
                login(request, user)
                logger.info(f"Logged in")
                return redirect('create_employee')
            if hasattr(user, 'employee'):  # Ensure User has an Employee profile
                logger.info(f"User has attribute Employee")
                if user.employee.role in ['Manager', 'HR', 'Employee']:
                    logger.info(f"User is a Manager, HR, or Employee")
                    login(request, user)  # Log the user in (create session)
                    logger.info(f"Logged in")
                    # Retrieve CSRF token from the cookies
                    csrf_token = get_token(request)
                    logger.info("%s the csrf token", csrf_token)
                    logger.info(f"Employee: {user.employee}")
                    employee = user.employee
                    return JsonResponse(
                        {
                            "message": f"You are logged in as {username}",
                            "role": employee.role,
                            "employee_id": employee.id,
                            "auth_token": token.key,
                            "csrf_token": csrf_token,  # Send the cookie token in the response
                        },
                        status=200
                    )
                return JsonResponse({"error": "Access Denied: You do not have the required role."}, status=403)
            return JsonResponse({"error": "Invalid credentials"}, status=401)
        return JsonResponse({"error": "Unable to find user"}, status=400)
    elif request.method == 'GET':  # Handling for GET requests
        # In this case, simply render the login form
        return render(request, 'management/login.html')
    else:
        # In case of any other HTTP methods, return not allowed response
        return JsonResponse({'error': 'Method not allowed'}, status=405)


@api_view(["GET"])
@permission_classes([AllowAny])
def csrf_setup(request):
    csrf_token = get_token(request)  # Retrieve the CSRF token
    return JsonResponse({"csrf_token": csrf_token})

@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def verify_token(request):
    # If the request is authenticated (valid token), send a success response
    return JsonResponse({"message": "Token is valid."}, status=200)


# Logout View
@csrf_exempt
@permission_classes([AllowAny])
@api_view(['POST'])
def logout_view(request):
    logger.info(f"CSRF Token from Client: {request.headers.get('X-CSRFToken')}")
    logger.info(f"CSRF Token Expected: {get_token(request)}")
    logout(request)  # Destroy the user session
    return Response({"message": "You have been logged out successfully."}, status=200)


@login_required
@csrf_exempt
def create_employee_page(request):
    if request.method == "POST":
        user_form = EmployeeUserForm(request.POST)
        employee_form = EmployeeForm(request.POST)
        if user_form.is_valid() and employee_form.is_valid():
            user = user_form.save()
            employee = employee_form.save(commit=False)
            employee.user = user
            employee.save()
            return redirect('create_employee')
    else:
        user_form = EmployeeUserForm()
        employee_form = EmployeeForm()
    return render(request, 'management/create_employee.html', {'user_form': user_form, 'employee_form': employee_form})


def csrf(request):
    return JsonResponse({"csrfToken": get_token(request)})


class IsManagerOrHR(BasePermission):
    def has_permission(self, request, view):
        logger.info(f"In check permissions")
        # Ensure user has an employee profile
        if not hasattr(request.user, 'employee'):
            logger.info(f"Doesn't have permissions")
            return False
        logger.info(f"Not in if")
        # Allow if the user has Manager or HR role
        return request.user.employee.role in ['Manager', 'HR']


class EmployeeListView(APIView):
    permission_classes = [IsManagerOrHR]

    def get(self, request):
        logger.info(f"In Employee List View get")
        if request.user.employee.role == 'HR':
            # HR sees all management in the organization
            employees = Employee.objects.all()
        elif request.user.employee.role == 'Manager':
            # Managers see only management within their department
            employees = Employee.objects.filter(department=request.user.employee.department)
        else:
            return Response({"error": "You do not have access to this resource."}, status=403)

        serializer = EmployeeSerializer(employees, many=True)
        return Response(serializer.data)


class TimeLogListView(APIView):
    def get(self, *args, **kwargs):
        employee_id = self.kwargs.get('employee_id')
        if not employee_id:
            return Response({"error": "employee_id is required"}, status=400)

        # Prepare data to be sent to queue
        queue_data = {
            "employee_id": employee_id,
        }

        # Send data to queue for further processing
        """FIXME Update the queue name to be an environment variable"""
        message_id = send_message_to_topic('timelog_list_queue', queue_data, 'GET')

        return Response(
            {
                "message": "Time log list retrieval request successfully sent to the queue for processing.",
                "message_id": message_id,
            },
            status=200,
        )


class SubmitTimeLogView(APIView):
    def post(self, request, *args, **kwargs):
        if request.data is None:
            return Response({"message": "Request data cannot be empty."}, status=400)

        message_body = json.dumps(request.data)

        # Send to timelog service
        message_id = send_message_to_topic('timelog_processing_queue', message_body, 'POST')

        # Send dashboard update payload to dashboard-queue
        dashboard_payload = {
            "employee_id": request.data.get("employee"),
            "type": "timelog_submitted",
            "payload": {
                "week_start_date": request.data.get("week_start_date"),
                "pto_hours": request.data.get("pto_hours"),
                "employee_id": request.data.get("employee"),
            },
        }

        send_message_to_topic('dashboard-queue', dashboard_payload, 'POST')

        return Response(
            {
                "message": "Time log successfully sent to the queue for processing.",
                "message_id": message_id,
            },
            status=200,
        )


class EmployeeTimeLogsView(APIView):
    def get(self, *args, **kwargs):
        # Make sure the incoming request has user data
        if self.request.user is None or self.request.user.employee.role is None:
            return Response(
                {
                    "message": "Request data is missing user or user role."
                },
                status=400,
            )

        role = self.request.user.employee.role
        employee_id = self.request.user.employee.id
        queue_data = {
            "role": role,
            "employee_id": employee_id
        }

        # Send data to queue for further processing in TimeLog Management Service
        """FIXME Update the queue name to be an environment variable"""
        message_id = send_message_to_topic('employee_timelog_list_queue', queue_data, 'GET')

        return Response(
            {
                "message": "Time log list request successfully sent to the queue for processing.",
                "message_id": message_id,
            },
            status=200,
        )


class PTOUpdateView(APIView):
    permission_classes = [IsManagerOrHR]

    def patch(self, request, employee_id):
        if self.request.user.employee.role != 'HR':
            return Response({"error": "Only HR can update PTO balance."}, status=403)

        try:
            employee = Employee.objects.get(pk=employee_id)
        except Employee.DoesNotExist:
            return Response({"error": "Employee not found."}, status=404)

        new_balance = request.data.get("pto_balance")
        if new_balance is None:
            return Response({"error": "PTO balance is required."}, status=400)

        queue_data = {
            "employee_id": employee_id,
            "new_balance": new_balance,
        }

        message_id = send_message_to_topic('pto_update_processing_queue', queue_data, 'PATCH')

        # Send real-time update to dashboard
        dashboard_payload = {
            "employee_id": employee_id,
            "type": "pto_updated",
            "payload": {
                "pto_balance": new_balance
            },
        }
        send_message_to_topic('dashboard-queue', dashboard_payload, 'POST')

        return Response(
            {
                "message": "PTO update request successfully sent to the queue for processing.",
                "message_id": message_id,
            },
            status=200,
        )


class CurrentWeekView(APIView):
    def get(self, request):
        # Get current date
        today = timezone.localtime(timezone.now()).date()

        # Check if today is Saturday or Sunday
        if today.weekday() >= 5:  # 5 and 6 corresponds to Saturday and Sunday
            # if it's the weekend shift 'start' to next Monday
            start = today + timedelta(days=7 - today.weekday())
        else:
            # Calculate start of the week (Monday)
            start = today - timedelta(days=today.weekday())

        # Calculate end of the week (Friday)
        end = start + timedelta(days=4)

        return Response({
            'week_start_date': start,
            'week_end_date': end
        })



class GetPTOView(APIView):
    def get(self, *args, **kwargs):
        employee_id = self.request.query_params.get('employee_id')
        if not employee_id:
            return Response({"error": "employee_id is required"}, status=400)

        # Prepare data to be sent to queue
        queue_data = {
            "employee_id": employee_id,
        }

        # Send data to queue for further processing
        """FIXME Update the queue name to be an environment variable"""
        message_id = send_message_to_topic('user_pto_queue', queue_data, 'GET')

        return Response(
            {
                "message": "PTO retrieval request successfully sent to the queue for processing.",
                "message_id": message_id,
            },
            status=200,
        )


class IsHR(permissions.BasePermission):
    """
    Custom permission to check if authenticated user is HR.
    """

    def has_object_permission(self, request, view, obj):
        return request.user.employee.role == 'HR'


class IsManagerOfEmployee(permissions.BasePermission):
    """
    Custom permission to only allow managers of an employee to edit the TimeLog.
    """

    def has_object_permission(self, request, view, obj):
        return request.user.employee.role == 'Manager' and obj.employee.manager == request.user.employee


class TimeLogUpdateView(APIView):
    permission_classes = [IsAuthenticated, IsHR | IsManagerOfEmployee]

    def patch(self, request, timelog_id):
        # Check the incoming request data contains timelog data.
        data = request.data
        if not data:
            return Response({"error": "TimeLog data is required."}, status=status.HTTP_400_BAD_REQUEST)

        # Prepare data to be sent to queue
        queue_data = {
            "timelog_id": timelog_id,
            "data": data,
        }

        # Send data to queue for further processing in TimeLog Update Service
        """FIXME Update the queue name to be an environment variable"""
        message_id = send_message_to_topic('timelog_update_queue', queue_data, 'PATCH')

        return Response(
            {
                "message": "TimeLog update request successfully sent to the queue for processing.",
                "message_id": message_id,
            },
            status=status.HTTP_200_OK,
        )
