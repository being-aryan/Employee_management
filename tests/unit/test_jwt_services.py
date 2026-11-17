from datetime import UTC, datetime, timedelta

import jwt
import pytest

from app.managers.jwt_service import JWTService


@pytest.fixture
def jwt_service():
    return JWTService()


def test_create_access_token_success(jwt_service):
    token = jwt_service.create_access_token("123")

    assert isinstance(token, str)
    assert token


def test_create_access_token_contains_expected_claims(jwt_service):
    token = jwt_service.create_access_token("123")

    payload = jwt.decode(
        token,
        jwt_service.secret_key,
        algorithms=[jwt_service.algorithm],
    )

    assert payload["sub"] == "123"
    assert "iat" in payload
    assert "exp" in payload


def test_verify_access_token_success(jwt_service):
    token = jwt_service.create_access_token("123")

    payload = jwt_service.verify_access_token(token)

    assert payload["sub"] == "123"


def test_verify_access_token_invalid_signature(jwt_service):
    token = jwt.encode(
        {
            "sub": "123",
            "exp": datetime.now(UTC) + timedelta(minutes=5),
        },
        "incorrect_secret_key_for_testing_123456",
        algorithm=jwt_service.algorithm,
    )

    with pytest.raises(jwt.InvalidTokenError):
        jwt_service.verify_access_token(token)


def test_verify_access_token_expired(jwt_service):
    token = jwt.encode(
        {
            "sub": "123",
            "exp": datetime.now(UTC) - timedelta(minutes=5),
        },
        jwt_service.secret_key,
        algorithm=jwt_service.algorithm,
    )

    with pytest.raises(jwt.ExpiredSignatureError):
        jwt_service.verify_access_token(token)


def test_verify_access_token_missing_subject(jwt_service):
    token = jwt.encode(
        {
            "exp": datetime.now(UTC) + timedelta(minutes=5),
        },
        jwt_service.secret_key,
        algorithm=jwt_service.algorithm,
    )

    with pytest.raises(jwt.MissingRequiredClaimError):
        jwt_service.verify_access_token(token)


def test_verify_access_token_malformed(jwt_service):
    with pytest.raises(jwt.InvalidTokenError):
        jwt_service.verify_access_token("invalid.token.value")
