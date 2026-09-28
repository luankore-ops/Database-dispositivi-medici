
from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
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
    MedicalAPIConflictError,
    MedicalAPIValidationError,
)


# ============================================================
# DIALOG DISPOSITIVO
# ============================================================

class MedicalDeviceDialog(QDialog):
    def __init__(
        self,
        parent: QWidget | None = None,
        device: dict[str, Any] | None = None,
        departments: list[dict[str, Any]] | None = None,
        suppliers: list[dict[str, Any]] | None = None,
    ):
        super().__init__(parent)

        self.device = device
        self.departments = departments or []
        self.suppliers = suppliers or []

        self.setWindowTitle(
            "Modifica dispositivo"
            if self.device
            else "Nuovo dispositivo"
        )

        self.setMinimumWidth(500)

        self._build_ui()

        if self.device:
            self._load_existing_data()

    # ========================================================
    # UI
    # ========================================================

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        form_layout = QFormLayout()
        form_layout.setSpacing(10)

        # ====================================================
        # NOME
        # ====================================================

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText(
            "Nome dispositivo"
        )

        form_layout.addRow(
            "Nome *:",
            self.name_input,
        )

        # ====================================================
        # CATEGORIA
        # ====================================================

        self.category_input = QLineEdit()
        self.category_input.setPlaceholderText(
            "Categoria"
        )

        form_layout.addRow(
            "Categoria *:",
            self.category_input,
        )

        # ====================================================
        # NUMERO SERIALE
        # ====================================================

        self.serial_input = QLineEdit()
        self.serial_input.setPlaceholderText(
            "Numero seriale"
        )

        form_layout.addRow(
            "Numero seriale *:",
            self.serial_input,
        )

        # ====================================================
        # UDI
        # ====================================================

        self.udi_input = QLineEdit()
        self.udi_input.setPlaceholderText(
            "UDI"
        )

        form_layout.addRow(
            "UDI:",
            self.udi_input,
        )

        # ====================================================
        # PRODUTTORE
        # ====================================================

        self.manufacturer_input = QLineEdit()
        self.manufacturer_input.setPlaceholderText(
            "Produttore"
        )

        form_layout.addRow(
            "Produttore *:",
            self.manufacturer_input,
        )

        # ====================================================
        # MODELLO
        # ====================================================

        self.model_input = QLineEdit()
        self.model_input.setPlaceholderText(
            "Modello"
        )

        form_layout.addRow(
            "Modello:",
            self.model_input,
        )

        # ====================================================
        # DATA ACQUISTO
        # ====================================================

        self.purchase_date_input = QLineEdit()
        self.purchase_date_input.setPlaceholderText(
            "YYYY-MM-DD"
        )

        form_layout.addRow(
            "Data acquisto:",
            self.purchase_date_input,
        )

        # ====================================================
        # COSTO
        # ====================================================

        self.cost_input = QLineEdit()
        self.cost_input.setPlaceholderText(
            "Es. 12500.50"
        )

        form_layout.addRow(
            "Costo:",
            self.cost_input,
        )

        # ====================================================
        # SCADENZA GARANZIA
        # ====================================================

        self.warranty_date_input = QLineEdit()
        self.warranty_date_input.setPlaceholderText(
            "YYYY-MM-DD"
        )

        form_layout.addRow(
            "Scadenza garanzia:",
            self.warranty_date_input,
        )

        # ====================================================
        # STATO
        # ====================================================
        #
        # Valori accettati dal backend:
        #
        #   in_uso
        #   manutenzione
        #   guasto
        #   dismesso
        #
        # L'utente vede invece le descrizioni leggibili.
        # ====================================================

        self.status_combo = QComboBox()

        self.status_combo.addItem(
            "In uso",
            "in_uso",
        )

        self.status_combo.addItem(
            "Manutenzione",
            "manutenzione",
        )

        self.status_combo.addItem(
            "Guasto",
            "guasto",
        )

        self.status_combo.addItem(
            "Dismesso",
            "dismesso",
        )

        form_layout.addRow(
            "Stato:",
            self.status_combo,
        )

        # ====================================================
        # REPARTO
        # ====================================================

        self.department_combo = QComboBox()

        self.department_combo.addItem(
            "Nessun reparto",
            None,
        )

        for department in self.departments:
            department_id = department.get(
                "id"
            )

            department_name = (
                department.get("nome")
                or department.get("name")
                or f"Reparto {department_id}"
            )

            self.department_combo.addItem(
                str(department_name),
                department_id,
            )

        form_layout.addRow(
            "Reparto:",
            self.department_combo,
        )

        # ====================================================
        # FORNITORE
        # ====================================================

        self.supplier_combo = QComboBox()

        self.supplier_combo.addItem(
            "Nessun fornitore",
            None,
        )

        for supplier in self.suppliers:
            supplier_id = supplier.get(
                "id"
            )

            supplier_name = (
                supplier.get("nome")
                or supplier.get("ragione_sociale")
                or supplier.get("name")
                or f"Fornitore {supplier_id}"
            )

            self.supplier_combo.addItem(
                str(supplier_name),
                supplier_id,
            )

        form_layout.addRow(
            "Fornitore:",
            self.supplier_combo,
        )

        layout.addLayout(
            form_layout
        )

        # ====================================================
        # PULSANTI
        # ====================================================

        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )

        button_box.accepted.connect(
            self.accept
        )

        button_box.rejected.connect(
            self.reject
        )

        layout.addWidget(
            button_box
        )

    # ========================================================
    # CARICAMENTO DATI ESISTENTI
    # ========================================================

    def _load_existing_data(self) -> None:
        if not self.device:
            return

        # ====================================================
        # DATI GENERALI
        # ====================================================

        self.name_input.setText(
            str(
                self.device.get("nome")
                or ""
            )
        )

        self.category_input.setText(
            str(
                self.device.get("categoria")
                or ""
            )
        )

        self.serial_input.setText(
            str(
                self.device.get("numero_seriale")
                or ""
            )
        )

        self.udi_input.setText(
            str(
                self.device.get("udi")
                or ""
            )
        )

        self.manufacturer_input.setText(
            str(
                self.device.get("produttore")
                or ""
            )
        )

        self.model_input.setText(
            str(
                self.device.get("modello")
                or ""
            )
        )

        self.purchase_date_input.setText(
            str(
                self.device.get("data_acquisto")
                or ""
            )
        )

        cost = self.device.get(
            "costo"
        )

        if cost is not None:
            self.cost_input.setText(
                str(cost)
            )

        self.warranty_date_input.setText(
            str(
                self.device.get(
                    "data_scadenza_garanzia"
                )
                or ""
            )
        )

        # ====================================================
        # STATO
        # ====================================================

        stato = self.device.get(
            "stato"
        )

        if isinstance(stato, dict):
            stato = (
                stato.get("value")
                or stato.get("name")
                or stato.get("stato")
            )

        if stato is not None:
            stato = str(
                stato
            ).strip().lower()

            stato_mapping = {
                "in_uso": "in_uso",
                "in uso": "in_uso",
                "dismesso": "dismesso",
                "manutenzione": "manutenzione",
                "guasto": "guasto",
            }

            stato = stato_mapping.get(
                stato,
                stato,
            )

            index = self.status_combo.findData(
                stato
            )

            if index >= 0:
                self.status_combo.setCurrentIndex(
                    index
                )

        # ====================================================
        # REPARTO
        # ====================================================

        reparto_id = self.device.get(
            "reparto_id"
        )

        if reparto_id is None:
            reparto = self.device.get(
                "reparto"
            )

            if isinstance(reparto, dict):
                reparto_id = reparto.get(
                    "id"
                )

        if reparto_id is not None:
            index = self.department_combo.findData(
                reparto_id
            )

            if index >= 0:
                self.department_combo.setCurrentIndex(
                    index
                )

        # ====================================================
        # FORNITORE
        # ====================================================

        fornitore_id = self.device.get(
            "fornitore_id"
        )

        if fornitore_id is None:
            fornitore = self.device.get(
                "fornitore"
            )

            if isinstance(fornitore, dict):
                fornitore_id = fornitore.get(
                    "id"
                )

        if fornitore_id is not None:
            index = self.supplier_combo.findData(
                fornitore_id
            )

            if index >= 0:
                self.supplier_combo.setCurrentIndex(
                    index
                )

    # ========================================================
    # DATI DEL FORM
    # ========================================================

    def get_form_data(self) -> dict[str, Any]:
        # ====================================================
        # STATO
        # ====================================================

        stato = self.status_combo.currentData()

        if stato is None:
            stato = "in_uso"

        stato = str(
            stato
        ).strip().lower()

        stato_mapping = {
            "in_uso": "in_uso",
            "in uso": "in_uso",
            "dismesso": "dismesso",
            "manutenzione": "manutenzione",
            "guasto": "guasto",
        }

        stato = stato_mapping.get(
            stato,
            stato,
        )

        # ====================================================
        # DATI
        # ====================================================

        data = {
            "nome": self.name_input.text().strip(),

            "categoria": (
                self.category_input.text().strip()
            ),

            "numero_seriale": (
                self.serial_input.text().strip()
            ),

            "udi": (
                self.udi_input.text().strip()
                or None
            ),

            "produttore": (
                self.manufacturer_input.text().strip()
            ),

            "modello": (
                self.model_input.text().strip()
                or None
            ),

            "data_acquisto": (
                self.purchase_date_input.text().strip()
                or None
            ),

            "costo": None,

            "data_scadenza_garanzia": (
                self.warranty_date_input.text().strip()
                or None
            ),

            "stato": stato,

            "reparto_id": (
                self.department_combo.currentData()
            ),

            "fornitore_id": (
                self.supplier_combo.currentData()
            ),
        }

        # ====================================================
        # COSTO
        # ====================================================

        cost_text = self.cost_input.text().strip()

        if cost_text:
            try:
                data["costo"] = float(
                    cost_text.replace(
                        ",",
                        ".",
                    )
                )

            except ValueError:
                raise ValueError(
                    "Il costo deve essere un numero valido."
                )

        return data

    # ========================================================
    # VALIDAZIONE
    # ========================================================

    def accept(self) -> None:
        try:
            data = self.get_form_data()

        except ValueError as exc:
            QMessageBox.warning(
                self,
                "Dati non validi",
                str(exc),
            )

            return

        # ====================================================
        # CAMPI OBBLIGATORI
        # ====================================================

        required_fields = {
            "nome": "Nome",
            "categoria": "Categoria",
            "numero_seriale": "Numero seriale",
            "produttore": "Produttore",
        }

        missing_fields = [
            label
            for key, label in required_fields.items()
            if not data.get(key)
        ]

        if missing_fields:
            QMessageBox.warning(
                self,
                "Dati mancanti",
                "Compila i seguenti "
                "campi obbligatori:\n\n"
                + "\n".join(
                    f"• {field}"
                    for field in missing_fields
                ),
            )

            return

        # ====================================================
        # CONTROLLO STATO
        # ====================================================

        valid_statuses = {
            "in_uso",
            "dismesso",
            "manutenzione",
            "guasto",
        }

        if data["stato"] not in valid_statuses:
            QMessageBox.warning(
                self,
                "Stato non valido",
                "Lo stato deve essere uno "
                "dei seguenti:\n\n"
                "• in_uso\n"
                "• manutenzione\n"
                "• guasto\n"
                "• dismesso",
            )

            return

        super().accept()


# ============================================================
# PAGINA DISPOSITIVI
# ============================================================

class MedicalDevicesPage(QWidget):
    def __init__(
        self,
        user_session=None,
        parent: QWidget | None = None,
        api_connector=None,
    ):
        super().__init__(parent)

        # ====================================================
        # USER SESSION
        # ====================================================

        self.user_session = user_session

        # ====================================================
        # API CONNECTOR
        # ====================================================

        if api_connector is not None:
            self.api_connector = api_connector

        else:
            from gui.medical_api_connector import (
                medical_api_connector,
            )

            self.api_connector = (
                medical_api_connector
            )

        # ====================================================
        # DATI
        # ====================================================

        self.devices: list[
            dict[str, Any]
        ] = []

        self.departments: list[
            dict[str, Any]
        ] = []

        self.suppliers: list[
            dict[str, Any]
        ] = []

        # ====================================================
        # UI
        # ====================================================

        self._build_ui()

        # NON carichiamo i dati qui.
        #
        # La pagina può essere creata dal dashboard
        # prima del login.
        #
        # Il caricamento viene eseguito tramite refresh_page()
        # dopo l'autenticazione.

    # ========================================================
    # UI
    # ========================================================

    def _build_ui(self) -> None:
        main_layout = QVBoxLayout(
            self
        )

        # ====================================================
        # TITOLO
        # ====================================================

        title = QLabel(
            "Gestione dispositivi medici"
        )

        title.setStyleSheet(
            """
            QLabel {
                font-size: 24px;
                font-weight: bold;
                padding: 10px 0;
            }
            """
        )

        main_layout.addWidget(
            title
        )

        # ====================================================
        # BARRA SUPERIORE
        # ====================================================

        top_layout = QHBoxLayout()

        self.search_input = QLineEdit()

        self.search_input.setPlaceholderText(
            "Cerca per nome, seriale, produttore..."
        )

        self.search_input.textChanged.connect(
            self.filter_table
        )

        top_layout.addWidget(
            self.search_input
        )

        # ====================================================
        # AGGIUNGI
        # ====================================================

        self.add_button = QPushButton(
            "Aggiungi"
        )

        self.add_button.clicked.connect(
            self.create_device
        )

        top_layout.addWidget(
            self.add_button
        )

        # ====================================================
        # MODIFICA
        # ====================================================

        self.edit_button = QPushButton(
            "Modifica"
        )

        self.edit_button.clicked.connect(
            self.edit_selected_device
        )

        top_layout.addWidget(
            self.edit_button
        )

        # ====================================================
        # ELIMINA
        # ====================================================

        self.delete_button = QPushButton(
            "Elimina"
        )

        self.delete_button.clicked.connect(
            self.delete_selected_device
        )

        top_layout.addWidget(
            self.delete_button
        )

        # ====================================================
        # AGGIORNA
        # ====================================================

        self.refresh_button = QPushButton(
            "Aggiorna"
        )

        self.refresh_button.clicked.connect(
            self.refresh_page
        )

        top_layout.addWidget(
            self.refresh_button
        )

        main_layout.addLayout(
            top_layout
        )

        # ====================================================
        # TABELLA
        # ====================================================

        self.table = QTableWidget()

        self.table.setColumnCount(
            8
        )

        self.table.setHorizontalHeaderLabels(
            [
                "ID",
                "Nome",
                "Categoria",
                "Numero seriale",
                "Produttore",
                "Modello",
                "Stato",
                "Reparto",
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

        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )

        self.table.verticalHeader().setVisible(
            False
        )

        main_layout.addWidget(
            self.table
        )

    # ========================================================
    # REFRESH
    # ========================================================

    def refresh_page(self) -> None:
        """
        Ricarica i dispositivi, i reparti e i fornitori.

        Viene utilizzato dal dashboard dopo il login
        e dal pulsante "Aggiorna".
        """

        self.load_data()

    # ========================================================
    # CARICAMENTO DATI
    # ========================================================

    def load_data(self) -> None:
        try:
            self.devices = (
                self.api_connector.get_devices()
            )

            self.departments = (
                self.api_connector.get_departments()
            )

            self.suppliers = (
                self.api_connector.get_suppliers()
            )

            self.populate_table(
                self.devices
            )

        except Exception as exc:
            QMessageBox.critical(
                self,
                "Errore",
                "Errore durante il caricamento "
                f"dei dati:\n{exc}",
            )

    # ========================================================
    # TABELLA
    # ========================================================

    def populate_table(
        self,
        devices: list[dict[str, Any]],
    ) -> None:
        self.table.setRowCount(
            0
        )

        for device in devices:
            row = self.table.rowCount()

            self.table.insertRow(
                row
            )

            device_id = device.get(
                "id",
                "",
            )

            # ====================================================
            # STATO
            # ====================================================

            stato = device.get(
                "stato",
                "",
            )

            if isinstance(stato, dict):
                stato = (
                    stato.get("value")
                    or stato.get("name")
                    or ""
                )

            stato_mapping = {
                "IN_USO": "In uso",
                "in_uso": "In uso",
                "in uso": "In uso",
                "DISMESSO": "Dismesso",
                "dismesso": "Dismesso",
                "MANUTENZIONE": "Manutenzione",
                "manutenzione": "Manutenzione",
                "GUASTO": "Guasto",
                "guasto": "Guasto",
            }

            stato_visualizzato = (
                stato_mapping.get(
                    str(stato),
                    str(stato),
                )
            )

            # ====================================================
            # REPARTO
            # ====================================================

            reparto = device.get(
                "reparto"
            )

            if isinstance(reparto, dict):
                reparto = (
                    reparto.get("nome")
                    or reparto.get("name")
                    or ""
                )

            # ====================================================
            # VALORI
            # ====================================================

            values = [
                device_id,
                device.get(
                    "nome",
                    "",
                ),
                device.get(
                    "categoria",
                    "",
                ),
                device.get(
                    "numero_seriale",
                    "",
                ),
                device.get(
                    "produttore",
                    "",
                ),
                device.get(
                    "modello",
                    "",
                ),
                stato_visualizzato,
                reparto or "",
            ]

            for column, value in enumerate(
                values
            ):
                item = QTableWidgetItem(
                    str(value)
                    if value is not None
                    else ""
                )

                item.setTextAlignment(
                    Qt.AlignmentFlag.AlignVCenter
                    | Qt.AlignmentFlag.AlignLeft
                )

                self.table.setItem(
                    row,
                    column,
                    item,
                )

    # ========================================================
    # FILTRO
    # ========================================================

    def filter_table(
        self,
        text: str,
    ) -> None:
        text = text.strip().lower()

        if not text:
            self.populate_table(
                self.devices
            )

            return

        filtered_devices = []

        for device in self.devices:
            searchable_values = [
                device.get("nome"),
                device.get("categoria"),
                device.get("numero_serosiale"),
                device.get("produttore"),
                device.get("modello"),
                device.get("stato"),
            ]

            searchable_text = " ".join(
                str(value or "")
                for value in searchable_values
            ).lower()

            if text in searchable_text:
                filtered_devices.append(
                    device
                )

        self.populate_table(
            filtered_devices
        )

    # ========================================================
    # DISPOSITIVO SELEZIONATO
    # ========================================================

    def get_selected_device(
        self,
    ) -> dict[str, Any] | None:
        selected_rows = (
            self.table.selectionModel()
            .selectedRows()
        )

        if not selected_rows:
            QMessageBox.information(
                self,
                "Selezione",
                "Seleziona prima un dispositivo.",
            )

            return None

        row = selected_rows[0].row()

        id_item = self.table.item(
            row,
            0,
        )

        if not id_item:
            return None

        try:
            device_id = int(
                id_item.text()
            )

        except ValueError:
            return None

        for device in self.devices:
            if device.get("id") == device_id:
                return device

        return None

    # ========================================================
    # CREAZIONE
    # ========================================================

    def create_device(self) -> None:
        dialog = MedicalDeviceDialog(
            parent=self,
            departments=self.departments,
            suppliers=self.suppliers,
        )

        if (
            dialog.exec()
            != QDialog.DialogCode.Accepted
        ):
            return

        try:
            data = dialog.get_form_data()

            self.api_connector.create_device(
                data
            )

            QMessageBox.information(
                self,
                "Operazione completata",
                "Dispositivo creato correttamente.",
            )

            self.refresh_page()

        except MedicalAPIConflictError as exc:
            QMessageBox.warning(
                self,
                "Dispositivo già esistente",
                str(exc),
            )

        except MedicalAPIValidationError as exc:
            QMessageBox.warning(
                self,
                "Dati non validi",
                str(exc),
            )

        except ValueError as exc:
            QMessageBox.warning(
                self,
                "Dati non validi",
                str(exc),
            )

        except Exception as exc:
            QMessageBox.critical(
                self,
                "Errore",
                "Errore durante la creazione "
                f"del dispositivo:\n{exc}",
            )

    # ========================================================
    # MODIFICA
    # ========================================================

    def edit_selected_device(self) -> None:
        device = self.get_selected_device()

        if not device:
            return

        dialog = MedicalDeviceDialog(
            parent=self,
            device=device,
            departments=self.departments,
            suppliers=self.suppliers,
        )

        if (
            dialog.exec()
            != QDialog.DialogCode.Accepted
        ):
            return

        try:
            data = dialog.get_form_data()

            device_id = device.get(
                "id"
            )

            if device_id is None:
                QMessageBox.warning(
                    self,
                    "Errore",
                    "ID del dispositivo "
                    "non disponibile.",
                )

                return

            # L'endpoint PUT non accetta
            # data_acquisto.
            data.pop(
                "data_acquisto",
                None,
            )

            self.api_connector.update_device(
                int(device_id),
                data,
            )

            QMessageBox.information(
                self,
                "Operazione completata",
                "Dispositivo modificato correttamente.",
            )

            self.refresh_page()

        except MedicalAPIConflictError as exc:
            QMessageBox.warning(
                self,
                "Conflitto",
                str(exc),
            )

        except MedicalAPIValidationError as exc:
            QMessageBox.warning(
                self,
                "Dati non validi",
                str(exc),
            )

        except ValueError as exc:
            QMessageBox.warning(
                self,
                "Dati non validi",
                str(exc),
            )

        except Exception as exc:
            QMessageBox.critical(
                self,
                "Errore",
                "Errore durante la modifica:\n"
                f"{exc}",
            )

    # ========================================================
    # ELIMINAZIONE
    # ========================================================

    def delete_selected_device(self) -> None:
        device = self.get_selected_device()

        if not device:
            return

        device_id = device.get(
            "id"
        )

        nome = (
            device.get("nome")
            or "dispositivo"
        )

        reply = QMessageBox.question(
            self,
            "Conferma eliminazione",
            "Vuoi eliminare definitivamente "
            f"il dispositivo '{nome}'?",
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
        )

        if (
            reply
            != QMessageBox.StandardButton.Yes
        ):
            return

        try:
            self.api_connector.delete_device(
                int(device_id)
            )

            QMessageBox.information(
                self,
                "Operazione completata",
                "Dispositivo eliminato correttamente.",
            )

            self.refresh_page()

        except MedicalAPIConflictError as exc:
            QMessageBox.warning(
                self,
                "Operazione non consentita",
                str(exc),
            )

        except Exception as exc:
            QMessageBox.critical(
                self,
                "Errore",
                "Errore durante l'eliminazione:\n"
                f"{exc}",
            )
