"""
auth.py
-------
Gestione autenticazione, password hashing, JWT
e controllo dei ruoli utente.
"""

import os
from datetime import datetime, timedelta, timezone
from typing import Callable

import jwt
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pwdlib import PasswordHash
from sqlalchemy.orm import Session

import models
from database import get_db


# ============================================================
# CONFIGURAZIONE
# ============================================================

load_dotenv()

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")

if not JWT_SECRET_KEY:
    raise RuntimeError(
        "JWT_SECRET_KEY non configurata. "
        "Creare un file .env nella cartella principale del progetto."
    )

JWT_ALGORITHM = "HS256"

JWT_EXPIRE_MINUTES = int(
    os.getenv("JWT_EXPIRE_MINUTES", "30")
)


# ============================================================
# PASSWORD HASHING
# ============================================================

password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    """
    Genera l'hash sicuro della password.
    """
    return password_hash.hash(password)


def verify_password(
    password: str,
    hashed_password: str,
) -> bool:
    """
    Verifica una password rispetto al relativo hash.
    """
    return password_hash.verify(
        password,
        hashed_password,
    )


# ============================================================
# JWT
# ============================================================

security = HTTPBearer(
    auto_error=False
)


def create_access_token(
    user: models.Utente,
) -> str:
    """
    Crea un JWT per l'utente autenticato.
    """

    now = datetime.now(timezone.utc)

    payload = {
        "sub": str(user.id),
        "username": user.username,
        "role": user.ruolo.value,
        "iat": now,
        "exp": now + timedelta(
            minutes=JWT_EXPIRE_MINUTES
        ),
    }

    token = jwt.encode(
        payload,
        JWT_SECRET_KEY,
        algorithm=JWT_ALGORITHM,
    )

    return token


# ============================================================
# CURRENT USER
# ============================================================

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> models.Utente:
    """
    Recupera l'utente associato al JWT.
    """

    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Autenticazione richiesta.",
            headers={
                "WWW-Authenticate": "Bearer"
            },
        )

    token = credentials.credentials

    try:
        payload = jwt.decode(
            token,
            JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM],
        )

        user_id = payload.get("sub")

        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token non valido.",
                headers={
                    "WWW-Authenticate": "Bearer"
                },
            )

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token scaduto.",
            headers={
                "WWW-Authenticate": "Bearer"
            },
        )

    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token non valido.",
            headers={
                "WWW-Authenticate": "Bearer"
            },
        )

    try:
        user_id_int = int(user_id)

    except (TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="ID utente non valido.",
            headers={
                "WWW-Authenticate": "Bearer"
            },
        )

    user = db.get(
        models.Utente,
        user_id_int,
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Utente non trovato.",
            headers={
                "WWW-Authenticate": "Bearer"
            },
        )

    if not user.attivo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Utente disattivato.",
        )

    return user


# ============================================================
# ROLE CHECK
# ============================================================

def require_roles(
    *allowed_roles: models.RuoloUtente,
) -> Callable:
    """
    Restituisce una dependency FastAPI che consente
    l'accesso solamente agli utenti con i ruoli specificati.

    Esempio:

        @app.post("/devices")
        def create_device(
            current_user = Depends(
                require_roles(
                    models.RuoloUtente.ADMIN,
                    models.RuoloUtente.TECNICO,
                )
            )
        ):
            ...
    """

    def role_checker(
        current_user: models.Utente = Depends(
            get_current_user
        ),
    ) -> models.Utente:

        if current_user.ruolo not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permessi insufficienti.",
            )

        return current_user

    return role_checker


# ============================================================
# LOGIN
# ============================================================

def authenticate_user(
    db: Session,
    username: str,
    password: str,
):
    """
    Verifica username e password.

    Restituisce l'utente se le credenziali sono corrette.
    Restituisce None in caso contrario.
    """

    user = (
        db.query(models.Utente)
        .filter(
            models.Utente.username == username
        )
        .first()
    )

    if user is None:
        return None

    if not user.attivo:
        return None

    if not verify_password(
        password,
        user.password_hash,
    ):
        return None

    return user