from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from app.managers.auth_manager import AuthManager


@pytest.mark.asyncio
async def test_authenticate_admin_success(mock_session):
    admin = SimpleNamespace(
        id=1,
        email="admin@example.com",
        hashed_password="hashed_password",
        is_active=True,
        role="admin",
    )

    mock_session.scalar.return_value = admin

    manager = AuthManager(mock_session)

    with patch(
        "app.managers.auth_manager.run_in_threadpool",
        new_callable=AsyncMock,
    ) as mock_verify:
        mock_verify.return_value = True

        result = await manager.authenticate_admin(
            "  ADMIN@EXAMPLE.COM  ",
            "correct_password",
        )

    assert result is admin
    mock_session.scalar.assert_awaited_once()

    statement = mock_session.scalar.await_args.args[0]
    assert "admin@example.com" in statement.compile().params.values()

    mock_verify.assert_awaited_once_with(
        manager.password_service.verify_password,
        "correct_password",
        "hashed_password",
    )


@pytest.mark.asyncio
async def test_authenticate_admin_not_found(mock_session):
    mock_session.scalar.return_value = None

    manager = AuthManager(mock_session)

    with patch(
        "app.managers.auth_manager.run_in_threadpool",
        new_callable=AsyncMock,
    ) as mock_verify:
        result = await manager.authenticate_admin(
            "admin@example.com",
            "password",
        )

    assert result is None
    mock_verify.assert_not_awaited()


@pytest.mark.asyncio
async def test_authenticate_admin_inactive(mock_session):
    admin = SimpleNamespace(
        id=1,
        email="admin@example.com",
        hashed_password="hashed_password",
        is_active=False,
        role="admin",
    )

    mock_session.scalar.return_value = admin

    manager = AuthManager(mock_session)

    with patch(
        "app.managers.auth_manager.run_in_threadpool",
        new_callable=AsyncMock,
    ) as mock_verify:
        result = await manager.authenticate_admin(
            "admin@example.com",
            "password",
        )

    assert result is None
    mock_verify.assert_not_awaited()


@pytest.mark.asyncio
async def test_authenticate_admin_invalid_password(mock_session):
    admin = SimpleNamespace(
        id=1,
        email="admin@example.com",
        hashed_password="hashed_password",
        is_active=True,
        role="admin",
    )

    mock_session.scalar.return_value = admin

    manager = AuthManager(mock_session)

    with patch(
        "app.managers.auth_manager.run_in_threadpool",
        new_callable=AsyncMock,
    ) as mock_verify:
        mock_verify.return_value = False

        result = await manager.authenticate_admin(
            "admin@example.com",
            "wrong_password",
        )

    assert result is None
    mock_verify.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_admin_by_id_success(mock_session):
    admin = SimpleNamespace(
        id=1,
        email="admin@example.com",
        is_active=True,
        role="admin",
    )

    mock_session.get.return_value = admin

    manager = AuthManager(mock_session)

    result = await manager.get_admin_by_id(1)

    assert result is admin
    mock_session.get.assert_awaited_once_with(
        type(manager).__module__
        and __import__(
            "app.models.admin",
            fromlist=["Admin"],
        ).Admin,
        1,
    )


@pytest.mark.asyncio
async def test_get_admin_by_id_not_found(mock_session):
    mock_session.get.return_value = None

    manager = AuthManager(mock_session)

    result = await manager.get_admin_by_id(999)

    assert result is None
    mock_session.get.assert_awaited_once()
