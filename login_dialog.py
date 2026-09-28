"""
login_dialog.py
---------------
Finestra di autenticazione dell'applicazione desktop.
"""

import requests

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QFormLayout,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QLabel,
    QMessageBox,
)

from api_client import ApiClient


class LoginDialog(QDialog):
    """
    Finestra di login.

    Riceve un ApiClient già esistente e utilizza quello
    per effettuare l'autenticazione.
    """

    def __init__(
        self,
        client: ApiClient,
        parent=None,
    ):
        super().__init__(parent)

        self.client = client

        self.setWindowTitle(
            "Accesso - Gestione Dispositivi Medici"
        )

        self.setMinimumWidth(420)

        self.setModal(True)

        self._build_ui()

    # ==========================================================
    # INTERFACCIA
    # ==========================================================

    def _build_ui(self):

        layout = QVBoxLayout(self)

        titolo = QLabel(
            "Gestione Dispositivi Medici"
        )

        titolo.setAlignment(Qt.AlignCenter)

        titolo.setStyleSheet(
            """
            QLabel {
                font-size: 22px;
                font-weight: bold;
                padding: 15px;
            }
            """
        )

        layout.addWidget(titolo)

        sottotitolo = QLabel(
            "Autenticazione richiesta"
        )

        sottotitolo.setAlignment(Qt.AlignCenter)

        sottotitolo.setStyleSheet(
            """
            QLabel {
                font-size: 14px;
                color: #666666;
                padding-bottom: 15px;
            }
            """
        )

        layout.addWidget(sottotitolo)

        # ------------------------------------------------------
        # Form
        # ------------------------------------------------------

        form = QFormLayout()

        self.input_username = QLineEdit()

        self.input_username.setPlaceholderText(
            "Username"
        )

        self.input_username.setMinimumHeight(35)

        self.input_password = QLineEdit()

        self.input_password.setPlaceholderText(
            "Password"
        )

        self.input_password.setEchoMode(
            QLineEdit.Password
        )

        self.input_password.setMinimumHeight(35)

        form.addRow(
            "Username:",
            self.input_username,
        )

        form.addRow(
            "Password:",
            self.input_password,
        )

        layout.addLayout(form)

        # ------------------------------------------------------
        # Pulsante login
        # ------------------------------------------------------

        self.btn_login = QPushButton(
            "Accedi"
        )

        self.btn_login.setMinimumHeight(40)

        self.btn_login.setDefault(True)

        self.btn_login.clicked.connect(
            self._esegui_login
        )

        layout.addWidget(
            self.btn_login
        )

        # ------------------------------------------------------
        # Informazioni
        # ------------------------------------------------------

        info = QLabel(
            "Inserisci le credenziali dell'utente "
            "amministratore o di un altro utente autorizzato."
        )

        info.setWordWrap(True)

        info.setAlignment(Qt.AlignCenter)

        info.setStyleSheet(
            """
            QLabel {
                color: #777777;
                font-size: 11px;
                padding: 10px;
            }
            """
        )

        layout.addWidget(info)

        self.input_username.setFocus()

    # ==========================================================
    # LOGIN
    # ==========================================================

    def _esegui_login(self):

        username = (
            self.input_username
            .text()
            .strip()
        )

        password = (
            self.input_password
            .text()
        )

        if not username:

            QMessageBox.warning(
                self,
                "Campo mancante",
                "Inserisci lo username.",
            )

            self.input_username.setFocus()

            return

        if not password:

            QMessageBox.warning(
                self,
                "Campo mancante",
                "Inserisci la password.",
            )

            self.input_password.setFocus()

            return

        self.btn_login.setEnabled(False)

        self.btn_login.setText(
            "Autenticazione..."
        )

        try:

            # --------------------------------------------------
            # Login
            # --------------------------------------------------

            self.client.login(
                username,
                password,
            )

            # --------------------------------------------------
            # Recupera informazioni utente
            # --------------------------------------------------

            try:

                self.client.get_me()

            except requests.RequestException:
                # Il login è già riuscito.
                # Se /me dovesse fallire, lasciamo comunque
                # proseguire il login.
                pass

            # --------------------------------------------------
            # Login riuscito
            # --------------------------------------------------

            self.accept()

        except requests.HTTPError as exc:

            status_code = (
                exc.response.status_code
                if exc.response is not None
                else None
            )

            if status_code == 401:

                QMessageBox.warning(
                    self,
                    "Accesso negato",
                    "Username o password non corretti.",
                )

            elif status_code == 403:

                QMessageBox.warning(
                    self,
                    "Accesso negato",
                    "L'utente è disattivato o "
                    "non dispone dei permessi necessari.",
                )

            else:

                QMessageBox.critical(
                    self,
                    "Errore di autenticazione",
                    "Il server ha restituito un errore.\n\n"
                    f"Codice HTTP: {status_code}\n\n"
                    f"Dettagli:\n{exc}",
                )

        except requests.ConnectionError:

            QMessageBox.critical(
                self,
                "Backend non disponibile",
                "Non è possibile raggiungere il backend FastAPI.\n\n"
                "Verifica che il backend sia in esecuzione.",
            )

        except requests.Timeout:

            QMessageBox.critical(
                self,
                "Timeout",
                "Il backend non ha risposto entro "
                "il tempo previsto.",
            )

        except requests.RequestException as exc:

            QMessageBox.critical(
                self,
                "Errore di comunicazione",
                "Si è verificato un errore durante "
                "la comunicazione con il backend.\n\n"
                f"Dettagli:\n{exc}",
            )

        except Exception as exc:

            QMessageBox.critical(
                self,
                "Errore imprevisto",
                "Si è verificato un errore inatteso.\n\n"
                f"Dettagli:\n{exc}",
            )

        finally:

            self.btn_login.setEnabled(True)

            self.btn_login.setText(
                "Accedi"
            )