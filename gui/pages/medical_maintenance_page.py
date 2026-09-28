"""
medical_maintenance_page.py

Pagina desktop PySide6 per la gestione delle manutenzioni
dei dispositivi medici.

Funzionalità:
- selezione del dispositivo medico;
- visualizzazione delle manutenzioni;
- ricerca;
- filtro per tipo;
- indicazione delle scadenze;
- creazione di una nuova manutenzione;
- visualizzazione dei dettagli;
- rispetto dei ruoli ADMIN / TECNICO / LETTORE.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Optional

from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
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
    QPlainTextEdit,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QDateEdit,
    QHeaderView,
)

from gui.medical_api_connector import (
    MedicalAPIConnectorError,
    MedicalAPIAuthenticationError,
    MedicalAPIAuthorizationError,
    MedicalAPINotFoundError,
    MedicalAPIValidationError,
    MedicalAPIServerError,
)
from gui.medical_user_session import (
    MedicalUserSession,
    medical_user_session,
)


class MedicalMaintenanceDialog(QDialog):
    """
    Dialog per la creazione di una nuova manutenzione.
    """

    def __init__(
        self,
        device: dict[str, Any],
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)

        self.device = device

        self.setWindowTitle("Nuova manutenzione")
        self.setMinimumWidth(500)

        self._build_ui()

    def _build_ui(self) -> None:
        main_layout = QVBoxLayout(self)

        # ---------------------------------------------------------
        # Informazioni dispositivo
        # ---------------------------------------------------------

        device_group = QGroupBox("Dispositivo medico")
        device_layout = QFormLayout(device_group)

        device_name = self.device.get("nome", "-")
        serial_number = self.device.get("numero_seriale", "-")

        device_layout.addRow(
            "Dispositivo:",
            QLabel(str(device_name)),
        )

        device_layout.addRow(
            "Numero seriale:",
            QLabel(str(serial_number)),
        )

        main_layout.addWidget(device_group)

        # ---------------------------------------------------------
        # Dati manutenzione
        # ---------------------------------------------------------

        maintenance_group = QGroupBox("Dati manutenzione")
        form_layout = QFormLayout(maintenance_group)

        # Data manutenzione
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setDisplayFormat("dd/MM/yyyy")

        form_layout.addRow(
            "Data manutenzione:",
            self.date_edit,
        )

        # Tipo
        self.type_combo = QComboBox()
        self.type_combo.addItem(
            "Manutenzione preventiva",
            "preventiva",
        )
        self.type_combo.addItem(
            "Manutenzione correttiva",
            "correttiva",
        )

        form_layout.addRow(
            "Tipo:",
            self.type_combo,
        )

        # Tecnico
        self.technician_edit = QLineEdit()
        self.technician_edit.setPlaceholderText(
            "Nome del tecnico responsabile"
        )

        form_layout.addRow(
            "Tecnico:",
            self.technician_edit,
        )

        # Descrizione
        self.description_edit = QPlainTextEdit()
        self.description_edit.setPlaceholderText(
            "Descrizione dell'intervento, attività eseguite, "
            "eventuali anomalie riscontrate..."
        )
        self.description_edit.setMinimumHeight(120)

        form_layout.addRow(
            "Descrizione:",
            self.description_edit,
        )

        # Prossima scadenza
        self.next_deadline_edit = QDateEdit()
        self.next_deadline_edit.setCalendarPopup(True)
        self.next_deadline_edit.setDisplayFormat("dd/MM/yyyy")

        # Permettiamo anche una scadenza vuota tramite checkbox
        self.no_deadline_checkbox = QPushButton(
            "Nessuna scadenza"
        )
        self.no_deadline_checkbox.setCheckable(True)
        self.no_deadline_checkbox.setChecked(False)
        self.no_deadline_checkbox.clicked.connect(
            self._toggle_deadline
        )

        deadline_layout = QHBoxLayout()
        deadline_layout.setContentsMargins(0, 0, 0, 0)

        deadline_layout.addWidget(
            self.next_deadline_edit,
            stretch=1,
        )

        deadline_layout.addWidget(
            self.no_deadline_checkbox,
        )

        form_layout.addRow(
            "Prossima scadenza:",
            deadline_layout,
        )

        main_layout.addWidget(maintenance_group)

        # ---------------------------------------------------------
        # Pulsanti
        # ---------------------------------------------------------

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )

        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        main_layout.addWidget(buttons)

    def _toggle_deadline(self) -> None:
        disabled = self.no_deadline_checkbox.isChecked()

        self.next_deadline_edit.setEnabled(not disabled)

    def get_form_data(self) -> dict[str, Any]:
        """
        Restituisce i dati nel formato previsto dall'API.
        """

        maintenance_date = self.date_edit.date().toString(
            "yyyy-MM-dd"
        )

        if self.no_deadline_checkbox.isChecked():
            next_deadline = None
        else:
            next_deadline = self.next_deadline_edit.date().toString(
                "yyyy-MM-dd"
            )

        return {
            "data": maintenance_date,
            "tipo": self.type_combo.currentData(),
            "tecnico": self.technician_edit.text().strip() or None,
            "descrizione": (
                self.description_edit.toPlainText().strip()
                or None
            ),
            "prossima_scadenza": next_deadline,
        }

    def accept(self) -> None:
        """
        Valida i dati prima di chiudere il dialog.
        """

        if not self.date_edit.date().isValid():
            QMessageBox.warning(
                self,
                "Dati non validi",
                "Inserisci una data di manutenzione valida.",
            )
            return

        if (
            not self.no_deadline_checkbox.isChecked()
            and not self.next_deadline_edit.date().isValid()
        ):
            QMessageBox.warning(
                self,
                "Dati non validi",
                "Inserisci una prossima scadenza valida "
                "oppure seleziona 'Nessuna scadenza'.",
            )
            return

        super().accept()


class MedicalMaintenancePage(QWidget):
    """
    Pagina principale per la gestione delle manutenzioni.
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

        from gui.medical_api_connector import medical_api_connector

        self.api = medical_api_connector

        self.devices: list[dict[str, Any]] = []
        self.maintenances: list[dict[str, Any]] = []

        self.current_device_id: Optional[int] = None

        self._build_ui()
        self._configure_permissions()

    # ============================================================
    # UI
    # ============================================================

    def _build_ui(self) -> None:
        main_layout = QVBoxLayout(self)

        # ---------------------------------------------------------
        # Titolo
        # ---------------------------------------------------------

        title_layout = QHBoxLayout()

        title = QLabel("Gestione manutenzioni")
        title.setStyleSheet(
            """
            QLabel {
                font-size: 24px;
                font-weight: 700;
            }
            """
        )

        subtitle = QLabel(
            "Gestisci gli interventi di manutenzione "
            "dei dispositivi medici."
        )

        subtitle.setStyleSheet(
            """
            QLabel {
                color: #777777;
                font-size: 13px;
            }
            """
        )

        title_column = QVBoxLayout()
        title_column.addWidget(title)
        title_column.addWidget(subtitle)

        title_layout.addLayout(title_column)
        title_layout.addStretch()

        main_layout.addLayout(title_layout)

        # ---------------------------------------------------------
        # Selezione dispositivo
        # ---------------------------------------------------------

        device_group = QGroupBox("Dispositivo")

        device_layout = QHBoxLayout(device_group)

        self.device_combo = QComboBox()
        self.device_combo.setMinimumHeight(36)

        self.device_combo.currentIndexChanged.connect(
            self._device_changed
        )

        device_layout.addWidget(
            QLabel("Seleziona dispositivo:")
        )

        device_layout.addWidget(
            self.device_combo,
            stretch=1,
        )

        self.refresh_devices_button = QPushButton(
            "↻ Aggiorna"
        )
        self.refresh_devices_button.clicked.connect(
            self.load_devices
        )

        device_layout.addWidget(
            self.refresh_devices_button
        )

        main_layout.addWidget(device_group)

        # ---------------------------------------------------------
        # Toolbar
        # ---------------------------------------------------------

        toolbar = QHBoxLayout()

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText(
            "Cerca per tecnico o descrizione..."
        )
        self.search_edit.textChanged.connect(
            self._apply_filters
        )

        toolbar.addWidget(
            self.search_edit,
            stretch=1,
        )

        toolbar.addWidget(
            QLabel("Tipo:")
        )

        self.type_filter = QComboBox()

        self.type_filter.addItem(
            "Tutti",
            None,
        )

        self.type_filter.addItem(
            "Preventiva",
            "preventiva",
        )

        self.type_filter.addItem(
            "Correttiva",
            "correttiva",
        )

        self.type_filter.currentIndexChanged.connect(
            self._apply_filters
        )

        toolbar.addWidget(
            self.type_filter
        )

        self.refresh_button = QPushButton(
            "↻ Aggiorna"
        )
        self.refresh_button.clicked.connect(
            self.load_maintenances
        )

        toolbar.addWidget(
            self.refresh_button
        )

        self.new_button = QPushButton(
            "＋ Nuova manutenzione"
        )
        self.new_button.clicked.connect(
            self.create_maintenance
        )

        toolbar.addWidget(
            self.new_button
        )

        main_layout.addLayout(toolbar)

        # ---------------------------------------------------------
        # Tabella
        # ---------------------------------------------------------

        self.table = QTableWidget()
        self.table.setColumnCount(7)

        self.table.setHorizontalHeaderLabels(
            [
                "ID",
                "Data",
                "Tipo",
                "Tecnico",
                "Descrizione",
                "Prossima scadenza",
                "Stato scadenza",
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

        self.table.doubleClicked.connect(
            self.show_details
        )

        header = self.table.horizontalHeader()

        header.setSectionResizeMode(
            0,
            QHeaderView.ResizeMode.ResizeToContents,
        )

        header.setSectionResizeMode(
            1,
            QHeaderView.ResizeMode.ResizeToContents,
        )

        header.setSectionResizeMode(
            2,
            QHeaderView.ResizeMode.ResizeToContents,
        )

        header.setSectionResizeMode(
            3,
            QHeaderView.ResizeMode.ResizeToContents,
        )

        header.setSectionResizeMode(
            4,
            QHeaderView.ResizeMode.Stretch,
        )

        header.setSectionResizeMode(
            5,
            QHeaderView.ResizeMode.ResizeToContents,
        )

        header.setSectionResizeMode(
            6,
            QHeaderView.ResizeMode.ResizeToContents,
        )

        main_layout.addWidget(
            self.table,
            stretch=1,
        )

        # ---------------------------------------------------------
        # Barra inferiore
        # ---------------------------------------------------------

        bottom_layout = QHBoxLayout()

        self.status_label = QLabel(
            "Nessuna manutenzione caricata."
        )

        self.status_label.setStyleSheet(
            """
            QLabel {
                color: #666666;
            }
            """
        )

        bottom_layout.addWidget(
            self.status_label
        )

        bottom_layout.addStretch()

        self.details_button = QPushButton(
            "Dettagli"
        )
        self.details_button.clicked.connect(
            self.show_details
        )

        bottom_layout.addWidget(
            self.details_button
        )

        main_layout.addLayout(bottom_layout)

    # ============================================================
    # PERMESSI
    # ============================================================

    def _configure_permissions(self) -> None:
        """
        Applica i permessi GUI in base al ruolo dell'utente.
        """

        can_create = (
            self.user_session.can_create_maintenances()
        )

        self.new_button.setVisible(
            can_create
        )

    # ============================================================
    # CARICAMENTO DISPOSITIVI
    # ============================================================

    def load_devices(self) -> None:
        """
        Carica i dispositivi disponibili dall'API.
        """

        try:
            devices = self.api.get(
                "/dispositivi"
            )

            if not isinstance(devices, list):
                devices = []

            self.devices = devices

            previous_id = self.current_device_id

            self.device_combo.blockSignals(True)
            self.device_combo.clear()

            selected_index = -1

            for index, device in enumerate(self.devices):
                device_id = device.get("id")

                name = device.get(
                    "nome",
                    "Dispositivo senza nome",
                )

                serial = device.get(
                    "numero_seriale",
                    "-",
                )

                label = (
                    f"{name} "
                    f"— SN: {serial}"
                )

                self.device_combo.addItem(
                    label,
                    device_id,
                )

                if (
                    previous_id is not None
                    and device_id == previous_id
                ):
                    selected_index = index

            self.device_combo.blockSignals(False)

            if selected_index >= 0:
                self.device_combo.setCurrentIndex(
                    selected_index
                )
            elif self.device_combo.count() > 0:
                self.device_combo.setCurrentIndex(0)

            else:
                self.current_device_id = None
                self.maintenances = []
                self._populate_table([])

            if self.device_combo.count() > 0:
                self._device_changed(
                    self.device_combo.currentIndex()
                )

        except MedicalAPIAuthenticationError:
            self._show_error(
                "Sessione scaduta",
                "La sessione utente è scaduta. "
                "Effettua nuovamente il login.",
            )

        except MedicalAPIAuthorizationError:
            self._show_error(
                "Accesso negato",
                "Non disponi dei permessi necessari "
                "per visualizzare i dispositivi.",
            )

        except MedicalAPIValidationError as exc:
            self._show_error(
                "Errore di validazione",
                str(exc),
            )

        except MedicalAPIServerError as exc:
            self._show_error(
                "Errore del server",
                str(exc),
            )

        except MedicalAPIConnectorError as exc:
            self._show_error(
                "Errore di connessione",
                str(exc),
            )

        except Exception as exc:
            self._show_error(
                "Errore",
                f"Errore imprevisto:\n{exc}",
            )

    # ============================================================
    # CAMBIO DISPOSITIVO
    # ============================================================

    def _device_changed(self, index: int) -> None:
        if index < 0:
            self.current_device_id = None
            self.maintenances = []
            self._populate_table([])
            return

        device_id = self.device_combo.itemData(
            index
        )

        if device_id is None:
            return

        self.current_device_id = int(
            device_id
        )

        self.load_maintenances()

    # ============================================================
    # CARICAMENTO MANUTENZIONI
    # ============================================================

    def load_maintenances(self) -> None:
        """
        Carica le manutenzioni del dispositivo selezionato.
        """

        if self.current_device_id is None:
            self.maintenances = []
            self._populate_table([])
            return

        try:
            data = self.api.get(
                f"/dispositivi/"
                f"{self.current_device_id}/manutenzioni"
            )

            if not isinstance(data, list):
                data = []

            self.maintenances = data

            self._apply_filters()

        except MedicalAPIAuthenticationError:
            self._show_error(
                "Sessione scaduta",
                "La sessione utente è scaduta. "
                "Effettua nuovamente il login.",
            )

        except MedicalAPIAuthorizationError:
            self._show_error(
                "Accesso negato",
                "Non disponi dei permessi necessari "
                "per visualizzare le manutenzioni.",
            )

        except MedicalAPINotFoundError:
            self._show_error(
                "Dispositivo non trovato",
                "Il dispositivo selezionato "
                "non è più disponibile.",
            )

        except MedicalAPIServerError as exc:
            self._show_error(
                "Errore del server",
                str(exc),
            )

        except MedicalAPIConnectorError as exc:
            self._show_error(
                "Errore di connessione",
                str(exc),
            )

        except Exception as exc:
            self._show_error(
                "Errore",
                f"Errore imprevisto:\n{exc}",
            )

    # ============================================================
    # FILTRI
    # ============================================================

    def _apply_filters(self) -> None:
        search_text = (
            self.search_edit.text()
            .strip()
            .lower()
        )

        selected_type = (
            self.type_filter.currentData()
        )

        filtered = []

        for maintenance in self.maintenances:
            technician = str(
                maintenance.get(
                    "tecnico",
                    "",
                )
                or ""
            ).lower()

            description = str(
                maintenance.get(
                    "descrizione",
                    "",
                )
                or ""
            ).lower()

            maintenance_type = (
                maintenance.get(
                    "tipo"
                )
            )

            if search_text:
                if (
                    search_text not in technician
                    and search_text not in description
                ):
                    continue

            if (
                selected_type is not None
                and maintenance_type
                != selected_type
            ):
                continue

            filtered.append(
                maintenance
            )

        self._populate_table(
            filtered
        )

    # ============================================================
    # TABELLA
    # ============================================================

    def _populate_table(
        self,
        maintenances: list[dict[str, Any]],
    ) -> None:
        self.table.setRowCount(0)

        for maintenance in maintenances:
            row = self.table.rowCount()

            self.table.insertRow(row)

            maintenance_id = maintenance.get(
                "id",
                "-",
            )

            maintenance_date = maintenance.get(
                "data",
                "-",
            )

            maintenance_type = maintenance.get(
                "tipo",
                "-",
            )

            technician = maintenance.get(
                "tecnico",
                "-",
            ) or "-"

            description = maintenance.get(
                "descrizione",
                "-",
            ) or "-"

            next_deadline = maintenance.get(
                "prossima_scadenza"
            )

            # ID
            self.table.setItem(
                row,
                0,
                QTableWidgetItem(
                    str(maintenance_id)
                ),
            )

            # Data
            self.table.setItem(
                row,
                1,
                QTableWidgetItem(
                    self._format_date(
                        maintenance_date
                    )
                ),
            )

            # Tipo
            type_item = QTableWidgetItem(
                self._format_maintenance_type(
                    maintenance_type
                )
            )

            self.table.setItem(
                row,
                2,
                type_item,
            )

            # Tecnico
            self.table.setItem(
                row,
                3,
                QTableWidgetItem(
                    str(technician)
                ),
            )

            # Descrizione
            self.table.setItem(
                row,
                4,
                QTableWidgetItem(
                    str(description)
                ),
            )

            # Scadenza
            deadline_text = (
                self._format_date(
                    next_deadline
                )
                if next_deadline
                else "Nessuna"
            )

            self.table.setItem(
                row,
                5,
                QTableWidgetItem(
                    deadline_text
                ),
            )

            # Stato scadenza
            status_text, status_type = (
                self._get_deadline_status(
                    next_deadline
                )
            )

            status_item = QTableWidgetItem(
                status_text
            )

            self._apply_deadline_style(
                status_item,
                status_type,
            )

            self.table.setItem(
                row,
                6,
                status_item,
            )

        self.status_label.setText(
            f"{len(maintenances)} manutenzione/i visualizzata/e."
        )

    # ============================================================
    # FORMATTAZIONE
    # ============================================================

    @staticmethod
    def _format_date(
        value: Any,
    ) -> str:
        if not value:
            return "-"

        try:
            parsed = date.fromisoformat(
                str(value)
            )

            return parsed.strftime(
                "%d/%m/%Y"
            )

        except ValueError:
            return str(value)

    @staticmethod
    def _format_maintenance_type(
        value: Any,
    ) -> str:
        mapping = {
            "preventiva": "Preventiva",
            "correttiva": "Correttiva",
        }

        return mapping.get(
            str(value),
            str(value) if value else "-",
        )

    @staticmethod
    def _get_deadline_status(
        value: Any,
    ) -> tuple[str, str]:
        """
        Restituisce:

        testo,
        categoria colore:
            none
            ok
            warning
            danger
        """

        if not value:
            return (
                "Nessuna scadenza",
                "none",
            )

        try:
            deadline = date.fromisoformat(
                str(value)
            )

        except ValueError:
            return (
                "Data non valida",
                "danger",
            )

        today = date.today()

        days = (
            deadline - today
        ).days

        if days < 0:
            return (
                f"Scaduta ({abs(days)} gg)",
                "danger",
            )

        if days == 0:
            return (
                "Scade oggi",
                "danger",
            )

        if days <= 30:
            return (
                f"In scadenza ({days} gg)",
                "warning",
            )

        return (
            f"Valida ({days} gg)",
            "ok",
        )

    @staticmethod
    def _apply_deadline_style(
        item: QTableWidgetItem,
        status_type: str,
    ) -> None:
        if status_type == "danger":
            item.setForeground(
                QColor("#b00020")
            )

            item.setFont(
                item.font()
            )

        elif status_type == "warning":
            item.setForeground(
                QColor("#b26a00")
            )

        elif status_type == "ok":
            item.setForeground(
                QColor("#167c35")
            )

    # ============================================================
    # DISPOSITIVO SELEZIONATO
    # ============================================================

    def _get_selected_device(
        self,
    ) -> Optional[dict[str, Any]]:
        if self.current_device_id is None:
            return None

        for device in self.devices:
            if (
                device.get("id")
                == self.current_device_id
            ):
                return device

        return None

    # ============================================================
    # CREA MANUTENZIONE
    # ============================================================

    def create_maintenance(self) -> None:
        """
        Crea una nuova manutenzione.
        """

        if not self.user_session.can_create_maintenances():
            QMessageBox.warning(
                self,
                "Operazione non consentita",
                "Il tuo ruolo non permette "
                "di creare manutenzioni.",
            )
            return

        device = self._get_selected_device()

        if device is None:
            QMessageBox.warning(
                self,
                "Nessun dispositivo",
                "Seleziona prima un dispositivo medico.",
            )
            return

        dialog = MedicalMaintenanceDialog(
            device=device,
            parent=self,
        )

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        payload = dialog.get_form_data()

        try:
            self.api.post(
                f"/dispositivi/"
                f"{self.current_device_id}/manutenzioni",
                json=payload,
            )

            QMessageBox.information(
                self,
                "Manutenzione creata",
                "La manutenzione è stata registrata "
                "correttamente.",
            )

            self.load_maintenances()

        except MedicalAPIAuthenticationError:
            self._show_error(
                "Sessione scaduta",
                "La sessione utente è scaduta. "
                "Effettua nuovamente il login.",
            )

        except MedicalAPIAuthorizationError:
            self._show_error(
                "Accesso negato",
                "Non disponi dei permessi necessari "
                "per creare una manutenzione.",
            )

        except MedicalAPIValidationError as exc:
            self._show_error(
                "Dati non validi",
                str(exc),
            )

        except MedicalAPIServerError as exc:
            self._show_error(
                "Errore del server",
                str(exc),
            )

        except MedicalAPIConnectorError as exc:
            self._show_error(
                "Errore di connessione",
                str(exc),
            )

        except Exception as exc:
            self._show_error(
                "Errore",
                f"Errore imprevisto:\n{exc}",
            )

    # ============================================================
    # DETTAGLI
    # ============================================================

    def show_details(self) -> None:
        """
        Mostra i dettagli della manutenzione selezionata.
        """

        row = self.table.currentRow()

        if row < 0:
            QMessageBox.information(
                self,
                "Selezione",
                "Seleziona una manutenzione "
                "dalla tabella.",
            )
            return

        id_item = self.table.item(
            row,
            0,
        )

        if id_item is None:
            return

        try:
            maintenance_id = int(
                id_item.text()
            )

        except ValueError:
            return

        maintenance = None

        for item in self.maintenances:
            if (
                item.get("id")
                == maintenance_id
            ):
                maintenance = item
                break

        if maintenance is None:
            return

        device = self._get_selected_device()

        device_name = (
            device.get("nome", "-")
            if device
            else "-"
        )

        serial_number = (
            device.get(
                "numero_seriale",
                "-",
            )
            if device
            else "-"
        )

        dialog = QDialog(self)

        dialog.setWindowTitle(
            "Dettagli manutenzione"
        )

        dialog.setMinimumWidth(550)

        layout = QVBoxLayout(dialog)

        title = QLabel(
            "Dettagli della manutenzione"
        )

        title.setStyleSheet(
            """
            QLabel {
                font-size: 20px;
                font-weight: 700;
            }
            """
        )

        layout.addWidget(title)

        form = QFormLayout()

        form.addRow(
            "ID:",
            QLabel(
                str(
                    maintenance.get(
                        "id",
                        "-",
                    )
                )
            ),
        )

        form.addRow(
            "Dispositivo:",
            QLabel(
                str(device_name)
            ),
        )

        form.addRow(
            "Numero seriale:",
            QLabel(
                str(serial_number)
            ),
        )

        form.addRow(
            "Data:",
            QLabel(
                self._format_date(
                    maintenance.get(
                        "data"
                    )
                )
            ),
        )

        form.addRow(
            "Tipo:",
            QLabel(
                self._format_maintenance_type(
                    maintenance.get(
                        "tipo"
                    )
                )
            ),
        )

        form.addRow(
            "Tecnico:",
            QLabel(
                str(
                    maintenance.get(
                        "tecnico"
                    )
                    or "-"
                )
            ),
        )

        form.addRow(
            "Prossima scadenza:",
            QLabel(
                self._format_date(
                    maintenance.get(
                        "prossima_scadenza"
                    )
                )
            ),
        )

        layout.addLayout(form)

        description_label = QLabel(
            "Descrizione:"
        )

        description_label.setStyleSheet(
            "font-weight: 600;"
        )

        layout.addWidget(
            description_label
        )

        description = QPlainTextEdit()

        description.setPlainText(
            str(
                maintenance.get(
                    "descrizione"
                )
                or "Nessuna descrizione."
            )
        )

        description.setReadOnly(True)
        description.setMinimumHeight(120)

        layout.addWidget(
            description
        )

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Close
        )

        buttons.rejected.connect(
            dialog.reject
        )

        buttons.accepted.connect(
            dialog.accept
        )

        layout.addWidget(
            buttons
        )

        dialog.exec()

    # ============================================================
    # REFRESH
    # ============================================================

    def refresh_page(self) -> None:
        """
        Ricarica completamente la pagina.
        """

        self._configure_permissions()
        self.load_devices()

    def showEvent(self, event) -> None:
        """
        Aggiorna la pagina quando viene mostrata.
        """

        super().showEvent(event)

        if not self.devices:
            self.load_devices()

    # ============================================================
    # ERRORI
    # ============================================================

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