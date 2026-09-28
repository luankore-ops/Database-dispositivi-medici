"""
auth_schemas.py
---------------
Schemi Pydantic per autenticazione e utenti.
"""

from pydantic import BaseModel, Field

from models import RuoloUtente


class LoginRequest(BaseModel):
    username: str = Field(
        min_length=3,
        max_length=100,
    )

    password: str = Field(
        min_length=12,
        max_length=128,
    )


class TokenResponse(BaseModel):
    access_token: str

    token_type: str = "bearer"

    expires_in: int

    username: str

    ruolo: RuoloUtente


class MeResponse(BaseModel):
    id: int
    username: str
    ruolo: RuoloUtente
    attivo: bool