from __future__ import annotations

from typing import Any, Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from gui.medical_api_connector import (
    MedicalAPIAuthenticationError,
    MedicalAPIAuthorizationError,
    MedicalAPIConnectorError,
    MedicalAPIServerError,
    medical_api_connector,
)
from gui.medical_user_session import medical_user_session


class MedicalAuditDetailsDialog(QDialog):
    """
    Dialog per visualizzare nel dettaglio un record di Audit Log.
    """

    def __init__(
        self,
        audit_log: dict[str, Any],
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)

        self.audit_log = audit_log

        self.setWindowTitle("Dettagli Audit Log")
        self.setModal(True)
        self.setMinimumWidth(600)
        self.setMinimumHeight(400)

        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        title = QLabel("Dettagli operazione")

        font = QFont()
        font.setPointSize(15)
        font.setBold(True)
        title.setFont(font)

        layout.addWidget(title)

        info_layout = QVBoxLayout()
        info_layout.setSpacing(8)

        timestamp = self._get_value(
            "timestamp",
            "data_ora",
            "creato_il",
        )

        username = self._get_value(
            "username",
            "utente",
            "utente_username",
        )

        action = self._get_value(
            "azione",
            "action",
            "operazione",
        )

        table = self._get_value(
            "tabella",
            "table",
            "entita",
        )

        details = self._get_value(
            "dettagli",
            "details",
            "descrizione",
        )

        info_layout.addWidget(
            self._create_info_label(
                "Data/Ora",
                self._format_datetime(timestamp),
            )
        )

        info_layout.addWidget(
            self._create_info_label(
                "Utente",
                str(username) if username else "-",
            )
        )

        info_layout.addWidget(
            self._create_info_label(
                "Operazione",
                str(action) if action else "-",
            )
        )

        info_layout.addWidget(
            self._create_info_label(
                "Tabella",
                str(table) if table else "-",
            )
        )

        info_layout.addWidget(
            self._create_info_label(
                "Dettagli",
                str(details) if details else "-",
            )
        )

        layout.addLayout(info_layout)
        layout.addStretch()

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Close
        )

        buttons.rejected.connect(self.reject)
        buttons.accepted.connect(self.accept)

        layout.addWidget(buttons)

    def _get_value(self, *keys: str) -> Any:
        for key in keys:
            if key in self.audit_log:
                return self.audit_log.get(key)

        return None

    @staticmethod
    def _create_info_label(
        label: str,
        value: str,
    ) -> QLabel:
        widget = QLabel(
            f"<b>{label}:</b> {value}"
        )

        widget.setWordWrap(True)
        widget.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )

        return widget

    @staticmethod
    def _format_datetime(value: Any) -> str:
        if not value:
            return "-"

        value = str(value)

        if "T" in value:
            value = value.replace("T", " ")

        if value.endswith("Z"):
            value = value[:-1]

        if "." in value:
            value = value.split(".", 1)[0]

        return value


class MedicalAuditPage(QWidget):
    """
    Pagina di consultazione dell'Audit Log.

    La pagina è pensata principalmente per l'ADMIN e utilizza
    il permesso can_view_audit_logs() della sessione utente.
    """

    def __init__(
        self,
        user_session=medical_user_session,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)

        self.user_session = user_session
        self.api = medical_api_connector

        self.audit_logs: list[dict[str, Any]] = []
        self.filtered_logs: list[dict[str, Any]] = []

        self._build_ui()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        main_layout = QVBoxLayout(self)

        main_layout.setContentsMargins(
            20,
            20,
            20,
            20,
        )

        main_layout.setSpacing(15)

        title = QLabel("Audit Log")

        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)

        title.setFont(title_font)

        main_layout.addWidget(title)

        subtitle = QLabel(
            "Registro delle operazioni effettuate "
            "dagli utenti dell'applicazione."
        )

        subtitle.setStyleSheet(
            "color: #666666;"
        )

        main_layout.addWidget(subtitle)

        # --------------------------------------------------------------
        # Toolbar
        # --------------------------------------------------------------

        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)

        self.search_edit = QLineEdit()

        self.search_edit.setPlaceholderText(
            "Cerca nei dettagli..."
        )

        self.search_edit.setClearButtonEnabled(True)

        self.search_edit.textChanged.connect(
            self._apply_filters
        )

        toolbar.addWidget(self.search_edit)

        self.user_filter = QComboBox()

        self.user_filter.addItem(
            "Tutti gli utenti",
            None,
        )

        self.user_filter.currentIndexChanged.connect(
            self._apply_filters
        )

        toolbar.addWidget(self.user_filter)

        self.action_filter = QComboBox()

        self.action_filter.addItem(
            "Tutte le operazioni",
            None,
        )

        self.action_filter.currentIndexChanged.connect(
            self._apply_filters
        )

        toolbar.addWidget(self.action_filter)

        self.table_filter = QComboBox()

        self.table_filter.addItem(
            "Tutte le tabelle",
            None,
        )

        self.table_filter.currentIndexChanged.connect(
            self._apply_filters
        )

        toolbar.addWidget(self.table_filter)

        self.refresh_button = QPushButton(
            "Aggiorna"
        )

        self.refresh_button.clicked.connect(
            self.load_audit_logs
        )

        toolbar.addWidget(
            self.refresh_button
        )

        toolbar.addStretch()

        main_layout.addLayout(toolbar)

        # --------------------------------------------------------------
        # Tabella
        # --------------------------------------------------------------

        self.table = QTableWidget()

        self.table.setColumnCount(6)

        self.table.setHorizontalHeaderLabels(
            [
                "ID",
                "Data/Ora",
                "Utente",
                "Operazione",
                "Tabella",
                "Dettagli",
            ]
        )

        self.table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )

        self.table.setSelectionMode(
            QTableWidget.SelectionMode.SingleSelection
        )

        self.table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )

        self.table.setAlternatingRowColors(
            True
        )

        self.table.cellDoubleClicked.connect(
            self._show_selected_details
        )

        main_layout.addWidget(
            self.table
        )

        # --------------------------------------------------------------
        # Bottom actions
        # --------------------------------------------------------------

        bottom_layout = QHBoxLayout()

        self.details_button = QPushButton(
            "Visualizza dettagli"
        )

        self.details_button.clicked.connect(
            self.show_details
        )

        bottom_layout.addWidget(
            self.details_button
        )

        bottom_layout.addStretch()

        self.status_label = QLabel(
            ""
        )

        bottom_layout.addWidget(
            self.status_label
        )

        main_layout.addLayout(
            bottom_layout
        )

        self._apply_permissions()

    # ------------------------------------------------------------------
    # Permissions
    # ------------------------------------------------------------------

    def _apply_permissions(self) -> None:
        can_view = (
            self.user_session.can_view_audit_logs()
        )

        self.setEnabled(can_view)

        if not can_view:
            self.status_label.setText(
                "Accesso non autorizzato"
            )

    # ------------------------------------------------------------------
    # Loading
    # ------------------------------------------------------------------

    def load_audit_logs(self) -> None:
        if not self.user_session.can_view_audit_logs():
            QMessageBox.warning(
                self,
                "Accesso negato",
                (
                    "Non disponi dei permessi necessari "
                    "per visualizzare l'Audit Log."
                ),
            )

            return

        try:
            self.status_label.setText(
                "Caricamento audit log..."
            )

            logs = self.api.get_audit_logs()

            if logs is None:
                logs = []

            self.audit_logs = list(logs)

            self._populate_filter_values()
            self._apply_filters()

            self.status_label.setText(
                f"{len(self.filtered_logs)} record visualizzati"
            )

        except MedicalAPIAuthenticationError as exc:
            self._show_api_error(
                "Autenticazione",
                exc,
            )

        except MedicalAPIAuthorizationError as exc:
            self._show_api_error(
                "Accesso negato",
                exc,
            )

        except MedicalAPIServerError as exc:
            self._show_api_error(
                "Errore server",
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
    # Filters
    # ------------------------------------------------------------------

    def _populate_filter_values(self) -> None:
        current_user = (
            self.user_filter.currentData()
        )

        current_action = (
            self.action_filter.currentData()
        )

        current_table = (
            self.table_filter.currentData()
        )

        users: set[str] = set()
        actions: set[str] = set()
        tables: set[str] = set()

        for log in self.audit_logs:
            username = self._get_username(log)
            action = self._get_action(log)
            table = self._get_table(log)

            if username:
                users.add(username)

            if action:
                actions.add(action)

            if table:
                tables.add(table)

        self.user_filter.blockSignals(True)
        self.user_filter.clear()

        self.user_filter.addItem(
            "Tutti gli utenti",
            None,
        )

        for username in sorted(users):
            self.user_filter.addItem(
                username,
                username,
            )

        index = self.user_filter.findData(
            current_user
        )

        if index >= 0:
            self.user_filter.setCurrentIndex(
                index
            )

        self.user_filter.blockSignals(False)

        self.action_filter.blockSignals(True)
        self.action_filter.clear()

        self.action_filter.addItem(
            "Tutte le operazioni",
            None,
        )

        for action in sorted(actions):
            self.action_filter.addItem(
                action,
                action,
            )

        index = self.action_filter.findData(
            current_action
        )

        if index >= 0:
            self.action_filter.setCurrentIndex(
                index
            )

        self.action_filter.blockSignals(False)

        self.table_filter.blockSignals(True)
        self.table_filter.clear()

        self.table_filter.addItem(
            "Tutte le tabelle",
            None,
        )

        for table in sorted(tables):
            self.table_filter.addItem(
                table,
                table,
            )

        index = self.table_filter.findData(
            current_table
        )

        if index >= 0:
            self.table_filter.setCurrentIndex(
                index
            )

        self.table_filter.blockSignals(False)

    def _apply_filters(self) -> None:
        search_text = (
            self.search_edit.text()
            .strip()
            .lower()
        )

        selected_user = (
            self.user_filter.currentData()
        )

        selected_action = (
            self.action_filter.currentData()
        )

        selected_table = (
            self.table_filter.currentData()
        )

        filtered: list[dict[str, Any]] = []

        for log in self.audit_logs:
            username = self._get_username(log)
            action = self._get_action(log)
            table = self._get_table(log)
            details = self._get_details(log)

            if selected_user:
                if username != selected_user:
                    continue

            if selected_action:
                if action != selected_action:
                    continue

            if selected_table:
                if table != selected_table:
                    continue

            if search_text:
                searchable = " ".join(
                    [
                        username,
                        action,
                        table,
                        details,
                    ]
                ).lower()

                if search_text not in searchable:
                    continue

            filtered.append(log)

        # Dal più recente al meno recente.
        filtered.sort(
            key=lambda item: str(
                item.get(
                    "timestamp",
                    item.get(
                        "data_ora",
                        "",
                    ),
                )
            ),
            reverse=True,
        )

        self.filtered_logs = filtered

        self._populate_table()

        self.status_label.setText(
            f"{len(self.filtered_logs)} record visualizzati"
        )

    # ------------------------------------------------------------------
    # Table
    # ------------------------------------------------------------------

    def _populate_table(self) -> None:
        self.table.setRowCount(0)

        for row, log in enumerate(
            self.filtered_logs
        ):
            self.table.insertRow(row)

            audit_id = log.get(
                "id",
                "",
            )

            timestamp = self._get_timestamp(
                log
            )

            username = self._get_username(
                log
            )

            action = self._get_action(
                log
            )

            table = self._get_table(
                log
            )

            details = self._get_details(
                log
            )

            values = [
                str(audit_id),
                self._format_datetime(
                    timestamp
                ),
                username or "-",
                action or "-",
                table or "-",
                details or "-",
            ]

            for column, value in enumerate(
                values
            ):
                item = QTableWidgetItem(
                    value
                )

                item.setToolTip(
                    value
                )

                if column == 0:
                    item.setTextAlignment(
                        Qt.AlignmentFlag.AlignCenter
                    )

                self.table.setItem(
                    row,
                    column,
                    item,
                )

        self.table.resizeColumnsToContents()

        self.table.setColumnWidth(
            0,
            70,
        )

        self.table.setColumnWidth(
            1,
            160,
        )

        self.table.setColumnWidth(
            2,
            130,
        )

        self.table.setColumnWidth(
            3,
            130,
        )

        self.table.setColumnWidth(
            4,
            150,
        )

        self.table.horizontalHeader().setStretchLastSection(
            True
        )

    # ------------------------------------------------------------------
    # Details
    # ------------------------------------------------------------------

    def _get_selected_log(
        self,
    ) -> Optional[dict[str, Any]]:
        selected_rows = (
            self.table.selectionModel()
            .selectedRows()
        )

        if not selected_rows:
            return None

        row = selected_rows[0].row()

        if (
            row < 0
            or row >= len(self.filtered_logs)
        ):
            return None

        return self.filtered_logs[row]

    def show_details(self) -> None:
        log = self._get_selected_log()

        if log is None:
            QMessageBox.information(
                self,
                "Selezione richiesta",
                "Seleziona un record dell'Audit Log.",
            )

            return

        dialog = MedicalAuditDetailsDialog(
            log,
            self,
        )

        dialog.exec()

    def _show_selected_details(
        self,
        row: int,
        column: int,
    ) -> None:
        if (
            row < 0
            or row >= len(self.filtered_logs)
        ):
            return

        log = self.filtered_logs[row]

        dialog = MedicalAuditDetailsDialog(
            log,
            self,
        )

        dialog.exec()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _get_username(
        log: dict[str, Any],
    ) -> str:
        for key in (
            "username",
            "utente_username",
        ):
            value = log.get(key)

            if value:
                return str(value)

        user = log.get("utente")

        if isinstance(user, dict):
            username = user.get("username")

            if username:
                return str(username)

        if user is not None:
            return str(user)

        return ""

    @staticmethod
    def _get_action(
        log: dict[str, Any],
    ) -> str:
        for key in (
            "azione",
            "action",
            "operazione",
        ):
            value = log.get(key)

            if value:
                return str(value)

        return ""

    @staticmethod
    def _get_table(
        log: dict[str, Any],
    ) -> str:
        for key in (
            "tabella",
            "table",
            "entita",
        ):
            value = log.get(key)

            if value:
                return str(value)

        return ""

    @staticmethod
    def _get_details(
        log: dict[str, Any],
    ) -> str:
        for key in (
            "dettagli",
            "details",
            "descrizione",
        ):
            value = log.get(key)

            if value is not None:
                return str(value)

        return ""

    @staticmethod
    def _get_timestamp(
        log: dict[str, Any],
    ) -> Any:
        for key in (
            "timestamp",
            "data_ora",
            "creato_il",
        ):
            value = log.get(key)

            if value:
                return value

        return None

    @staticmethod
    def _format_datetime(
        value: Any,
    ) -> str:
        if not value:
            return "-"

        value = str(value)

        if "T" in value:
            value = value.replace(
                "T",
                " ",
            )

        if value.endswith("Z"):
            value = value[:-1]

        if "." in value:
            value = value.split(
                ".",
                1,
            )[0]

        return value

    # ------------------------------------------------------------------
    # Events
    # ------------------------------------------------------------------

    def refresh_page(self) -> None:
        self.load_audit_logs()

    def showEvent(self, event) -> None:
        super().showEvent(event)

        if not self.audit_logs:
            self.load_audit_logs()

    # ------------------------------------------------------------------
    # Error handling
    # ------------------------------------------------------------------

    @staticmethod
    def _exception_message(
        exc: Exception,
    ) -> str:
        message = str(exc).strip()

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
            self._exception_message(exc),
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