from tests.auth.test_registration import create_auth_client, registration_payload


def bearer(token: object) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def register(client, **overrides: object) -> dict[str, object]:
    response = client.post(
        "/api/v1/auth/register",
        json=registration_payload(**overrides),
    )
    assert response.status_code == 201
    return response.json()


__all__ = ["bearer", "create_auth_client", "register", "registration_payload"]
