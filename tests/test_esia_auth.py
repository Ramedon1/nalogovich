import asyncio

import pytest

import nalogovich.lknpd as lknpd
from nalogovich.exceptions import AuthenticationError, EsiaAuthError


def test_auth_esia_rejects_mismatched_state(monkeypatch):
    client = lknpd.NpdClient()

    async def fake_post_auth(endpoint, payload, prefix):
        if endpoint == "auth/esia/url":
            return {"url": "https://esia.gosuslugi.ru/test?state=expected"}
        pytest.fail("The authorization code must not be exchanged")

    async def fake_esia_login(**kwargs):
        return "code", "different"

    monkeypatch.setattr(client, "_post_auth", fake_post_auth)
    monkeypatch.setattr(lknpd, "esia_login", fake_esia_login)

    with pytest.raises(EsiaAuthError, match="State"):
        asyncio.run(client.auth_esia("login", "password"))


def test_esia_http_422_does_not_claim_bad_inn_or_password():
    client = lknpd.NpdClient()

    with pytest.raises(
        AuthenticationError, match="Ошибка авторизации через ЕСИА: HTTP 422"
    ):
        client._raise_for_auth_status(422, None, "Ошибка авторизации через ЕСИА")
