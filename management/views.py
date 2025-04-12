import json
import uuid

from django.utils import timezone
from rest_framework import permissions
from rest_framework.permissions import BasePermission
from rest_framework.views import APIView
from management.models import Employee
from management.serializers import EmployeeSerializer
from django.views.decorators.csrf import csrf_exempt
from rest_framework.permissions import AllowAny
from .utils import send_message_to_topic
from django.middleware.csrf import get_token
from django.http import JsonResponse
from django.shortcuts import render, redirect
from .forms import EmployeeUserForm, EmployeeForm
from datetime import timedelta
import logging
from google.cloud import logging as cloud_logging
from rest_framework import status
from dotenv import load_dotenv
from rest_framework.response import Response
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
import os
from passlib.context import CryptContext

logger = logging.getLogger(__name__)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

load_dotenv()

log_group = os.getenv('LOG_GROUP_MAIN')
stream_name = os.getenv('STREAM_NAME_MAIN')

client = cloud_logging.Client()
client.setup_logging()

# Logger setup
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.propagate = False

def authenticate_employee(username: str, password: str):
    """
    Returns an Employee object if the username/password are valid,
    else returns None.
    """
    employee = Employee.get_by_username(username)
    if not employee:
        return None
    # check password
    if employee.verify_password(password):
        return employee
    return None

@csrf_exempt
def create_employee_page(request):
    if request.method == "POST":
        employee_form = EmployeeForm(request.POST)

        if employee_form.is_valid():
            emp = employee_form.save()
            return redirect('create_employee')
    else:
        employee_form = EmployeeForm()

    return render(request, 'management/create_employee.html', {
        'employee_form': employee_form,
    })


@api_view(["POST"])
@permission_classes([AllowAny])
def create_employee_view(request):
    data = request.data

    username = data.get("username")
    password = data.get("password")
    name = data.get("name")
    role = data.get("role", "Employee")         # default to Employee if not specified
    department = data.get("department", "")
    manager_id = data.get("manager_id", None)

    # Basic validation
    if not username or not password or not name:
        return Response({"error": "username, password, and name are required"},
                        status=status.HTTP_400_BAD_REQUEST)

    # Check if username already exists in Firestore
    existing = Employee.get_by_username(username)
    if existing:
        return Response({"error": "Username already taken."}, status=status.HTTP_400_BAD_REQUEST)

    # Generate a doc ID
    employee_id = str(uuid.uuid4())

    # Hash the password
    hashed_password = pwd_context.hash(password)

    # Create the Employee object
    emp = Employee(
        employee_id=employee_id,
        user_id="",  # or if you want to store some user id
        name=name,
        role=role,
        department=department,
        manager_id=manager_id,
        username=username,
        hashed_password=hashed_password,
    )
    emp.save()  # Writes to Firestore

    return Response(
        {
            "message": "Employee created successfully.",
            "employee_id": emp.employee_id,
            "username": emp.username,
            "role": emp.role,
            "department": emp.department,
            "manager_id": emp.manager_id,
        },
        status=status.HTTP_201_CREATED
    )

@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
@csrf_exempt
def login_view(request):
    if request.method == 'POST':
        logger.info("LOGIN VIEW REACHED")
        username = request.data.get('username')
        password = request.data.get('password')
        logger.info(f"Username: {username}, Password: {password}")

        # Use your custom Firestore-based auth
        employee = authenticate_employee(username, password)
        logger.info("Employee authenticated? %s", bool(employee))

        if employee is not None:  # Means valid username/password
            # For example, create a fake token (UUID) or implement your own token logic
            token = str(uuid.uuid4())

            # If you previously had "superuser" logic, you could store it in employee.role or a separate field:
            if employee.role == 'Superuser':
                logger.info("Employee is superuser")
                # Possibly do a redirect or just return a JSON
                return redirect('create_employee')

            # If the employee has a recognized role
            if employee.role in ['Manager', 'HR', 'Employee']:
                logger.info(f"Employee is a {employee.role}")
                # If you still want a session-based approach, you can set session data:
                # request.session['employee_id'] = employee.employee_id
                # (Only works if you still have SessionMiddleware, but that's optional.)

                csrf_token = get_token(request)  # If you still have CSRF enabled
                logger.info("%s the csrf token", csrf_token)

                # Return a JSON response with similar structure
                return JsonResponse(
                    {
                        "message": f"You are logged in as {username}",
                        "role": employee.role,
                        "employee_id": employee.employee_id,
                        "auth_token": token,
                        "csrf_token": csrf_token,  # just for example
                    },
                    status=200
                )
                # Or if the role isn't recognized as 'Manager', 'HR', or 'Employee'
            return JsonResponse({"error": "Access Denied: You do not have the required role."}, status=403)
        else:
            return JsonResponse({"error": "Unable to find user or invalid password"}, status=400)

    elif request.method == 'GET':
        # In this case, simply render the login form template (if you still use templates)
        return render(request, 'management/login.html')
    else:
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

    return Response({"message": "You have been logged out successfully."}, status=200)


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
            employees = Employee.get_all()
        elif request.user.employee.role == 'Manager':
            # Managers see only management within their department
            employees = Employee.get_by_department(request.user.employee.department)
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
        if not request.data:
            return Response({"message": "Request data cannot be empty."}, status=400)

        # Build the message body using all keys from request.data
        message_body = {
            "employee": request.data.get("employee"),
            "week_start_date": request.data.get("week_start_date"),
            "week_end_date": request.data.get("week_end_date"),
            "monday_hours": request.data.get("monday_hours"),
            "tuesday_hours": request.data.get("tuesday_hours"),
            "wednesday_hours": request.data.get("wednesday_hours"),
            "thursday_hours": request.data.get("thursday_hours"),
            "friday_hours": request.data.get("friday_hours"),
            "pto_hours": request.data.get("pto_hours")
        }

        message_id = send_message_to_topic(
            'timelog-processing-queue',
            json.dumps(message_body),
            'POST'
        )

        return Response(
            {
                "message": "Time log successfully sent to the queue for processing.",
                "message_id": message_id,
            },
            status=200,
        )



class EmployeeTimeLogsView(APIView):
    def get(self, *args, **kwargs):
        # Ensure the request has user data and role.
        if self.request.user is None or self.request.user.employee.role is None:
            return Response(
                {"message": "Request data is missing user or user role."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        role = self.request.user.employee.role
        current_employee = self.request.user.employee

        # Build the list of employee IDs.
        if role == "HR":
            # HR sees all employees.
            employee_ids = list(Employee.get_all().values_list('id', flat=True))
        elif role == "Manager":
            # Retrieve all employees that report to this manager using the reverse relation,
            # then include the manager's own ID.
            subordinates = Employee.get_subordinates(current_employee.employee_id)
            subordinate_ids = [sub.employee_id for sub in subordinates]
            subordinate_ids.append(current_employee.employee_id)  # manager sees themself too
            employee_ids = subordinate_ids
        else:
            # Regular employee sees only their own timelogs.
            employee_ids = [current_employee.employee_id]

        queue_data = {
            "role": role,
            "employee_ids": employee_ids,
        }

        message_id = send_message_to_topic('employee_timelog_list_queue', queue_data, 'GET')

        return Response(
            {
                "message": "Time log list request successfully sent to the queue for processing.",
                "message_id": message_id,
            },
            status=status.HTTP_200_OK,
        )

class PTOUpdateView(APIView):
    permission_classes = [IsManagerOrHR]

    def patch(self, request, employee_id):
        # Only HR is allowed
        if self.request.user.employee.role != 'HR':
            return Response({"error": "Only HR can update PTO balance."}, status=403)

        employee = Employee.get_by_id(employee_id)
        if not employee:
            return Response({"error": "Employee not found."}, status=404)

        new_balance = request.data.get("pto_balance")
        if new_balance is None:
            return Response({"error": "PTO balance is required."}, status=400)

        # Only send message to the PTO service for actual update and logging
        queue_data = {
            "employee_id": employee_id,
            "new_balance": new_balance
        }

        message_id = send_message_to_topic(
            'pto_update_processing_queue',
            json.dumps(queue_data),  # Make sure message is JSON string
            'PATCH'
        )

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

    def patch(self, request, pk):
        data = request.data
        if not data:
            return Response({"error": "TimeLog data is required."}, status=status.HTTP_400_BAD_REQUEST)

        queue_data = {
            "timelog_id": pk,
            "data": data,
        }

        message_id = send_message_to_topic('timelog_update_queue', queue_data, 'PATCH')
        logger.info(f"Sending patch to timelog_update_queue for TimeLogUpdateView")
        return Response(
            {
                "message": "TimeLog update request successfully sent to the queue for processing.",
                "message_id": message_id,
            },
            status=status.HTTP_200_OK,
        )


class BulkPTOView(APIView):
    permission_classes = [IsHR]

    def post(self, request, *args, **kwargs):
        if not request.data:
            return Response({"error": "Request data cannot be empty."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            message_body = request.data

            message_id = send_message_to_topic('bulk_pto_queue', json.dumps(message_body), 'POST')

            logger.info(f"Bulk PTO update message published. Message ID: {message_id}")

            return Response({
                "message": "Bulk PTO update request successfully sent to the queue for processing.",
                "message_id": message_id,
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.exception(f"Error processing Bulk PTO update: {str(e)}")
            return Response({"error": f"Error processing Bulk PTO update: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

