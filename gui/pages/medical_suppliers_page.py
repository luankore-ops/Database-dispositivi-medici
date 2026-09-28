"""
Pagina GUI per la gestione dei fornitori.

Funzionalità:
- visualizzazione elenco fornitori
- ricerca
- creazione
- modifica
- eliminazione
- gestione errori API
- controllo permessi RBAC
"""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
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
    MedicalAPIConnectorError,
    MedicalAPIConflictError,
    MedicalAPINotFoundError,
    MedicalAPIValidationError,
    MedicalAPIAuthorizationError,
)
from gui.medical_user_session import medical_user_session


class MedicalSupplierDialog(QDialog):
    """
    Dialog per creazione/modifica di un fornitore.
    """

    def __init__(
        self,
        parent: QWidget | None = None,
        supplier: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(parent)

        self.supplier = supplier
        self.is_edit_mode = supplier is not None

        self.setWindowTitle(
            "Modifica fornitore" if self.is_edit_mode else "Nuovo fornitore"
        )
        self.setModal(True)
        self.resize(500, 260)

        self._build_ui()

        if self.is_edit_mode and self.supplier:
            self._load_supplier_data()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        title = QLabel(
            "Modifica fornitore"
            if self.is_edit_mode
            else "Inserimento nuovo fornitore"
        )

        title.setStyleSheet(
            """
            QLabel {
                font-size: 18px;
                font-weight: bold;
                padding: 8px 0;
            }
            """
        )

        layout.addWidget(title)

        form_layout = QFormLayout()
        form_layout.setSpacing(12)

        self.nome_input = QLineEdit()
        self.nome_input.setMaxLength(150)
        self.nome_input.setPlaceholderText("Es. Siemens Healthineers")

        self.email_input = QLineEdit()
        self.email_input.setMaxLength(150)
        self.email_input.setPlaceholderText("Es. assistenza@azienda.it")

        self.telefono_input = QLineEdit()
        self.telefono_input.setMaxLength(30)
        self.telefono_input.setPlaceholderText("Es. +39 071 123456")

        form_layout.addRow("Ragione sociale *:", self.nome_input)
        form_layout.addRow("Email di contatto:", self.email_input)
        form_layout.addRow("Telefono:", self.telefono_input)

        layout.addLayout(form_layout)

        info = QLabel("* Campo obbligatorio")
        info.setStyleSheet("color: #777;")
        layout.addWidget(info)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )

        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout.addWidget(buttons)

        self.nome_input.setFocus()

    def _load_supplier_data(self) -> None:
        if not self.supplier:
            return

        self.nome_input.setText(
            str(self.supplier.get("ragione_sociale") or "")
        )

        self.email_input.setText(
            str(self.supplier.get("email_contatto") or "")
        )

        self.telefono_input.setText(
            str(self.supplier.get("telefono") or "")
        )

    def get_form_data(self) -> dict[str, Any]:
        """
        Restituisce i dati compilati nel formato previsto dall'API.
        """

        ragione_sociale = self.nome_input.text().strip()
        email = self.email_input.text().strip()
        telefono = self.telefono_input.text().strip()

        return {
            "ragione_sociale": ragione_sociale,
            "email_contatto": email or None,
            "telefono": telefono or None,
        }

    def accept(self) -> None:
        """
        Valida il form prima di chiudere il dialog.
        """

        ragione_sociale = self.nome_input.text().strip()
        email = self.email_input.text().strip()
        telefono = self.telefono_input.text().strip()

        if not ragione_sociale:
            QMessageBox.warning(
                self,
                "Dati mancanti",
                "La ragione sociale è obbligatoria.",
            )
            self.nome_input.setFocus()
            return

        if len(ragione_sociale) > 150:
            QMessageBox.warning(
                self,
                "Dati non validi",
                "La ragione sociale non può superare 150 caratteri.",
            )
            self.nome_input.setFocus()
            return

        if len(email) > 150:
            QMessageBox.warning(
                self,
                "Dati non validi",
                "L'email non può superare 150 caratteri.",
            )
            self.email_input.setFocus()
            return

        if len(telefono) > 30:
            QMessageBox.warning(
                self,
                "Dati non validi",
                "Il telefono non può superare 30 caratteri.",
            )
            self.telefono_input.setFocus()
            return

        super().accept()


class MedicalSuppliersPage(QWidget):
    """
    Pagina principale per la gestione dei fornitori.
    """

    def __init__(
        self,
        user_session=medical_user_session,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self.user_session = user_session

        from gui.medical_api_connector import medical_api_connector

        self.api_connector = medical_api_connector

        self.suppliers: list[dict[str, Any]] = []

        self._build_ui()
        self._configure_permissions()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        title = QLabel("Gestione Fornitori")
        title.setStyleSheet(
            """
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #f9fafb;
            }
            """
        )

        subtitle = QLabel(
            "Gestisci i fornitori associati ai dispositivi medici."
        )
        subtitle.setStyleSheet(
            """
            QLabel {
                color: #9ca3af;
                font-size: 13px;
            }
            """
        )

        main_layout.addWidget(title)
        main_layout.addWidget(subtitle)

        # --------------------------------------------------------------
        # Toolbar
        # --------------------------------------------------------------

        toolbar = QHBoxLayout()
        toolbar.setSpacing(10)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(
            "Cerca per ragione sociale, email o telefono..."
        )
        self.search_input.setClearButtonEnabled(True)

        self.search_input.textChanged.connect(self._apply_filters)

        toolbar.addWidget(self.search_input, 1)

        self.refresh_button = QPushButton("↻ Aggiorna")
        self.refresh_button.clicked.connect(self.load_suppliers)

        toolbar.addWidget(self.refresh_button)

        self.new_button = QPushButton("+ Nuovo fornitore")
        self.new_button.clicked.connect(self.create_supplier)

        toolbar.addWidget(self.new_button)

        main_layout.addLayout(toolbar)

        # --------------------------------------------------------------
        # Table
        # --------------------------------------------------------------

        self.table = QTableWidget()
        self.table.setObjectName("suppliersTable")

        self.table.setColumnCount(5)

        self.table.setHorizontalHeaderLabels(
            [
                "ID",
                "Ragione sociale",
                "Email",
                "Telefono",
                "Azioni",
            ]
        )

        self.table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )

        self.table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )

        self.table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )

        # --------------------------------------------------------------
        # IMPORTANTE:
        # disattiviamo l'alternanza della palette globale.
        # Tutte le righe avranno lo stesso colore.
        # --------------------------------------------------------------

        self.table.setAlternatingRowColors(False)

        self.table.setStyleSheet(
            """
            QTableWidget#suppliersTable {
                background-color: #1f2937;
                color: #f9fafb;
                border: 1px solid #374151;
                border-radius: 8px;
                gridline-color: #374151;
                selection-background-color: #374151;
                selection-color: #ffffff;
                alternate-background-color: #1f2937;
            }

            QTableWidget#suppliersTable::item {
                background-color: #1f2937;
                color: #f9fafb;
                padding: 8px;
                border: none;
            }

            QTableWidget#suppliersTable::item:selected {
                background-color: #374151;
                color: #ffffff;
            }

            QTableWidget#suppliersTable::item:hover {
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

        self.table.horizontalHeader().setStretchLastSection(True)

        self.table.doubleClicked.connect(self._table_double_clicked)

        main_layout.addWidget(self.table, 1)

        # --------------------------------------------------------------
        # Bottom area
        # --------------------------------------------------------------

        bottom_layout = QHBoxLayout()

        self.status_label = QLabel("Nessun fornitore caricato.")
        self.status_label.setStyleSheet(
            "color: #9ca3af;"
        )

        bottom_layout.addWidget(self.status_label)

        bottom_layout.addStretch()

        self.edit_button = QPushButton("✎ Modifica")
        self.edit_button.clicked.connect(self.edit_supplier)

        bottom_layout.addWidget(self.edit_button)

        self.delete_button = QPushButton("🗑 Elimina")
        self.delete_button.clicked.connect(self.delete_supplier)

        bottom_layout.addWidget(self.delete_button)

        main_layout.addLayout(bottom_layout)

    # ------------------------------------------------------------------
    # Permissions
    # ------------------------------------------------------------------

    def _configure_permissions(self) -> None:
        can_write = self.user_session.can_create_suppliers()

        self.new_button.setVisible(can_write)
        self.edit_button.setVisible(can_write)
        self.delete_button.setVisible(can_write)

    # ------------------------------------------------------------------
    # Loading
    # ------------------------------------------------------------------

    def load_suppliers(self) -> None:
        """
        Carica i fornitori dal backend.
        """

        try:
            suppliers = self.api_connector.get_suppliers()

            if not isinstance(suppliers, list):
                suppliers = []

            self.suppliers = suppliers

            self._apply_filters()

            self.status_label.setText(
                f"{len(self.suppliers)} fornitori caricati."
            )

        except MedicalAPIAuthenticationError:
            self._show_error(
                "Sessione scaduta",
                "La sessione utente è scaduta. Effettua nuovamente il login.",
            )

        except MedicalAPIAuthorizationError:
            self._show_error(
                "Accesso negato",
                "Non disponi dei permessi necessari per visualizzare "
                "i fornitori.",
            )

        except MedicalAPIConnectorError as exc:
            self._show_error(
                "Errore API",
                str(exc),
            )

        except Exception as exc:
            self._show_error(
                "Errore",
                f"Si è verificato un errore imprevisto:\n{exc}",
            )

    # ------------------------------------------------------------------
    # Filtering
    # ------------------------------------------------------------------

    def _apply_filters(self) -> None:
        search_text = self.search_input.text().strip().lower()

        filtered_suppliers = []

        for supplier in self.suppliers:
            ragione_sociale = str(
                supplier.get("ragione_sociale") or ""
            ).lower()

            email = str(
                supplier.get("email_contatto") or ""
            ).lower()

            telefono = str(
                supplier.get("telefono") or ""
            ).lower()

            searchable_text = (
                f"{ragione_sociale} "
                f"{email} "
                f"{telefono}"
            )

            if search_text and search_text not in searchable_text:
                continue

            filtered_suppliers.append(supplier)

        self._populate_table(filtered_suppliers)

        self.status_label.setText(
            f"{len(filtered_suppliers)} fornitori visualizzati "
            f"su {len(self.suppliers)}."
        )

    # ------------------------------------------------------------------
    # Table
    # ------------------------------------------------------------------

    def _populate_table(
        self,
        suppliers: list[dict[str, Any]],
    ) -> None:
        self.table.setRowCount(0)

        for supplier in suppliers:
            row = self.table.rowCount()
            self.table.insertRow(row)

            supplier_id = supplier.get("id")

            values = [
                supplier_id,
                supplier.get("ragione_sociale") or "",
                supplier.get("email_contatto") or "",
                supplier.get("telefono") or "",
            ]

            for column, value in enumerate(values):
                item = QTableWidgetItem(str(value))

                if column == 0:
                    item.setTextAlignment(
                        Qt.AlignmentFlag.AlignCenter
                    )

                self.table.setItem(row, column, item)

            # ----------------------------------------------------------
            # Azioni
            # ----------------------------------------------------------

            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(4, 2, 4, 2)
            actions_layout.setSpacing(5)

            edit_button = QPushButton("Modifica")
            edit_button.clicked.connect(
                lambda checked=False, sid=supplier_id:
                self.edit_supplier_by_id(sid)
            )

            delete_button = QPushButton("Elimina")
            delete_button.clicked.connect(
                lambda checked=False, sid=supplier_id:
                self.delete_supplier_by_id(sid)
            )

            if not self.user_session.can_create_suppliers():
                edit_button.hide()
                delete_button.hide()

            actions_layout.addWidget(edit_button)
            actions_layout.addWidget(delete_button)

            self.table.setCellWidget(
                row,
                4,
                actions_widget,
            )

        self.table.resizeColumnsToContents()

        # Evita colonne troppo larghe
        self.table.setColumnWidth(0, 70)
        self.table.setColumnWidth(1, 260)
        self.table.setColumnWidth(2, 250)
        self.table.setColumnWidth(3, 150)

    # ------------------------------------------------------------------
    # Selection
    # ------------------------------------------------------------------

    def _get_selected_supplier(self) -> dict[str, Any] | None:
        row = self.table.currentRow()

        if row < 0:
            return None

        id_item = self.table.item(row, 0)

        if id_item is None:
            return None

        try:
            supplier_id = int(id_item.text())
        except ValueError:
            return None

        for supplier in self.suppliers:
            if supplier.get("id") == supplier_id:
                return supplier

        return None

    def _get_supplier_by_id(
        self,
        supplier_id: int | None,
    ) -> dict[str, Any] | None:
        if supplier_id is None:
            return None

        for supplier in self.suppliers:
            if supplier.get("id") == supplier_id:
                return supplier

        return None

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------

    def create_supplier(self) -> None:
        if not self.user_session.can_create_suppliers():
            QMessageBox.warning(
                self,
                "Accesso negato",
                "Non disponi dei permessi necessari.",
            )
            return

        dialog = MedicalSupplierDialog(self)

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        payload = dialog.get_form_data()

        try:
            self.api_connector.create_supplier(payload)

            QMessageBox.information(
                self,
                "Operazione completata",
                "Il fornitore è stato creato correttamente.",
            )

            self.load_suppliers()

        except MedicalAPIAuthenticationError:
            self._show_error(
                "Sessione scaduta",
                "La sessione utente è scaduta. Effettua nuovamente il login.",
            )

        except MedicalAPIAuthorizationError:
            self._show_error(
                "Accesso negato",
                "Non disponi dei permessi necessari per creare un fornitore.",
            )

        except MedicalAPIConflictError as exc:
            self._show_error(
                "Conflitto",
                str(exc),
            )

        except MedicalAPIValidationError as exc:
            self._show_error(
                "Dati non validi",
                str(exc),
            )

        except MedicalAPIConnectorError as exc:
            self._show_error(
                "Errore API",
                str(exc),
            )

        except Exception as exc:
            self._show_error(
                "Errore",
                f"Si è verificato un errore imprevisto:\n{exc}",
            )

    # ------------------------------------------------------------------
    # Edit
    # ------------------------------------------------------------------

    def edit_supplier(self) -> None:
        supplier = self._get_selected_supplier()

        if supplier is None:
            QMessageBox.information(
                self,
                "Selezione richiesta",
                "Seleziona un fornitore da modificare.",
            )
            return

        self.edit_supplier_by_id(supplier.get("id"))

    def edit_supplier_by_id(
        self,
        supplier_id: int | None,
    ) -> None:
        if not self.user_session.can_create_suppliers():
            QMessageBox.warning(
                self,
                "Accesso negato",
                "Non disponi dei permessi necessari.",
            )
            return

        supplier = self._get_supplier_by_id(supplier_id)

        if supplier is None:
            QMessageBox.warning(
                self,
                "Fornitore non trovato",
                "Il fornitore selezionato non è più disponibile.",
            )
            return

        dialog = MedicalSupplierDialog(
            self,
            supplier=supplier,
        )

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        payload = dialog.get_form_data()

        try:
            self.api_connector.update_supplier(
                int(supplier_id),
                payload,
            )

            QMessageBox.information(
                self,
                "Operazione completata",
                "Il fornitore è stato modificato correttamente.",
            )

            self.load_suppliers()

        except MedicalAPIAuthenticationError:
            self._show_error(
                "Sessione scaduta",
                "La sessione utente è scaduta. Effettua nuovamente il login.",
            )

        except MedicalAPIAuthorizationError:
            self._show_error(
                "Accesso negato",
                "Non disponi dei permessi necessari per modificare "
                "il fornitore.",
            )

        except MedicalAPINotFoundError as exc:
            self._show_error(
                "Fornitore non trovato",
                str(exc),
            )

        except MedicalAPIConflictError as exc:
            self._show_error(
                "Conflitto",
                str(exc),
            )

        except MedicalAPIValidationError as exc:
            self._show_error(
                "Dati non validi",
                str(exc),
            )

        except MedicalAPIConnectorError as exc:
            self._show_error(
                "Errore API",
                str(exc),
            )

        except Exception as exc:
            self._show_error(
                "Errore",
                f"Si è verificato un errore imprevisto:\n{exc}",
            )

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    def delete_supplier(self) -> None:
        supplier = self._get_selected_supplier()

        if supplier is None:
            QMessageBox.information(
                self,
                "Selezione richiesta",
                "Seleziona un fornitore da eliminare.",
            )
            return

        self.delete_supplier_by_id(supplier.get("id"))

    def delete_supplier_by_id(
        self,
        supplier_id: int | None,
    ) -> None:
        if not self.user_session.can_create_suppliers():
            QMessageBox.warning(
                self,
                "Accesso negato",
                "Non disponi dei permessi necessari.",
            )
            return

        supplier = self._get_supplier_by_id(supplier_id)

        if supplier is None:
            QMessageBox.warning(
                self,
                "Fornitore non trovato",
                "Il fornitore selezionato non è più disponibile.",
            )
            return

        supplier_name = (
            supplier.get("ragione_sociale")
            or f"ID {supplier_id}"
        )

        answer = QMessageBox.question(
            self,
            "Conferma eliminazione",
            (
                f"Sei sicuro di voler eliminare il fornitore:\n\n"
                f"{supplier_name}\n\n"
                "L'operazione non può essere annullata."
            ),
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if answer != QMessageBox.StandardButton.Yes:
            return

        try:
            self.api_connector.delete_supplier(
                int(supplier_id)
            )

            QMessageBox.information(
                self,
                "Operazione completata",
                "Il fornitore è stato eliminato correttamente.",
            )

            self.load_suppliers()

        except MedicalAPIAuthenticationError:
            self._show_error(
                "Sessione scaduta",
                "La sessione utente è scaduta. Effettua nuovamente il login.",
            )

        except MedicalAPIAuthorizationError:
            self._show_error(
                "Accesso negato",
                "Non disponi dei permessi necessari per eliminare "
                "il fornitore.",
            )

        except MedicalAPINotFoundError as exc:
            self._show_error(
                "Fornitore non trovato",
                str(exc),
            )

        except MedicalAPIConflictError as exc:
            self._show_error(
                "Impossibile eliminare",
                str(exc),
            )

        except MedicalAPIConnectorError as exc:
            self._show_error(
                "Errore API",
                str(exc),
            )

        except Exception as exc:
            self._show_error(
                "Errore",
                f"Si è verificato un errore imprevisto:\n{exc}",
            )

    # ------------------------------------------------------------------
    # Events
    # ------------------------------------------------------------------

    def _table_double_clicked(self, index) -> None:
        if not index.isValid():
            return

        self.edit_supplier()

    def refresh_page(self) -> None:
        self.load_suppliers()

    def showEvent(self, event) -> None:
        super().showEvent(event)

        if not self.suppliers:
            self.load_suppliers()

    # ------------------------------------------------------------------
    # Error handling
    # ------------------------------------------------------------------

    def _show_error(
        self,
        title: str,
        message: str,
    ) -> None:
        QMessageBox.critical(
            self,
            title,
            message,
        )