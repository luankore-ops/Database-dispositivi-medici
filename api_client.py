"""
api_client.py — Client HTTP per comunicare con il backend FastAPI

La GUI desktop non tocca mai il database direttamente: passa sempre da qui.
Backend e frontend restano disaccoppiati (in futuro il backend potrebbe
girare su un server della rete ospedaliera cambiando solo BASE_URL).
"""

from typing import Optional

import requests

BASE_URL = "http://127.0.0.1:8000"
TIMEOUT = 5  # secondi


class ApiClient:
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url

    def _get(self, path: str, params: Optional[dict] = None):
        r = requests.get(f"{self.base_url}{path}", params=params, timeout=TIMEOUT)
        r.raise_for_status()
        return r.json()

    def _post(self, path: str, json_data: dict):
        r = requests.post(f"{self.base_url}{path}", json=json_data, timeout=TIMEOUT)
        r.raise_for_status()
        return r.json()

    def _put(self, path: str, json_data: dict):
        r = requests.put(f"{self.base_url}{path}", json=json_data, timeout=TIMEOUT)
        r.raise_for_status()
        return r.json()

    def _delete(self, path: str):
        r = requests.delete(f"{self.base_url}{path}", timeout=TIMEOUT)
        r.raise_for_status()

    # --- Dispositivi ---

    def lista_dispositivi(self, categoria: Optional[str] = None, stato: Optional[str] = None):
        params = {}
        if categoria:
            params["categoria"] = categoria
        if stato:
            params["stato"] = stato
        return self._get("/dispositivi", params=params)

    def get_dispositivo(self, dispositivo_id: int):
        return self._get(f"/dispositivi/{dispositivo_id}")

    def crea_dispositivo(self, dati: dict):
        return self._post("/dispositivi", dati)

    def aggiorna_dispositivo(self, dispositivo_id: int, dati: dict):
        return self._put(f"/dispositivi/{dispositivo_id}", dati)

    def elimina_dispositivo(self, dispositivo_id: int):
        self._delete(f"/dispositivi/{dispositivo_id}")

    # --- Reparti ---

    def lista_reparti(self):
        return self._get("/reparti")

    def crea_reparto(self, dati: dict):
        return self._post("/reparti", dati)

    # --- Fornitori ---

    def lista_fornitori(self):
        return self._get("/fornitori")

    def crea_fornitore(self, dati: dict):
        return self._post("/fornitori", dati)

    # --- Manutenzioni / Calibrazioni ---

    def crea_manutenzione(self, dispositivo_id: int, dati: dict):
        return self._post(f"/dispositivi/{dispositivo_id}/manutenzioni", dati)

    def lista_manutenzioni(self, dispositivo_id: int):
        return self._get(f"/dispositivi/{dispositivo_id}/manutenzioni")

    def crea_calibrazione(self, dispositivo_id: int, dati: dict):
        return self._post(f"/dispositivi/{dispositivo_id}/calibrazioni", dati)

    def lista_calibrazioni(self, dispositivo_id: int):
        return self._get(f"/dispositivi/{dispositivo_id}/calibrazioni")

    # --- Scadenze ---

    def dispositivi_in_scadenza(self, entro_giorni: int = 30):
        return self._get("/dispositivi/scadenze", params={"entro_giorni": entro_giorni})