"""
tests/test_users.py
-------------------
Test automatici della gestione utenti.

Vengono verificati:
- creazione utenti
- duplicazione username
- modifica utenti
- cambio password
- attivazione/disattivazione utenti
- protezioni dell'amministratore
- audit log
- controllo dei permessi RBAC
"""


# ============================================================
# CREAZIONE UTENTI
# ============================================================

def test_admin_puo_creare_utente(
    client,
    admin_user,
    login_admin,
):
    response = client.post(
        "/utenti",
        headers=login_admin,
        json={
            "username": "nuovo_utente",
            "password": "NuovaPassword123!",
            "ruolo": "lettore",
            "attivo": True,
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["username"] == "nuovo_utente"
    assert data["ruolo"] == "lettore"
    assert data["attivo"] is True
    assert "id" in data


def test_tecnico_non_puo_creare_utente(
    client,
    tecnico_user,
    login_tecnico,
):
    response = client.post(
        "/utenti",
        headers=login_tecnico,
        json={
            "username": "utente_da_bloccare",
            "password": "NuovaPassword123!",
            "ruolo": "lettore",
            "attivo": True,
        },
    )

    assert response.status_code == 403


def test_lettore_non_puo_creare_utente(
    client,
    lettore_user,
    login_lettore,
):
    response = client.post(
        "/utenti",
        headers=login_lettore,
        json={
            "username": "utente_da_bloccare",
            "password": "NuovaPassword123!",
            "ruolo": "lettore",
            "attivo": True,
        },
    )

    assert response.status_code == 403


# ============================================================
# USERNAME DUPLICATO
# ============================================================

def test_username_duplicato(
    client,
    admin_user,
    tecnico_user,
    login_admin,
):
    response = client.post(
        "/utenti",
        headers=login_admin,
        json={
            "username": "tecnico_test",
            "password": "NuovaPassword123!",
            "ruolo": "lettore",
            "attivo": True,
        },
    )

    assert response.status_code == 409


# ============================================================
# LETTURA SINGOLO UTENTE
# ============================================================

def test_admin_puo_leggere_utente(
    client,
    admin_user,
    tecnico_user,
    login_admin,
):
    response = client.get(
        f"/utenti/{tecnico_user.id}",
        headers=login_admin,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == tecnico_user.id
    assert data["username"] == "tecnico_test"
    assert data["ruolo"] == "tecnico"


def test_utente_non_esistente(
    client,
    admin_user,
    login_admin,
):
    response = client.get(
        "/utenti/99999",
        headers=login_admin,
    )

    assert response.status_code == 404


# ============================================================
# MODIFICA UTENTE
# ============================================================

def test_admin_puo_modificare_utente(
    client,
    admin_user,
    tecnico_user,
    login_admin,
):
    response = client.put(
        f"/utenti/{tecnico_user.id}",
        headers=login_admin,
        json={
            "username": "tecnico_modificato",
            "ruolo": "lettore",
            "attivo": True,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["username"] == "tecnico_modificato"
    assert data["ruolo"] == "lettore"
    assert data["attivo"] is True


def test_tecnico_non_puo_modificare_utente(
    client,
    admin_user,
    tecnico_user,
    login_tecnico,
):
    response = client.put(
        f"/utenti/{admin_user.id}",
        headers=login_tecnico,
        json={
            "username": "admin_modificato",
        },
    )

    assert response.status_code == 403


def test_lettore_non_puo_modificare_utente(
    client,
    admin_user,
    lettore_user,
    login_lettore,
):
    response = client.put(
        f"/utenti/{admin_user.id}",
        headers=login_lettore,
        json={
            "username": "admin_modificato",
        },
    )

    assert response.status_code == 403


# ============================================================
# CAMBIO PASSWORD
# ============================================================

def test_admin_puo_cambiare_password(
    client,
    admin_user,
    tecnico_user,
    login_admin,
):
    response = client.put(
        f"/utenti/{tecnico_user.id}/password",
        headers=login_admin,
        json={
            "password": "NuovaPassword456!",
        },
    )

    assert response.status_code == 200


def test_password_cambiata_non_e_quella_precedente(
    client,
    admin_user,
    tecnico_user,
    login_admin,
):
    response = client.put(
        f"/utenti/{tecnico_user.id}/password",
        headers=login_admin,
        json={
            "password": "NuovaPassword456!",
        },
    )

    assert response.status_code == 200

    login_vecchia = client.post(
        "/login",
        params={
            "username": "tecnico_test",
            "password": "TecnicoPassword123!",
        },
    )

    assert login_vecchia.status_code == 401

    login_nuova = client.post(
        "/login",
        params={
            "username": "tecnico_test",
            "password": "NuovaPassword456!",
        },
    )

    assert login_nuova.status_code == 200


def test_tecnico_non_puo_cambiare_password(
    client,
    admin_user,
    tecnico_user,
    login_tecnico,
):
    response = client.put(
        f"/utenti/{admin_user.id}/password",
        headers=login_tecnico,
        json={
            "password": "NuovaPassword456!",
        },
    )

    assert response.status_code == 403


# ============================================================
# DISATTIVAZIONE UTENTE
# ============================================================

def test_admin_puo_disattivare_utente(
    client,
    admin_user,
    tecnico_user,
    login_admin,
):
    response = client.put(
        f"/utenti/{tecnico_user.id}/stato",
        headers=login_admin,
        json={
            "attivo": False,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["attivo"] is False


def test_utente_disattivato_non_puo_effettuare_login(
    client,
    admin_user,
    tecnico_user,
    login_admin,
):
    response = client.put(
        f"/utenti/{tecnico_user.id}/stato",
        headers=login_admin,
        json={
            "attivo": False,
        },
    )

    assert response.status_code == 200

    login_response = client.post(
        "/login",
        params={
            "username": "tecnico_test",
            "password": "TecnicoPassword123!",
        },
    )

    assert login_response.status_code == 401


def test_admin_puo_riattivare_utente(
    client,
    admin_user,
    tecnico_user,
    login_admin,
):
    disattiva = client.put(
        f"/utenti/{tecnico_user.id}/stato",
        headers=login_admin,
        json={
            "attivo": False,
        },
    )

    assert disattiva.status_code == 200

    riattiva = client.put(
        f"/utenti/{tecnico_user.id}/stato",
        headers=login_admin,
        json={
            "attivo": True,
        },
    )

    assert riattiva.status_code == 200

    data = riattiva.json()

    assert data["attivo"] is True


# ============================================================
# PROTEZIONE DELL'AMMINISTRATORE
# ============================================================

def test_admin_non_puo_disattivare_se_stesso(
    client,
    admin_user,
    login_admin,
):
    response = client.put(
        f"/utenti/{admin_user.id}/stato",
        headers=login_admin,
        json={
            "attivo": False,
        },
    )

    assert response.status_code in (400, 409)


def test_admin_non_puo_rimuovere_proprio_ruolo(
    client,
    admin_user,
    login_admin,
):
    response = client.put(
        f"/utenti/{admin_user.id}",
        headers=login_admin,
        json={
            "ruolo": "tecnico",
        },
    )

    assert response.status_code in (400, 409)


def test_non_si_puo_disattivare_l_ultimo_admin(
    client,
    admin_user,
    login_admin,
):
    response = client.put(
        f"/utenti/{admin_user.id}/stato",
        headers=login_admin,
        json={
            "attivo": False,
        },
    )

    assert response.status_code in (400, 409)


# ============================================================
# AUDIT LOG
# ============================================================

def test_creazione_utente_genera_audit_log(
    client,
    admin_user,
    login_admin,
):
    prima = client.get(
        "/audit-log",
        headers=login_admin,
    )

    assert prima.status_code == 200

    numero_log_prima = len(prima.json())

    response = client.post(
        "/utenti",
        headers=login_admin,
        json={
            "username": "utente_audit",
            "password": "AuditPassword123!",
            "ruolo": "lettore",
            "attivo": True,
        },
    )

    assert response.status_code == 201

    dopo = client.get(
        "/audit-log",
        headers=login_admin,
    )

    assert dopo.status_code == 200

    numero_log_dopo = len(dopo.json())

    assert numero_log_dopo > numero_log_prima


def test_modifica_utente_genera_audit_log(
    client,
    admin_user,
    tecnico_user,
    login_admin,
):
    prima = client.get(
        "/audit-log",
        headers=login_admin,
    )

    assert prima.status_code == 200

    numero_log_prima = len(prima.json())

    response = client.put(
        f"/utenti/{tecnico_user.id}",
        headers=login_admin,
        json={
            "username": "tecnico_audit",
        },
    )

    assert response.status_code == 200

    dopo = client.get(
        "/audit-log",
        headers=login_admin,
    )

    assert dopo.status_code == 200

    numero_log_dopo = len(dopo.json())

    assert numero_log_dopo > numero_log_prima


def test_cambio_password_genera_audit_log(
    client,
    admin_user,
    tecnico_user,
    login_admin,
):
    prima = client.get(
        "/audit-log",
        headers=login_admin,
    )

    assert prima.status_code == 200

    numero_log_prima = len(prima.json())

    response = client.put(
        f"/utenti/{tecnico_user.id}/password",
        headers=login_admin,
        json={
            "password": "AuditPassword456!",
        },
    )

    assert response.status_code == 200

    dopo = client.get(
        "/audit-log",
        headers=login_admin,
    )

    assert dopo.status_code == 200

    numero_log_dopo = len(dopo.json())

    assert numero_log_dopo > numero_log_prima


def test_disattivazione_genera_audit_log(
    client,
    admin_user,
    tecnico_user,
    login_admin,
):
    prima = client.get(
        "/audit-log",
        headers=login_admin,
    )

    assert prima.status_code == 200

    numero_log_prima = len(prima.json())

    response = client.put(
        f"/utenti/{tecnico_user.id}/stato",
        headers=login_admin,
        json={
            "attivo": False,
        },
    )

    assert response.status_code == 200

    dopo = client.get(
        "/audit-log",
        headers=login_admin,
    )

    assert dopo.status_code == 200

    numero_log_dopo = len(dopo.json())

    assert numero_log_dopo > numero_log_prima