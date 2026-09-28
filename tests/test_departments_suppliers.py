"""
tests/test_departments_suppliers.py
------------------------------------
Test automatici per la gestione di:

- reparti;
- fornitori.

Gli endpoint testati sono:

    POST /reparti
    GET  /reparti

    POST /fornitori
    GET  /fornitori
"""


# ============================================================
# PAYLOAD DI TEST
# ============================================================


def reparto_payload(
    nome="Cardiologia",
    piano="1",
):
    """
    Restituisce un payload valido per un reparto.
    """

    return {
        "nome": nome,
        "piano": piano,
    }


def fornitore_payload(
    ragione_sociale="Medical Supplier S.r.l.",
    email_contatto="info@medicalsupplier.test",
    telefono="0711234567",
):
    """
    Restituisce un payload valido per un fornitore.
    """

    return {
        "ragione_sociale": ragione_sociale,
        "email_contatto": email_contatto,
        "telefono": telefono,
    }


# ============================================================
# REPARTI - LETTURA
# ============================================================


def test_lista_reparti_con_database_vuoto(
    client,
    admin_user,
    login_admin,
):
    """
    La lista dei reparti deve essere vuota
    quando non sono presenti reparti.
    """

    response = client.get(
        "/reparti",
        headers=login_admin,
    )

    assert response.status_code == 200
    assert response.json() == []


def test_lista_reparti_richiede_autenticazione(
    client,
):
    """
    L'accesso ai reparti senza token deve
    essere rifiutato.
    """

    response = client.get(
        "/reparti",
    )

    assert response.status_code == 401


def test_admin_puo_leggere_reparti(
    client,
    admin_user,
    login_admin,
):
    """
    L'amministratore può leggere i reparti.
    """

    response = client.get(
        "/reparti",
        headers=login_admin,
    )

    assert response.status_code == 200


def test_tecnico_puo_leggere_reparti(
    client,
    tecnico_user,
    login_tecnico,
):
    """
    Il tecnico può leggere i reparti.
    """

    response = client.get(
        "/reparti",
        headers=login_tecnico,
    )

    assert response.status_code == 200


def test_lettore_puo_leggere_reparti(
    client,
    lettore_user,
    login_lettore,
):
    """
    Il lettore autenticato può leggere i reparti.
    """

    response = client.get(
        "/reparti",
        headers=login_lettore,
    )

    assert response.status_code == 200


# ============================================================
# REPARTI - CREAZIONE
# ============================================================


def test_admin_puo_creare_reparto(
    client,
    admin_user,
    login_admin,
):
    """
    Un amministratore può creare un reparto.
    """

    response = client.post(
        "/reparti",
        json=reparto_payload(),
        headers=login_admin,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] > 0
    assert data["nome"] == "Cardiologia"
    assert data["piano"] == "1"


def test_tecnico_puo_creare_reparto(
    client,
    tecnico_user,
    login_tecnico,
):
    """
    Un tecnico può creare un reparto.
    """

    response = client.post(
        "/reparti",
        json=reparto_payload(
            nome="Radiologia",
            piano="2",
        ),
        headers=login_tecnico,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] > 0
    assert data["nome"] == "Radiologia"
    assert data["piano"] == "2"


def test_lettore_non_puo_creare_reparto(
    client,
    lettore_user,
    login_lettore,
):
    """
    Un lettore non può creare reparti.
    """

    response = client.post(
        "/reparti",
        json=reparto_payload(),
        headers=login_lettore,
    )

    assert response.status_code == 403


def test_creazione_reparto_senza_token(
    client,
):
    """
    La creazione di un reparto senza
    autenticazione deve essere rifiutata.
    """

    response = client.post(
        "/reparti",
        json=reparto_payload(),
    )

    assert response.status_code == 401


# ============================================================
# REPARTI - CAMPI OPZIONALI
# ============================================================


def test_reparto_senza_piano(
    client,
    admin_user,
    login_admin,
):
    """
    Il campo piano è opzionale.
    """

    response = client.post(
        "/reparti",
        json={
            "nome": "Neurologia",
        },
        headers=login_admin,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["nome"] == "Neurologia"
    assert data["piano"] is None


def test_reparto_con_piano_opzionale_stringa(
    client,
    admin_user,
    login_admin,
):
    """
    Il piano può essere valorizzato
    con una stringa.
    """

    response = client.post(
        "/reparti",
        json={
            "nome": "Pronto Soccorso",
            "piano": "PT",
        },
        headers=login_admin,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["nome"] == "Pronto Soccorso"
    assert data["piano"] == "PT"


# ============================================================
# REPARTI - VALIDAZIONE
# ============================================================


def test_reparto_nome_obbligatorio(
    client,
    admin_user,
    login_admin,
):
    """
    Il nome del reparto è obbligatorio.
    """

    response = client.post(
        "/reparti",
        json={
            "piano": "1",
        },
        headers=login_admin,
    )

    assert response.status_code == 422


def test_reparto_nome_non_puo_essere_vuoto(
    client,
    admin_user,
    login_admin,
):
    """
    Il nome del reparto deve contenere
    almeno un carattere.
    """

    response = client.post(
        "/reparti",
        json={
            "nome": "",
            "piano": "1",
        },
        headers=login_admin,
    )

    assert response.status_code == 422


def test_reparto_nome_troppo_lungo(
    client,
    admin_user,
    login_admin,
):
    """
    Il nome del reparto non può superare
    100 caratteri.
    """

    response = client.post(
        "/reparti",
        json={
            "nome": "A" * 101,
            "piano": "1",
        },
        headers=login_admin,
    )

    assert response.status_code == 422


def test_reparto_piano_troppo_lungo(
    client,
    admin_user,
    login_admin,
):
    """
    Il piano non può superare 20 caratteri.
    """

    response = client.post(
        "/reparti",
        json={
            "nome": "Oncologia",
            "piano": "A" * 21,
        },
        headers=login_admin,
    )

    assert response.status_code == 422


# ============================================================
# REPARTI - PIÙ ELEMENTI
# ============================================================


def test_creazione_di_piu_reparti(
    client,
    admin_user,
    login_admin,
):
    """
    È possibile creare più reparti distinti.
    """

    reparto_1 = client.post(
        "/reparti",
        json=reparto_payload(
            nome="Cardiologia",
            piano="1",
        ),
        headers=login_admin,
    )

    reparto_2 = client.post(
        "/reparti",
        json=reparto_payload(
            nome="Neurologia",
            piano="2",
        ),
        headers=login_admin,
    )

    reparto_3 = client.post(
        "/reparti",
        json=reparto_payload(
            nome="Radiologia",
            piano="3",
        ),
        headers=login_admin,
    )

    assert reparto_1.status_code == 200
    assert reparto_2.status_code == 200
    assert reparto_3.status_code == 200

    response = client.get(
        "/reparti",
        headers=login_admin,
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 3

    nomi = {
        reparto["nome"]
        for reparto in data
    }

    assert nomi == {
        "Cardiologia",
        "Neurologia",
        "Radiologia",
    }


def test_lista_reparti_contiene_id(
    client,
    admin_user,
    login_admin,
):
    """
    Ogni reparto restituito deve avere
    un identificativo numerico.
    """

    response = client.post(
        "/reparti",
        json=reparto_payload(),
        headers=login_admin,
    )

    assert response.status_code == 200

    reparto_id = response.json()["id"]

    response = client.get(
        "/reparti",
        headers=login_admin,
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["id"] == reparto_id


# ============================================================
# REPARTI - AUDIT LOG
# ============================================================


def test_creazione_reparto_registra_audit(
    client,
    admin_user,
    login_admin,
):
    """
    La creazione di un reparto deve
    generare una voce nell'audit log.
    """

    response = client.post(
        "/reparti",
        json=reparto_payload(
            nome="Laboratorio Analisi",
            piano="1",
        ),
        headers=login_admin,
    )

    assert response.status_code == 200

    response = client.get(
        "/audit-log",
        headers=login_admin,
    )

    assert response.status_code == 200

    logs = response.json()

    reparto_logs = [
        log
        for log in logs
        if (
            log["tabella"] == "reparti"
            and log["azione"] == "CREATE"
        )
    ]

    assert len(reparto_logs) == 1

    log = reparto_logs[0]

    assert log["utente"] == "admin_test"
    assert "Laboratorio Analisi" in log["dettagli"]


def test_tecnico_creazione_reparto_registra_audit(
    client,
    tecnico_user,
    login_tecnico,
    admin_user,
    login_admin,
):
    """
    Anche la creazione effettuata da un tecnico
    deve essere registrata nell'audit log.
    """

    response = client.post(
        "/reparti",
        json=reparto_payload(
            nome="Terapia Intensiva",
            piano="3",
        ),
        headers=login_tecnico,
    )

    assert response.status_code == 200

    # Il tecnico non ha accesso all'audit log.
    response = client.get(
        "/audit-log",
        headers=login_tecnico,
    )

    assert response.status_code == 403

    # L'admin può verificare il log.
    response = client.get(
        "/audit-log",
        headers=login_admin,
    )

    assert response.status_code == 200

    logs = response.json()

    reparto_logs = [
        log
        for log in logs
        if (
            log["tabella"] == "reparti"
            and log["azione"] == "CREATE"
            and log["utente"] == "tecnico_test"
        )
    ]

    assert len(reparto_logs) == 1
    assert "Terapia Intensiva" in reparto_logs[0]["dettagli"]


# ============================================================
# FORNITORI - LETTURA
# ============================================================


def test_lista_fornitori_con_database_vuoto(
    client,
    admin_user,
    login_admin,
):
    """
    La lista dei fornitori deve essere vuota
    quando non sono presenti fornitori.
    """

    response = client.get(
        "/fornitori",
        headers=login_admin,
    )

    assert response.status_code == 200
    assert response.json() == []


def test_lista_fornitori_richiede_autenticazione(
    client,
):
    """
    L'accesso ai fornitori senza token
    deve essere rifiutato.
    """

    response = client.get(
        "/fornitori",
    )

    assert response.status_code == 401


def test_admin_puo_leggere_fornitori(
    client,
    admin_user,
    login_admin,
):
    """
    L'amministratore può leggere i fornitori.
    """

    response = client.get(
        "/fornitori",
        headers=login_admin,
    )

    assert response.status_code == 200


def test_tecnico_puo_leggere_fornitori(
    client,
    tecnico_user,
    login_tecnico,
):
    """
    Il tecnico può leggere i fornitori.
    """

    response = client.get(
        "/fornitori",
        headers=login_tecnico,
    )

    assert response.status_code == 200


def test_lettore_puo_leggere_fornitori(
    client,
    lettore_user,
    login_lettore,
):
    """
    Il lettore autenticato può leggere i fornitori.
    """

    response = client.get(
        "/fornitori",
        headers=login_lettore,
    )

    assert response.status_code == 200


# ============================================================
# FORNITORI - CREAZIONE
# ============================================================


def test_admin_puo_creare_fornitore(
    client,
    admin_user,
    login_admin,
):
    """
    Un amministratore può creare un fornitore.
    """

    response = client.post(
        "/fornitori",
        json=fornitore_payload(),
        headers=login_admin,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] > 0
    assert data["ragione_sociale"] == "Medical Supplier S.r.l."
    assert data["email_contatto"] == "info@medicalsupplier.test"
    assert data["telefono"] == "0711234567"


def test_tecnico_puo_creare_fornitore(
    client,
    tecnico_user,
    login_tecnico,
):
    """
    Un tecnico può creare un fornitore.
    """

    response = client.post(
        "/fornitori",
        json=fornitore_payload(
            ragione_sociale="Hospital Equipment S.p.A.",
            email_contatto="info@hospital-equipment.test",
            telefono="0719876543",
        ),
        headers=login_tecnico,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] > 0
    assert data["ragione_sociale"] == "Hospital Equipment S.p.A."


def test_lettore_non_puo_creare_fornitore(
    client,
    lettore_user,
    login_lettore,
):
    """
    Un lettore non può creare fornitori.
    """

    response = client.post(
        "/fornitori",
        json=fornitore_payload(),
        headers=login_lettore,
    )

    assert response.status_code == 403


def test_creazione_fornitore_senza_token(
    client,
):
    """
    La creazione di un fornitore senza
    autenticazione deve essere rifiutata.
    """

    response = client.post(
        "/fornitori",
        json=fornitore_payload(),
    )

    assert response.status_code == 401


# ============================================================
# FORNITORI - CAMPI OPZIONALI
# ============================================================


def test_fornitore_senza_email(
    client,
    admin_user,
    login_admin,
):
    """
    L'email di contatto è opzionale.
    """

    response = client.post(
        "/fornitori",
        json={
            "ragione_sociale": "Supplier Senza Email",
            "telefono": "0711111111",
        },
        headers=login_admin,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["ragione_sociale"] == "Supplier Senza Email"
    assert data["email_contatto"] is None
    assert data["telefono"] == "0711111111"


def test_fornitore_senza_telefono(
    client,
    admin_user,
    login_admin,
):
    """
    Il telefono è opzionale.
    """

    response = client.post(
        "/fornitori",
        json={
            "ragione_sociale": "Supplier Senza Telefono",
            "email_contatto": "info@supplier.test",
        },
        headers=login_admin,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["ragione_sociale"] == "Supplier Senza Telefono"
    assert data["email_contatto"] == "info@supplier.test"
    assert data["telefono"] is None


def test_fornitore_solo_ragione_sociale(
    client,
    admin_user,
    login_admin,
):
    """
    È possibile creare un fornitore
    specificando solamente la ragione sociale.
    """

    response = client.post(
        "/fornitori",
        json={
            "ragione_sociale": "Minimal Supplier",
        },
        headers=login_admin,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["ragione_sociale"] == "Minimal Supplier"
    assert data["email_contatto"] is None
    assert data["telefono"] is None


# ============================================================
# FORNITORI - VALIDAZIONE
# ============================================================


def test_fornitore_ragione_sociale_obbligatoria(
    client,
    admin_user,
    login_admin,
):
    """
    La ragione sociale è obbligatoria.
    """

    response = client.post(
        "/fornitori",
        json={
            "email_contatto": "info@supplier.test",
        },
        headers=login_admin,
    )

    assert response.status_code == 422


def test_fornitore_ragione_sociale_vuota(
    client,
    admin_user,
    login_admin,
):
    """
    La ragione sociale non può essere vuota.
    """

    response = client.post(
        "/fornitori",
        json={
            "ragione_sociale": "",
        },
        headers=login_admin,
    )

    assert response.status_code == 422


def test_fornitore_ragione_sociale_troppo_lunga(
    client,
    admin_user,
    login_admin,
):
    """
    La ragione sociale non può superare
    150 caratteri.
    """

    response = client.post(
        "/fornitori",
        json={
            "ragione_sociale": "A" * 151,
        },
        headers=login_admin,
    )

    assert response.status_code == 422


def test_fornitore_email_troppo_lunga(
    client,
    admin_user,
    login_admin,
):
    """
    L'email di contatto non può superare
    150 caratteri.
    """

    response = client.post(
        "/fornitori",
        json={
            "ragione_sociale": "Supplier Test",
            "email_contatto": "A" * 151,
        },
        headers=login_admin,
    )

    assert response.status_code == 422


def test_fornitore_telefono_troppo_lungo(
    client,
    admin_user,
    login_admin,
):
    """
    Il telefono non può superare
    30 caratteri.
    """

    response = client.post(
        "/fornitori",
        json={
            "ragione_sociale": "Supplier Test",
            "telefono": "1" * 31,
        },
        headers=login_admin,
    )

    assert response.status_code == 422


# ============================================================
# FORNITORI - PIÙ ELEMENTI
# ============================================================


def test_creazione_di_piu_fornitori(
    client,
    admin_user,
    login_admin,
):
    """
    È possibile creare più fornitori distinti.
    """

    fornitore_1 = client.post(
        "/fornitori",
        json=fornitore_payload(
            ragione_sociale="Supplier A",
        ),
        headers=login_admin,
    )

    fornitore_2 = client.post(
        "/fornitori",
        json=fornitore_payload(
            ragione_sociale="Supplier B",
        ),
        headers=login_admin,
    )

    fornitore_3 = client.post(
        "/fornitori",
        json=fornitore_payload(
            ragione_sociale="Supplier C",
        ),
        headers=login_admin,
    )

    assert fornitore_1.status_code == 200
    assert fornitore_2.status_code == 200
    assert fornitore_3.status_code == 200

    response = client.get(
        "/fornitori",
        headers=login_admin,
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 3

    nomi = {
        fornitore["ragione_sociale"]
        for fornitore in data
    }

    assert nomi == {
        "Supplier A",
        "Supplier B",
        "Supplier C",
    }


def test_lista_fornitori_contiene_id(
    client,
    admin_user,
    login_admin,
):
    """
    Ogni fornitore restituito deve avere
    un identificativo numerico.
    """

    response = client.post(
        "/fornitori",
        json=fornitore_payload(),
        headers=login_admin,
    )

    assert response.status_code == 200

    fornitore_id = response.json()["id"]

    response = client.get(
        "/fornitori",
        headers=login_admin,
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["id"] == fornitore_id


# ============================================================
# FORNITORI - AUDIT LOG
# ============================================================


def test_creazione_fornitore_registra_audit(
    client,
    admin_user,
    login_admin,
):
    """
    La creazione di un fornitore deve
    generare una voce nell'audit log.
    """

    response = client.post(
        "/fornitori",
        json=fornitore_payload(
            ragione_sociale="Audit Supplier",
        ),
        headers=login_admin,
    )

    assert response.status_code == 200

    response = client.get(
        "/audit-log",
        headers=login_admin,
    )

    assert response.status_code == 200

    logs = response.json()

    fornitore_logs = [
        log
        for log in logs
        if (
            log["tabella"] == "fornitori"
            and log["azione"] == "CREATE"
        )
    ]

    assert len(fornitore_logs) == 1

    log = fornitore_logs[0]

    assert log["utente"] == "admin_test"
    assert "Audit Supplier" in log["dettagli"]


def test_tecnico_creazione_fornitore_registra_audit(
    client,
    tecnico_user,
    login_tecnico,
    admin_user,
    login_admin,
):
    """
    La creazione effettuata da un tecnico
    deve essere registrata nell'audit log.
    """

    response = client.post(
        "/fornitori",
        json=fornitore_payload(
            ragione_sociale="Tecnico Supplier",
        ),
        headers=login_tecnico,
    )

    assert response.status_code == 200

    # Il tecnico non può leggere l'audit log.
    response = client.get(
        "/audit-log",
        headers=login_tecnico,
    )

    assert response.status_code == 403

    # L'admin può verificare il log.
    response = client.get(
        "/audit-log",
        headers=login_admin,
    )

    assert response.status_code == 200

    logs = response.json()

    fornitore_logs = [
        log
        for log in logs
        if (
            log["tabella"] == "fornitori"
            and log["azione"] == "CREATE"
            and log["utente"] == "tecnico_test"
        )
    ]

    assert len(fornitore_logs) == 1
    assert "Tecnico Supplier" in fornitore_logs[0]["dettagli"]