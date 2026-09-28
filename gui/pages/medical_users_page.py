from __future__ import annotations

from typing import Any, Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
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
    MedicalAPIConflictError,
    MedicalAPIConnectorError,
    MedicalAPINotFoundError,
    MedicalAPIServerError,
    MedicalAPIValidationError,
    medical_api_connector,
)
from gui.medical_user_session import medical_user_session


class MedicalUserDialog(QDialog):
    """
    Dialog per la creazione e modifica di un utente.

    In modalità creazione:
        - username
        - password
        - ruolo
        - stato

    In modalità modifica:
        - username
        - ruolo
        - stato
        - cambio password separato
    """

    def __init__(
        self,
        user: Optional[dict[str, Any]] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)

        self.user = user
        self.is_edit_mode = user is not None

        self.setWindowTitle(
            "Modifica utente" if self.is_edit_mode else "Nuovo utente"
        )
        self.setModal(True)
        self.setMinimumWidth(430)

        self._build_ui()

        if self.user:
            self._load_user_data()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        title = QLabel(
            "Modifica utente" if self.is_edit_mode else "Crea nuovo utente"
        )

        title_font = QFont()
        title_font.setPointSize(15)
        title_font.setBold(True)
        title.setFont(title_font)

        layout.addWidget(title)

        form_group = QGroupBox("Dati account")
        form_layout = QFormLayout()
        form_layout.setSpacing(10)

        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("Inserisci username")
        self.username_edit.setMaxLength(100)

        form_layout.addRow("Username:", self.username_edit)

        self.password_edit = QLineEdit()
        self.password_edit.setPlaceholderText(
            "Minimo 12 caratteri"
        )
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_edit.setMaxLength(255)

        if self.is_edit_mode:
            self.password_edit.setPlaceholderText(
                "Lascia vuoto per non modificare"
            )

        form_layout.addRow(
            "Password:" if not self.is_edit_mode else "Nuova password:",
            self.password_edit,
        )

        self.role_combo = QComboBox()
        self.role_combo.addItem("Amministratore", "admin")
        self.role_combo.addItem("Tecnico", "tecnico")
        self.role_combo.addItem("Lettore", "lettore")

        form_layout.addRow("Ruolo:", self.role_combo)

        self.active_checkbox = QCheckBox("Account attivo")
        self.active_checkbox.setChecked(True)

        form_layout.addRow("Stato:", self.active_checkbox)

        form_group.setLayout(form_layout)
        layout.addWidget(form_group)

        info = QLabel(
            "La password deve contenere almeno 12 caratteri."
        )
        info.setWordWrap(True)
        info.setStyleSheet("color: #666666;")
        layout.addWidget(info)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )

        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        self.buttons = buttons

        layout.addWidget(buttons)

        self.username_edit.setFocus()

    def _load_user_data(self) -> None:
        username = self.user.get("username", "")
        role = self.user.get("ruolo", "lettore")
        active = self.user.get("attivo", True)

        self.username_edit.setText(str(username))

        role = str(role).lower()

        index = self.role_combo.findData(role)

        if index >= 0:
            self.role_combo.setCurrentIndex(index)

        self.active_checkbox.setChecked(bool(active))

    def get_form_data(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "username": self.username_edit.text().strip(),
            "ruolo": self.role_combo.currentData(),
            "attivo": self.active_checkbox.isChecked(),
        }

        password = self.password_edit.text()

        if password:
            data["password"] = password

        return data

    def accept(self) -> None:
        username = self.username_edit.text().strip()
        password = self.password_edit.text()

        if not username:
            QMessageBox.warning(
                self,
                "Dati mancanti",
                "Inserisci lo username.",
            )
            self.username_edit.setFocus()
            return

        if len(username) > 100:
            QMessageBox.warning(
                self,
                "Username non valido",
                "Lo username non può superare 100 caratteri.",
            )
            self.username_edit.setFocus()
            return

        # In creazione la password è obbligatoria.
        if not self.is_edit_mode and not password:
            QMessageBox.warning(
                self,
                "Password mancante",
                "Inserisci una password.",
            )
            self.password_edit.setFocus()
            return

        # Se viene specificata una nuova password, deve avere almeno 12 caratteri.
        if password and len(password) < 12:
            QMessageBox.warning(
                self,
                "Password non valida",
                "La password deve contenere almeno 12 caratteri.",
            )
            self.password_edit.setFocus()
            return

        super().accept()


class MedicalUsersPage(QWidget):
    """
    Pagina desktop per la gestione degli utenti dell'applicazione.

    Le operazioni amministrative sono disponibili esclusivamente
    secondo i permessi definiti in MedicalUserSession.
    """

    def __init__(
        self,
        user_session=medical_user_session,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)

        self.user_session = user_session
        self.api = medical_api_connector

        self.users: list[dict[str, Any]] = []
        self.filtered_users: list[dict[str, Any]] = []

        self._build_ui()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        title = QLabel("Gestione utenti")

        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title.setFont(title_font)

        main_layout.addWidget(title)

        subtitle = QLabel(
            "Gestisci gli account, i ruoli e lo stato degli utenti "
            "dell'applicazione."
        )
        subtitle.setStyleSheet("color: #666666;")

        main_layout.addWidget(subtitle)

        # --------------------------------------------------------------
        # Toolbar
        # --------------------------------------------------------------

        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Cerca username...")
        self.search_edit.setClearButtonEnabled(True)
        self.search_edit.setMinimumWidth(220)

        self.search_edit.textChanged.connect(self._apply_filters)

        toolbar.addWidget(self.search_edit)

        self.role_filter = QComboBox()
        self.role_filter.addItem("Tutti i ruoli", None)
        self.role_filter.addItem("Amministratori", "admin")
        self.role_filter.addItem("Tecnici", "tecnico")
        self.role_filter.addItem("Lettori", "lettore")

        self.role_filter.currentIndexChanged.connect(
            self._apply_filters
        )

        toolbar.addWidget(self.role_filter)

        self.status_filter = QComboBox()
        self.status_filter.addItem("Tutti gli stati", None)
        self.status_filter.addItem("Attivi", True)
        self.status_filter.addItem("Disattivati", False)

        self.status_filter.currentIndexChanged.connect(
            self._apply_filters
        )

        toolbar.addWidget(self.status_filter)

        self.refresh_button = QPushButton("Aggiorna")
        self.refresh_button.clicked.connect(self.load_users)

        toolbar.addWidget(self.refresh_button)

        self.new_button = QPushButton("+ Nuovo utente")
        self.new_button.clicked.connect(self.create_user)

        toolbar.addWidget(self.new_button)

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
                "Username",
                "Ruolo",
                "Stato",
                "Creato il",
                "Azioni",
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
        self.table.setAlternatingRowColors(True)

        self.table.cellDoubleClicked.connect(
            self._table_double_clicked
        )

        main_layout.addWidget(self.table)

        # --------------------------------------------------------------
        # Azioni
        # --------------------------------------------------------------

        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(8)

        self.edit_button = QPushButton("Modifica")
        self.edit_button.clicked.connect(self.edit_user)

        actions_layout.addWidget(self.edit_button)

        self.password_button = QPushButton("Cambia password")
        self.password_button.clicked.connect(
            self.change_password
        )

        actions_layout.addWidget(self.password_button)

        self.status_button = QPushButton("Cambia stato")
        self.status_button.clicked.connect(
            self.toggle_user_status
        )

        actions_layout.addWidget(self.status_button)

        actions_layout.addStretch()

        self.status_label = QLabel("")

        actions_layout.addWidget(self.status_label)

        main_layout.addLayout(actions_layout)

        self._apply_permissions()

    # ------------------------------------------------------------------
    # Permissions
    # ------------------------------------------------------------------

    def _apply_permissions(self) -> None:
        can_create = self.user_session.can_create_users()
        can_edit = self.user_session.can_edit_users()
        can_password = self.user_session.can_change_user_password()
        can_status = self.user_session.can_change_user_status()

        self.new_button.setVisible(can_create)
        self.edit_button.setVisible(can_edit)
        self.password_button.setVisible(can_password)
        self.status_button.setVisible(can_status)

    # ------------------------------------------------------------------
    # Data loading
    # ------------------------------------------------------------------

    def load_users(self) -> None:
        try:
            self.status_label.setText("Caricamento utenti...")

            users = self.api.get_users()

            if users is None:
                users = []

            self.users = list(users)

            self._apply_filters()

            self.status_label.setText(
                f"{len(self.filtered_users)} utenti visualizzati"
            )

        except MedicalAPIAuthenticationError as exc:
            self._show_api_error(
                "Autenticazione",
                exc,
            )

        except MedicalAPIAuthorizationError as exc:
            self._show_api_error(
                "Autorizzazione",
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
    # Filtering
    # ------------------------------------------------------------------

    def _apply_filters(self) -> None:
        search_text = self.search_edit.text().strip().lower()

        selected_role = self.role_filter.currentData()
        selected_status = self.status_filter.currentData()

        filtered: list[dict[str, Any]] = []

        for user in self.users:
            username = str(
                user.get("username", "")
            ).lower()

            role = str(
                user.get("ruolo", "")
            ).lower()

            active = user.get("attivo", True)

            if search_text and search_text not in username:
                continue

            if selected_role is not None:
                if role != str(selected_role).lower():
                    continue

            if selected_status is not None:
                if bool(active) != bool(selected_status):
                    continue

            filtered.append(user)

        self.filtered_users = filtered

        self._populate_table()

        self.status_label.setText(
            f"{len(self.filtered_users)} utenti visualizzati"
        )

    # ------------------------------------------------------------------
    # Table
    # ------------------------------------------------------------------

    def _populate_table(self) -> None:
        self.table.setRowCount(0)

        for row_index, user in enumerate(self.filtered_users):
            self.table.insertRow(row_index)

            user_id = user.get("id", "")
            username = user.get("username", "")
            role = user.get("ruolo", "lettore")
            active = bool(user.get("attivo", True))
            created_at = user.get("creato_il", "")

            values = [
                str(user_id),
                str(username),
                self._format_role(role),
                "Attivo" if active else "Disattivato",
                self._format_datetime(created_at),
            ]

            for column_index, value in enumerate(values):
                item = QTableWidgetItem(value)

                if column_index in (0,):
                    item.setTextAlignment(
                        Qt.AlignmentFlag.AlignCenter
                    )

                self.table.setItem(
                    row_index,
                    column_index,
                    item,
                )

            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)

            actions_layout.setContentsMargins(4, 2, 4, 2)
            actions_layout.setSpacing(5)

            edit_button = QPushButton("Modifica")
            edit_button.clicked.connect(
                lambda checked=False, u=user: self.edit_user(u)
            )

            if self.user_session.can_edit_users():
                actions_layout.addWidget(edit_button)

            password_button = QPushButton("Password")
            password_button.clicked.connect(
                lambda checked=False, u=user: self.change_password(u)
            )

            if self.user_session.can_change_user_password():
                actions_layout.addWidget(password_button)

            status_button = QPushButton(
                "Disattiva" if active else "Attiva"
            )

            status_button.clicked.connect(
                lambda checked=False, u=user: self.toggle_user_status(u)
            )

            if self.user_session.can_change_user_status():
                actions_layout.addWidget(status_button)

            actions_layout.addStretch()

            self.table.setCellWidget(
                row_index,
                5,
                actions_widget,
            )

        self.table.resizeColumnsToContents()

        # La colonna azioni deve avere spazio sufficiente.
        self.table.setColumnWidth(5, 280)

    # ------------------------------------------------------------------
    # Formatting
    # ------------------------------------------------------------------

    @staticmethod
    def _format_role(role: Any) -> str:
        role = str(role).lower()

        mapping = {
            "admin": "Amministratore",
            "tecnico": "Tecnico",
            "lettore": "Lettore",
        }

        return mapping.get(role, str(role))

    @staticmethod
    def _format_datetime(value: Any) -> str:
        if not value:
            return "-"

        value = str(value)

        # Conversione semplice delle date ISO restituite da FastAPI.
        if "T" in value:
            value = value.replace("T", " ")

        if value.endswith("Z"):
            value = value[:-1]

        # Mostriamo solo fino ai secondi.
        if "." in value:
            value = value.split(".", 1)[0]

        return value

    # ------------------------------------------------------------------
    # Selection
    # ------------------------------------------------------------------

    def _get_selected_user(
        self,
    ) -> Optional[dict[str, Any]]:
        selected_rows = self.table.selectionModel().selectedRows()

        if not selected_rows:
            return None

        row = selected_rows[0].row()

        if row < 0 or row >= len(self.filtered_users):
            return None

        return self.filtered_users[row]

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------

    def create_user(self) -> None:
        if not self.user_session.can_create_users():
            QMessageBox.warning(
                self,
                "Operazione non consentita",
                "Non disponi dei permessi necessari per creare utenti.",
            )
            return

        dialog = MedicalUserDialog(parent=self)

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        data = dialog.get_form_data()

        try:
            self.api.create_user(data)

            QMessageBox.information(
                self,
                "Utente creato",
                "L'utente è stato creato correttamente.",
            )

            self.load_users()

        except MedicalAPIConflictError as exc:
            self._show_api_error(
                "Username già esistente",
                exc,
            )

        except MedicalAPIValidationError as exc:
            self._show_api_error(
                "Dati non validi",
                exc,
            )

        except MedicalAPIAuthorizationError as exc:
            self._show_api_error(
                "Operazione non autorizzata",
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
    # Edit
    # ------------------------------------------------------------------

    def edit_user(
        self,
        user: Optional[dict[str, Any]] = None,
    ) -> None:
        if not self.user_session.can_edit_users():
            QMessageBox.warning(
                self,
                "Operazione non consentita",
                "Non disponi dei permessi necessari per modificare utenti.",
            )
            return

        if user is None:
            user = self._get_selected_user()

        if user is None:
            QMessageBox.information(
                self,
                "Selezione richiesta",
                "Seleziona un utente da modificare.",
            )
            return

        dialog = MedicalUserDialog(
            user=user,
            parent=self,
        )

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        data = dialog.get_form_data()

        # La password viene gestita separatamente dall'endpoint
        # /password.
        password = data.pop("password", None)

        try:
            self.api.update_user(
                int(user["id"]),
                data,
            )

            if password:
                self.api.update_user_password(
                    int(user["id"]),
                    password,
                )

            QMessageBox.information(
                self,
                "Utente modificato",
                "I dati dell'utente sono stati aggiornati.",
            )

            self.load_users()

        except MedicalAPIConflictError as exc:
            self._show_api_error(
                "Username già esistente",
                exc,
            )

        except MedicalAPIValidationError as exc:
            self._show_api_error(
                "Dati non validi",
                exc,
            )

        except MedicalAPIAuthorizationError as exc:
            self._show_api_error(
                "Operazione non autorizzata",
                exc,
            )

        except MedicalAPINotFoundError as exc:
            self._show_api_error(
                "Utente non trovato",
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
    # Password
    # ------------------------------------------------------------------

    def change_password(
        self,
        user: Optional[dict[str, Any]] = None,
    ) -> None:
        if not self.user_session.can_change_user_password():
            QMessageBox.warning(
                self,
                "Operazione non consentita",
                "Non disponi dei permessi necessari per cambiare "
                "la password.",
            )
            return

        if user is None:
            user = self._get_selected_user()

        if user is None:
            QMessageBox.information(
                self,
                "Selezione richiesta",
                "Seleziona un utente.",
            )
            return

        username = str(user.get("username", ""))

        password_dialog = QDialog(self)
        password_dialog.setWindowTitle(
            f"Cambia password - {username}"
        )
        password_dialog.setModal(True)
        password_dialog.setMinimumWidth(400)

        layout = QVBoxLayout(password_dialog)

        form = QFormLayout()

        password_edit = QLineEdit()
        password_edit.setEchoMode(
            QLineEdit.EchoMode.Password
        )
        password_edit.setMaxLength(255)
        password_edit.setPlaceholderText(
            "Minimo 12 caratteri"
        )

        confirm_edit = QLineEdit()
        confirm_edit.setEchoMode(
            QLineEdit.EchoMode.Password
        )
        confirm_edit.setMaxLength(255)

        form.addRow(
            "Nuova password:",
            password_edit,
        )

        form.addRow(
            "Conferma password:",
            confirm_edit,
        )

        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )

        buttons.accepted.connect(
            password_dialog.accept
        )
        buttons.rejected.connect(
            password_dialog.reject
        )

        layout.addWidget(buttons)

        while True:
            result = password_dialog.exec()

            if result != QDialog.DialogCode.Accepted:
                return

            password = password_edit.text()
            confirmation = confirm_edit.text()

            if len(password) < 12:
                QMessageBox.warning(
                    password_dialog,
                    "Password non valida",
                    "La password deve contenere almeno 12 caratteri.",
                )
                password_edit.clear()
                confirm_edit.clear()
                password_edit.setFocus()
                continue

            if password != confirmation:
                QMessageBox.warning(
                    password_dialog,
                    "Password non coincidente",
                    "Le due password non coincidono.",
                )
                confirm_edit.clear()
                confirm_edit.setFocus()
                continue

            break

        try:
            self.api.update_user_password(
                int(user["id"]),
                password,
            )

            QMessageBox.information(
                self,
                "Password aggiornata",
                f"La password di '{username}' è stata aggiornata.",
            )

        except MedicalAPIValidationError as exc:
            self._show_api_error(
                "Password non valida",
                exc,
            )

        except MedicalAPIAuthorizationError as exc:
            self._show_api_error(
                "Operazione non autorizzata",
                exc,
            )

        except MedicalAPINotFoundError as exc:
            self._show_api_error(
                "Utente non trovato",
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
    # Status
    # ------------------------------------------------------------------

    def toggle_user_status(
        self,
        user: Optional[dict[str, Any]] = None,
    ) -> None:
        if not self.user_session.can_change_user_status():
            QMessageBox.warning(
                self,
                "Operazione non consentita",
                "Non disponi dei permessi necessari per modificare "
                "lo stato degli utenti.",
            )
            return

        if user is None:
            user = self._get_selected_user()

        if user is None:
            QMessageBox.information(
                self,
                "Selezione richiesta",
                "Seleziona un utente.",
            )
            return

        user_id = int(user["id"])
        username = str(user.get("username", ""))
        current_status = bool(user.get("attivo", True))
        new_status = not current_status

        new_status_text = (
            "attivare" if new_status else "disattivare"
        )

        answer = QMessageBox.question(
            self,
            "Conferma modifica stato",
            (
                f"Vuoi {new_status_text} l'account "
                f"'{username}'?"
            ),
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if answer != QMessageBox.StandardButton.Yes:
            return

        try:
            self.api.update_user_status(
                user_id,
                new_status,
            )

            QMessageBox.information(
                self,
                "Stato aggiornato",
                (
                    f"L'account '{username}' è stato "
                    f"{'attivato' if new_status else 'disattivato'}."
                ),
            )

            self.load_users()

        except MedicalAPIAuthorizationError as exc:
            self._show_api_error(
                "Operazione non autorizzata",
                exc,
            )

        except MedicalAPINotFoundError as exc:
            self._show_api_error(
                "Utente non trovato",
                exc,
            )

        except MedicalAPIValidationError as exc:
            self._show_api_error(
                "Operazione non valida",
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
    # Events
    # ------------------------------------------------------------------

    def _table_double_clicked(
        self,
        row: int,
        column: int,
    ) -> None:
        if not self.user_session.can_edit_users():
            return

        if row < 0 or row >= len(self.filtered_users):
            return

        user = self.filtered_users[row]

        self.edit_user(user)

    def refresh_page(self) -> None:
        self.load_users()

    def showEvent(self, event) -> None:
        super().showEvent(event)

        if not self.users:
            self.load_users()

    # ------------------------------------------------------------------
    # Error handling
    # ------------------------------------------------------------------

    @staticmethod
    def _get_exception_message(exc: Exception) -> str:
        message = str(exc).strip()

        if message:
            return message

        return "Si è verificato un errore durante l'operazione."

    def _show_api_error(
        self,
        title: str,
        exc: Exception,
    ) -> None:
        QMessageBox.warning(
            self,
            title,
            self._get_exception_message(exc),
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
                f"{self._get_exception_message(exc)}\n\n"
                "Controlla il terminale per ulteriori dettagli."
            ),
        )