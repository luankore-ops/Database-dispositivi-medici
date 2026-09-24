"""
app.py — Entry point dell'applicazione desktop

Il backend FastAPI viene avviato automaticamente in un thread interno:
non serve più aprire un secondo terminale con uvicorn.

Avvio:
    python app.py
"""

import sys
import threading
import time

import requests
import uvicorn
from PySide6.QtWidgets import QApplication, QMessageBox

from main import app as fastapi_app
from main_window import MainWindow

HOST = "127.0.0.1"
PORT = 8000
BASE_URL = f"http://{HOST}:{PORT}"


def avvia_backend():
    """Fa girare il server FastAPI in un thread separato, in sottofondo."""
    config = uvicorn.Config(fastapi_app, host=HOST, port=PORT, log_level="warning")
    server = uvicorn.Server(config)
    server.run()


def attendi_backend_pronto(timeout: float = 10.0) -> bool:
    scadenza = time.time() + timeout
    while time.time() < scadenza:
        try:
            requests.get(f"{BASE_URL}/dispositivi", timeout=1)
            return True
        except requests.RequestException:
            time.sleep(0.3)
    return False


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Gestione Dispositivi Medici")

    # Il thread è "daemon": si chiude automaticamente insieme all'applicazione
    backend_thread = threading.Thread(target=avvia_backend, daemon=True)
    backend_thread.start()

    if not attendi_backend_pronto():
        QMessageBox.critical(
            None, "Errore di avvio",
            "Il backend non ha risposto in tempo. Riprova ad avviare l'applicazione."
        )
        sys.exit(1)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()