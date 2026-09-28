"""
tests/test_deadlines.py
-----------------------
Test automatici della gestione delle scadenze.

L'endpoint testato è:

    GET /dispositivi/scadenze

La logica attuale considera:
- scadenze delle manutenzioni;
- scadenze delle calibrazioni.

Le scadenze della garanzia NON sono attualmente
considerate dalla funzione dispositivi_in_scadenza().
"""

from datetime import date, timedelta


# ============================================================
# PAYLOAD
# ============================================================

def dispositivo_payload(
    numero_seriale="DEADLINE-SN-001",
    udi="DEADLINE-UDI-001",
):
    """
    Restituisce un payload valido per creare
    un dispositivo di test.
    """

    return {
        "nome": "Ventilatore Polmonare Test",
        "categoria": "Ventilazione",
        "numero_seriale": numero_seriale,
        "udi": udi,
        "produttore": "Test Medical",
        "modello": "VENT-100",
        "data_acquisto": "2025-01-15",
        "costo": 8000.00,
        "data_scadenza_garanzia": "2028-01-15",
        "stato": "in_uso",
    }


def manutenzione_payload(
    prossima_scadenza,
):
    """
    Restituisce un payload di manutenzione
    con la scadenza specificata.
    """

    return {
        "data": "2026-09-01",
        "tipo": "preventiva",
        "tecnico": "Tecnico Test",
        "descrizione": "Manutenzione di test.",
        "prossima_scadenza": prossima_scadenza,
    }


def calibrazione_payload(
    prossima_scadenza,
    esito="conforme",
):
    """
    Restituisce un payload di calibrazione
    con la scadenza specificata.
    """

    return {
        "data": "2026-09-01",
        "esito": esito,
        "ente_certificatore": "Laboratorio Test",
        "prossima_scadenza": prossima_scadenza,
    }


def crea_dispositivo_test(
    client,
    headers,
    numero_seriale="DEADLINE-SN-001",
    udi="DEADLINE-UDI-001",
):
    """
    Crea un dispositivo di test.
    """

    response = client.post(
        "/dispositivi",
        json=dispositivo_payload(
            numero_seriale=numero_seriale,
            udi=udi,
        ),
        headers=headers,
    )

    assert response.status_code == 200

    return response.json()


# ============================================================
# ACCESSO ENDPOINT
# ============================================================

def test_admin_puo_leggere_scadenze(
    client,
    admin_user,
    login_admin,
):
    """
    Un amministratore autenticato può
    consultare le scadenze.
    """

    response = client.get(
        "/dispositivi/scadenze",
        headers=login_admin,
    )

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_tecnico_puo_leggere_scadenze(
    client,
    tecnico_user,
    login_tecnico,
):
    """
    Un tecnico autenticato può
    consultare le scadenze.
    """

    response = client.get(
        "/dispositivi/scadenze",
        headers=login_tecnico,
    )

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_lettore_puo_leggere_scadenze(
    client,
    lettore_user,
    login_lettore,
):
    """
    Un lettore autenticato può
    consultare le scadenze.
    """

    response = client.get(
        "/dispositivi/scadenze",
        headers=login_lettore,
    )

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_scadenze_senza_token(
    client,
):
    """
    Una richiesta senza autenticazione
    deve essere rifiutata.
    """

    response = client.get(
        "/dispositivi/scadenze",
    )

    assert response.status_code == 401


# ============================================================
# SCADENZA MANUTENZIONE
# ============================================================

def test_scadenza_manutenzione_inclusa(
    client,
    admin_user,
    login_admin,
):
    """
    Una manutenzione con scadenza entro
    la finestra richiesta deve comparire
    nell'elenco.
    """

    oggi = date.today()
    scadenza = oggi + timedelta(days=10)

    dispositivo = crea_dispositivo_test(
        client,
        login_admin,
    )

    response = client.post(
        f"/dispositivi/{dispositivo['id']}/manutenzioni",
        json=manutenzione_payload(
            scadenza.isoformat()
        ),
        headers=login_admin,
    )

    assert response.status_code == 200

    response = client.get(
        "/dispositivi/scadenze",
        params={
            "entro_giorni": 30,
        },
        headers=login_admin,
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1

    item = data[0]

    assert item["dispositivo_id"] == dispositivo["id"]
    assert item["dispositivo_nome"] == dispositivo["nome"]
    assert item["tipo_scadenza"] == "manutenzione"
    assert item["data_scadenza"] == scadenza.isoformat()
    assert item["giorni_rimanenti"] == 10


def test_scadenza_manutenzione_oggi(
    client,
    admin_user,
    login_admin,
):
    """
    Una manutenzione che scade oggi deve
    essere considerata in scadenza.
    """

    oggi = date.today()

    dispositivo = crea_dispositivo_test(
        client,
        login_admin,
    )

    response = client.post(
        f"/dispositivi/{dispositivo['id']}/manutenzioni",
        json=manutenzione_payload(
            oggi.isoformat()
        ),
        headers=login_admin,
    )

    assert response.status_code == 200

    response = client.get(
        "/dispositivi/scadenze",
        params={
            "entro_giorni": 0,
        },
        headers=login_admin,
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1

    assert data[0]["tipo_scadenza"] == "manutenzione"
    assert data[0]["giorni_rimanenti"] == 0


def test_scadenza_manutenzione_scaduta(
    client,
    admin_user,
    login_admin,
):
    """
    Una manutenzione già scaduta viene
    inclusa dalla logica attuale.
    """

    oggi = date.today()
    scadenza = oggi - timedelta(days=5)

    dispositivo = crea_dispositivo_test(
        client,
        login_admin,
    )

    response = client.post(
        f"/dispositivi/{dispositivo['id']}/manutenzioni",
        json=manutenzione_payload(
            scadenza.isoformat()
        ),
        headers=login_admin,
    )

    assert response.status_code == 200

    response = client.get(
        "/dispositivi/scadenze",
        params={
            "entro_giorni": 30,
        },
        headers=login_admin,
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1

    assert data[0]["giorni_rimanenti"] == -5


def test_scadenza_manutenzione_oltre_limite_non_inclusa(
    client,
    admin_user,
    login_admin,
):
    """
    Una manutenzione oltre la finestra
    temporale richiesta non deve comparire.
    """

    oggi = date.today()
    scadenza = oggi + timedelta(days=31)

    dispositivo = crea_dispositivo_test(
        client,
        login_admin,
    )

    response = client.post(
        f"/dispositivi/{dispositivo['id']}/manutenzioni",
        json=manutenzione_payload(
            scadenza.isoformat()
        ),
        headers=login_admin,
    )

    assert response.status_code == 200

    response = client.get(
        "/dispositivi/scadenze",
        params={
            "entro_giorni": 30,
        },
        headers=login_admin,
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 0


# ============================================================
# SCADENZA CALIBRAZIONE
# ============================================================

def test_scadenza_calibrazione_inclusa(
    client,
    admin_user,
    login_admin,
):
    """
    Una calibrazione con scadenza entro
    la finestra richiesta deve comparire.
    """

    oggi = date.today()
    scadenza = oggi + timedelta(days=15)

    dispositivo = crea_dispositivo_test(
        client,
        login_admin,
    )

    response = client.post(
        f"/dispositivi/{dispositivo['id']}/calibrazioni",
        json=calibrazione_payload(
            scadenza.isoformat()
        ),
        headers=login_admin,
    )

    assert response.status_code == 200

    response = client.get(
        "/dispositivi/scadenze",
        params={
            "entro_giorni": 30,
        },
        headers=login_admin,
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1

    item = data[0]

    assert item["dispositivo_id"] == dispositivo["id"]
    assert item["dispositivo_nome"] == dispositivo["nome"]
    assert item["tipo_scadenza"] == "calibrazione"
    assert item["data_scadenza"] == scadenza.isoformat()
    assert item["giorni_rimanenti"] == 15


def test_scadenza_calibrazione_oggi(
    client,
    admin_user,
    login_admin,
):
    """
    Una calibrazione che scade oggi deve
    essere considerata in scadenza.
    """

    oggi = date.today()

    dispositivo = crea_dispositivo_test(
        client,
        login_admin,
    )

    response = client.post(
        f"/dispositivi/{dispositivo['id']}/calibrazioni",
        json=calibrazione_payload(
            oggi.isoformat()
        ),
        headers=login_admin,
    )

    assert response.status_code == 200

    response = client.get(
        "/dispositivi/scadenze",
        params={
            "entro_giorni": 0,
        },
        headers=login_admin,
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1

    assert data[0]["tipo_scadenza"] == "calibrazione"
    assert data[0]["giorni_rimanenti"] == 0


def test_scadenza_calibrazione_oltre_limite_non_inclusa(
    client,
    admin_user,
    login_admin,
):
    """
    Una calibrazione oltre la finestra
    temporale richiesta non deve comparire.
    """

    oggi = date.today()
    scadenza = oggi + timedelta(days=31)

    dispositivo = crea_dispositivo_test(
        client,
        login_admin,
    )

    response = client.post(
        f"/dispositivi/{dispositivo['id']}/calibrazioni",
        json=calibrazione_payload(
            scadenza.isoformat()
        ),
        headers=login_admin,
    )

    assert response.status_code == 200

    response = client.get(
        "/dispositivi/scadenze",
        params={
            "entro_giorni": 30,
        },
        headers=login_admin,
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 0


# ============================================================
# PIÙ SCADENZE
# ============================================================

def test_manutenzione_e_calibrazione_nello_stesso_dispositivo(
    client,
    admin_user,
    login_admin,
):
    """
    Lo stesso dispositivo può avere
    contemporaneamente una scadenza di
    manutenzione e una di calibrazione.
    """

    oggi = date.today()

    scadenza_manutenzione = oggi + timedelta(
        days=5
    )

    scadenza_calibrazione = oggi + timedelta(
        days=15
    )

    dispositivo = crea_dispositivo_test(
        client,
        login_admin,
    )

    manutenzione_response = client.post(
        f"/dispositivi/{dispositivo['id']}/manutenzioni",
        json=manutenzione_payload(
            scadenza_manutenzione.isoformat()
        ),
        headers=login_admin,
    )

    calibrazione_response = client.post(
        f"/dispositivi/{dispositivo['id']}/calibrazioni",
        json=calibrazione_payload(
            scadenza_calibrazione.isoformat()
        ),
        headers=login_admin,
    )

    assert manutenzione_response.status_code == 200
    assert calibrazione_response.status_code == 200

    response = client.get(
        "/dispositivi/scadenze",
        params={
            "entro_giorni": 30,
        },
        headers=login_admin,
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2

    tipi = {
        item["tipo_scadenza"]
        for item in data
    }

    assert tipi == {
        "manutenzione",
        "calibrazione",
    }


def test_scadenze_di_piu_dispositivi(
    client,
    admin_user,
    login_admin,
):
    """
    Le scadenze di dispositivi differenti
    devono essere restituite insieme.
    """

    oggi = date.today()

    dispositivo_1 = crea_dispositivo_test(
        client,
        login_admin,
        numero_seriale="DEADLINE-SN-101",
        udi="DEADLINE-UDI-101",
    )

    dispositivo_2 = crea_dispositivo_test(
        client,
        login_admin,
        numero_seriale="DEADLINE-SN-102",
        udi="DEADLINE-UDI-102",
    )

    response_1 = client.post(
        f"/dispositivi/{dispositivo_1['id']}/manutenzioni",
        json=manutenzione_payload(
            (
                oggi + timedelta(days=5)
            ).isoformat()
        ),
        headers=login_admin,
    )

    response_2 = client.post(
        f"/dispositivi/{dispositivo_2['id']}/calibrazioni",
        json=calibrazione_payload(
            (
                oggi + timedelta(days=10)
            ).isoformat()
        ),
        headers=login_admin,
    )

    assert response_1.status_code == 200
    assert response_2.status_code == 200

    response = client.get(
        "/dispositivi/scadenze",
        params={
            "entro_giorni": 30,
        },
        headers=login_admin,
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2

    dispositivi = {
        item["dispositivo_id"]
        for item in data
    }

    assert dispositivi == {
        dispositivo_1["id"],
        dispositivo_2["id"],
    }


# ============================================================
# ORDINAMENTO
# ============================================================

def test_scadenze_ordinate_per_giorni_rimanenti(
    client,
    admin_user,
    login_admin,
):
    """
    Le scadenze devono essere ordinate
    dal minor numero di giorni rimanenti
    al maggiore.
    """

    oggi = date.today()

    dispositivo = crea_dispositivo_test(
        client,
        login_admin,
    )

    scadenza_1 = oggi + timedelta(days=20)
    scadenza_2 = oggi + timedelta(days=5)
    scadenza_3 = oggi + timedelta(days=10)

    for scadenza in (
        scadenza_1,
        scadenza_2,
        scadenza_3,
    ):
        response = client.post(
            f"/dispositivi/{dispositivo['id']}/manutenzioni",
            json=manutenzione_payload(
                scadenza.isoformat()
            ),
            headers=login_admin,
        )

        assert response.status_code == 200

    response = client.get(
        "/dispositivi/scadenze",
        params={
            "entro_giorni": 30,
        },
        headers=login_admin,
    )

    assert response.status_code == 200

    data = response.json()

    giorni = [
        item["giorni_rimanenti"]
        for item in data
    ]

    assert giorni == [
        5,
        10,
        20,
    ]


# ============================================================
# PARAMETRO entro_giorni
# ============================================================

def test_parametro_entro_giorni(
    client,
    admin_user,
    login_admin,
):
    """
    Verifica che entro_giorni modifichi
    correttamente la finestra temporale.
    """

    oggi = date.today()

    dispositivo = crea_dispositivo_test(
        client,
        login_admin,
    )

    scadenza = oggi + timedelta(days=20)

    response = client.post(
        f"/dispositivi/{dispositivo['id']}/manutenzioni",
        json=manutenzione_payload(
            scadenza.isoformat()
        ),
        headers=login_admin,
    )

    assert response.status_code == 200

    response = client.get(
        "/dispositivi/scadenze",
        params={
            "entro_giorni": 10,
        },
        headers=login_admin,
    )

    assert response.status_code == 200
    assert len(response.json()) == 0

    response = client.get(
        "/dispositivi/scadenze",
        params={
            "entro_giorni": 20,
        },
        headers=login_admin,
    )

    assert response.status_code == 200
    assert len(response.json()) == 1


def test_entro_giorni_zero(
    client,
    admin_user,
    login_admin,
):
    """
    entro_giorni=0 deve accettare la richiesta
    e considerare le scadenze di oggi
    e quelle già scadute.
    """

    oggi = date.today()

    dispositivo = crea_dispositivo_test(
        client,
        login_admin,
    )

    response = client.post(
        f"/dispositivi/{dispositivo['id']}/manutenzioni",
        json=manutenzione_payload(
            oggi.isoformat()
        ),
        headers=login_admin,
    )

    assert response.status_code == 200

    response = client.get(
        "/dispositivi/scadenze",
        params={
            "entro_giorni": 0,
        },
        headers=login_admin,
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["giorni_rimanenti"] == 0


def test_entro_giorni_negativo_non_valido(
    client,
    admin_user,
    login_admin,
):
    """
    entro_giorni non può essere negativo.
    """

    response = client.get(
        "/dispositivi/scadenze",
        params={
            "entro_giorni": -1,
        },
        headers=login_admin,
    )

    assert response.status_code == 422


def test_entro_giorni_troppo_alto_non_valido(
    client,
    admin_user,
    login_admin,
):
    """
    entro_giorni non può superare 3650 giorni.
    """

    response = client.get(
        "/dispositivi/scadenze",
        params={
            "entro_giorni": 3651,
        },
        headers=login_admin,
    )

    assert response.status_code == 422


# ============================================================
# SCADENZE ASSENTI
# ============================================================

def test_dispositivo_senza_scadenze(
    client,
    admin_user,
    login_admin,
):
    """
    Un dispositivo senza manutenzioni o
    calibrazioni con scadenza non deve
    generare risultati.
    """

    crea_dispositivo_test(
        client,
        login_admin,
    )

    response = client.get(
        "/dispositivi/scadenze",
        params={
            "entro_giorni": 30,
        },
        headers=login_admin,
    )

    assert response.status_code == 200

    assert response.json() == []


def test_manutenzione_senza_prossima_scadenza(
    client,
    admin_user,
    login_admin,
):
    """
    Una manutenzione senza prossima scadenza
    non deve comparire nell'elenco.
    """

    dispositivo = crea_dispositivo_test(
        client,
        login_admin,
    )

    payload = {
        "data": "2026-09-01",
        "tipo": "preventiva",
        "tecnico": "Tecnico Test",
        "descrizione": "Nessuna scadenza.",
        "prossima_scadenza": None,
    }

    response = client.post(
        f"/dispositivi/{dispositivo['id']}/manutenzioni",
        json=payload,
        headers=login_admin,
    )

    assert response.status_code == 200

    response = client.get(
        "/dispositivi/scadenze",
        params={
            "entro_giorni": 30,
        },
        headers=login_admin,
    )

    assert response.status_code == 200

    assert response.json() == []


def test_calibrazione_senza_prossima_scadenza(
    client,
    admin_user,
    login_admin,
):
    """
    Una calibrazione senza prossima scadenza
    non deve comparire nell'elenco.
    """

    dispositivo = crea_dispositivo_test(
        client,
        login_admin,
    )

    payload = {
        "data": "2026-09-01",
        "esito": "conforme",
        "ente_certificatore": "Laboratorio Test",
        "prossima_scadenza": None,
    }

    response = client.post(
        f"/dispositivi/{dispositivo['id']}/calibrazioni",
        json=payload,
        headers=login_admin,
    )

    assert response.status_code == 200

    response = client.get(
        "/dispositivi/scadenze",
        params={
            "entro_giorni": 30,
        },
        headers=login_admin,
    )

    assert response.status_code == 200

    assert response.json() == []


# ============================================================
# GARANZIA
# ============================================================

def test_scadenza_garanzia_non_inclusa_nella_logica_attuale(
    client,
    admin_user,
    login_admin,
):
    """
    La data_scadenza_garanzia del dispositivo
    è presente nel modello, ma attualmente
    NON viene considerata da
    dispositivi_in_scadenza().
    """

    oggi = date.today()

    dispositivo = crea_dispositivo_test(
        client,
        login_admin,
    )

    # Il dispositivo ha una garanzia che scade
    # entro 10 giorni.
    nuova_data_garanzia = (
        oggi + timedelta(days=10)
    ).isoformat()

    update_response = client.put(
        f"/dispositivi/{dispositivo['id']}",
        json={
            "data_scadenza_garanzia": nuova_data_garanzia,
        },
        headers=login_admin,
    )

    assert update_response.status_code == 200

    response = client.get(
        "/dispositivi/scadenze",
        params={
            "entro_giorni": 30,
        },
        headers=login_admin,
    )

    assert response.status_code == 200

    data = response.json()

    assert data == []