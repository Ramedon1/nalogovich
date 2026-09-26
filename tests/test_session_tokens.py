import asyncio

from nalogovich.lknpd import NpdClient


def test_replacing_access_token_clears_previous_refresh_token():
    client = NpdClient.from_token("old_access", "old_refresh")

    asyncio.run(client.auth_with_token("new_access"))

    assert client.export_session()["token"] == "new_access"
    assert client.export_session()["refresh_token"] is None
