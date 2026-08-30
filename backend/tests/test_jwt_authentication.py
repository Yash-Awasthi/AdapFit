"""Tests for JWT authentication service."""

import time
import pytest
from app.services.jwt_authentication import (
    JWTConfig,
    TokenPayload,
    create_jwt_token,
    create_token_pair,
    decode_jwt_token,
    validate_token_type,
    is_token_expired,
    refresh_access_token,
    extract_token_from_header,
    extract_token_from_cookie,
    extract_token_from_query,
    generate_csrf_token,
    verify_csrf_token,
    sign_data,
    verify_signature,
)


@pytest.fixture
def config():
    return JWTConfig(secret_key="test-secret", access_token_expire_minutes=30)


class TestSigning:
    def test_sign_and_verify(self):
        data = "test data"
        secret = "test-secret"
        sig = sign_data(data, secret)
        assert verify_signature(data, sig, secret)

    def test_invalid_signature(self):
        assert not verify_signature("data", "invalid-sig", "secret")

    def test_algorithms(self):
        for alg in ["HS256", "HS384", "HS512"]:
            sig = sign_data("data", "secret", alg)
            assert verify_signature("data", sig, "secret", alg)


class TestTokenCreation:
    def test_create_token(self, config):
        payload = TokenPayload(sub="user1", exp=time.time() + 3600, iat=time.time())
        token = create_jwt_token(payload, config)
        assert token.count(".") == 2

    def test_create_token_pair(self, config):
        pair = create_token_pair("user1", config)
        assert pair.access_token
        assert pair.refresh_token
        assert pair.expires_in > 0


class TestTokenValidation:
    def test_decode_valid_token(self, config):
        pair = create_token_pair("user1", config)
        payload = decode_jwt_token(pair.access_token, config)
        assert payload is not None
        assert payload.sub == "user1"
        assert payload.type == "access"

    def test_decode_invalid_token(self, config):
        assert decode_jwt_token("invalid.token.here", config) is None

    def test_validate_type(self):
        payload = TokenPayload(sub="user1", exp=time.time() + 3600, iat=time.time(), type="access")
        assert validate_token_type(payload, "access")
        assert not validate_token_type(payload, "refresh")

    def test_expired_token(self):
        payload = TokenPayload(sub="user1", exp=time.time() - 100, iat=time.time() - 200)
        assert is_token_expired(payload)


class TestTokenRefresh:
    def test_refresh_success(self, config):
        pair = create_token_pair("user1", config)
        new_pair = refresh_access_token(pair.refresh_token, config)
        assert new_pair is not None
        assert new_pair.access_token
        assert new_pair.refresh_token

    def test_refresh_with_invalid_token(self, config):
        assert refresh_access_token("invalid", config) is None


class TestTokenExtraction:
    def test_from_header(self):
        assert extract_token_from_header("Bearer abc123") == "abc123"
        assert extract_token_from_header("abc123", "") == "abc123"
        assert extract_token_from_header(None) is None

    def test_from_cookie(self):
        assert extract_token_from_cookie({"access_token": "abc"}, "access_token") == "abc"
        assert extract_token_from_cookie({}, "access_token") is None

    def test_from_query(self):
        assert extract_token_from_query({"token": "abc"}) == "abc"
        assert extract_token_from_query({}) is None


class TestCSRF:
    def test_generate_and_verify(self):
        token = generate_csrf_token("secret", "session1")
        assert verify_csrf_token(token, "secret", "session1")

    def test_invalid_csrf(self):
        assert not verify_csrf_token("invalid", "secret", "session1")

    def test_expired_csrf(self):
        token = f"{int(time.time()) - 7200}:invalid"
        assert not verify_csrf_token(token, "secret", "session1")
