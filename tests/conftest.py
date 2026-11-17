from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models.employee import EmployeeStatus as ModelEmployeeStatus


@pytest.fixture
def mock_session():
    session = AsyncMock()

    session.add = MagicMock()
    session.add_all = MagicMock()

    return session


@pytest.fixture
def fake_department():
    return SimpleNamespace(
        id=1,
        name="Engineering",
    )


@pytest.fixture
def fake_employee(fake_department):
    return SimpleNamespace(
        id=1,
        name="Aryan",
        email="aryan@example.com",
        department_id=1,
        department=fake_department,
        salary=Decimal("50000.00"),
        status=ModelEmployeeStatus.ACTIVE,
        is_deleted=False,
    )
