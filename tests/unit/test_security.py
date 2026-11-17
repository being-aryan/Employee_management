import pytest

from app.security import PasswordService


@pytest.fixture
def password_service():
    return PasswordService()


def test_hash_password_returns_hashed_value(password_service):
    password = "StrongPassword123!"

    hashed_password = password_service.hash_password(password)

    assert hashed_password != password
    assert hashed_password


def test_hash_password_generates_different_hashes(password_service):
    password = "StrongPassword123!"

    first_hash = password_service.hash_password(password)
    second_hash = password_service.hash_password(password)

    assert first_hash != second_hash


def test_verify_password_success(password_service):
    password = "StrongPassword123!"
    hashed_password = password_service.hash_password(password)

    result = password_service.verify_password(
        password,
        hashed_password,
    )

    assert result is True


def test_verify_password_wrong_password(password_service):
    hashed_password = password_service.hash_password("StrongPassword123!")

    result = password_service.verify_password(
        "WrongPassword123!",
        hashed_password,
    )

    assert result is False
