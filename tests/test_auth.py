"""
tests/test_auth.py
------------------
Test automatici dell'autenticazione.
"""


# ============================================================
# LOGIN CORRETTO
# ============================================================

def test_login_corretto(
    client,
    admin_user,
):
    response = client.post(
        "/login",
        params={
            "username": "admin_test",
            "password": "AdminPassword123!",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert "access_token" in data
    assert data["token_type"] == "bearer"

    assert data["user"]["username"] == "admin_test"


# ============================================================
# PASSWORD ERRATA
# ============================================================

def test_login_password_errata(
    client,
    admin_user,
):
    response = client.post(
        "/login",
        params={
            "username": "admin_test",
            "password": "PasswordSbagliata123!",
        },
    )

    assert response.status_code == 401


# ============================================================
# UTENTE INESISTENTE
# ============================================================

def test_login_utente_inesistente(
    client,
):
    response = client.post(
        "/login",
        params={
            "username": "utente_inesistente",
            "password": "Password123456!",
        },
    )

    assert response.status_code == 401


# ============================================================
# ACCESSO SENZA TOKEN
# ============================================================

def test_accesso_senza_token(
    client,
):
    response = client.get(
        "/me"
    )

    assert response.status_code == 401


# ============================================================
# /ME
# ============================================================

def test_me(
    client,
    admin_user,
    login_admin,
):
    response = client.get(
        "/me",
        headers=login_admin,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["username"] == "admin_test"
    assert data["role"] == "admin"


# ============================================================
# TOKEN NON VALIDO
# ============================================================

def test_token_non_valido(
    client,
):
    response = client.get(
        "/me",
        headers={
            "Authorization": "Bearer token_falso"
        },
    )

    assert response.status_code == 401