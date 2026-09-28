# gui/medical_api_connector.py

from __future__ import annotations

from typing import Any, Optional

import requests


class MedicalAPIConnectorError(Exception):
    """Errore generico del collegamento con il backend."""


class MedicalAPIAuthenticationError(MedicalAPIConnectorError):
    """Errore di autenticazione."""


class MedicalAPIAuthorizationError(MedicalAPIConnectorError):
    """Errore di autorizzazione: l'utente non ha i permessi necessari."""


class MedicalAPINotFoundError(MedicalAPIConnectorError):
    """Risorsa non trovata."""


class MedicalAPIConflictError(MedicalAPIConnectorError):
    """Conflitto con una risorsa già esistente."""


class MedicalAPIValidationError(MedicalAPIConnectorError):
    """Errore di validazione dei dati inviati."""


class MedicalAPIServerError(MedicalAPIConnectorError):
    """Errore interno del backend."""


class MedicalAPIConnector:
    """
    Client HTTP utilizzato dalla GUI per comunicare con il backend FastAPI.

    Il connector si occupa di:
    - autenticazione;
    - gestione del token JWT;
    - richieste GET/POST/PUT/DELETE;
    - gestione degli errori HTTP;
    - gestione degli utenti;
    - gestione dei reparti;
    - gestione dei fornitori;
    - gestione dei dispositivi;
    - gestione delle manutenzioni;
    - gestione delle calibrazioni;
    - gestione delle scadenze;
    - lettura dell'audit log.
    """

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:8000",
        timeout: float = 10.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

        self.token: Optional[str] = None
        self.user: Optional[dict[str, Any]] = None

        self.session = requests.Session()

    # ============================================================
    # PROPRIETÀ SESSIONE
    # ============================================================

    @property
    def is_authenticated(self) -> bool:
        """Restituisce True se esiste una sessione autenticata."""
        return self.token is not None and self.user is not None

    @property
    def username(self) -> Optional[str]:
        """Restituisce lo username dell'utente autenticato."""
        if self.user is None:
            return None

        return self.user.get("username")

    @property
    def role(self) -> Optional[str]:
        """Restituisce il ruolo dell'utente autenticato."""
        if self.user is None:
            return None

        return self.user.get("ruolo")

    @property
    def user_id(self) -> Optional[int]:
        """Restituisce l'ID dell'utente autenticato."""
        if self.user is None:
            return None

        return self.user.get("id")

    # ============================================================
    # URL E HEADER
    # ============================================================

    def _build_url(self, endpoint: str) -> str:
        """
        Costruisce l'URL completo del backend.
        """
        endpoint = endpoint.strip()

        if not endpoint.startswith("/"):
            endpoint = f"/{endpoint}"

        return f"{self.base_url}{endpoint}"

    def _get_headers(
        self,
        include_json: bool = False,
    ) -> dict[str, str]:
        """
        Costruisce gli header HTTP della richiesta.
        """

        headers: dict[str, str] = {
            "Accept": "application/json",
        }

        if include_json:
            headers["Content-Type"] = "application/json"

        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        return headers

    # ============================================================
    # GESTIONE ERRORI
    # ============================================================

    def _extract_error_detail(
        self,
        response: requests.Response,
    ) -> Any:
        """
        Estrae il dettaglio dell'errore restituito dal backend.
        """

        try:
            data = response.json()
        except ValueError:
            return response.text or "Errore HTTP."

        if isinstance(data, dict):
            return data.get("detail", data)

        return data

    def _detail_to_message(self, detail: Any) -> str:
        """
        Converte il dettaglio dell'errore in un messaggio leggibile.
        """

        if isinstance(detail, str):
            return detail

        if isinstance(detail, list):
            messages: list[str] = []

            for item in detail:
                if isinstance(item, dict):
                    message = item.get("msg")

                    if message:
                        messages.append(str(message))
                    else:
                        messages.append(str(item))
                else:
                    messages.append(str(item))

            return "; ".join(messages)

        if isinstance(detail, dict):
            message = detail.get("message")

            if message:
                return str(message)

            return str(detail)

        return str(detail)

    def _raise_for_status(
        self,
        response: requests.Response,
    ) -> None:
        """
        Traduce gli status HTTP in eccezioni specifiche.
        """

        if response.ok:
            return

        detail = self._extract_error_detail(response)
        message = self._detail_to_message(detail)

        status_code = response.status_code

        if status_code in (401, 403):
            if status_code == 401:
                raise MedicalAPIAuthenticationError(message)

            raise MedicalAPIAuthorizationError(message)

        if status_code == 404:
            raise MedicalAPINotFoundError(message)

        if status_code == 409:
            raise MedicalAPIConflictError(message)

        if status_code == 422:
            raise MedicalAPIValidationError(message)

        if status_code >= 500:
            raise MedicalAPIServerError(message)

        raise MedicalAPIConnectorError(
            f"Errore HTTP {status_code}: {message}"
        )

    # ============================================================
    # RICHIESTE HTTP GENERICHE
    # ============================================================

    def _request(
        self,
        method: str,
        endpoint: str,
        *,
        params: Optional[dict[str, Any]] = None,
        json: Optional[dict[str, Any]] = None,
    ) -> Any:
        """
        Esegue una richiesta HTTP verso il backend.
        """

        url = self._build_url(endpoint)

        try:
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                json=json,
                headers=self._get_headers(
                    include_json=json is not None
                ),
                timeout=self.timeout,
            )

        except requests.exceptions.Timeout as exc:
            raise MedicalAPIConnectorError(
                "Il server non ha risposto entro il tempo previsto."
            ) from exc

        except requests.exceptions.ConnectionError as exc:
            raise MedicalAPIConnectorError(
                "Impossibile connettersi al backend FastAPI. "
                "Verifica che il server sia avviato."
            ) from exc

        except requests.exceptions.RequestException as exc:
            raise MedicalAPIConnectorError(
                f"Errore durante la comunicazione con il backend: {exc}"
            ) from exc

        self._raise_for_status(response)

        if response.status_code == 204:
            return None

        if not response.content:
            return None

        try:
            return response.json()
        except ValueError:
            return response.text

    def get(
        self,
        endpoint: str,
        params: Optional[dict[str, Any]] = None,
    ) -> Any:
        return self._request(
            "GET",
            endpoint,
            params=params,
        )

    def post(
        self,
        endpoint: str,
        json: Optional[dict[str, Any]] = None,
        params: Optional[dict[str, Any]] = None,
    ) -> Any:
        return self._request(
            "POST",
            endpoint,
            params=params,
            json=json,
        )

    def put(
        self,
        endpoint: str,
        json: Optional[dict[str, Any]] = None,
    ) -> Any:
        return self._request(
            "PUT",
            endpoint,
            json=json,
        )

    def delete(
        self,
        endpoint: str,
    ) -> Any:
        return self._request(
            "DELETE",
            endpoint,
        )

    # ============================================================
    # AUTENTICAZIONE
    # ============================================================

    def login(
        self,
        username: str,
        password: str,
    ) -> dict[str, Any]:
        """
        Effettua il login.

        Il backend attuale espone:

            POST /login

        con username e password come query parameters.
        """

        response = self.post(
            "/login",
            params={
                "username": username,
                "password": password,
            },
        )

        if not isinstance(response, dict):
            raise MedicalAPIAuthenticationError(
                "Risposta di login non valida."
            )

        access_token = response.get("access_token")
        user = response.get("user")

        if not access_token:
            raise MedicalAPIAuthenticationError(
                "Il backend non ha restituito un token di accesso."
            )

        if not isinstance(user, dict):
            raise MedicalAPIAuthenticationError(
                "Il backend non ha restituito i dati dell'utente."
            )

        self.token = access_token
        self.user = user

        return user

    def logout(self) -> None:
        """
        Chiude la sessione locale.

        Il backend attuale non dispone di un endpoint /logout:
        il token viene quindi semplicemente eliminato dalla GUI.
        """

        self.token = None
        self.user = None

    def get_me(self) -> dict[str, Any]:
        """
        Recupera i dati dell'utente autenticato.
        """

        response = self.get("/me")

        if isinstance(response, dict):
            self.user = response

        return response

    # ============================================================
    # UTENTI
    # ============================================================

    def get_users(self) -> Any:
        """
        Recupera l'elenco degli utenti.
        """

        return self.get("/utenti")

    def get_user(
        self,
        user_id: int,
    ) -> Any:
        """
        Recupera un singolo utente.
        """

        return self.get(f"/utenti/{user_id}")

    def create_user(
        self,
        data: dict[str, Any],
    ) -> Any:
        """
        Crea un nuovo utente.
        """

        return self.post(
            "/utenti",
            json=data,
        )

    def update_user(
        self,
        user_id: int,
        data: dict[str, Any],
    ) -> Any:
        """
        Modifica un utente.
        """

        return self.put(
            f"/utenti/{user_id}",
            json=data,
        )

    def update_user_password(
        self,
        user_id: int,
        password: str,
    ) -> Any:
        """
        Modifica la password di un utente.
        """

        return self.put(
            f"/utenti/{user_id}/password",
            json={
                "password": password,
            },
        )

    def update_user_status(
        self,
        user_id: int,
        active: bool,
    ) -> Any:
        """
        Attiva o disattiva un utente.
        """

        return self.put(
            f"/utenti/{user_id}/stato",
            json={
                "attivo": active,
            },
        )

    # ============================================================
    # AUDIT LOG
    # ============================================================

    def get_audit_logs(
        self,
    ) -> Any:
        """
        Recupera il registro degli audit.
        """

        return self.get("/audit-log")

    # ============================================================
    # REPARTI
    # ============================================================

    def get_departments(self) -> Any:
        """
        Recupera tutti i reparti.
        """

        return self.get("/reparti")

    def create_department(
        self,
        data: dict[str, Any],
    ) -> Any:
        """
        Crea un nuovo reparto.
        """

        return self.post(
            "/reparti",
            json=data,
        )

    # ============================================================
    # FORNITORI
    # ============================================================

    def get_suppliers(self) -> Any:
        """
        Recupera tutti i fornitori.
        """

        return self.get("/fornitori")

    def create_supplier(
        self,
        data: dict[str, Any],
    ) -> Any:
        """
        Crea un nuovo fornitore.
        """

        return self.post(
            "/fornitori",
            json=data,
        )

    # ============================================================
    # DISPOSITIVI MEDICI
    # ============================================================

    def get_devices(
        self,
    ) -> Any:
        """
        Recupera tutti i dispositivi.
        """

        return self.get("/dispositivi")

    def get_device(
        self,
        device_id: int,
    ) -> Any:
        """
        Recupera un singolo dispositivo.
        """

        return self.get(
            f"/dispositivi/{device_id}"
        )

    def create_device(
        self,
        data: dict[str, Any],
    ) -> Any:
        """
        Crea un nuovo dispositivo medico.
        """

        return self.post(
            "/dispositivi",
            json=data,
        )

    def update_device(
        self,
        device_id: int,
        data: dict[str, Any],
    ) -> Any:
        """
        Modifica un dispositivo medico.
        """

        return self.put(
            f"/dispositivi/{device_id}",
            json=data,
        )

    def delete_device(
        self,
        device_id: int,
    ) -> Any:
        """
        Elimina un dispositivo medico.
        """

        return self.delete(
            f"/dispositivi/{device_id}"
        )

    # ============================================================
    # SCADENZE
    # ============================================================

    def get_deadlines(
        self,
    ) -> Any:
        """
        Recupera le prossime scadenze dei dispositivi.
        """

        return self.get(
            "/dispositivi/scadenze"
        )

    # ============================================================
    # MANUTENZIONI
    # ============================================================

    def get_maintenances(
        self,
        device_id: int,
    ) -> Any:
        """
        Recupera le manutenzioni di un dispositivo.
        """

        return self.get(
            f"/dispositivi/{device_id}/manutenzioni"
        )

    def create_maintenance(
        self,
        device_id: int,
        data: dict[str, Any],
    ) -> Any:
        """
        Registra una manutenzione.
        """

        return self.post(
            f"/dispositivi/{device_id}/manutenzioni",
            json=data,
        )

    # ============================================================
    # CALIBRAZIONI
    # ============================================================

    def get_calibrations(
        self,
        device_id: int,
    ) -> Any:
        """
        Recupera le calibrazioni di un dispositivo.
        """

        return self.get(
            f"/dispositivi/{device_id}/calibrazioni"
        )

    def create_calibration(
        self,
        device_id: int,
        data: dict[str, Any],
    ) -> Any:
        """
        Registra una calibrazione.
        """

        return self.post(
            f"/dispositivi/{device_id}/calibrazioni",
            json=data,
        )

    # ============================================================
    # HEALTH CHECK
    # ============================================================

    def check_connection(self) -> bool:
        """
        Verifica se il backend è raggiungibile.

        Non richiede autenticazione.
        """

        try:
            response = self.session.get(
                self._build_url("/health"),
                timeout=self.timeout,
            )

            return response.ok

        except requests.exceptions.RequestException:
            return False


# ================================================================
# ISTANZA CONDIVISA DEL CONNECTOR
# ================================================================

medical_api_connector = MedicalAPIConnector()