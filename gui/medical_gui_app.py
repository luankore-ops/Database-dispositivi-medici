# gui/medical_gui_app.py

from __future__ import annotations

import sys
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication

from gui.medical_dashboard import MedicalDashboard
from gui.medical_login_window import MedicalLoginWindow
from gui.medical_user_session import (
    MedicalUserSession,
    medical_user_session,
)


class MedicalGUIApplication:
    """
    Gestore principale dell'applicazione desktop.

    Responsabilità:
    - creare QApplication;
    - creare la sessione utente;
    - mostrare la finestra di login;
    - mostrare la dashboard dopo il login;
    - gestire logout;
    - gestire la chiusura dell'applicazione.
    """

    def __init__(
        self,
        application: QApplication,
    ) -> None:
        self.application = application

        self.user_session: MedicalUserSession = (
            medical_user_session
        )

        self.login_window: Optional[
            MedicalLoginWindow
        ] = None

        self.dashboard_window: Optional[
            MedicalDashboard
        ] = None

        self._create_windows()
        self._connect_signals()

    # ============================================================
    # CREAZIONE FINESTRE
    # ============================================================

    def _create_windows(self) -> None:
        """
        Crea le finestre principali dell'applicazione.
        """

        self.login_window = MedicalLoginWindow(
            user_session=self.user_session
        )

        self.dashboard_window = MedicalDashboard(
            user_session=self.user_session
        )

    # ============================================================
    # COLLEGAMENTO SEGNALI
    # ============================================================

    def _connect_signals(self) -> None:
        """
        Collega i segnali tra login e dashboard.
        """

        if self.login_window is not None:
            self.login_window.login_successful.connect(
                self._handle_login_success
            )

        if self.dashboard_window is not None:
            self.dashboard_window.logout_requested.connect(
                self._handle_logout
            )

    # ============================================================
    # AVVIO
    # ============================================================

    def start(self) -> int:
        """
        Avvia l'applicazione mostrando la finestra di login.
        """

        if self.login_window is None:
            raise RuntimeError(
                "Finestra di login non inizializzata."
            )

        self.login_window.show_login()

        return self.application.exec()

    # ============================================================
    # LOGIN RIUSCITO
    # ============================================================

    def _handle_login_success(self) -> None:
        """
        Gestisce il completamento corretto del login.
        """

        if self.login_window is not None:
            self.login_window.hide()

        if self.dashboard_window is not None:
            self.dashboard_window.show_dashboard()

    # ============================================================
    # LOGOUT
    # ============================================================

    def _handle_logout(self) -> None:
        """
        Gestisce il logout e riporta l'utente alla finestra
        di autenticazione.
        """

        if self.dashboard_window is not None:
            self.dashboard_window.hide()

        if self.login_window is not None:
            self.login_window.reset_form()
            self.login_window.show_login()

    # ============================================================
    # CHIUSURA
    # ============================================================

    def shutdown(self) -> None:
        """
        Chiude la sessione e le finestre dell'applicazione.
        """

        self.user_session.logout()

        if self.dashboard_window is not None:
            self.dashboard_window.close()

        if self.login_window is not None:
            self.login_window.close()


# ================================================================
# CONFIGURAZIONE QAPPLICATION
# ================================================================

def create_medical_qt_application(
    arguments: list[str],
) -> QApplication:
    """
    Crea e configura QApplication.
    """

    application = QApplication(
        arguments
    )

    application.setApplicationName(
        "Database Dispositivi Medici"
    )

    application.setApplicationDisplayName(
        "Database Dispositivi Medici"
    )

    application.setOrganizationName(
        "Medical Device Management"
    )

    application.setOrganizationDomain(
        "medical-device-management.local"
    )

    application.setStyle(
        "Fusion"
    )

    application.setFont(
        QFont(
            "Segoe UI",
            10,
        )
    )

    return application


# ================================================================
# ENTRY POINT
# ================================================================

def main() -> int:
    """
    Entry point principale della GUI.
    """

    application = create_medical_qt_application(
        sys.argv
    )

    gui_application = MedicalGUIApplication(
        application
    )

    return_code = 0

    try:
        return_code = gui_application.start()

    except KeyboardInterrupt:
        return_code = 0

    finally:
        gui_application.shutdown()

    return return_code


if __name__ == "__main__":
    sys.exit(
        main()
    )