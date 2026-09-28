"""
tests/conftest.py
-----------------
Configurazione comune per i test automatici.

I test utilizzano un database SQLite separato
dal database reale dell'applicazione.
"""

import os
import sys
from pathlib import Path


# ============================================================
# ROOT DEL PROGETTO
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(PROJECT_ROOT),
    )


# ============================================================
# CONFIGURAZIONE JWT PER I TEST
# ============================================================

os.environ["JWT_SECRET_KEY"] = (
    "test-secret-key-super-long-and-safe-for-tests"
)

os.environ["JWT_EXPIRE_MINUTES"] = "30"


# ============================================================
# IMPORT
# ============================================================

import pytest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import main
import auth

from auth import hash_password
from models import (
    Base,
    RuoloUtente,
    Utente,
)


# ============================================================
# DATABASE DI TEST
# ============================================================

TEST_DATABASE_URL = (
    "sqlite:///./test_dispositivi_medici.db"
)

engine_test = create_engine(
    TEST_DATABASE_URL,
    connect_args={
        "check_same_thread": False
    },
)

TestingSessionLocal = sessionmaker(
    bind=engine_test,
    autoflush=False,
    autocommit=False,
)


# ============================================================
# DATABASE FIXTURE
# ============================================================

@pytest.fixture()
def db():
    """
    Crea un database completamente pulito
    per ogni test.
    """

    Base.metadata.create_all(
        bind=engine_test
    )

    session = TestingSessionLocal()

    try:
        yield session

    finally:
        session.close()

        Base.metadata.drop_all(
            bind=engine_test
        )


# ============================================================
# CLIENT FASTAPI
# ============================================================

@pytest.fixture()
def client(db):
    """
    Crea un TestClient FastAPI utilizzando
    esclusivamente il database di test.

    IMPORTANTE:
    sia main.py sia auth.py devono utilizzare
    il database di test.
    """

    def override_get_db():
        try:
            yield db
        finally:
            pass

    # --------------------------------------------------------
    # Dependency usata dalle route di main.py
    # --------------------------------------------------------

    main.app.dependency_overrides[
        main.get_db
    ] = override_get_db

    # --------------------------------------------------------
    # Dependency usata da auth.py
    #
    # get_current_user() utilizza infatti:
    #
    #     Depends(database.get_db)
    #
    # quindi dobbiamo sostituire anche quella.
    # --------------------------------------------------------

    main.app.dependency_overrides[
        auth.get_db
    ] = override_get_db

    try:

        with TestClient(
            main.app
        ) as test_client:

            yield test_client

    finally:

        main.app.dependency_overrides.clear()


# ============================================================
# UTENTE ADMIN
# ============================================================

@pytest.fixture()
def admin_user(db):
    """
    Crea un amministratore di test.
    """

    user = Utente(
        username="admin_test",
        password_hash=hash_password(
            "AdminPassword123!"
        ),
        ruolo=RuoloUtente.ADMIN,
        attivo=True,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


# ============================================================
# UTENTE TECNICO
# ============================================================

@pytest.fixture()
def tecnico_user(db):
    """
    Crea un tecnico di test.
    """

    user = Utente(
        username="tecnico_test",
        password_hash=hash_password(
            "TecnicoPassword123!"
        ),
        ruolo=RuoloUtente.TECNICO,
        attivo=True,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


# ============================================================
# UTENTE LETTORE
# ============================================================

@pytest.fixture()
def lettore_user(db):
    """
    Crea un lettore di test.
    """

    user = Utente(
        username="lettore_test",
        password_hash=hash_password(
            "LettorePassword123!"
        ),
        ruolo=RuoloUtente.LETTORE,
        attivo=True,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


# ============================================================
# LOGIN ADMIN
# ============================================================

@pytest.fixture()
def login_admin(
    client,
    admin_user,
):
    """
    Effettua il login dell'amministratore
    utilizzando il database di test.
    """

    response = client.post(
        "/login",
        params={
            "username": "admin_test",
            "password": "AdminPassword123!",
        },
    )

    assert response.status_code == 200

    data = response.json()

    token = data["access_token"]

    return {
        "Authorization": f"Bearer {token}"
    }


# ============================================================
# LOGIN TECNICO
# ============================================================

@pytest.fixture()
def login_tecnico(
    client,
    tecnico_user,
):
    """
    Effettua il login del tecnico.
    """

    response = client.post(
        "/login",
        params={
            "username": "tecnico_test",
            "password": "TecnicoPassword123!",
        },
    )

    assert response.status_code == 200

    data = response.json()

    token = data["access_token"]

    return {
        "Authorization": f"Bearer {token}"
    }


# ============================================================
# LOGIN LETTORE
# ============================================================

@pytest.fixture()
def login_lettore(
    client,
    lettore_user,
):
    """
    Effettua il login del lettore.
    """

    response = client.post(
        "/login",
        params={
            "username": "lettore_test",
            "password": "LettorePassword123!",
        },
    )

    assert response.status_code == 200

    data = response.json()

    token = data["access_token"]

    return {
        "Authorization": f"Bearer {token}"
    }