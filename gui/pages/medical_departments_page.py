from __future__ import annotations

from typing import Any, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
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
    MedicalAPIValidationError,
    medical_api_connector,
)

from gui.medical_user_session import (
    MedicalUserSession,
    medical_user_session,
)


class MedicalDepartmentDialog(QDialog):
    """
    Dialog per la creazione o modifica di un reparto.
    """

    def __init__(
        self,
        department: Optional[dict[str, Any]] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)

        self.department = department or {}

        if self.department:
            self.setWindowTitle("Modifica reparto")
        else:
            self.setWindowTitle("Nuovo reparto")

        self.setMinimumWidth(450)

        self._build_interface()
        self._load_data()

    # ============================================================
    # INTERFACCIA
    # ============================================================

    def _build_interface(self) -> None:
        main_layout = QVBoxLayout(self)

        main_layout.setContentsMargins(
            20,
            20,
            20,
            20,
        )

        main_layout.setSpacing(15)

        title = QLabel("Dati del reparto")
        title.setObjectName("sectionTitle")

        main_layout.addWidget(title)

        form_layout = QFormLayout()

        # --------------------------------------------------------
        # NOME
        # --------------------------------------------------------

        self.name_edit = QLineEdit()

        self.name_edit.setPlaceholderText(
            "Es. Radiologia"
        )

        self.name_edit.setMaxLength(100)

        form_layout.addRow(
            "Nome reparto:",
            self.name_edit,
        )

        # --------------------------------------------------------
        # PIANO
        # --------------------------------------------------------

        self.floor_edit = QLineEdit()

        self.floor_edit.setPlaceholderText(
            "Es. Piano 2"
        )

        self.floor_edit.setMaxLength(20)

        form_layout.addRow(
            "Piano:",
            self.floor_edit,
        )

        main_layout.addLayout(form_layout)

        # --------------------------------------------------------
        # PULSANTI
        # --------------------------------------------------------

        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )

        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        main_layout.addWidget(self.button_box)

    # ============================================================
    # CARICAMENTO DATI
    # ============================================================

    def _load_data(self) -> None:
        """
        Carica i dati del reparto nel form durante la modifica.
        """

        if not self.department:
            return

        self.name_edit.setText(
            str(
                self.department.get(
                    "nome",
                    "",
                )
            )
        )

        self.floor_edit.setText(
            str(
                self.department.get(
                    "piano",
                    "",
                )
                or ""
            )
        )

    # ============================================================
    # VALIDAZIONE
    # ============================================================

    def accept(self) -> None:
        """
        Valida i dati prima di chiudere il dialog.
        """

        name = (
            self.name_edit
            .text()
            .strip()
        )

        floor = (
            self.floor_edit
            .text()
            .strip()
        )

        if not name:
            QMessageBox.warning(
                self,
                "Dati mancanti",
                "Inserisci il nome del reparto.",
            )

            self.name_edit.setFocus()

            return

        if len(name) > 100:
            QMessageBox.warning(
                self,
                "Dati non validi",
                "Il nome del reparto non può superare "
                "i 100 caratteri.",
            )

            self.name_edit.setFocus()

            return

        if len(floor) > 20:
            QMessageBox.warning(
                self,
                "Dati non validi",
                "Il piano non può superare i 20 caratteri.",
            )

            self.floor_edit.setFocus()

            return

        super().accept()

    # ============================================================
    # DATI FORM
    # ============================================================

    def get_form_data(self) -> dict[str, Any]:
        """
        Restituisce i dati del form nel formato API.
        """

        return {
            "nome": (
                self.name_edit
                .text()
                .strip()
            ),
            "piano": (
                self.floor_edit
                .text()
                .strip()
                or None
            ),
        }


class MedicalDepartmentsPage(QWidget):
    """
    Pagina GUI per la gestione dei reparti.

    Funzionalità:
    - visualizzazione reparti;
    - ricerca;
    - creazione;
    - modifica;
    - eliminazione;
    - gestione permessi;
    - aggiornamento dati.
    """

    def __init__(
        self,
        user_session: Optional[MedicalUserSession] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)

        self.user_session = (
            user_session
            if user_session is not None
            else medical_user_session
        )

        self.api_connector = medical_api_connector

        self.departments: list[dict[str, Any]] = []

        self._build_interface()
        self._configure_permissions()

    # ============================================================
    # INTERFACCIA
    # ============================================================

    def _build_interface(self) -> None:
        main_layout = QVBoxLayout(self)

        main_layout.setContentsMargins(
            30,
            25,
            30,
            25,
        )

        main_layout.setSpacing(15)

        # ========================================================
        # TITOLO
        # ========================================================

        title = QLabel("Reparti")
        title.setObjectName("pageTitle")

        main_layout.addWidget(title)

        subtitle = QLabel(
            "Gestione dei reparti ospedalieri associati "
            "ai dispositivi medici."
        )

        subtitle.setObjectName("pageSubtitle")
        subtitle.setWordWrap(True)

        main_layout.addWidget(subtitle)

        # ========================================================
        # TOOLBAR
        # ========================================================

        toolbar_layout = QHBoxLayout()
        toolbar_layout.setSpacing(10)

        search_label = QLabel("Ricerca:")

        toolbar_layout.addWidget(search_label)

        self.search_edit = QLineEdit()

        self.search_edit.setPlaceholderText(
            "Cerca per nome o piano..."
        )

        self.search_edit.setMinimumWidth(300)

        self.search_edit.textChanged.connect(
            self._apply_filters
        )

        toolbar_layout.addWidget(
            self.search_edit
        )

        toolbar_layout.addStretch()

        # --------------------------------------------------------
        # AGGIORNA
        # --------------------------------------------------------

        self.refresh_button = QPushButton("Aggiorna")

        self.refresh_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        self.refresh_button.clicked.connect(
            self.refresh_page
        )

        toolbar_layout.addWidget(
            self.refresh_button
        )

        # --------------------------------------------------------
        # NUOVO
        # --------------------------------------------------------

        self.new_button = QPushButton("Nuovo reparto")

        self.new_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        self.new_button.clicked.connect(
            self.create_department
        )

        toolbar_layout.addWidget(
            self.new_button
        )

        main_layout.addLayout(
            toolbar_layout
        )

        # ========================================================
        # TABELLA
        # ========================================================

        self.table = QTableWidget()

        self.table.setObjectName("departmentsTable")

        self.table.setColumnCount(3)

        self.table.setHorizontalHeaderLabels(
            [
                "ID",
                "Nome reparto",
                "Piano",
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

        # --------------------------------------------------------
        # IMPORTANTE:
        # disattiviamo l'alternanza delle righe.
        # In questo modo la palette globale non può introdurre
        # colori diversi tra una riga e l'altra.
        # --------------------------------------------------------

        self.table.setAlternatingRowColors(False)

        # --------------------------------------------------------
        # STYLE LOCALE DELLA TABELLA
        # --------------------------------------------------------

        self.table.setStyleSheet(
            """
            QTableWidget#departmentsTable {
                background-color: #1f2937;
                color: #f9fafb;
                border: 1px solid #374151;
                border-radius: 8px;
                gridline-color: #374151;
                selection-background-color: #374151;
                selection-color: #ffffff;
                alternate-background-color: #1f2937;
            }

            QTableWidget#departmentsTable::item {
                background-color: #1f2937;
                color: #f9fafb;
                padding: 8px;
                border: none;
            }

            QTableWidget#departmentsTable::item:selected {
                background-color: #374151;
                color: #ffffff;
            }

            QTableWidget#departmentsTable::item:hover {
                background-color: #293548;
                color: #ffffff;
            }

            QHeaderView::section {
                background-color: #111827;
                color: #d1d5db;
                padding: 8px;
                border: none;
                border-bottom: 1px solid #374151;
                font-weight: 600;
            }

            QTableCornerButton::section {
                background-color: #111827;
                border: none;
            }
            """
        )

        self.table.setSortingEnabled(True)

        self.table.doubleClicked.connect(
            self.edit_department
        )

        header = self.table.horizontalHeader()

        header.setStretchLastSection(True)

        main_layout.addWidget(
            self.table
        )

        # ========================================================
        # PARTE INFERIORE
        # ========================================================

        bottom_layout = QHBoxLayout()

        self.status_label = QLabel(
            "Nessun reparto caricato."
        )

        self.status_label.setObjectName(
            "statusText"
        )

        bottom_layout.addWidget(
            self.status_label
        )

        bottom_layout.addStretch()

        # --------------------------------------------------------
        # MODIFICA
        # --------------------------------------------------------

        self.edit_button = QPushButton("Modifica")

        self.edit_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        self.edit_button.clicked.connect(
            self.edit_department
        )

        bottom_layout.addWidget(
            self.edit_button
        )

        # --------------------------------------------------------
        # ELIMINA
        # --------------------------------------------------------

        self.delete_button = QPushButton("Elimina")

        self.delete_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        self.delete_button.clicked.connect(
            self.delete_department
        )

        bottom_layout.addWidget(
            self.delete_button
        )

        main_layout.addLayout(
            bottom_layout
        )

    # ============================================================
    # PERMESSI
    # ============================================================

    def _configure_permissions(self) -> None:
        """
        Configura i controlli in base al ruolo dell'utente.
        """

        can_create = (
            self.user_session.can_create_departments()
        )

        self.new_button.setVisible(
            can_create
        )

        self.edit_button.setVisible(
            can_create
        )

        self.delete_button.setVisible(
            can_create
        )

    # ============================================================
    # CARICAMENTO
    # ============================================================

    def load_departments(self) -> None:
        """
        Carica i reparti dall'API.
        """

        departments = (
            self.api_connector.get_departments()
        )

        if not isinstance(
            departments,
            list,
        ):
            departments = []

        self.departments = [
            department
            for department in departments
            if isinstance(
                department,
                dict,
            )
        ]

        self._apply_filters()

        self.status_label.setText(
            f"{len(self.departments)} reparto/i caricato/i."
        )

    # ============================================================
    # FILTRI
    # ============================================================

    def _apply_filters(self) -> None:
        """
        Applica la ricerca alla lista dei reparti.
        """

        search_text = (
            self.search_edit
            .text()
            .strip()
            .lower()
        )

        filtered: list[dict[str, Any]] = []

        for department in self.departments:

            name = str(
                department.get(
                    "nome",
                    "",
                )
            )

            floor = str(
                department.get(
                    "piano",
                    "",
                )
                or ""
            )

            if search_text:

                searchable_text = (
                    f"{name} {floor}"
                ).lower()

                if search_text not in searchable_text:
                    continue

            filtered.append(
                department
            )

        self._populate_table(filtered)

    # ============================================================
    # TABELLA
    # ============================================================

    def _populate_table(
        self,
        departments: list[dict[str, Any]],
    ) -> None:
        """
        Popola la tabella dei reparti.
        """

        self.table.setSortingEnabled(False)

        self.table.setRowCount(0)

        for department in departments:

            row = self.table.rowCount()

            self.table.insertRow(row)

            department_id = department.get(
                "id",
                "",
            )

            name = department.get(
                "nome",
                "",
            )

            floor = department.get(
                "piano"
            )

            values = [
                str(department_id),
                str(name or "N/D"),
                str(floor or "N/D"),
            ]

            for column, value in enumerate(values):

                item = QTableWidgetItem(value)

                if column == 0:

                    item.setData(
                        Qt.ItemDataRole.UserRole,
                        department,
                    )

                self.table.setItem(
                    row,
                    column,
                    item,
                )

        self.table.setSortingEnabled(True)

        self.table.resizeColumnsToContents()

    # ============================================================
    # REPARTO SELEZIONATO
    # ============================================================

    def _get_selected_department(
        self,
    ) -> Optional[dict[str, Any]]:
        """
        Restituisce il reparto selezionato nella tabella.
        """

        selected_rows = (
            self.table.selectionModel()
            .selectedRows()
        )

        if not selected_rows:
            return None

        row = selected_rows[0].row()

        item = self.table.item(
            row,
            0,
        )

        if item is None:
            return None

        department = item.data(
            Qt.ItemDataRole.UserRole
        )

        if not isinstance(
            department,
            dict,
        ):
            return None

        return department

    # ============================================================
    # CREAZIONE
    # ============================================================

    def create_department(self) -> None:
        """
        Crea un nuovo reparto.
        """

        if not self.user_session.can_create_departments():

            QMessageBox.warning(
                self,
                "Accesso negato",
                "Non disponi dei permessi necessari "
                "per creare un reparto.",
            )

            return

        dialog = MedicalDepartmentDialog(
            parent=self
        )

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        payload = dialog.get_form_data()

        try:

            self.api_connector.create_department(
                payload
            )

            QMessageBox.information(
                self,
                "Reparti",
                "Reparto creato correttamente.",
            )

            self.load_departments()

        except MedicalAPIAuthenticationError:

            QMessageBox.warning(
                self,
                "Sessione scaduta",
                "La sessione di autenticazione non è più valida.",
            )

        except MedicalAPIAuthorizationError as exc:

            QMessageBox.warning(
                self,
                "Accesso negato",
                str(exc),
            )

        except MedicalAPIConflictError as exc:

            QMessageBox.warning(
                self,
                "Reparto già esistente",
                str(exc),
            )

        except MedicalAPIValidationError as exc:

            QMessageBox.warning(
                self,
                "Dati non validi",
                str(exc),
            )

        except MedicalAPIConnectorError as exc:

            QMessageBox.warning(
                self,
                "Errore",
                str(exc),
            )

        except Exception as exc:

            QMessageBox.warning(
                self,
                "Errore inatteso",
                f"Impossibile creare il reparto:\n{exc}",
            )

    # ============================================================
    # MODIFICA
    # ============================================================

    def edit_department(self) -> None:
        """
        Modifica il reparto selezionato.
        """

        if not self.user_session.can_create_departments():

            QMessageBox.warning(
                self,
                "Accesso negato",
                "Non disponi dei permessi necessari "
                "per modificare un reparto.",
            )

            return

        department = (
            self._get_selected_department()
        )

        if department is None:

            QMessageBox.information(
                self,
                "Reparto",
                "Seleziona prima un reparto.",
            )

            return

        department_id = department.get(
            "id"
        )

        if department_id is None:

            QMessageBox.warning(
                self,
                "Reparto",
                "ID del reparto non valido.",
            )

            return

        dialog = MedicalDepartmentDialog(
            department=department,
            parent=self,
        )

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        payload = dialog.get_form_data()

        try:

            self.api_connector.update_department(
                department_id,
                payload,
            )

            QMessageBox.information(
                self,
                "Reparti",
                "Reparto modificato correttamente.",
            )

            self.load_departments()

        except MedicalAPIAuthenticationError:

            QMessageBox.warning(
                self,
                "Sessione scaduta",
                "La sessione di autenticazione non è più valida.",
            )

        except MedicalAPIAuthorizationError as exc:

            QMessageBox.warning(
                self,
                "Accesso negato",
                str(exc),
            )

        except MedicalAPINotFoundError as exc:

            QMessageBox.warning(
                self,
                "Reparto",
                str(exc),
            )

        except MedicalAPIConflictError as exc:

            QMessageBox.warning(
                self,
                "Reparto già esistente",
                str(exc),
            )

        except MedicalAPIValidationError as exc:

            QMessageBox.warning(
                self,
                "Dati non validi",
                str(exc),
            )

        except MedicalAPIConnectorError as exc:

            QMessageBox.warning(
                self,
                "Errore",
                str(exc),
            )

        except Exception as exc:

            QMessageBox.warning(
                self,
                "Errore inatteso",
                f"Impossibile modificare il reparto:\n{exc}",
            )

    # ============================================================
    # ELIMINAZIONE
    # ============================================================

    def delete_department(self) -> None:
        """
        Elimina il reparto selezionato.
        """

        if not self.user_session.can_create_departments():

            QMessageBox.warning(
                self,
                "Accesso negato",
                "Non disponi dei permessi necessari "
                "per eliminare un reparto.",
            )

            return

        department = (
            self._get_selected_department()
        )

        if department is None:

            QMessageBox.information(
                self,
                "Reparto",
                "Seleziona prima un reparto.",
            )

            return

        department_id = department.get(
            "id"
        )

        department_name = str(
            department.get(
                "nome",
                "reparto",
            )
        )

        if department_id is None:

            QMessageBox.warning(
                self,
                "Reparto",
                "ID del reparto non valido.",
            )

            return

        answer = QMessageBox.question(
            self,
            "Conferma eliminazione",
            (
                f"Sei sicuro di voler eliminare il reparto "
                f"'{department_name}'?"
            ),
            (
                QMessageBox.StandardButton.Yes
                | QMessageBox.StandardButton.No
            ),
            QMessageBox.StandardButton.No,
        )

        if answer != QMessageBox.StandardButton.Yes:
            return

        try:

            self.api_connector.delete_department(
                department_id
            )

            QMessageBox.information(
                self,
                "Reparti",
                "Reparto eliminato correttamente.",
            )

            self.load_departments()

        except MedicalAPIAuthenticationError:

            QMessageBox.warning(
                self,
                "Sessione scaduta",
                "La sessione di autenticazione non è più valida.",
            )

        except MedicalAPIAuthorizationError as exc:

            QMessageBox.warning(
                self,
                "Accesso negato",
                str(exc),
            )

        except MedicalAPINotFoundError as exc:

            QMessageBox.warning(
                self,
                "Reparto",
                str(exc),
            )

        except MedicalAPIConflictError as exc:

            QMessageBox.warning(
                self,
                "Impossibile eliminare",
                str(exc),
            )

        except MedicalAPIConnectorError as exc:

            QMessageBox.warning(
                self,
                "Errore",
                str(exc),
            )

        except Exception as exc:

            QMessageBox.warning(
                self,
                "Errore inatteso",
                f"Impossibile eliminare il reparto:\n{exc}",
            )

    # ============================================================
    # REFRESH
    # ============================================================

    def refresh_page(self) -> None:
        """
        Aggiorna completamente la pagina.
        """

        try:

            self.load_departments()

        except MedicalAPIAuthenticationError:

            QMessageBox.warning(
                self,
                "Sessione scaduta",
                "La sessione di autenticazione non è più valida.",
            )

        except MedicalAPIAuthorizationError as exc:

            QMessageBox.warning(
                self,
                "Accesso negato",
                str(exc),
            )

        except MedicalAPIConnectorError as exc:

            QMessageBox.warning(
                self,
                "Errore di comunicazione",
                str(exc),
            )

        except Exception as exc:

            QMessageBox.warning(
                self,
                "Reparti",
                f"Impossibile aggiornare la pagina:\n{exc}",
            )

    # ============================================================
    # SHOW EVENT
    # ============================================================

    def showEvent(
        self,
        event,
    ) -> None:
        """
        Carica i dati quando la pagina viene visualizzata.
        """

        super().showEvent(event)

        if not self.departments:

            try:
                self.refresh_page()

            except Exception:
                pass