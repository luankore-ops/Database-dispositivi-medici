"""
tests/test_rbac.py
------------------
Test automatici del sistema RBAC.

Ruoli:
- admin
- tecnico
- lettore
"""


# ============================================================
# ADMIN
# ============================================================

def test_admin_accesso_utenti(
    client,
    admin_user,
    login_admin,
):
    response = client.get(
        "/utenti",
        headers=login_admin,
    )

    assert response.status_code == 200


# ============================================================
# TECNICO
# ============================================================

def test_tecnico_non_puo_gestire_utenti(
    client,
    tecnico_user,
    login_tecnico,
):
    response = client.get(
        "/utenti",
        headers=login_tecnico,
    )

    assert response.status_code == 403


# ============================================================
# LETTORE
# ============================================================

def test_lettore_non_puo_gestire_utenti(
    client,
    lettore_user,
    login_lettore,
):
    response = client.get(
        "/utenti",
        headers=login_lettore,
    )

    assert response.status_code == 403


# ============================================================
# AUDIT LOG ADMIN
# ============================================================

def test_admin_accesso_audit_log(
    client,
    admin_user,
    login_admin,
):
    response = client.get(
        "/audit-log",
        headers=login_admin,
    )

    assert response.status_code == 200


# ============================================================
# AUDIT LOG TECNICO
# ============================================================

def test_tecnico_non_puo_leggere_audit_log(
    client,
    tecnico_user,
    login_tecnico,
):
    response = client.get(
        "/audit-log",
        headers=login_tecnico,
    )

    assert response.status_code == 403


# ============================================================
# AUDIT LOG LETTORE
# ============================================================

def test_lettore_non_puo_leggere_audit_log(
    client,
    lettore_user,
    login_lettore,
):
    response = client.get(
        "/audit-log",
        headers=login_lettore,
    )

    assert response.status_code == 403