from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from sqlalchemy.exc import IntegrityError

from app.exceptions import (
    DepartmentNotFoundError,
    EmployeeEmailAlreadyExistError,
    EmployeeNotFoundError,
)
from app.managers.employee_service import EmployeeManager
from app.models.department import Department as DepartmentModel
from app.models.employee import EmployeeStatus as ModelEmployeeStatus
from app.schemas import (
    CreateEmployee,
    EmployeeReplace,
    EmployeeStatus,
    EmployeeStatusUpdate,
    EmployeeUpdate,
)


def make_department():
    return DepartmentModel(id=1, name="Engineering")


def make_employee(
    employee_id=1,
    email="aryan@example.com",
    is_deleted=False,
):
    department = make_department()

    return SimpleNamespace(
        id=employee_id,
        name="Aryan",
        email=email,
        department_id=department.id,
        department=department,
        salary=Decimal("50000.00"),
        status=ModelEmployeeStatus.ACTIVE,
        is_deleted=is_deleted,
    )


def make_integrity_error(constraint_name):
    original_error = SimpleNamespace(
        diag=SimpleNamespace(constraint_name=constraint_name)
    )

    return IntegrityError(
        "INSERT statement",
        {},
        original_error,
    )


def configure_paginated_result(mock_session, employees, total):
    result = MagicMock()
    result.unique.return_value.all.return_value = employees

    mock_session.scalar.return_value = total
    mock_session.scalars.return_value = result


@pytest.mark.asyncio
async def test_get_employee_by_id_success(mock_session, fake_employee):
    mock_session.scalar.return_value = fake_employee

    result = await EmployeeManager().get_employee_by_id(
        mock_session,
        fake_employee.id,
    )

    assert result.id == fake_employee.id
    assert result.name == fake_employee.name
    assert result.email == fake_employee.email
    assert result.department == fake_employee.department.name
    mock_session.scalar.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_employee_by_id_not_found(mock_session):
    mock_session.scalar.return_value = None

    with pytest.raises(EmployeeNotFoundError):
        await EmployeeManager().get_employee_by_id(mock_session, 999)


@pytest.mark.asyncio
async def test_create_employee_success(mock_session):
    department = make_department()

    mock_session.scalar.side_effect = [department, None]
    mock_session.add.side_effect = lambda employee: setattr(employee, "id", 101)

    employee_data = CreateEmployee(
        name="Aryan",
        email="ARYAN@example.com",
        department="Engineering",
        salary=50000,
        status=EmployeeStatus.ACTIVE,
    )

    result = await EmployeeManager().create_employee(
        mock_session,
        employee_data,
    )

    assert result.id == 101
    assert result.email == "aryan@example.com"
    assert result.department == "Engineering"
    mock_session.add.assert_called_once()
    mock_session.commit.assert_awaited_once()
    mock_session.refresh.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_employee_department_not_found(mock_session):
    mock_session.scalar.return_value = None

    employee_data = CreateEmployee(
        name="Aryan",
        email="aryan@example.com",
        department="Unknown",
        salary=50000,
        status=EmployeeStatus.ACTIVE,
    )

    with pytest.raises(DepartmentNotFoundError):
        await EmployeeManager().create_employee(
            mock_session,
            employee_data,
        )

    mock_session.add.assert_not_called()


@pytest.mark.asyncio
async def test_create_employee_duplicate_email(mock_session):
    department = make_department()

    mock_session.scalar.side_effect = [department, 10]

    employee_data = CreateEmployee(
        name="Aryan",
        email="aryan@example.com",
        department="Engineering",
        salary=50000,
        status=EmployeeStatus.ACTIVE,
    )

    with pytest.raises(EmployeeEmailAlreadyExistError):
        await EmployeeManager().create_employee(
            mock_session,
            employee_data,
        )

    mock_session.add.assert_not_called()


@pytest.mark.asyncio
async def test_create_employee_integrity_error(mock_session):
    department = make_department()

    mock_session.scalar.side_effect = [department, None]
    mock_session.commit.side_effect = make_integrity_error("uq_employees_active_email")

    employee_data = CreateEmployee(
        name="Aryan",
        email="aryan@example.com",
        department="Engineering",
        salary=50000,
        status=EmployeeStatus.ACTIVE,
    )

    with pytest.raises(EmployeeEmailAlreadyExistError):
        await EmployeeManager().create_employee(
            mock_session,
            employee_data,
        )

    mock_session.rollback.assert_awaited_once()


@pytest.mark.asyncio
async def test_commit_employee_change_unrelated_integrity_error(
    mock_session,
):
    error = make_integrity_error("some_other_constraint")
    mock_session.commit.side_effect = error

    with pytest.raises(IntegrityError) as exc_info:
        await EmployeeManager._commit_employee_change(mock_session)

    assert exc_info.value is error
    mock_session.rollback.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_employee_success(mock_session):
    employee = make_employee()
    department = make_department()

    mock_session.scalar.side_effect = [
        employee,
        department,
        None,
    ]

    employee_data = EmployeeReplace(
        name="Updated Aryan",
        email="UPDATED@example.com",
        department="Engineering",
        salary=60000,
        status=EmployeeStatus.ACTIVE,
    )

    result = await EmployeeManager().update_employee(
        mock_session,
        employee.id,
        employee_data,
    )

    assert result.name == "Updated Aryan"
    assert result.email == "updated@example.com"
    assert result.salary == 60000
    mock_session.commit.assert_awaited_once()
    mock_session.refresh.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_employee_not_found(mock_session):
    mock_session.scalar.return_value = None

    employee_data = EmployeeReplace(
        name="Updated Aryan",
        email="updated@example.com",
        department="Engineering",
        salary=60000,
        status=EmployeeStatus.ACTIVE,
    )

    with pytest.raises(EmployeeNotFoundError):
        await EmployeeManager().update_employee(
            mock_session,
            999,
            employee_data,
        )


@pytest.mark.asyncio
async def test_update_employee_department_not_found(mock_session):
    employee = make_employee()

    mock_session.scalar.side_effect = [
        employee,
        None,
    ]

    employee_data = EmployeeReplace(
        name="Updated Aryan",
        email="updated@example.com",
        department="Unknown",
        salary=60000,
        status=EmployeeStatus.ACTIVE,
    )

    with pytest.raises(DepartmentNotFoundError):
        await EmployeeManager().update_employee(
            mock_session,
            employee.id,
            employee_data,
        )


@pytest.mark.asyncio
async def test_update_employee_duplicate_email(mock_session):
    employee = make_employee()
    department = make_department()

    mock_session.scalar.side_effect = [
        employee,
        department,
        10,
    ]

    employee_data = EmployeeReplace(
        name="Updated Aryan",
        email="another@example.com",
        department="Engineering",
        salary=60000,
        status=EmployeeStatus.ACTIVE,
    )

    with pytest.raises(EmployeeEmailAlreadyExistError):
        await EmployeeManager().update_employee(
            mock_session,
            employee.id,
            employee_data,
        )


@pytest.mark.asyncio
async def test_update_employee_partial_success(mock_session):
    employee = make_employee()
    mock_session.scalar.return_value = employee

    employee_data = EmployeeUpdate(
        name="Updated Aryan",
        salary=70000,
    )

    result = await EmployeeManager().update_employee_partial(
        mock_session,
        employee.id,
        employee_data,
    )

    assert result.name == "Updated Aryan"
    assert result.salary == 70000
    mock_session.commit.assert_awaited_once()
    mock_session.refresh.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_employee_partial_no_changes(mock_session):
    employee = make_employee()
    mock_session.scalar.return_value = employee

    result = await EmployeeManager().update_employee_partial(
        mock_session,
        employee.id,
        EmployeeUpdate(),
    )

    assert result.id == employee.id
    mock_session.commit.assert_not_awaited()
    mock_session.refresh.assert_not_awaited()


@pytest.mark.asyncio
async def test_update_employee_partial_not_found(mock_session):
    mock_session.scalar.return_value = None

    with pytest.raises(EmployeeNotFoundError):
        await EmployeeManager().update_employee_partial(
            mock_session,
            999,
            EmployeeUpdate(name="Updated Aryan"),
        )


@pytest.mark.asyncio
async def test_update_employee_partial_null_value(mock_session):
    employee = make_employee()
    mock_session.scalar.return_value = employee

    with pytest.raises(ValueError, match="Name cannot be null"):
        await EmployeeManager().update_employee_partial(
            mock_session,
            employee.id,
            EmployeeUpdate(name=None),
        )

    mock_session.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_update_employee_partial_department(mock_session):
    employee = make_employee()
    department = DepartmentModel(id=2, name="HR")

    mock_session.scalar.side_effect = [
        employee,
        department,
    ]

    result = await EmployeeManager().update_employee_partial(
        mock_session,
        employee.id,
        EmployeeUpdate(department="HR"),
    )

    assert result.department == "HR"
    mock_session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_employee_partial_department_not_found(mock_session):
    employee = make_employee()

    mock_session.scalar.side_effect = [
        employee,
        None,
    ]

    with pytest.raises(DepartmentNotFoundError):
        await EmployeeManager().update_employee_partial(
            mock_session,
            employee.id,
            EmployeeUpdate(department="Unknown"),
        )


@pytest.mark.asyncio
async def test_update_employee_partial_duplicate_email(mock_session):
    employee = make_employee()

    mock_session.scalar.side_effect = [
        employee,
        10,
    ]

    with pytest.raises(EmployeeEmailAlreadyExistError):
        await EmployeeManager().update_employee_partial(
            mock_session,
            employee.id,
            EmployeeUpdate(email="another@example.com"),
        )


@pytest.mark.asyncio
async def test_update_employee_partial_email(mock_session):
    employee = make_employee()

    mock_session.scalar.side_effect = [
        employee,
        None,
    ]

    result = await EmployeeManager().update_employee_partial(
        mock_session,
        employee.id,
        EmployeeUpdate(email="NEWEMAIL@example.com"),
    )

    assert employee.email == "newemail@example.com"
    assert result.email == "newemail@example.com"
    mock_session.commit.assert_awaited_once()
    mock_session.refresh.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_employee_partial_status(mock_session):
    employee = make_employee()
    mock_session.scalar.return_value = employee

    result = await EmployeeManager().update_employee_partial(
        mock_session,
        employee.id,
        EmployeeUpdate(status=EmployeeStatus.INACTIVE),
    )

    assert result.status == EmployeeStatus.INACTIVE
    mock_session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_employee_status_success(mock_session):
    employee = make_employee()
    mock_session.scalar.return_value = employee

    result = await EmployeeManager().update_employee_status(
        mock_session,
        employee.id,
        EmployeeStatusUpdate(status=EmployeeStatus.INACTIVE),
    )

    assert result.status == EmployeeStatus.INACTIVE
    mock_session.commit.assert_awaited_once()
    mock_session.refresh.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_employee_status_not_found(mock_session):
    mock_session.scalar.return_value = None

    with pytest.raises(EmployeeNotFoundError):
        await EmployeeManager().update_employee_status(
            mock_session,
            999,
            EmployeeStatusUpdate(status=EmployeeStatus.INACTIVE),
        )


@pytest.mark.asyncio
async def test_delete_employee_success(mock_session):
    employee = make_employee()
    mock_session.scalar.return_value = employee

    result = await EmployeeManager().delete_employee(
        mock_session,
        employee.id,
    )

    assert employee.is_deleted is True
    assert result.is_deleted is True
    mock_session.commit.assert_awaited_once()
    mock_session.refresh.assert_awaited_once()


@pytest.mark.asyncio
async def test_delete_employee_not_found(mock_session):
    mock_session.scalar.return_value = None

    with pytest.raises(EmployeeNotFoundError):
        await EmployeeManager().delete_employee(mock_session, 999)


@pytest.mark.asyncio
async def test_restore_employee_success(mock_session):
    employee = make_employee(is_deleted=True)

    mock_session.scalar.side_effect = [
        employee,
        None,
    ]

    result = await EmployeeManager().restore_employee(
        mock_session,
        employee.id,
    )

    assert employee.is_deleted is False
    assert result.is_deleted is False
    mock_session.commit.assert_awaited_once()
    mock_session.refresh.assert_awaited_once()


@pytest.mark.asyncio
async def test_restore_employee_not_found(mock_session):
    mock_session.scalar.return_value = None

    with pytest.raises(EmployeeNotFoundError):
        await EmployeeManager().restore_employee(
            mock_session,
            999,
        )


@pytest.mark.asyncio
async def test_restore_employee_already_active(mock_session):
    employee = make_employee(is_deleted=False)
    mock_session.scalar.return_value = employee

    with pytest.raises(
        EmployeeNotFoundError,
        match="Deleted employee not found",
    ):
        await EmployeeManager().restore_employee(
            mock_session,
            employee.id,
        )

    mock_session.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_restore_employee_duplicate_email(mock_session):
    employee = make_employee(
        email="aryan@example.com",
        is_deleted=True,
    )

    mock_session.scalar.side_effect = [
        employee,
        10,
    ]

    with pytest.raises(EmployeeEmailAlreadyExistError):
        await EmployeeManager().restore_employee(
            mock_session,
            employee.id,
        )


@pytest.mark.asyncio
async def test_get_all_employees_success(mock_session):
    employee = make_employee()
    configure_paginated_result(
        mock_session,
        [employee],
        1,
    )

    result = await EmployeeManager().get_all_employees(
        mock_session,
    )

    assert len(result["items"]) == 1
    assert result["pagination"]["total"] == 1
    assert result["pagination"]["page"] == 1


@pytest.mark.asyncio
async def test_get_all_employees_empty(mock_session):
    configure_paginated_result(
        mock_session,
        [],
        0,
    )

    result = await EmployeeManager().get_all_employees(
        mock_session,
    )

    assert result["items"] == []
    assert result["pagination"]["total"] == 0
    assert result["pagination"]["total_pages"] == 0


@pytest.mark.asyncio
async def test_get_all_employees_pagination(mock_session):
    employees = [
        make_employee(employee_id=1),
        make_employee(employee_id=2),
    ]

    configure_paginated_result(
        mock_session,
        employees,
        25,
    )

    result = await EmployeeManager().get_all_employees(
        mock_session,
        page=2,
        page_size=10,
    )

    assert result["pagination"]["page"] == 2
    assert result["pagination"]["page_size"] == 10
    assert result["pagination"]["total"] == 25
    assert result["pagination"]["total_pages"] == 3
    assert result["pagination"]["has_next"] is True
    assert result["pagination"]["has_previous"] is True


@pytest.mark.asyncio
async def test_get_deleted_employees_success(mock_session):
    employee = make_employee(is_deleted=True)

    configure_paginated_result(
        mock_session,
        [employee],
        1,
    )

    result = await EmployeeManager().get_deleted_employees(
        mock_session,
    )

    assert len(result["items"]) == 1
    assert result["items"][0].is_deleted is True


@pytest.mark.asyncio
async def test_get_deleted_employees_empty(mock_session):
    configure_paginated_result(
        mock_session,
        [],
        0,
    )

    result = await EmployeeManager().get_deleted_employees(
        mock_session,
    )

    assert result["items"] == []
    assert result["pagination"]["total"] == 0


@pytest.mark.asyncio
async def test_search_employees_success(mock_session):
    employee = make_employee()

    configure_paginated_result(
        mock_session,
        [employee],
        1,
    )

    result = await EmployeeManager().search_employees(
        mock_session,
        query="Aryan",
    )

    assert len(result["items"]) == 1
    assert result["items"][0].name == "Aryan"


@pytest.mark.asyncio
async def test_search_employees_blank_query(mock_session):
    configure_paginated_result(
        mock_session,
        [],
        0,
    )

    result = await EmployeeManager().search_employees(
        mock_session,
        query="   ",
    )

    assert result["items"] == []
    assert result["pagination"]["total"] == 0


@pytest.mark.asyncio
async def test_search_employees_with_pagination(mock_session):
    employees = [
        make_employee(employee_id=1),
        make_employee(employee_id=2),
    ]

    configure_paginated_result(
        mock_session,
        employees,
        20,
    )

    result = await EmployeeManager().search_employees(
        mock_session,
        query="Aryan",
        page=2,
        page_size=5,
    )

    assert result["pagination"]["page"] == 2
    assert result["pagination"]["page_size"] == 5
    assert result["pagination"]["total"] == 20
    assert result["pagination"]["has_next"] is True


@pytest.mark.asyncio
async def test_filter_employees_success(mock_session):
    employee = make_employee()

    configure_paginated_result(
        mock_session,
        [employee],
        1,
    )

    result = await EmployeeManager().filter_employees(
        mock_session,
        department="Engineering",
    )

    assert len(result["items"]) == 1
    assert result["items"][0].department == "Engineering"


@pytest.mark.asyncio
async def test_filter_employees_by_status(mock_session):
    employee = make_employee()

    configure_paginated_result(
        mock_session,
        [employee],
        1,
    )

    result = await EmployeeManager().filter_employees(
        mock_session,
        status=EmployeeStatus.ACTIVE,
    )

    assert len(result["items"]) == 1
    assert result["items"][0].status == EmployeeStatus.ACTIVE


@pytest.mark.asyncio
async def test_filter_employees_by_min_salary(mock_session):
    employee = make_employee()

    configure_paginated_result(
        mock_session,
        [employee],
        1,
    )

    result = await EmployeeManager().filter_employees(
        mock_session,
        min_salary=40000,
    )

    assert len(result["items"]) == 1


@pytest.mark.asyncio
async def test_filter_employees_by_max_salary(mock_session):
    employee = make_employee()

    configure_paginated_result(
        mock_session,
        [employee],
        1,
    )

    result = await EmployeeManager().filter_employees(
        mock_session,
        max_salary=60000,
    )

    assert len(result["items"]) == 1


@pytest.mark.asyncio
async def test_filter_employees_invalid_salary_range(mock_session):
    with pytest.raises(
        ValueError,
        match="min_salary cannot be greater than max_salary",
    ):
        await EmployeeManager().filter_employees(
            mock_session,
            min_salary=70000,
            max_salary=50000,
        )

    mock_session.scalar.assert_not_awaited()


@pytest.mark.asyncio
async def test_filter_employees_no_results(mock_session):
    configure_paginated_result(
        mock_session,
        [],
        0,
    )

    result = await EmployeeManager().filter_employees(
        mock_session,
        department="Engineering",
    )

    assert result["items"] == []
    assert result["pagination"]["total"] == 0
