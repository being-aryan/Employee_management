from .department_service import DepartmentManager
from .employee_service import EmployeeManager

department_manager = DepartmentManager()
employee_manager = EmployeeManager(department_manager)
