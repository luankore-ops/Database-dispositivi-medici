from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from gui.medical_api_connector import (
    MedicalAPIAuthenticationError,
    MedicalAPIAuthorizationError,
    MedicalAPIConnectorError,
    medical_api_connector,
)

from gui.medical_user_session import medical_user_session

from gui.pages.medical_devices_page import MedicalDevicesPage
from gui.pages.medical_maintenance_page import MedicalMaintenancePage
from gui.pages.medical_calibration_page import MedicalCalibrationPage
from gui.pages.medical_departments_page import MedicalDepartmentsPage
from gui.pages.medical_suppliers_page import MedicalSuppliersPage
from gui.pages.medical_users_page import MedicalUsersPage
from gui.pages.medical_audit_page import MedicalAuditPage

from gui.widgets.medical_statistics_widget import (
    MedicalStatisticsWidget,
)


class MedicalDashboard(QWidget):
    """
    Dashboard principale dell'applicazione.

    Gestisce:
    - navigazione laterale;
    - dashboard principale;
    - statistiche dispositivi;
    - dispositivi;
    - manutenzioni;
    - calibrazioni;
    - reparti;
    - fornitori;
    - utenti;
    - audit log;
    - logout.
    """

    logout_requested = Signal()

    def __init__(
        self,
        user_session=medical_user_session,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)

        self.user_session = user_session
        self.api = medical_api_connector

        self.setWindowTitle(
            "Medical Devices Management System"
        )

        self.setMinimumSize(
            1200,
            750,
        )

        self._build_ui()
        self._create_pages()
        self._connect_navigation()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        # ==============================================================
        # STILE GLOBALE DASHBOARD
        # ==============================================================

        self.setStyleSheet(
            """
            QWidget {
                background-color: #111827;
                color: #f9fafb;
                font-family: "Segoe UI";
            }

            /* ==========================================================
               SIDEBAR
               ========================================================== */

            QFrame#sidebar {
                background-color: #0f172a;
                border-right: 1px solid #1f2937;
            }

            /* ==========================================================
               HEADER
               ========================================================== */

            QFrame#header {
                background-color: #111827;
                border-bottom: 1px solid #1f2937;
            }

            /* ==========================================================
               STACK DELLE PAGINE
               ========================================================== */

            QStackedWidget#pages_stack {
                background-color: #111827;
                border: none;
            }

            QStackedWidget#pages_stack > QWidget {
                background-color: #111827;
            }

            QStackedWidget#pages_stack QWidget {
                background-color: #111827;
            }

            /* ==========================================================
               NAVIGAZIONE
               ========================================================== */

            QListWidget#navigation_list {
                background-color: transparent;
                color: #f3f4f6;
                border: none;
                outline: none;
                padding: 0px;
            }

            QListWidget#navigation_list::item {
                background-color: transparent;
                color: #f3f4f6;
                border-radius: 7px;
                padding: 9px 12px;
                margin: 1px 0px;
            }

            QListWidget#navigation_list::item:hover {
                background-color: #1f2937;
                color: #ffffff;
            }

            QListWidget#navigation_list::item:selected {
                background-color: #2563eb;
                color: #ffffff;
            }

            /* ==========================================================
               LOGOUT
               ========================================================== */

            QPushButton#logout_button {
                background-color: #1f2937;
                color: #f3f4f6;
                border: 1px solid #374151;
                border-radius: 7px;
                padding: 9px 12px;
                font-weight: 600;
            }

            QPushButton#logout_button:hover {
                background-color: #374151;
                border-color: #4b5563;
            }

            /* ==========================================================
               SIDEBAR - TESTI
               ========================================================== */

            QLabel#sidebar_title {
                color: #ffffff;
            }

            QLabel#sidebar_subtitle {
                color: #d1d5db;
            }

            QLabel#username_label {
                color: #ffffff;
            }

            QLabel#role_label {
                color: #d1d5db;
            }

            /* ==========================================================
               HEADER - TITOLO
               ========================================================== */

            QLabel#page_title {
                color: #ffffff;
            }

            /* ==========================================================
               USER FRAME
               ========================================================== */

            QFrame#user_frame {
                background-color: #111827;
                border: 1px solid #1f2937;
                border-radius: 8px;
            }

            /* ==========================================================
               STATISTICHE
               ========================================================== */

            QFrame#stat_card {
                background-color: #1f2937;
                border: 1px solid #374151;
                border-radius: 10px;
            }

            QLabel#stat_title {
                color: #e5e7eb;
            }

            QLabel#stat_value {
                color: #ffffff;
            }

            /* ==========================================================
               DASHBOARD
               ========================================================== */

            QLabel#dashboard_title {
                color: #ffffff;
            }

            QLabel#dashboard_welcome {
                color: #e5e7eb;
            }

            /* ==========================================================
               INFORMAZIONI SISTEMA
               ========================================================== */

            QFrame#system_frame {
                background-color: #1f2937;
                border: 1px solid #374151;
                border-radius: 10px;
            }

            QLabel#system_title {
                color: #ffffff;
            }

            QLabel#system_status {
                color: #e5e7eb;
            }

            /* ==========================================================
               SCROLLBAR VERTICALE
               ========================================================== */

            QScrollBar:vertical {
                background-color: #111827;
                width: 10px;
                margin: 0px;
            }

            QScrollBar::handle:vertical {
                background-color: #374151;
                border-radius: 5px;
                min-height: 30px;
            }

            QScrollBar::handle:vertical:hover {
                background-color: #4b5563;
            }

            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                height: 0px;
            }

            /* ==========================================================
               SCROLLBAR ORIZZONTALE
               ========================================================== */

            QScrollBar:horizontal {
                background-color: #111827;
                height: 10px;
                margin: 0px;
            }

            QScrollBar::handle:horizontal {
                background-color: #374151;
                border-radius: 5px;
                min-width: 30px;
            }

            QScrollBar::handle:horizontal:hover {
                background-color: #4b5563;
            }

            QScrollBar::add-line:horizontal,
            QScrollBar::sub-line:horizontal {
                width: 0px;
            }
            """
        )

        main_layout = QHBoxLayout(self)

        main_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        main_layout.setSpacing(0)

        # ==============================================================
        # SIDEBAR
        # ==============================================================

        self.sidebar = QFrame()

        self.sidebar.setObjectName(
            "sidebar"
        )

        self.sidebar.setMinimumWidth(230)
        self.sidebar.setMaximumWidth(260)

        sidebar_layout = QVBoxLayout(
            self.sidebar
        )

        sidebar_layout.setContentsMargins(
            15,
            15,
            15,
            15,
        )

        sidebar_layout.setSpacing(6)

        # --------------------------------------------------------------
        # Titolo applicazione
        # --------------------------------------------------------------

        app_title = QLabel(
            "MEDICAL DEVICES"
        )

        app_title.setObjectName(
            "sidebar_title"
        )

        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)

        app_title.setFont(
            title_font
        )

        app_title.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        sidebar_layout.addWidget(
            app_title
        )

        subtitle = QLabel(
            "Management System"
        )

        subtitle.setObjectName(
            "sidebar_subtitle"
        )

        subtitle.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        sidebar_layout.addWidget(
            subtitle
        )

        sidebar_layout.addSpacing(
            10
        )

        # ==============================================================
        # NAVIGAZIONE
        # ==============================================================

        self.navigation_list = QListWidget()

        self.navigation_list.setObjectName(
            "navigation_list"
        )

        self.navigation_list.setSpacing(
            2
        )

        self.navigation_list.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        self.navigation_list.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        navigation_items = [
            ("Dashboard", 0),
            ("Dispositivi", 1),
            ("Manutenzioni", 2),
            ("Calibrazioni", 3),
            ("Reparti", 4),
            ("Fornitori", 5),
            ("Utenti", 6),
            ("Audit Log", 7),
        ]

        for label, index in navigation_items:
            item = QListWidgetItem(
                label
            )

            item.setData(
                Qt.ItemDataRole.UserRole,
                index,
            )

            self.navigation_list.addItem(
                item
            )

        sidebar_layout.addWidget(
            self.navigation_list
        )

        sidebar_layout.addStretch()

        # ==============================================================
        # UTENTE
        # ==============================================================

        user_frame = QFrame()

        user_frame.setObjectName(
            "user_frame"
        )

        user_layout = QVBoxLayout(
            user_frame
        )

        user_layout.setContentsMargins(
            8,
            8,
            8,
            8,
        )

        user_layout.setSpacing(
            3
        )

        self.username_label = QLabel(
            ""
        )

        self.username_label.setObjectName(
            "username_label"
        )

        username_font = QFont()
        username_font.setBold(True)

        self.username_label.setFont(
            username_font
        )

        self.username_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        user_layout.addWidget(
            self.username_label
        )

        self.role_label = QLabel(
            ""
        )

        self.role_label.setObjectName(
            "role_label"
        )

        self.role_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        user_layout.addWidget(
            self.role_label
        )

        sidebar_layout.addWidget(
            user_frame
        )

        # --------------------------------------------------------------
        # Logout
        # --------------------------------------------------------------

        self.logout_button = QPushButton(
            "Esci"
        )

        self.logout_button.setObjectName(
            "logout_button"
        )

        self.logout_button.clicked.connect(
            self._logout
        )

        sidebar_layout.addWidget(
            self.logout_button
        )

        main_layout.addWidget(
            self.sidebar
        )

        # ==============================================================
        # AREA PRINCIPALE
        # ==============================================================

        content_frame = QFrame()

        content_frame.setObjectName(
            "content_frame"
        )

        content_layout = QVBoxLayout(
            content_frame
        )

        content_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        content_layout.setSpacing(
            0
        )

        # ==============================================================
        # HEADER
        # ==============================================================

        self.header = QFrame()

        self.header.setObjectName(
            "header"
        )

        header_layout = QHBoxLayout(
            self.header
        )

        header_layout.setContentsMargins(
            25,
            15,
            25,
            15,
        )

        self.page_title = QLabel(
            "Dashboard"
        )

        self.page_title.setObjectName(
            "page_title"
        )

        header_font = QFont()
        header_font.setPointSize(18)
        header_font.setBold(True)

        self.page_title.setFont(
            header_font
        )

        header_layout.addWidget(
            self.page_title
        )

        header_layout.addStretch()

        content_layout.addWidget(
            self.header
        )

        # ==============================================================
        # STACK DELLE PAGINE
        # ==============================================================

        self.pages_stack = QStackedWidget()

        self.pages_stack.setObjectName(
            "pages_stack"
        )

        self.pages_stack.setAutoFillBackground(
            True
        )

        content_layout.addWidget(
            self.pages_stack
        )

        main_layout.addWidget(
            content_frame
        )

    # ------------------------------------------------------------------
    # Pagine
    # ------------------------------------------------------------------

    def _create_pages(self) -> None:
        """
        Crea tutte le pagine dell'applicazione.
        """

        # ==============================================================
        # 0 - DASHBOARD
        # ==============================================================

        dashboard_page = (
            self._create_dashboard_page()
        )

        self.pages_stack.addWidget(
            dashboard_page
        )

        # ==============================================================
        # 1 - DISPOSITIVI
        # ==============================================================

        self.devices_page = MedicalDevicesPage(
            user_session=self.user_session,
            parent=self,
        )

        self.pages_stack.addWidget(
            self.devices_page
        )

        # ==============================================================
        # 2 - MANUTENZIONI
        # ==============================================================

        self.maintenance_page = (
            MedicalMaintenancePage(
                user_session=self.user_session,
                parent=self,
            )
        )

        self.pages_stack.addWidget(
            self.maintenance_page
        )

        # ==============================================================
        # 3 - CALIBRAZIONI
        # ==============================================================

        self.calibration_page = (
            MedicalCalibrationPage(
                user_session=self.user_session,
                parent=self,
            )
        )

        self.pages_stack.addWidget(
            self.calibration_page
        )

        # ==============================================================
        # 4 - REPARTI
        # ==============================================================

        self.departments_page = (
            self._create_departments_page()
        )

        self.pages_stack.addWidget(
            self.departments_page
        )

        # ==============================================================
        # 5 - FORNITORI
        # ==============================================================

        self.suppliers_page = (
            self._create_suppliers_page()
        )

        self.pages_stack.addWidget(
            self.suppliers_page
        )

        # ==============================================================
        # 6 - UTENTI
        # ==============================================================

        self.users_page = MedicalUsersPage(
            user_session=self.user_session,
            parent=self,
        )

        self.pages_stack.addWidget(
            self.users_page
        )

        # ==============================================================
        # 7 - AUDIT LOG
        # ==============================================================

        self.audit_page = MedicalAuditPage(
            user_session=self.user_session,
            parent=self,
        )

        self.pages_stack.addWidget(
            self.audit_page
        )

    # ------------------------------------------------------------------
    # Dashboard principale
    # ------------------------------------------------------------------

    def _create_dashboard_page(self) -> QWidget:
        page = QWidget()

        page.setObjectName(
            "dashboard_page"
        )

        layout = QVBoxLayout(
            page
        )

        layout.setContentsMargins(
            30,
            30,
            30,
            30,
        )

        layout.setSpacing(
            20
        )

        # --------------------------------------------------------------
        # Titolo
        # --------------------------------------------------------------

        title = QLabel(
            "Benvenuto nel Medical Devices Management System"
        )

        title.setObjectName(
            "dashboard_title"
        )

        title_font = QFont()
        title_font.setPointSize(22)
        title_font.setBold(True)

        title.setFont(
            title_font
        )

        layout.addWidget(
            title
        )

        self.dashboard_welcome_label = QLabel(
            ""
        )

        self.dashboard_welcome_label.setObjectName(
            "dashboard_welcome"
        )

        layout.addWidget(
            self.dashboard_welcome_label
        )

        # ==============================================================
        # STATISTICHE DISPOSITIVI
        # ==============================================================

        self.statistics_widget = (
            MedicalStatisticsWidget()
        )

        layout.addWidget(
            self.statistics_widget
        )

        # ==============================================================
        # INFORMAZIONI SISTEMA
        # ==============================================================

        info_frame = QFrame()

        info_frame.setObjectName(
            "system_frame"
        )

        info_layout = QVBoxLayout(
            info_frame
        )

        info_layout.setContentsMargins(
            18,
            18,
            18,
            18,
        )

        info_title = QLabel(
            "Sistema"
        )

        info_title.setObjectName(
            "system_title"
        )

        info_font = QFont()
        info_font.setPointSize(14)
        info_font.setBold(True)

        info_title.setFont(
            info_font
        )

        info_layout.addWidget(
            info_title
        )

        self.dashboard_status_label = QLabel(
            "Caricamento informazioni..."
        )

        self.dashboard_status_label.setObjectName(
            "system_status"
        )

        self.dashboard_status_label.setWordWrap(
            True
        )

        info_layout.addWidget(
            self.dashboard_status_label
        )

        layout.addWidget(
            info_frame
        )

        layout.addStretch()

        return page

    # ------------------------------------------------------------------
    # Reparti
    # ------------------------------------------------------------------

    def _create_departments_page(
        self,
    ) -> QWidget:
        return MedicalDepartmentsPage(
            user_session=self.user_session,
            parent=self,
        )

    # ------------------------------------------------------------------
    # Fornitori
    # ------------------------------------------------------------------

    def _create_suppliers_page(
        self,
    ) -> QWidget:
        return MedicalSuppliersPage(
            user_session=self.user_session,
            parent=self,
        )

    # ------------------------------------------------------------------
    # Navigazione
    # ------------------------------------------------------------------

    def _connect_navigation(self) -> None:
        self.navigation_list.currentRowChanged.connect(
            self._show_navigation_page
        )

        self.navigation_list.setCurrentRow(
            0
        )

    def _show_navigation_page(
        self,
        index: int,
    ) -> None:
        if index < 0:
            return

        if index >= self.pages_stack.count():
            return

        self.pages_stack.setCurrentIndex(
            index
        )

        titles = {
            0: "Dashboard",
            1: "Dispositivi",
            2: "Manutenzioni",
            3: "Calibrazioni",
            4: "Reparti",
            5: "Fornitori",
            6: "Utenti",
            7: "Audit Log",
        }

        self.page_title.setText(
            titles.get(
                index,
                "Medical Devices",
            )
        )

        try:
            if index == 0:
                self._load_dashboard_statistics()

            elif index == 1:
                self.devices_page.refresh_page()

            elif index == 2:
                self.maintenance_page.refresh_page()

            elif index == 3:
                self.calibration_page.refresh_page()

            elif index == 4:
                self.departments_page.refresh_page()

            elif index == 5:
                self.suppliers_page.refresh_page()

            elif index == 6:
                self.users_page.refresh_page()

            elif index == 7:
                self.audit_page.refresh_page()

        except MedicalAPIAuthenticationError as exc:
            self._show_api_error(
                "Sessione scaduta",
                exc,
            )

        except MedicalAPIAuthorizationError as exc:
            self._show_api_error(
                "Accesso negato",
                exc,
            )

        except MedicalAPIConnectorError as exc:
            self._show_api_error(
                "Errore API",
                exc,
            )

        except Exception as exc:
            self._show_generic_error(
                "Errore",
                exc,
            )

    # ------------------------------------------------------------------
    # Dashboard statistiche
    # ------------------------------------------------------------------

    def _load_dashboard_statistics(
        self,
    ) -> None:
        """
        Aggiorna il widget delle statistiche.

        Il widget utilizza direttamente l'API per recuperare
        l'elenco aggiornato dei dispositivi.
        """

        try:
            self.statistics_widget.refresh()

            self.dashboard_status_label.setText(
                "Connessione al database attiva. "
                "Statistiche aggiornate correttamente."
            )

        except MedicalAPIAuthenticationError as exc:
            self.dashboard_status_label.setText(
                "Sessione scaduta."
            )

            self._show_api_error(
                "Sessione scaduta",
                exc,
            )

        except MedicalAPIAuthorizationError as exc:
            self.dashboard_status_label.setText(
                "Accesso negato."
            )

            self._show_api_error(
                "Accesso negato",
                exc,
            )

        except MedicalAPIConnectorError as exc:
            self.dashboard_status_label.setText(
                "Errore di comunicazione con il server."
            )

            self._show_api_error(
                "Errore API",
                exc,
            )

        except Exception as exc:
            self.dashboard_status_label.setText(
                "Impossibile caricare le statistiche."
            )

            print(
                "Errore caricamento statistiche "
                f"dashboard: {exc}"
            )

    # ------------------------------------------------------------------
    # Sessione
    # ------------------------------------------------------------------

    def _update_user_information(
        self,
    ) -> None:
        username = (
            self.user_session.username
        )

        role = (
            self.user_session.role
        )

        self.username_label.setText(
            username or "Utente"
        )

        role_names = {
            "admin": "Amministratore",
            "tecnico": "Tecnico",
            "lettore": "Lettore",
        }

        self.role_label.setText(
            role_names.get(
                str(role).lower(),
                str(role or ""),
            )
        )

        self.dashboard_welcome_label.setText(
            f"Accesso effettuato come "
            f"<b>{username or 'Utente'}</b>."
        )

    def show_dashboard(
        self,
    ) -> None:
        """
        Mostra la dashboard massimizzata e aggiorna
        le informazioni relative alla sessione corrente.
        """

        self._update_user_information()

        self.navigation_list.setCurrentRow(
            0
        )

        # Apertura massimizzata.
        # La barra del titolo di Windows rimane visibile,
        # quindi sono disponibili i pulsanti:
        # minimizza, massimizza/ripristina e chiudi.
        self.showMaximized()

        self.raise_()
        self.activateWindow()

    # ------------------------------------------------------------------
    # Logout
    # ------------------------------------------------------------------

    def _logout(self) -> None:
        """
        Effettua il logout con conferma in italiano.
        """

        message_box = QMessageBox(
            QMessageBox.Icon.Question,
            "Conferma logout",
            "Vuoi uscire dall'applicazione?",
            parent=self,
        )

        yes_button = message_box.addButton(
            "Sì",
            QMessageBox.ButtonRole.YesRole,
        )

        no_button = message_box.addButton(
            "No",
            QMessageBox.ButtonRole.NoRole,
        )

        message_box.setDefaultButton(
            no_button
        )

        message_box.exec()

        if message_box.clickedButton() != yes_button:
            return

        self.user_session.logout()

        self.hide()

        self.logout_requested.emit()

    # ------------------------------------------------------------------
    # Error handling
    # ------------------------------------------------------------------

    @staticmethod
    def _exception_message(
        exc: Exception,
    ) -> str:
        message = str(
            exc
        ).strip()

        if message:
            return message

        return (
            "Si è verificato un errore "
            "durante l'operazione."
        )

    def _show_api_error(
        self,
        title: str,
        exc: Exception,
    ) -> None:
        QMessageBox.warning(
            self,
            title,
            self._exception_message(
                exc
            ),
        )

    def _show_generic_error(
        self,
        title: str,
        exc: Exception,
    ) -> None:
        QMessageBox.critical(
            self,
            title,
            (
                f"{self._exception_message(exc)}\n\n"
                "Controlla il terminale per ulteriori dettagli."
            ),
        )

    # ------------------------------------------------------------------
    # Close
    # ------------------------------------------------------------------

    def closeEvent(
        self,
        event,
    ) -> None:
        """
        Gestisce la chiusura dell'applicazione.

        La finestra di conferma utilizza esplicitamente
        i pulsanti italiani "Sì" e "No".
        """

        if self.user_session.is_authenticated:

            message_box = QMessageBox(
                QMessageBox.Icon.Question,
                "Conferma uscita",
                "Sei sicuro di voler chiudere il programma?",
                parent=self,
            )

            yes_button = message_box.addButton(
                "Sì",
                QMessageBox.ButtonRole.YesRole,
            )

            no_button = message_box.addButton(
                "No",
                QMessageBox.ButtonRole.NoRole,
            )

            message_box.setDefaultButton(
                no_button
            )

            message_box.exec()

            if message_box.clickedButton() != yes_button:
                event.ignore()
                return

            self.user_session.logout()

        event.accept()