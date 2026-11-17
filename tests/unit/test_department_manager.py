from unittest.mock import MagicMock

import pytest
from sqlalchemy.exc import IntegrityError

from app.exceptions import DepartmentAlreadyExistError
from app.managers.department_service import DepartmentManager


@pytest.fixture
def department_manager():
    return DepartmentManager()


@pytest.mark.asyncio
async def test_get_all_departments_success(department_manager, mock_session):
    result = MagicMock()
    result.all.return_value = ["Engineering", "HR", "Finance"]
    mock_session.scalars.return_value = result

    departments = await department_manager.get_all_departments(mock_session)

    assert departments == ["Engineering", "HR", "Finance"]
    mock_session.scalars.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_all_departments_empty(department_manager, mock_session):
    result = MagicMock()
    result.all.return_value = []
    mock_session.scalars.return_value = result

    departments = await department_manager.get_all_departments(mock_session)

    assert departments == []


@pytest.mark.asyncio
async def test_create_department_success(department_manager, mock_session):
    mock_session.scalar.return_value = None

    department = await department_manager.create_department(
        mock_session,
        "  Engineering  ",
    )

    assert department == "Engineering"
    mock_session.add.assert_called_once()

    created_department = mock_session.add.call_args.args[0]
    assert created_department.name == "Engineering"

    mock_session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_department_empty_name(department_manager, mock_session):
    with pytest.raises(ValueError, match="Department name cannot be empty"):
        await department_manager.create_department(mock_session, "   ")

    mock_session.scalar.assert_not_awaited()
    mock_session.add.assert_not_called()
    mock_session.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_create_department_already_exists(
    department_manager,
    mock_session,
):
    mock_session.scalar.return_value = 1

    with pytest.raises(DepartmentAlreadyExistError):
        await department_manager.create_department(
            mock_session,
            "Engineering",
        )

    mock_session.add.assert_not_called()
    mock_session.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_create_department_integrity_error(
    department_manager,
    mock_session,
):
    mock_session.scalar.return_value = None
    mock_session.commit.side_effect = IntegrityError(
        "INSERT INTO departments",
        {},
        Exception("Duplicate department"),
    )

    with pytest.raises(DepartmentAlreadyExistError):
        await department_manager.create_department(
            mock_session,
            "Engineering",
        )

    mock_session.rollback.assert_awaited_once()


@pytest.mark.asyncio
async def test_department_exists_true(department_manager, mock_session):
    mock_session.scalar.return_value = 1

    result = await department_manager.department_exists(
        mock_session,
        "Engineering",
    )

    assert result is True
    mock_session.scalar.assert_awaited_once()


@pytest.mark.asyncio
async def test_department_exists_false(department_manager, mock_session):
    mock_session.scalar.return_value = None

    result = await department_manager.department_exists(
        mock_session,
        "Engineering",
    )

    assert result is False


@pytest.mark.asyncio
async def test_department_exists_normalizes_name(
    department_manager,
    mock_session,
):
    mock_session.scalar.return_value = 1

    result = await department_manager.department_exists(
        mock_session,
        "  ENGINEERING  ",
    )

    assert result is True
    mock_session.scalar.assert_awaited_once()
