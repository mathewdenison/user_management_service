# new_employee.py (for example)
from typing import Optional
from google.cloud import firestore

db = firestore.Client()  # Make sure you have credentials set up for Firestore

class Employee:
    """
    A Firestore-backed Employee "model".
    """
    def __init__(self,
                 employee_id: str,         # typically the Firestore doc ID
                 user_id: str,            # store the associated user ID as a string
                 name: str,
                 role: str,
                 department: str,
                 manager_id: Optional[str] = None):  # store manager's doc ID or None
        self.employee_id = employee_id
        self.user_id = user_id
        self.name = name
        self.role = role
        self.department = department
        self.manager_id = manager_id

    @staticmethod
    def from_dict(doc_id: str, source: dict):
        """
        Rebuild an EmployeeFS instance from a Firestore document dict.
        """
        return Employee(
            employee_id=doc_id,
            user_id=source.get('user_id', ''),
            name=source.get('name', ''),
            role=source.get('role', ''),
            department=source.get('department', ''),
            manager_id=source.get('manager_id')  # Could be None or a string
        )

    def to_dict(self) -> dict:
        """
        Convert this in-memory object to a dict for Firestore.
        """
        return {
            'user_id': self.user_id,
            'name': self.name,
            'role': self.role,
            'department': self.department,
            'manager_id': self.manager_id
        }

    def save(self):
        """
        Save this object to Firestore. If the employee_id doesn't exist yet,
        Firestore creates a new doc. If it does exist, Firestore overwrites/updates it.
        """
        doc_ref = db.collection("employees").document(self.employee_id)
        doc_ref.set(self.to_dict())

    @staticmethod
    def get_by_id(employee_id: str):
        doc_ref = db.collection("employees").document(employee_id).get()
        if doc_ref.exists:
            return Employee.from_dict(doc_ref.id, doc_ref.to_dict())
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
        # Query Firestore for employees whose manager_id == manager_id
        docs = db.collection("employees").where("manager_id", "==", manager_id).stream()
        return [Employee.from_dict(doc.id, doc.to_dict()) for doc in docs]

    def delete(self):
        db.collection("employees").document(self.employee_id).delete()
