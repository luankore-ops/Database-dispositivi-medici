# gui/medical_login_window.py

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from gui.medical_api_connector import (
    MedicalAPIAuthenticationError,
    MedicalAPIConnectorError,
    MedicalAPIAuthorizationError,
)
from gui.medical_user_session import (
    MedicalUserSession,
    medical_user_session,
)


class MedicalLoginWindow(QWidget):
    """
    Finestra principale di autenticazione dell'applicazione.

    La finestra:
    - raccoglie username e password;
    - permette di mostrare/nascondere la password;
    - comunica con il backend tramite MedicalUserSession;
    - gestisce gli errori di autenticazione;
    - emette il segnale login_successful quando il login
      viene completato correttamente.
    """

    login_successful = Signal()

    def __init__(
        self,
        user_session: Optional[MedicalUserSession] = None,
    ) -> None:
        super().__init__()

        self.user_session = (
            user_session
            if user_session is not None
            else medical_user_session
        )

        self.setWindowTitle(
            "Database Dispositivi Medici - Accesso"
        )

        self.setFixedSize(
            500,
            620,
        )

        self._build_interface()
        self._connect_signals()

    # ============================================================
    # COSTRUZIONE INTERFACCIA
    # ============================================================

    def _build_interface(self) -> None:
        """
        Costruisce l'interfaccia grafica della finestra.
        """

        self.setStyleSheet(
            """
            QWidget {
                background-color: #f4f6f8;
                color: #1f2933;
                font-family: "Segoe UI";
            }

            QFrame#loginCard {
                background-color: white;
                border: 1px solid #d9dee5;
                border-radius: 14px;
            }

            QLabel#applicationTitle {
                color: #17202a;
                font-size: 24px;
                font-weight: 700;
            }

            QLabel#applicationSubtitle {
                color: #667085;
                font-size: 13px;
            }

            QLabel#fieldLabel {
                color: #344054;
                font-size: 13px;
                font-weight: 600;
            }

            QLineEdit {
                background-color: white;
                border: 1px solid #cbd5e1;
                border-radius: 7px;
                padding: 10px 12px;
                font-size: 14px;
                color: #1f2933;
            }

            QLineEdit:focus {
                border: 2px solid #2563eb;
                padding: 9px 11px;
            }

            QLineEdit:disabled {
                background-color: #f2f4f7;
                color: #98a2b3;
            }

            QPushButton#passwordToggleButton {
                background-color: transparent;
                color: #667085;
                border: none;
                padding: 0px;
                font-size: 16px;
                min-width: 30px;
                max-width: 30px;
            }

            QPushButton#passwordToggleButton:hover {
                color: #2563eb;
                background-color: transparent;
            }

            QPushButton#passwordToggleButton:pressed {
                color: #1d4ed8;
                background-color: transparent;
            }

            QPushButton#passwordToggleButton:disabled {
                color: #98a2b3;
                background-color: transparent;
            }

            QPushButton#loginButton {
                background-color: #2563eb;
                color: white;
                border: none;
                border-radius: 7px;
                padding: 11px;
                font-size: 14px;
                font-weight: 600;
            }

            QPushButton#loginButton:hover {
                background-color: #1d4ed8;
            }

            QPushButton#loginButton:pressed {
                background-color: #1e40af;
            }

            QPushButton#loginButton:disabled {
                background-color: #93c5fd;
                color: #e5e7eb;
            }

            QPushButton#exitButton {
                background-color: transparent;
                color: #475467;
                border: 1px solid #d0d5dd;
                border-radius: 7px;
                padding: 10px;
                font-size: 13px;
            }

            QPushButton#exitButton:hover {
                background-color: #f2f4f7;
            }

            QLabel#statusLabel {
                color: #667085;
                font-size: 12px;
            }

            QLabel#footerLabel {
                color: #98a2b3;
                font-size: 11px;
            }
            """
        )

        # --------------------------------------------------------
        # Layout principale
        # --------------------------------------------------------

        main_layout = QVBoxLayout(
            self
        )

        main_layout.setContentsMargins(
            40,
            35,
            40,
            30,
        )

        main_layout.setSpacing(0)

        # --------------------------------------------------------
        # Titolo applicazione
        # --------------------------------------------------------

        title_label = QLabel(
            "Database Dispositivi Medici"
        )

        title_label.setObjectName(
            "applicationTitle"
        )

        title_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        main_layout.addWidget(
            title_label
        )

        main_layout.addSpacing(
            8
        )

        # --------------------------------------------------------
        # Sottotitolo
        # --------------------------------------------------------

        subtitle_label = QLabel(
            "Sistema di gestione dei dispositivi medici"
        )

        subtitle_label.setObjectName(
            "applicationSubtitle"
        )

        subtitle_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        subtitle_label.setWordWrap(
            True
        )

        main_layout.addWidget(
            subtitle_label
        )

        main_layout.addSpacing(
            30
        )

        # --------------------------------------------------------
        # Card login
        # --------------------------------------------------------

        login_card = QFrame()

        login_card.setObjectName(
            "loginCard"
        )

        card_layout = QVBoxLayout(
            login_card
        )

        card_layout.setContentsMargins(
            35,
            35,
            35,
            30,
        )

        card_layout.setSpacing(
            0
        )

        # --------------------------------------------------------
        # Titolo card
        # --------------------------------------------------------

        login_title = QLabel(
            "Accesso"
        )

        login_title_font = QFont(
            "Segoe UI",
            18,
        )

        login_title_font.setBold(
            True
        )

        login_title.setFont(
            login_title_font
        )

        login_title.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        card_layout.addWidget(
            login_title
        )

        card_layout.addSpacing(
            8
        )

        login_description = QLabel(
            "Inserisci le tue credenziali per continuare."
        )

        login_description.setObjectName(
            "applicationSubtitle"
        )

        login_description.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        login_description.setWordWrap(
            True
        )

        card_layout.addWidget(
            login_description
        )

        card_layout.addSpacing(
            28
        )

        # --------------------------------------------------------
        # Username
        # --------------------------------------------------------

        username_label = QLabel(
            "Username"
        )

        username_label.setObjectName(
            "fieldLabel"
        )

        card_layout.addWidget(
            username_label
        )

        card_layout.addSpacing(
            7
        )

        self.username_input = QLineEdit()

        self.username_input.setPlaceholderText(
            "Inserisci username"
        )

        self.username_input.setClearButtonEnabled(
            True
        )

        self.username_input.setMinimumHeight(
            42
        )

        card_layout.addWidget(
            self.username_input
        )

        card_layout.addSpacing(
            18
        )

        # --------------------------------------------------------
        # Password
        # --------------------------------------------------------

        password_label = QLabel(
            "Password"
        )

        password_label.setObjectName(
            "fieldLabel"
        )

        card_layout.addWidget(
            password_label
        )

        card_layout.addSpacing(
            7
        )

        # Container del campo password
        password_container = QWidget()

        password_container.setMinimumHeight(
            42
        )

        password_layout = QHBoxLayout(
            password_container
        )

        password_layout.setContentsMargins(
            0,
            0,
            4,
            0,
        )

        password_layout.setSpacing(
            0
        )

        # Campo password
        self.password_input = QLineEdit()

        self.password_input.setPlaceholderText(
            "Inserisci password"
        )

        self.password_input.setEchoMode(
            QLineEdit.EchoMode.Password
        )

        self.password_input.setMinimumHeight(
            42
        )

        # --------------------------------------------------------
        # Pulsante mostra/nascondi password
        # --------------------------------------------------------

        self.password_toggle_button = QPushButton(
            "👁"
        )

        self.password_toggle_button.setObjectName(
            "passwordToggleButton"
        )

        self.password_toggle_button.setToolTip(
            "Mostra password"
        )

        self.password_toggle_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        self.password_toggle_button.setFixedWidth(
            34
        )

        self.password_toggle_button.setFixedHeight(
            34
        )

        # Il pulsante viene posizionato all'interno
        # del contenitore del campo password.
        password_layout.addWidget(
            self.password_input
        )

        password_layout.addWidget(
            self.password_toggle_button
        )

        card_layout.addWidget(
            password_container
        )

        card_layout.addSpacing(
            25
        )

        # --------------------------------------------------------
        # Stato
        # --------------------------------------------------------

        self.status_label = QLabel(
            ""
        )

        self.status_label.setObjectName(
            "statusLabel"
        )

        self.status_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.status_label.setWordWrap(
            True
        )

        card_layout.addWidget(
            self.status_label
        )

        card_layout.addSpacing(
            12
        )

        # --------------------------------------------------------
        # Pulsante login
        # --------------------------------------------------------

        self.login_button = QPushButton(
            "Accedi"
        )

        self.login_button.setObjectName(
            "loginButton"
        )

        self.login_button.setMinimumHeight(
            44
        )

        self.login_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        card_layout.addWidget(
            self.login_button
        )

        card_layout.addSpacing(
            10
        )

        # --------------------------------------------------------
        # Pulsante esci
        # --------------------------------------------------------

        self.exit_button = QPushButton(
            "Esci"
        )

        self.exit_button.setObjectName(
            "exitButton"
        )

        self.exit_button.setMinimumHeight(
            40
        )

        self.exit_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        card_layout.addWidget(
            self.exit_button
        )

        main_layout.addWidget(
            login_card
        )

        main_layout.addStretch()

        # --------------------------------------------------------
        # Footer
        # --------------------------------------------------------

        footer_label = QLabel(
            "Medical Device Management System"
        )

        footer_label.setObjectName(
            "footerLabel"
        )

        footer_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        main_layout.addWidget(
            footer_label
        )

    # ============================================================
    # SEGNALI
    # ============================================================

    def _connect_signals(self) -> None:
        """
        Collega i segnali dei pulsanti e della tastiera.
        """

        self.login_button.clicked.connect(
            self._handle_login
        )

        self.exit_button.clicked.connect(
            self._handle_exit
        )

        self.password_toggle_button.clicked.connect(
            self._toggle_password_visibility
        )

        self.password_input.returnPressed.connect(
            self._handle_login
        )

        self.username_input.returnPressed.connect(
            self._focus_password
        )

    # ============================================================
    # MOSTRA / NASCONDI PASSWORD
    # ============================================================

    def _toggle_password_visibility(
        self,
    ) -> None:
        """
        Mostra o nasconde la password digitata.

        Stato normale:
            password nascosta.

        Premendo il pulsante:
            password visibile.

        Premendo nuovamente:
            password nuovamente nascosta.
        """

        if (
            self.password_input.echoMode()
            == QLineEdit.EchoMode.Password
        ):
            self.password_input.setEchoMode(
                QLineEdit.EchoMode.Normal
            )

            self.password_toggle_button.setText(
                "🙈"
            )

            self.password_toggle_button.setToolTip(
                "Nascondi password"
            )

        else:
            self.password_input.setEchoMode(
                QLineEdit.EchoMode.Password
            )

            self.password_toggle_button.setText(
                "👁"
            )

            self.password_toggle_button.setToolTip(
                "Mostra password"
            )

        self.password_input.setFocus()

    # ============================================================
    # AZIONI LOGIN
    # ============================================================

    def _handle_login(self) -> None:
        """
        Gestisce il tentativo di login.
        """

        username = (
            self.username_input
            .text()
            .strip()
        )

        password = (
            self.password_input
            .text()
        )

        # --------------------------------------------------------
        # Validazione locale
        # --------------------------------------------------------

        if not username:
            self._show_status(
                "Inserisci lo username.",
                error=True,
            )

            self.username_input.setFocus()

            return

        if not password:
            self._show_status(
                "Inserisci la password.",
                error=True,
            )

            self.password_input.setFocus()

            return

        # --------------------------------------------------------
        # Stato caricamento
        # --------------------------------------------------------

        self._set_loading_state(
            True
        )

        self._show_status(
            "Autenticazione in corso...",
            error=False,
        )

        QApplication.processEvents()

        try:
            # ----------------------------------------------------
            # Login backend
            # ----------------------------------------------------

            user = self.user_session.login(
                username=username,
                password=password,
            )

            # ----------------------------------------------------
            # Login completato
            # ----------------------------------------------------

            self._show_status(
                "Accesso effettuato.",
                error=False,
            )

            # Puliamo la password dalla memoria della GUI
            self.password_input.clear()

            # Per sicurezza riportiamo il campo password
            # allo stato nascosto.
            self.password_input.setEchoMode(
                QLineEdit.EchoMode.Password
            )

            self.password_toggle_button.setText(
                "👁"
            )

            self.password_toggle_button.setToolTip(
                "Mostra password"
            )

            # Comunichiamo alla GUI principale che il login
            # è stato completato.
            self.login_successful.emit()

            # La login window può essere nascosta.
            self.hide()

        except MedicalAPIAuthenticationError as exc:
            self._handle_login_error(
                "Credenziali non valide.",
                str(exc),
            )

        except MedicalAPIAuthorizationError as exc:
            self._handle_login_error(
                "Accesso non autorizzato.",
                str(exc),
            )

        except MedicalAPIConnectorError as exc:
            self._handle_login_error(
                "Errore di comunicazione.",
                str(exc),
            )

        except Exception as exc:
            self._handle_login_error(
                "Errore inatteso.",
                str(exc),
            )

        finally:
            self._set_loading_state(
                False
            )

    # ============================================================
    # GESTIONE ERRORI
    # ============================================================

    def _handle_login_error(
        self,
        title: str,
        message: str,
    ) -> None:
        """
        Visualizza un errore di login.
        """

        self._show_status(
            message,
            error=True,
        )

        QMessageBox.warning(
            self,
            title,
            message,
        )

        self.password_input.clear()

        # La password deve rimanere nascosta dopo
        # un tentativo di login fallito.
        self.password_input.setEchoMode(
            QLineEdit.EchoMode.Password
        )

        self.password_toggle_button.setText(
            "👁"
        )

        self.password_toggle_button.setToolTip(
            "Mostra password"
        )

        self.password_input.setFocus()

    # ============================================================
    # STATO INTERFACCIA
    # ============================================================

    def _set_loading_state(
        self,
        loading: bool,
    ) -> None:
        """
        Abilita/disabilita i controlli durante il login.
        """

        self.username_input.setEnabled(
            not loading
        )

        self.password_input.setEnabled(
            not loading
        )

        self.password_toggle_button.setEnabled(
            not loading
        )

        self.login_button.setEnabled(
            not loading
        )

        self.exit_button.setEnabled(
            not loading
        )

        if loading:
            self.login_button.setText(
                "Accesso in corso..."
            )
        else:
            self.login_button.setText(
                "Accedi"
            )

    def _show_status(
        self,
        message: str,
        error: bool = False,
    ) -> None:
        """
        Aggiorna il messaggio di stato.
        """

        self.status_label.setText(
            message
        )

        if error:
            self.status_label.setStyleSheet(
                """
                color: #b42318;
                font-size: 12px;
                """
            )
        else:
            self.status_label.setStyleSheet(
                """
                color: #667085;
                font-size: 12px;
                """
            )

    # ============================================================
    # FOCUS
    # ============================================================

    def _focus_password(self) -> None:
        """
        Sposta il focus sul campo password.
        """

        self.password_input.setFocus()

    # ============================================================
    # USCITA
    # ============================================================

    def _handle_exit(self) -> None:
        """
        Chiude l'applicazione.
        """

        self.user_session.logout()

        QApplication.quit()

    # ============================================================
    # VISUALIZZAZIONE
    # ============================================================

    def show_login(self) -> None:
        """
        Mostra la finestra di login e porta il focus
        sul campo appropriato.
        """

        self.show()
        self.raise_()
        self.activateWindow()

        if self.username_input.text().strip():
            self.password_input.setFocus()
        else:
            self.username_input.setFocus()

    # ============================================================
    # RESET
    # ============================================================

    def reset_form(self) -> None:
        """
        Ripristina il form di login.
        """

        self.username_input.clear()
        self.password_input.clear()

        self.status_label.clear()

        self.username_input.setEnabled(
            True
        )

        self.password_input.setEnabled(
            True
        )

        self.password_toggle_button.setEnabled(
            True
        )

        self.login_button.setEnabled(
            True
        )

        self.exit_button.setEnabled(
            True
        )

        self.login_button.setText(
            "Accedi"
        )

        # Password sempre nascosta quando il form
        # viene ripristinato.
        self.password_input.setEchoMode(
            QLineEdit.EchoMode.Password
        )

        self.password_toggle_button.setText(
            "👁"
        )

        self.password_toggle_button.setToolTip(
            "Mostra password"
        )

        self.username_input.setFocus()

    # ============================================================
    # CHIUSURA FINESTRA
    # ============================================================

    def closeEvent(
        self,
        event,
    ) -> None:
        """
        Gestisce la chiusura della finestra.
        """

        self.user_session.logout()

        event.accept()