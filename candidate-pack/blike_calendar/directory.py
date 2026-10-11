from collections.abc import Iterable

from .models import Employee


class EmployeeDirectory:
    def __init__(self, employees: Iterable[Employee]):
        self._employees = {employee.employee_id: employee for employee in employees}

    def require(self, employee_id: str) -> Employee:
        try:
            return self._employees[employee_id]
        except KeyError:
            raise ValueError(f"Unknown employee: {employee_id}") from None
