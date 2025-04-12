# new_employee.py
from typing import Optional
from google.cloud import firestore
from passlib.context import CryptContext

db = firestore.Client()

# Set up a Passlib context for hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class Employee:
    """
    A Firestore-backed Employee "model".
    """
    def __init__(
            self,
            employee_id: str,
            user_id: str,             # keep if you still want a separate concept of user_id
            name: str,
            role: str,
            department: str,
            manager_id: Optional[str] = None,
            username: Optional[str] = None,    # new
            hashed_password: Optional[str] = None,  # new
    ):
        self.employee_id = employee_id
        self.user_id = user_id
        self.name = name
        self.role = role
        self.department = department
        self.manager_id = manager_id
        self.username = username or ""
        self.hashed_password = hashed_password or ""

    @staticmethod
    def from_dict(doc_id: str, source: dict):
        return Employee(
            employee_id=doc_id,
            user_id=source.get('user_id', ''),
            name=source.get('name', ''),
            role=source.get('role', ''),
            department=source.get('department', ''),
            manager_id=source.get('manager_id'),
            username=source.get('username', ''),         # load from Firestore
            hashed_password=source.get('hashed_password', ''),  # load
        )

    def to_dict(self) -> dict:
        return {
            'user_id': self.user_id,
            'name': self.name,
            'role': self.role,
            'department': self.department,
            'manager_id': self.manager_id,
            'username': self.username,                  # store username
            'hashed_password': self.hashed_password,    # store hashed password
        }

    def save(self):
        doc_ref = db.collection("employees").document(self.employee_id)
        doc_ref.set(self.to_dict())

    @staticmethod
    def get_by_id(employee_id: str):
        doc_snapshot = db.collection("employees").document(employee_id).get()
        if doc_snapshot.exists:
            return Employee.from_dict(doc_snapshot.id, doc_snapshot.to_dict())
        return None

    @staticmethod
    def get_by_username(username: str):
        # Firestore doesn't have a unique index, but we'll assume there's at most one doc with this username
        docs = db.collection("employees").where("username", "==", username).stream()
        for doc in docs:
            return Employee.from_dict(doc.id, doc.to_dict())
        return None

    @staticmethod
    def get_all():
        docs = db.collection("employees").get()
        return [Employee.from_dict(doc.id, doc.to_dict()) for doc in docs]

    @staticmethod
    def get_by_department(department: str):
        docs = db.collection("employees").where("department", "==", department).stream()
        return [Employee.from_dict(doc.id, doc.to_dict()) for doc in docs]

    @staticmethod
    def get_subordinates(manager_id: str):
        docs = db.collection("employees").where("manager_id", "==", manager_id).stream()
        return [Employee.from_dict(doc.id, doc.to_dict()) for doc in docs]

    def delete(self):
        db.collection("employees").document(self.employee_id).delete()

    # -----------------------
    # Password-related methods
    # -----------------------
    def set_password(self, raw_password: str):
        """Hashes and sets the password."""
        self.hashed_password = pwd_context.hash(raw_password)

    def verify_password(self, raw_password: str) -> bool:
        """Checks if the provided password matches the stored hash."""
        if not self.hashed_password:
            return False
        return pwd_context.verify(raw_password, self.hashed_password)
