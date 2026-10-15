from app.managers.department_service import DepartmentManager
from app.managers.employee_service import EmployeeManager

department_manager = DepartmentManager()
employee_manager = EmployeeManager(department_manager)