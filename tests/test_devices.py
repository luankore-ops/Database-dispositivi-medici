"""
tests/test_devices.py
---------------------
Test automatici della gestione dei dispositivi medici.

Vengono verificati:

- creazione dispositivo
- lettura dispositivo
- lista dispositivi
- modifica dispositivo
- eliminazione dispositivo
- dispositivo inesistente
- filtro per categoria
- filtro per stato
- numero seriale duplicato
- UDI duplicato
- autenticazione
- autorizzazioni RBAC
- gestione di reparto e fornitore
"""


def dispositivo_payload(
    numero_seriale="SN-TEST-001",
    udi="UDI-TEST-001",
):
    """
    Restituisce un payload completo per la creazione
    di un dispositivo medico.
    """

    return {
        "nome": "Monitor Multiparametrico Test",
        "categoria": "Monitoraggio",
        "numero_seriale": numero_seriale,
        "udi": udi,
        "produttore": "Azienda Medical Test",
        "modello": "MM-1000",
        "data_acquisto": "2026-01-15",
        "costo": 2500.00,
        "data_scadenza_garanzia": "2029-01-15",
        "stato": "in_uso",
        "reparto_id": None,
        "fornitore_id": None,
    }


# ============================================================
# CREAZIONE
# ============================================================

def test_admin_puo_creare_dispositivo(
    client,
    admin_user,
    login_admin,
):
    response = client.post(
        "/dispositivi",
        headers=login_admin,
        json=dispositivo_payload(),
    )

    assert response.status_code in (200, 201)

    data = response.json()

    assert "id" in data
    assert data["nome"] == "Monitor Multiparametrico Test"
    assert data["categoria"] == "Monitoraggio"
    assert data["numero_seriale"] == "SN-TEST-001"
    assert data["udi"] == "UDI-TEST-001"
    assert data["produttore"] == "Azienda Medical Test"
    assert data["stato"] == "in_uso"


def test_tecnico_puo_creare_dispositivo(
    client,
    tecnico_user,
    login_tecnico,
):
    response = client.post(
        "/dispositivi",
        headers=login_tecnico,
        json=dispositivo_payload(
            numero_seriale="SN-TECNICO-001",
            udi="UDI-TECNICO-001",
        ),
    )

    assert response.status_code in (200, 201)

    data = response.json()

    assert data["numero_seriale"] == "SN-TECNICO-001"


def test_lettore_non_puo_creare_dispositivo(
    client,
    lettore_user,
    login_lettore,
):
    response = client.post(
        "/dispositivi",
        headers=login_lettore,
        json=dispositivo_payload(
            numero_seriale="SN-LETTURA-BLOCCATA",
            udi="UDI-LETTURA-BLOCCATA",
        ),
    )

    assert response.status_code == 403


def test_creazione_dispositivo_senza_token(
    client,
):
    response = client.post(
        "/dispositivi",
        json=dispositivo_payload(
            numero_seriale="SN-NO-TOKEN",
            udi="UDI-NO-TOKEN",
        ),
    )

    assert response.status_code == 401


# ============================================================
# LETTURA
# ============================================================

def test_admin_puo_leggere_dispositivo(
    client,
    admin_user,
    login_admin,
):
    creazione = client.post(
        "/dispositivi",
        headers=login_admin,
        json=dispositivo_payload(),
    )

    assert creazione.status_code in (200, 201)

    dispositivo_id = creazione.json()["id"]

    response = client.get(
        f"/dispositivi/{dispositivo_id}",
        headers=login_admin,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == dispositivo_id
    assert data["nome"] == "Monitor Multiparametrico Test"


def test_tecnico_puo_leggere_dispositivo(
    client,
    admin_user,
    tecnico_user,
    login_admin,
    login_tecnico,
):
    creazione = client.post(
        "/dispositivi",
        headers=login_admin,
        json=dispositivo_payload(
            numero_seriale="SN-READ-TECNICO",
            udi="UDI-READ-TECNICO",
        ),
    )

    assert creazione.status_code in (200, 201)

    dispositivo_id = creazione.json()["id"]

    response = client.get(
        f"/dispositivi/{dispositivo_id}",
        headers=login_tecnico,
    )

    assert response.status_code == 200


def test_lettore_puo_leggere_dispositivo(
    client,
    admin_user,
    lettore_user,
    login_admin,
    login_lettore,
):
    creazione = client.post(
        "/dispositivi",
        headers=login_admin,
        json=dispositivo_payload(
            numero_seriale="SN-READ-LETTORE",
            udi="UDI-READ-LETTORE",
        ),
    )

    assert creazione.status_code in (200, 201)

    dispositivo_id = creazione.json()["id"]

    response = client.get(
        f"/dispositivi/{dispositivo_id}",
        headers=login_lettore,
    )

    assert response.status_code == 200


def test_lettura_dispositivo_senza_token(
    client,
):
    response = client.get(
        "/dispositivi/1"
    )

    assert response.status_code == 401


def test_dispositivo_non_esistente(
    client,
    admin_user,
    login_admin,
):
    response = client.get(
        "/dispositivi/99999",
        headers=login_admin,
    )

    assert response.status_code == 404


# ============================================================
# LISTA
# ============================================================

def test_admin_puo_vedere_lista_dispositivi(
    client,
    admin_user,
    login_admin,
):
    response = client.get(
        "/dispositivi",
        headers=login_admin,
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)


def test_tecnico_puo_vedere_lista_dispositivi(
    client,
    tecnico_user,
    login_tecnico,
):
    response = client.get(
        "/dispositivi",
        headers=login_tecnico,
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)


def test_lettore_puo_vedere_lista_dispositivi(
    client,
    lettore_user,
    login_lettore,
):
    response = client.get(
        "/dispositivi",
        headers=login_lettore,
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)


# ============================================================
# FILTRO CATEGORIA
# ============================================================

def test_filtro_dispositivi_per_categoria(
    client,
    admin_user,
    login_admin,
):
    client.post(
        "/dispositivi",
        headers=login_admin,
        json=dispositivo_payload(
            numero_seriale="SN-CAT-001",
            udi="UDI-CAT-001",
        ),
    )

    response = client.get(
        "/dispositivi",
        params={
            "categoria": "Monitoraggio"
        },
        headers=login_admin,
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)

    for dispositivo in data:
        assert dispositivo["categoria"] == "Monitoraggio"


# ============================================================
# FILTRO STATO
# ============================================================

def test_filtro_dispositivi_per_stato(
    client,
    admin_user,
    login_admin,
):
    client.post(
        "/dispositivi",
        headers=login_admin,
        json=dispositivo_payload(
            numero_seriale="SN-STATO-001",
            udi="UDI-STATO-001",
        ),
    )

    response = client.get(
        "/dispositivi",
        params={
            "stato": "in_uso"
        },
        headers=login_admin,
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)

    for dispositivo in data:
        assert dispositivo["stato"] == "in_uso"


# ============================================================
# MODIFICA
# ============================================================

def test_admin_puo_modificare_dispositivo(
    client,
    admin_user,
    login_admin,
):
    creazione = client.post(
        "/dispositivi",
        headers=login_admin,
        json=dispositivo_payload(
            numero_seriale="SN-UPDATE-001",
            udi="UDI-UPDATE-001",
        ),
    )

    assert creazione.status_code in (200, 201)

    dispositivo_id = creazione.json()["id"]

    response = client.put(
        f"/dispositivi/{dispositivo_id}",
        headers=login_admin,
        json={
            "nome": "Monitor Multiparametrico Aggiornato",
            "modello": "MM-2000",
            "costo": 3200.00,
            "stato": "manutenzione",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == dispositivo_id
    assert data["nome"] == "Monitor Multiparametrico Aggiornato"
    assert data["modello"] == "MM-2000"
    assert data["costo"] == 3200.00
    assert data["stato"] == "manutenzione"


def test_tecnico_puo_modificare_dispositivo(
    client,
    admin_user,
    tecnico_user,
    login_admin,
    login_tecnico,
):
    creazione = client.post(
        "/dispositivi",
        headers=login_admin,
        json=dispositivo_payload(
            numero_seriale="SN-UPDATE-TECNICO",
            udi="UDI-UPDATE-TECNICO",
        ),
    )

    assert creazione.status_code in (200, 201)

    dispositivo_id = creazione.json()["id"]

    response = client.put(
        f"/dispositivi/{dispositivo_id}",
        headers=login_tecnico,
        json={
            "nome": "Modificato dal tecnico"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["nome"] == "Modificato dal tecnico"


def test_lettore_non_puo_modificare_dispositivo(
    client,
    admin_user,
    lettore_user,
    login_admin,
    login_lettore,
):
    creazione = client.post(
        "/dispositivi",
        headers=login_admin,
        json=dispositivo_payload(
            numero_seriale="SN-UPDATE-LETTORE",
            udi="UDI-UPDATE-LETTORE",
        ),
    )

    assert creazione.status_code in (200, 201)

    dispositivo_id = creazione.json()["id"]

    response = client.put(
        f"/dispositivi/{dispositivo_id}",
        headers=login_lettore,
        json={
            "nome": "Tentativo modifica lettore"
        },
    )

    assert response.status_code == 403


def test_modifica_dispositivo_non_esistente(
    client,
    admin_user,
    login_admin,
):
    response = client.put(
        "/dispositivi/99999",
        headers=login_admin,
        json={
            "nome": "Dispositivo inesistente"
        },
    )

    assert response.status_code == 404


# ============================================================
# NUMERO SERIALE DUPLICATO
# ============================================================

def test_numero_seriale_duplicato(
    client,
    admin_user,
    login_admin,
):
    prima = client.post(
        "/dispositivi",
        headers=login_admin,
        json=dispositivo_payload(
            numero_seriale="SN-DUPLICATO",
            udi="UDI-DUPLICATO-001",
        ),
    )

    assert prima.status_code in (200, 201)

    seconda = client.post(
        "/dispositivi",
        headers=login_admin,
        json=dispositivo_payload(
            numero_seriale="SN-DUPLICATO",
            udi="UDI-DUPLICATO-002",
        ),
    )

    assert seconda.status_code in (400, 409, 500)


# ============================================================
# UDI DUPLICATO
# ============================================================

def test_udi_duplicato(
    client,
    admin_user,
    login_admin,
):
    prima = client.post(
        "/dispositivi",
        headers=login_admin,
        json=dispositivo_payload(
            numero_seriale="SN-UDI-001",
            udi="UDI-DUPLICATO",
        ),
    )

    assert prima.status_code in (200, 201)

    seconda = client.post(
        "/dispositivi",
        headers=login_admin,
        json=dispositivo_payload(
            numero_seriale="SN-UDI-002",
            udi="UDI-DUPLICATO",
        ),
    )

    assert seconda.status_code in (400, 409, 500)


# ============================================================
# ELIMINAZIONE
# ============================================================

def test_admin_puo_eliminare_dispositivo(
    client,
    admin_user,
    login_admin,
):
    creazione = client.post(
        "/dispositivi",
        headers=login_admin,
        json=dispositivo_payload(
            numero_seriale="SN-DELETE-001",
            udi="UDI-DELETE-001",
        ),
    )

    assert creazione.status_code in (200, 201)

    dispositivo_id = creazione.json()["id"]

    response = client.delete(
        f"/dispositivi/{dispositivo_id}",
        headers=login_admin,
    )

    assert response.status_code == 204

    verifica = client.get(
        f"/dispositivi/{dispositivo_id}",
        headers=login_admin,
    )

    assert verifica.status_code == 404


def test_tecnico_non_puo_eliminare_dispositivo(
    client,
    admin_user,
    tecnico_user,
    login_admin,
    login_tecnico,
):
    creazione = client.post(
        "/dispositivi",
        headers=login_admin,
        json=dispositivo_payload(
            numero_seriale="SN-DELETE-TECNICO",
            udi="UDI-DELETE-TECNICO",
        ),
    )

    assert creazione.status_code in (200, 201)

    dispositivo_id = creazione.json()["id"]

    response = client.delete(
        f"/dispositivi/{dispositivo_id}",
        headers=login_tecnico,
    )

    assert response.status_code == 403

    verifica = client.get(
        f"/dispositivi/{dispositivo_id}",
        headers=login_admin,
    )

    assert verifica.status_code == 200


def test_lettore_non_puo_eliminare_dispositivo(
    client,
    admin_user,
    lettore_user,
    login_admin,
    login_lettore,
):
    creazione = client.post(
        "/dispositivi",
        headers=login_admin,
        json=dispositivo_payload(
            numero_seriale="SN-DELETE-LETTORE",
            udi="UDI-DELETE-LETTORE",
        ),
    )

    assert creazione.status_code in (200, 201)

    dispositivo_id = creazione.json()["id"]

    response = client.delete(
        f"/dispositivi/{dispositivo_id}",
        headers=login_lettore,
    )

    assert response.status_code == 403


def test_eliminazione_dispositivo_non_esistente(
    client,
    admin_user,
    login_admin,
):
    response = client.delete(
        "/dispositivi/99999",
        headers=login_admin,
    )

    assert response.status_code == 404


def test_eliminazione_dispositivo_senza_token(
    client,
):
    response = client.delete(
        "/dispositivi/1"
    )

    assert response.status_code == 401


# ============================================================
# REPARTO E FORNITORE
# ============================================================

def test_dispositivo_con_reparto_e_fornitore(
    client,
    admin_user,
    login_admin,
):
    reparto_response = client.post(
        "/reparti",
        headers=login_admin,
        json={
            "nome": "Reparto Test Dispositivi",
            "piano": "1",
        },
    )

    assert reparto_response.status_code in (200, 201)

    reparto_id = reparto_response.json()["id"]

    fornitore_response = client.post(
        "/fornitori",
        headers=login_admin,
        json={
            "ragione_sociale": "Fornitore Test Dispositivi",
            "email_contatto": "test@example.com",
            "telefono": "0710000000",
        },
    )

    assert fornitore_response.status_code in (200, 201)

    fornitore_id = fornitore_response.json()["id"]

    payload = dispositivo_payload(
        numero_seriale="SN-RELAZIONI-001",
        udi="UDI-RELAZIONI-001",
    )

    payload["reparto_id"] = reparto_id
    payload["fornitore_id"] = fornitore_id

    response = client.post(
        "/dispositivi",
        headers=login_admin,
        json=payload,
    )

    assert response.status_code in (200, 201)

    data = response.json()

    assert data["reparto_id"] == reparto_id
    assert data["fornitore_id"] == fornitore_id


# ============================================================
# VALIDAZIONE DATI
# ============================================================

def test_creazione_dispositivo_dati_obbligatori_mancanti(
    client,
    admin_user,
    login_admin,
):
    response = client.post(
        "/dispositivi",
        headers=login_admin,
        json={
            "nome": "Dispositivo Incompleto"
        },
    )

    assert response.status_code == 422


def test_data_acquisto_valida(
    client,
    admin_user,
    login_admin,
):
    response = client.post(
        "/dispositivi",
        headers=login_admin,
        json=dispositivo_payload(
            numero_seriale="SN-DATA-001",
            udi="UDI-DATA-001",
        ),
    )

    assert response.status_code in (200, 201)

    data = response.json()

    assert data["data_acquisto"] == "2026-01-15"
    assert data["data_scadenza_garanzia"] == "2029-01-15"