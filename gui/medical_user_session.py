from __future__ import annotations

from typing import Any, Dict, Optional

from gui.medical_api_connector import (
    MedicalAPIAuthenticationError,
    MedicalAPIConnectorError,
    medical_api_connector,
)


class MedicalUserSession:
    """
    Gestisce la sessione dell'utente autenticato nell'applicazione GUI.

    Il login viene effettuato tramite MedicalAPIConnector.
    La sessione conserva i dati utente restituiti dal backend.
    """

    ROLE_ADMIN = "ADMIN"
    ROLE_TECNICO = "TECNICO"
    ROLE_LETTORE = "LETTORE"

    def __init__(
        self,
        api_connector=medical_api_connector,
    ) -> None:
        self.api = api_connector
        self._user: Optional[Dict[str, Any]] = None

    # ------------------------------------------------------------------
    # USER
    # ------------------------------------------------------------------

    @property
    def user(self) -> Optional[Dict[str, Any]]:
        return self._user

    @property
    def is_authenticated(self) -> bool:
        return self._user is not None and self.api.is_authenticated

    @property
    def user_id(self) -> Optional[int]:
        if not self._user:
            return None

        return self._user.get("id")

    @property
    def username(self) -> Optional[str]:
        if not self._user:
            return None

        return self._user.get("username")

    @property
    def role(self) -> Optional[str]:
        """
        Il backend restituisce il ruolo nel campo 'role'.

        Il modello SQLAlchemy usa invece 'ruolo'.
        La GUI utilizza 'role' perché è il formato restituito
        dalle API.
        """

        if not self._user:
            return None

        role = self._user.get("role")

        if role is None:
            role = self._user.get("ruolo")

        if role is None:
            return None

        if hasattr(role, "value"):
            role = role.value

        return str(role).upper()

    # ------------------------------------------------------------------
    # ROLE CHECKS
    # ------------------------------------------------------------------

    @property
    def is_admin(self) -> bool:
        return self.role == self.ROLE_ADMIN

    @property
    def is_tecnico(self) -> bool:
        return self.role == self.ROLE_TECNICO

    @property
    def is_lettore(self) -> bool:
        return self.role == self.ROLE_LETTORE

    # ------------------------------------------------------------------
    # LOGIN
    # ------------------------------------------------------------------

    def login(
        self,
        username: str,
        password: str,
    ) -> Dict[str, Any]:
        """
        Autentica l'utente tramite il backend.

        MedicalAPIConnector.login() esegue:

            POST /login

        e restituisce il dizionario user proveniente dal backend.
        """

        username = username.strip()

        if not username:
            raise ValueError(
                "Inserisci lo username."
            )

        if not password:
            raise ValueError(
                "Inserisci la password."
            )

        user_data = self.api.login(
            username=username,
            password=password,
        )

        if not isinstance(user_data, dict):
            raise MedicalAPIConnectorError(
                "Il server ha restituito dati utente non validi."
            )

        if not user_data.get("username"):
            raise MedicalAPIConnectorError(
                "Il server non ha restituito lo username dell'utente."
            )

        if user_data.get("role") is None and user_data.get("ruolo") is None:
            raise MedicalAPIConnectorError(
                "Il server non ha restituito il ruolo dell'utente."
            )

        self._user = dict(user_data)

        return self._user

    # ------------------------------------------------------------------
    # REFRESH
    # ------------------------------------------------------------------

    def refresh(self) -> Dict[str, Any]:
        """
        Aggiorna i dati dell'utente autenticato tramite GET /me.
        """

        if not self.api.is_authenticated:
            self._user = None

            raise MedicalAPIAuthenticationError(
                "Sessione non autenticata."
            )

        user_data = self.api.get_me()

        if not isinstance(user_data, dict):
            raise MedicalAPIConnectorError(
                "Il server ha restituito dati utente non validi."
            )

        self._user = dict(user_data)

        return self._user

    # ------------------------------------------------------------------
    # LOGOUT
    # ------------------------------------------------------------------

    def logout(self) -> None:
        """
        Chiude la sessione locale e rimuove il token dal connector.
        """

        self.api.logout()

        self._user = None

    # ------------------------------------------------------------------
    # GENERIC ROLE CHECKS
    # ------------------------------------------------------------------

    def has_role(
        self,
        role: str,
    ) -> bool:
        if not self.is_authenticated:
            return False

        if role is None:
            return False

        return self.role == str(role).upper()

    def has_any_role(
        self,
        *roles: str,
    ) -> bool:
        if not self.is_authenticated:
            return False

        normalized_roles = {
            str(role).upper()
            for role in roles
            if role is not None
        }

        return self.role in normalized_roles

    # ------------------------------------------------------------------
    # DEVICE PERMISSIONS
    # ------------------------------------------------------------------

    def can_view_devices(self) -> bool:
        return self.has_any_role(
            self.ROLE_ADMIN,
            self.ROLE_TECNICO,
            self.ROLE_LETTORE,
        )

    def can_create_devices(self) -> bool:
        return self.has_any_role(
            self.ROLE_ADMIN,
            self.ROLE_TECNICO,
        )

    def can_edit_devices(self) -> bool:
        return self.has_any_role(
            self.ROLE_ADMIN,
            self.ROLE_TECNICO,
        )

    def can_delete_devices(self) -> bool:
        return self.is_admin

    # ------------------------------------------------------------------
    # MAINTENANCE PERMISSIONS
    # ------------------------------------------------------------------

    def can_view_maintenances(self) -> bool:
        return self.has_any_role(
            self.ROLE_ADMIN,
            self.ROLE_TECNICO,
            self.ROLE_LETTORE,
        )

    def can_create_maintenances(self) -> bool:
        return self.has_any_role(
            self.ROLE_ADMIN,
            self.ROLE_TECNICO,
        )

    # ------------------------------------------------------------------
    # CALIBRATION PERMISSIONS
    # ------------------------------------------------------------------

    def can_view_calibrations(self) -> bool:
        return self.has_any_role(
            self.ROLE_ADMIN,
            self.ROLE_TECNICO,
            self.ROLE_LETTORE,
        )

    def can_create_calibrations(self) -> bool:
        return self.has_any_role(
            self.ROLE_ADMIN,
            self.ROLE_TECNICO,
        )

    # ------------------------------------------------------------------
    # DEPARTMENT PERMISSIONS
    # ------------------------------------------------------------------

    def can_view_departments(self) -> bool:
        return self.has_any_role(
            self.ROLE_ADMIN,
            self.ROLE_TECNICO,
            self.ROLE_LETTORE,
        )

    def can_create_departments(self) -> bool:
        return self.is_admin

    # ------------------------------------------------------------------
    # SUPPLIER PERMISSIONS
    # ------------------------------------------------------------------

    def can_view_suppliers(self) -> bool:
        return self.has_any_role(
            self.ROLE_ADMIN,
            self.ROLE_TECNICO,
            self.ROLE_LETTORE,
        )

    def can_create_suppliers(self) -> bool:
        return self.is_admin

    # ------------------------------------------------------------------
    # USER MANAGEMENT PERMISSIONS
    # ------------------------------------------------------------------

    def can_view_users(self) -> bool:
        return self.is_admin

    def can_create_users(self) -> bool:
        return self.is_admin

    def can_edit_users(self) -> bool:
        return self.is_admin

    def can_change_user_password(self) -> bool:
        return self.is_admin

    def can_change_user_status(self) -> bool:
        return self.is_admin

    # ------------------------------------------------------------------
    # AUDIT LOG PERMISSIONS
    # ------------------------------------------------------------------

    def can_view_audit_logs(self) -> bool:
        """
        L'Audit Log è accessibile esclusivamente agli amministratori.
        """

        return self.is_admin

    # ------------------------------------------------------------------
    # AUTHORIZATION HELPERS
    # ------------------------------------------------------------------

    def require_authentication(self) -> None:
        if not self.is_authenticated:
            raise PermissionError(
                "È necessario effettuare il login."
            )

    def require_admin(self) -> None:
        self.require_authentication()

        if not self.is_admin:
            raise PermissionError(
                "Sono necessari i privilegi di amministratore."
            )

    def require_technical_access(self) -> None:
        self.require_authentication()

        if not self.has_any_role(
            self.ROLE_ADMIN,
            self.ROLE_TECNICO,
        ):
            raise PermissionError(
                "Sono necessari privilegi tecnici."
            )

    # ------------------------------------------------------------------
    # DISPLAY
    # ------------------------------------------------------------------

    def get_display_name(self) -> str:
        if not self.is_authenticated:
            return "Utente non autenticato"

        return self.username or "Utente"

    def get_session_info(self) -> Dict[str, Any]:
        return {
            "authenticated": self.is_authenticated,
            "user_id": self.user_id,
            "username": self.username,
            "role": self.role,
        }


# ----------------------------------------------------------------------
# SESSIONE CONDIVISA
# ----------------------------------------------------------------------

medical_user_session = MedicalUserSession()