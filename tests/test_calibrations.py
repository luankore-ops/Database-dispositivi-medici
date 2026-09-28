"""
tests/test_calibrations.py
--------------------------
Test automatici della gestione delle calibrazioni.

Regole RBAC:
- ADMIN   -> può creare e leggere calibrazioni
- TECNICO -> può creare e leggere calibrazioni
- LETTORE -> può leggere, ma non creare
"""

# ============================================================
# PAYLOAD DI TEST
# ============================================================

def dispositivo_payload():
    """
    Restituisce un payload valido per creare
    un dispositivo di test.
    """

    return {
        "nome": "Elettrocardiografo Test",
        "categoria": "Diagnostica",
        "numero_seriale": "CALIB-SN-001",
        "udi": "CALIB-UDI-001",
        "produttore": "Test Medical",
        "modello": "ECG-100",
        "data_acquisto": "2025-01-15",
        "costo": 3500.00,
        "data_scadenza_garanzia": "2028-01-15",
        "stato": "in_uso",
    }


def calibrazione_payload():
    """
    Restituisce un payload valido per creare
    una calibrazione.
    """

    return {
        "data": "2026-09-26",
        "esito": "conforme",
        "ente_certificatore": "Laboratorio Accredia Test",
        "prossima_scadenza": "2027-09-26",
    }


def crea_dispositivo_test(
    client,
    headers,
):
    """
    Crea un dispositivo utilizzabile
    nei test delle calibrazioni.
    """

    response = client.post(
        "/dispositivi",
        json=dispositivo_payload(),
        headers=headers,
    )

    assert response.status_code == 200

    return response.json()


# ============================================================
# CREAZIONE CALIBRAZIONI
# ============================================================

def test_admin_puo_creare_calibrazione(
    client,
    admin_user,
    login_admin,
):
    """
    Un amministratore può registrare
    una calibrazione.
    """

    dispositivo = crea_dispositivo_test(
        client,
        login_admin,
    )

    dispositivo_id = dispositivo["id"]

    response = client.post(
        f"/dispositivi/{dispositivo_id}/calibrazioni",
        json=calibrazione_payload(),
        headers=login_admin,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["dispositivo_id"] == dispositivo_id
    assert data["data"] == "2026-09-26"
    assert data["esito"] == "conforme"
    assert (
        data["ente_certificatore"]
        == "Laboratorio Accredia Test"
    )
    assert data["prossima_scadenza"] == "2027-09-26"
    assert "id" in data


def test_tecnico_puo_creare_calibrazione(
    client,
    tecnico_user,
    login_tecnico,
):
    """
    Un tecnico può registrare
    una calibrazione.
    """

    dispositivo = crea_dispositivo_test(
        client,
        login_tecnico,
    )

    dispositivo_id = dispositivo["id"]

    response = client.post(
        f"/dispositivi/{dispositivo_id}/calibrazioni",
        json=calibrazione_payload(),
        headers=login_tecnico,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["dispositivo_id"] == dispositivo_id


def test_lettore_non_puo_creare_calibrazione(
    client,
    admin_user,
    lettore_user,
    login_admin,
    login_lettore,
):
    """
    Un lettore non può registrare
    una nuova calibrazione.
    """

    dispositivo = crea_dispositivo_test(
        client,
        login_admin,
    )

    dispositivo_id = dispositivo["id"]

    response = client.post(
        f"/dispositivi/{dispositivo_id}/calibrazioni",
        json=calibrazione_payload(),
        headers=login_lettore,
    )

    assert response.status_code == 403


def test_creazione_calibrazione_senza_token(
    client,
):
    """
    Una richiesta senza autenticazione
    deve essere rifiutata.
    """

    response = client.post(
        "/dispositivi/1/calibrazioni",
        json=calibrazione_payload(),
    )

    assert response.status_code == 401


# ============================================================
# LETTURA CALIBRAZIONI
# ============================================================

def test_admin_puo_leggere_calibrazioni(
    client,
    admin_user,
    login_admin,
):
    """
    Un amministratore può leggere
    le calibrazioni di un dispositivo.
    """

    dispositivo = crea_dispositivo_test(
        client,
        login_admin,
    )

    dispositivo_id = dispositivo["id"]

    create_response = client.post(
        f"/dispositivi/{dispositivo_id}/calibrazioni",
        json=calibrazione_payload(),
        headers=login_admin,
    )

    assert create_response.status_code == 200

    response = client.get(
        f"/dispositivi/{dispositivo_id}/calibrazioni",
        headers=login_admin,
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["dispositivo_id"] == dispositivo_id


def test_tecnico_puo_leggere_calibrazioni(
    client,
    tecnico_user,
    login_tecnico,
):
    """
    Un tecnico può leggere
    le calibrazioni.
    """

    dispositivo = crea_dispositivo_test(
        client,
        login_tecnico,
    )

    dispositivo_id = dispositivo["id"]

    create_response = client.post(
        f"/dispositivi/{dispositivo_id}/calibrazioni",
        json=calibrazione_payload(),
        headers=login_tecnico,
    )

    assert create_response.status_code == 200

    response = client.get(
        f"/dispositivi/{dispositivo_id}/calibrazioni",
        headers=login_tecnico,
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["dispositivo_id"] == dispositivo_id


def test_lettore_puo_leggere_calibrazioni(
    client,
    admin_user,
    lettore_user,
    login_admin,
    login_lettore,
):
    """
    Un lettore può consultare
    le calibrazioni.
    """

    dispositivo = crea_dispositivo_test(
        client,
        login_admin,
    )

    dispositivo_id = dispositivo["id"]

    create_response = client.post(
        f"/dispositivi/{dispositivo_id}/calibrazioni",
        json=calibrazione_payload(),
        headers=login_admin,
    )

    assert create_response.status_code == 200

    response = client.get(
        f"/dispositivi/{dispositivo_id}/calibrazioni",
        headers=login_lettore,
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["dispositivo_id"] == dispositivo_id


def test_lettura_calibrazioni_senza_token(
    client,
):
    """
    Una richiesta senza autenticazione
    deve essere rifiutata.
    """

    response = client.get(
        "/dispositivi/1/calibrazioni",
    )

    assert response.status_code == 401


# ============================================================
# DISPOSITIVO INESISTENTE
# ============================================================

def test_creazione_calibrazione_dispositivo_inesistente(
    client,
    admin_user,
    login_admin,
):
    """
    Non è possibile creare una calibrazione
    per un dispositivo inesistente.
    """

    response = client.post(
        "/dispositivi/999999/calibrazioni",
        json=calibrazione_payload(),
        headers=login_admin,
    )

    assert response.status_code == 404


def test_lettura_calibrazioni_dispositivo_inesistente(
    client,
    admin_user,
    login_admin,
):
    """
    La lettura delle calibrazioni di un
    dispositivo inesistente deve restituire 404.
    """

    response = client.get(
        "/dispositivi/999999/calibrazioni",
        headers=login_admin,
    )

    assert response.status_code == 404


# ============================================================
# ESITI CALIBRAZIONE
# ============================================================

def test_calibrazione_conforme(
    client,
    admin_user,
    login_admin,
):
    """
    Verifica la registrazione di una
    calibrazione conforme.
    """

    dispositivo = crea_dispositivo_test(
        client,
        login_admin,
    )

    response = client.post(
        f"/dispositivi/{dispositivo['id']}/calibrazioni",
        json={
            "data": "2026-09-26",
            "esito": "conforme",
            "ente_certificatore": "Laboratorio Test",
            "prossima_scadenza": "2027-09-26",
        },
        headers=login_admin,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["esito"] == "conforme"


def test_calibrazione_non_conforme(
    client,
    admin_user,
    login_admin,
):
    """
    Verifica la registrazione di una
    calibrazione non conforme.
    """

    dispositivo = crea_dispositivo_test(
        client,
        login_admin,
    )

    response = client.post(
        f"/dispositivi/{dispositivo['id']}/calibrazioni",
        json={
            "data": "2026-09-26",
            "esito": "non_conforme",
            "ente_certificatore": "Laboratorio Test",
            "prossima_scadenza": None,
        },
        headers=login_admin,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["esito"] == "non_conforme"


def test_calibrazione_esito_non_valido(
    client,
    admin_user,
    login_admin,
):
    """
    L'esito deve essere conforme oppure
    non_conforme.
    """

    dispositivo = crea_dispositivo_test(
        client,
        login_admin,
    )

    response = client.post(
        f"/dispositivi/{dispositivo['id']}/calibrazioni",
        json={
            "data": "2026-09-26",
            "esito": "non_valido",
            "ente_certificatore": "Laboratorio Test",
        },
        headers=login_admin,
    )

    assert response.status_code == 422


# ============================================================
# PIÙ CALIBRAZIONI
# ============================================================

def test_dispositivo_puo_avere_piu_calibrazioni(
    client,
    admin_user,
    login_admin,
):
    """
    Un dispositivo può avere più
    registrazioni di calibrazione.
    """

    dispositivo = crea_dispositivo_test(
        client,
        login_admin,
    )

    dispositivo_id = dispositivo["id"]

    calibrazione_1 = {
        "data": "2026-01-15",
        "esito": "conforme",
        "ente_certificatore": "Laboratorio A",
        "prossima_scadenza": "2027-01-15",
    }

    calibrazione_2 = {
        "data": "2026-06-20",
        "esito": "non_conforme",
        "ente_certificatore": "Laboratorio B",
        "prossima_scadenza": None,
    }

    response_1 = client.post(
        f"/dispositivi/{dispositivo_id}/calibrazioni",
        json=calibrazione_1,
        headers=login_admin,
    )

    response_2 = client.post(
        f"/dispositivi/{dispositivo_id}/calibrazioni",
        json=calibrazione_2,
        headers=login_admin,
    )

    assert response_1.status_code == 200
    assert response_2.status_code == 200

    response = client.get(
        f"/dispositivi/{dispositivo_id}/calibrazioni",
        headers=login_admin,
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2


# ============================================================
# VALIDAZIONE DATI
# ============================================================

def test_calibrazione_data_mancante(
    client,
    admin_user,
    login_admin,
):
    """
    Il campo data è obbligatorio.
    """

    dispositivo = crea_dispositivo_test(
        client,
        login_admin,
    )

    payload = {
        "esito": "conforme",
        "ente_certificatore": "Laboratorio Test",
    }

    response = client.post(
        f"/dispositivi/{dispositivo['id']}/calibrazioni",
        json=payload,
        headers=login_admin,
    )

    assert response.status_code == 422


def test_calibrazione_esito_mancante(
    client,
    admin_user,
    login_admin,
):
    """
    Il campo esito è obbligatorio.
    """

    dispositivo = crea_dispositivo_test(
        client,
        login_admin,
    )

    payload = {
        "data": "2026-09-26",
        "ente_certificatore": "Laboratorio Test",
    }

    response = client.post(
        f"/dispositivi/{dispositivo['id']}/calibrazioni",
        json=payload,
        headers=login_admin,
    )

    assert response.status_code == 422


def test_ente_certificatore_troppo_lungo(
    client,
    admin_user,
    login_admin,
):
    """
    L'ente certificatore non può superare
    150 caratteri.
    """

    dispositivo = crea_dispositivo_test(
        client,
        login_admin,
    )

    payload = {
        "data": "2026-09-26",
        "esito": "conforme",
        "ente_certificatore": "A" * 151,
    }

    response = client.post(
        f"/dispositivi/{dispositivo['id']}/calibrazioni",
        json=payload,
        headers=login_admin,
    )

    assert response.status_code == 422


# ============================================================
# CAMPI OPZIONALI
# ============================================================

def test_calibrazione_campi_opzionali_assenti(
    client,
    admin_user,
    login_admin,
):
    """
    Ente certificatore e prossima scadenza
    sono campi opzionali.
    """

    dispositivo = crea_dispositivo_test(
        client,
        login_admin,
    )

    payload = {
        "data": "2026-09-26",
        "esito": "conforme",
    }

    response = client.post(
        f"/dispositivi/{dispositivo['id']}/calibrazioni",
        json=payload,
        headers=login_admin,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["ente_certificatore"] is None
    assert data["prossima_scadenza"] is None


# ============================================================
# AUDIT LOG
# ============================================================

def test_creazione_calibrazione_registra_audit_log(
    client,
    admin_user,
    login_admin,
):
    """
    La creazione di una calibrazione
    deve generare una voce nell'audit log.
    """

    dispositivo = crea_dispositivo_test(
        client,
        login_admin,
    )

    dispositivo_id = dispositivo["id"]

    response = client.post(
        f"/dispositivi/{dispositivo_id}/calibrazioni",
        json=calibrazione_payload(),
        headers=login_admin,
    )

    assert response.status_code == 200

    audit_response = client.get(
        "/audit-log",
        headers=login_admin,
    )

    assert audit_response.status_code == 200

    logs = audit_response.json()

    calibrazione_logs = [
        log
        for log in logs
        if (
            log["tabella"] == "calibrazioni"
            and log["azione"] == "CREATE"
        )
    ]

    assert len(calibrazione_logs) >= 1

    assert any(
        str(dispositivo_id)
        in (log["dettagli"] or "")
        for log in calibrazione_logs
    )