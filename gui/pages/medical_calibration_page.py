# gui/pages/medical_calibration_page.py

from __future__ import annotations

from datetime import date
from typing import Any, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
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
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from gui.medical_api_connector import (
    MedicalAPIConnectorError,
    MedicalAPIAuthorizationError,
    MedicalAPIAuthenticationError,
    medical_api_connector,
)

from gui.medical_user_session import (
    MedicalUserSession,
    medical_user_session,
)


class MedicalCalibrationDialog(QDialog):
    """
    Dialog per la creazione di una nuova calibrazione.
    """

    def __init__(
        self,
        device: Optional[dict[str, Any]] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)

        self.device = device or {}

        self.setWindowTitle(
            "Nuova calibrazione"
        )

        self.setMinimumWidth(
            520
        )

        self._build_interface()

    # ============================================================
    # INTERFACCIA
    # ============================================================

    def _build_interface(self) -> None:
        """
        Costruisce il form della calibrazione.
        """

        main_layout = QVBoxLayout(
            self
        )

        main_layout.setContentsMargins(
            20,
            20,
            20,
            20,
        )

        main_layout.setSpacing(
            15
        )

        # ========================================================
        # INFORMAZIONI DISPOSITIVO
        # ========================================================

        device_group = QGroupBox(
            "Dispositivo"
        )

        device_layout = QFormLayout(
            device_group
        )

        device_name = str(
            self.device.get(
                "nome",
                "N/D",
            )
        )

        device_serial = str(
            self.device.get(
                "numero_seriale",
                "N/D",
            )
        )

        self.device_name_label = QLabel(
            device_name
        )

        self.device_name_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )

        self.device_serial_label = QLabel(
            device_serial
        )

        self.device_serial_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )

        device_layout.addRow(
            "Nome:",
            self.device_name_label,
        )

        device_layout.addRow(
            "Numero seriale:",
            self.device_serial_label,
        )

        main_layout.addWidget(
            device_group
        )

        # ========================================================
        # FORM CALIBRAZIONE
        # ========================================================

        calibration_group = QGroupBox(
            "Dati calibrazione"
        )

        form_layout = QFormLayout(
            calibration_group
        )

        # Data calibrazione
        self.date_edit = QDateEdit()

        self.date_edit.setCalendarPopup(
            True
        )

        self.date_edit.setDate(
            self._today_qdate()
        )

        self.date_edit.setDisplayFormat(
            "dd/MM/yyyy"
        )

        form_layout.addRow(
            "Data calibrazione:",
            self.date_edit,
        )

        # Esito
        self.result_combo = QComboBox()

        self.result_combo.addItem(
            "CONFORME",
            "CONFORME",
        )

        self.result_combo.addItem(
            "NON CONFORME",
            "NON_CONFORME",
        )

        form_layout.addRow(
            "Esito:",
            self.result_combo,
        )

        # Ente certificatore
        self.certifier_edit = QLineEdit()

        self.certifier_edit.setPlaceholderText(
            "Es. Laboratorio XYZ"
        )

        form_layout.addRow(
            "Ente certificatore:",
            self.certifier_edit,
        )

        # Prossima scadenza
        self.next_deadline_edit = QDateEdit()

        self.next_deadline_edit.setCalendarPopup(
            True
        )

        self.next_deadline_edit.setDate(
            self._today_qdate()
        )

        self.next_deadline_edit.setDisplayFormat(
            "dd/MM/yyyy"
        )

        form_layout.addRow(
            "Prossima scadenza:",
            self.next_deadline_edit,
        )

        # Nessuna scadenza
        self.no_deadline_button = QPushButton(
            "Nessuna scadenza"
        )

        self.no_deadline_button.setCheckable(
            True
        )

        self.no_deadline_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        self.no_deadline_button.toggled.connect(
            self._toggle_deadline
        )

        form_layout.addRow(
            "",
            self.no_deadline_button,
        )

        main_layout.addWidget(
            calibration_group
        )

        # ========================================================
        # PULSANTI
        # ========================================================

        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )

        self.button_box.accepted.connect(
            self.accept
        )

        self.button_box.rejected.connect(
            self.reject
        )

        main_layout.addWidget(
            self.button_box
        )

    # ============================================================
    # DATA ODIERNA
    # ============================================================

    @staticmethod
    def _today_qdate():
        """
        Restituisce la data odierna come QDate.
        """

        from PySide6.QtCore import QDate

        return QDate.currentDate()

    # ============================================================
    # SCADENZA
    # ============================================================

    def _toggle_deadline(
        self,
        checked: bool,
    ) -> None:
        """
        Abilita/disabilita il campo della prossima scadenza.
        """

        self.next_deadline_edit.setEnabled(
            not checked
        )

    # ============================================================
    # DATI FORM
    # ============================================================

    def get_form_data(self) -> dict[str, Any]:
        """
        Restituisce i dati del form nel formato richiesto
        dall'API.
        """

        calibration_date = (
            self.date_edit
            .date()
            .toString("yyyy-MM-dd")
        )

        result = self.result_combo.currentData()

        if self.no_deadline_button.isChecked():
            next_deadline = None
        else:
            next_deadline = (
                self.next_deadline_edit
                .date()
                .toString("yyyy-MM-dd")
            )

        return {
            "data": calibration_date,
            "esito": result,
            "ente_certificatore": (
                self.certifier_edit
                .text()
                .strip()
                or None
            ),
            "prossima_scadenza": next_deadline,
        }

    # ============================================================
    # VALIDAZIONE
    # ============================================================

    def accept(self) -> None:
        """
        Valida il form prima di confermare.
        """

        certifier = (
            self.certifier_edit
            .text()
            .strip()
        )

        if not certifier:
            QMessageBox.warning(
                self,
                "Dati mancanti",
                "Inserisci l'ente certificatore.",
            )

            self.certifier_edit.setFocus()

            return

        calibration_date = (
            self.date_edit
            .date()
        )

        if not self.no_deadline_button.isChecked():

            next_deadline = (
                self.next_deadline_edit
                .date()
            )

            if next_deadline < calibration_date:

                QMessageBox.warning(
                    self,
                    "Data non valida",
                    "La prossima scadenza non può essere precedente "
                    "alla data della calibrazione.",
                )

                self.next_deadline_edit.setFocus()

                return

        super().accept()


class MedicalCalibrationPage(QWidget):
    """
    Pagina GUI per la gestione delle calibrazioni.

    Funzionalità:
    - selezione dispositivo;
    - visualizzazione calibrazioni;
    - ricerca;
    - filtro per esito;
    - creazione calibrazione;
    - visualizzazione dettagli;
    - gestione delle scadenze;
    - controllo dei permessi.
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

        self.devices: list[dict[str, Any]] = []
        self.calibrations: list[dict[str, Any]] = []

        self._build_interface()
        self._configure_permissions()

    # ============================================================
    # INTERFACCIA
    # ============================================================

    def _build_interface(self) -> None:
        """
        Costruisce l'interfaccia della pagina.
        """

        main_layout = QVBoxLayout(
            self
        )

        main_layout.setContentsMargins(
            30,
            25,
            30,
            25,
        )

        main_layout.setSpacing(
            15
        )

        # ========================================================
        # TITOLO
        # ========================================================

        title = QLabel(
            "Calibrazioni"
        )

        title.setObjectName(
            "pageTitle"
        )

        main_layout.addWidget(
            title
        )

        subtitle = QLabel(
            "Gestione delle calibrazioni e delle verifiche "
            "periodiche dei dispositivi medici."
        )

        subtitle.setObjectName(
            "pageSubtitle"
        )

        subtitle.setWordWrap(
            True
        )

        main_layout.addWidget(
            subtitle
        )

        # ========================================================
        # TOOLBAR
        # ========================================================

        toolbar_layout = QHBoxLayout()

        toolbar_layout.setSpacing(
            10
        )

        # Dispositivo
        device_label = QLabel(
            "Dispositivo:"
        )

        toolbar_layout.addWidget(
            device_label
        )

        self.device_combo = QComboBox()

        self.device_combo.setMinimumWidth(
            280
        )

        self.device_combo.currentIndexChanged.connect(
            self._device_changed
        )

        toolbar_layout.addWidget(
            self.device_combo
        )

        # Ricerca
        self.search_edit = QLineEdit()

        self.search_edit.setPlaceholderText(
            "Cerca per ente certificatore..."
        )

        self.search_edit.setMinimumWidth(
            250
        )

        self.search_edit.textChanged.connect(
            self._apply_filters
        )

        toolbar_layout.addWidget(
            self.search_edit
        )

        # Filtro esito
        self.result_filter = QComboBox()

        self.result_filter.addItem(
            "Tutti gli esiti",
            None,
        )

        self.result_filter.addItem(
            "Conforme",
            "CONFORME",
        )

        self.result_filter.addItem(
            "Non conforme",
            "NON_CONFORME",
        )

        self.result_filter.currentIndexChanged.connect(
            self._apply_filters
        )

        toolbar_layout.addWidget(
            self.result_filter
        )

        toolbar_layout.addStretch()

        # Refresh
        self.refresh_button = QPushButton(
            "Aggiorna"
        )

        self.refresh_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        self.refresh_button.clicked.connect(
            self.refresh_page
        )

        toolbar_layout.addWidget(
            self.refresh_button
        )

        # Nuova calibrazione
        self.new_button = QPushButton(
            "Nuova calibrazione"
        )

        self.new_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        self.new_button.clicked.connect(
            self.create_calibration
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

        self.table.setColumnCount(
            6
        )

        self.table.setHorizontalHeaderLabels(
            [
                "ID",
                "Data",
                "Esito",
                "Ente certificatore",
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

        self.table.setAlternatingRowColors(
            True
        )

        self.table.setSortingEnabled(
            True
        )

        self.table.doubleClicked.connect(
            self.show_details
        )

        header = self.table.horizontalHeader()

        header.setStretchLastSection(
            True
        )

        main_layout.addWidget(
            self.table
        )

        # ========================================================
        # PARTE INFERIORE
        # ========================================================

        bottom_layout = QHBoxLayout()

        self.status_label = QLabel(
            "Nessuna calibrazione caricata."
        )

        self.status_label.setObjectName(
            "statusText"
        )

        bottom_layout.addWidget(
            self.status_label
        )

        bottom_layout.addStretch()

        self.details_button = QPushButton(
            "Dettagli"
        )

        self.details_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        self.details_button.clicked.connect(
            self.show_details
        )

        bottom_layout.addWidget(
            self.details_button
        )

        main_layout.addLayout(
            bottom_layout
        )

    # ============================================================
    # PERMESSI
    # ============================================================

    def _configure_permissions(self) -> None:
        """
        Configura i controlli della pagina in base al ruolo.
        """

        can_create = (
            self.user_session.can_create_calibrations()
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

        devices = (
            self.api_connector.get_devices()
        )

        if not isinstance(
            devices,
            list,
        ):
            devices = []

        self.devices = [
            device
            for device in devices
            if isinstance(
                device,
                dict,
            )
        ]

        current_device_id = (
            self.device_combo.currentData()
        )

        self.device_combo.blockSignals(
            True
        )

        self.device_combo.clear()

        self.device_combo.addItem(
            "Seleziona dispositivo...",
            None,
        )

        for device in self.devices:

            device_id = device.get(
                "id"
            )

            device_name = device.get(
                "nome",
                "Dispositivo",
            )

            serial_number = device.get(
                "numero_seriale"
            )

            if serial_number:

                display_text = (
                    f"{device_name} "
                    f"— SN: {serial_number}"
                )

            else:

                display_text = str(
                    device_name
                )

            self.device_combo.addItem(
                display_text,
                device_id,
            )

        # Mantiene la selezione precedente
        if current_device_id is not None:

            index = (
                self.device_combo.findData(
                    current_device_id
                )
            )

            if index >= 0:

                self.device_combo.setCurrentIndex(
                    index
                )

        self.device_combo.blockSignals(
            False
        )

    # ============================================================
    # CAMBIO DISPOSITIVO
    # ============================================================

    def _device_changed(
        self,
        index: int,
    ) -> None:
        """
        Gestisce il cambio del dispositivo selezionato.
        """

        device_id = (
            self.device_combo.currentData()
        )

        self.calibrations = []

        self.table.setRowCount(
            0
        )

        if device_id is None:

            self.status_label.setText(
                "Seleziona un dispositivo."
            )

            return

        self.load_calibrations(
            device_id
        )

    # ============================================================
    # CARICAMENTO CALIBRAZIONI
    # ============================================================

    def load_calibrations(
        self,
        device_id: int,
    ) -> None:
        """
        Carica le calibrazioni del dispositivo selezionato.
        """

        try:

            calibrations = (
                self.api_connector.get_calibrations(
                    device_id
                )
            )

            if not isinstance(
                calibrations,
                list,
            ):
                calibrations = []

            self.calibrations = [
                calibration
                for calibration in calibrations
                if isinstance(
                    calibration,
                    dict,
                )
            ]

            self._apply_filters()

            self.status_label.setText(
                f"{len(self.calibrations)} calibrazione/i trovata/e."
            )

        except MedicalAPIAuthenticationError:
            raise

        except MedicalAPIAuthorizationError:
            raise

        except MedicalAPIConnectorError:
            raise

        except Exception as exc:

            QMessageBox.warning(
                self,
                "Calibrazioni",
                f"Impossibile caricare le calibrazioni:\n{exc}",
            )

    # ============================================================
    # FILTRI
    # ============================================================

    def _apply_filters(self) -> None:
        """
        Applica ricerca e filtro per esito.
        """

        search_text = (
            self.search_edit
            .text()
            .strip()
            .lower()
        )

        selected_result = (
            self.result_filter.currentData()
        )

        filtered: list[dict[str, Any]] = []

        for calibration in self.calibrations:

            result = calibration.get(
                "esito"
            )

            certifier = str(
                calibration.get(
                    "ente_certificatore",
                    "",
                )
            )

            if selected_result is not None:

                if result != selected_result:
                    continue

            if search_text:

                if search_text not in certifier.lower():

                    continue

            filtered.append(
                calibration
            )

        self._populate_table(
            filtered
        )

    # ============================================================
    # POPOLAMENTO TABELLA
    # ============================================================

    def _populate_table(
        self,
        calibrations: list[dict[str, Any]],
    ) -> None:
        """
        Popola la tabella con le calibrazioni filtrate.
        """

        self.table.setSortingEnabled(
            False
        )

        self.table.setRowCount(
            0
        )

        for calibration in calibrations:

            row = self.table.rowCount()

            self.table.insertRow(
                row
            )

            calibration_id = calibration.get(
                "id",
                "",
            )

            calibration_date = calibration.get(
                "data",
                "",
            )

            result = calibration.get(
                "esito",
                "",
            )

            certifier = calibration.get(
                "ente_certificatore",
                "",
            )

            next_deadline = calibration.get(
                "prossima_scadenza"
            )

            values = [
                str(
                    calibration_id
                ),
                self._format_date(
                    calibration_date
                ),
                self._format_result(
                    result
                ),
                str(
                    certifier or "N/D"
                ),
                self._format_date(
                    next_deadline
                ),
                self._get_deadline_status(
                    next_deadline
                ),
            ]

            for column, value in enumerate(
                values
            ):

                item = QTableWidgetItem(
                    value
                )

                if column == 0:

                    item.setData(
                        Qt.ItemDataRole.UserRole,
                        calibration,
                    )

                self.table.setItem(
                    row,
                    column,
                    item,
                )

        self.table.setSortingEnabled(
            True
        )

        self.table.resizeColumnsToContents()

    # ============================================================
    # FORMATTAZIONE DATA
    # ============================================================

    @staticmethod
    def _format_date(
        value: Any,
    ) -> str:
        """
        Formatta una data ISO nel formato italiano.
        """

        if not value:
            return "—"

        value_string = str(
            value
        )

        try:

            parsed_date = date.fromisoformat(
                value_string
            )

            return parsed_date.strftime(
                "%d/%m/%Y"
            )

        except ValueError:

            return value_string

    # ============================================================
    # FORMATTAZIONE ESITO
    # ============================================================

    @staticmethod
    def _format_result(
        value: Any,
    ) -> str:
        """
        Formatta l'esito della calibrazione.
        """

        if value == "CONFORME":
            return "CONFORME"

        if value == "NON_CONFORME":
            return "NON CONFORME"

        return str(
            value or "N/D"
        )

    # ============================================================
    # STATO SCADENZA
    # ============================================================

    @staticmethod
    def _get_deadline_status(
        value: Any,
    ) -> str:
        """
        Determina lo stato della prossima scadenza.
        """

        if not value:
            return "Nessuna scadenza"

        try:

            deadline = date.fromisoformat(
                str(value)
            )

        except ValueError:

            return "Data non valida"

        today = date.today()

        days_remaining = (
            deadline - today
        ).days

        if days_remaining < 0:

            return (
                f"SCADUTA "
                f"({abs(days_remaining)} gg)"
            )

        if days_remaining == 0:

            return "SCADENZA OGGI"

        if days_remaining <= 30:

            return (
                f"In scadenza "
                f"({days_remaining} gg)"
            )

        return (
            f"Valida "
            f"({days_remaining} gg)"
        )

    # ============================================================
    # DISPOSITIVO SELEZIONATO
    # ============================================================

    def _get_selected_device(
        self,
    ) -> Optional[dict[str, Any]]:
        """
        Restituisce il dispositivo selezionato.
        """

        device_id = (
            self.device_combo.currentData()
        )

        if device_id is None:
            return None

        for device in self.devices:

            if device.get(
                "id"
            ) == device_id:

                return device

        return None

    # ============================================================
    # NUOVA CALIBRAZIONE
    # ============================================================

    def create_calibration(self) -> None:
        """
        Crea una nuova calibrazione.
        """

        if not self.user_session.can_create_calibrations():

            QMessageBox.warning(
                self,
                "Accesso negato",
                "Non disponi dei permessi necessari "
                "per creare una calibrazione.",
            )

            return

        device_id = (
            self.device_combo.currentData()
        )

        if device_id is None:

            QMessageBox.information(
                self,
                "Dispositivo",
                "Seleziona prima un dispositivo.",
            )

            return

        device = (
            self._get_selected_device()
        )

        if device is None:

            QMessageBox.warning(
                self,
                "Dispositivo",
                "Impossibile recuperare il dispositivo selezionato.",
            )

            return

        dialog = MedicalCalibrationDialog(
            device=device,
            parent=self,
        )

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        payload = (
            dialog.get_form_data()
        )

        try:

            self.api_connector.create_calibration(
                device_id,
                payload,
            )

            QMessageBox.information(
                self,
                "Calibrazione",
                "Calibrazione registrata correttamente.",
            )

            self.load_calibrations(
                device_id
            )

        except MedicalAPIAuthenticationError:

            QMessageBox.warning(
                self,
                "Sessione scaduta",
                "La sessione di autenticazione non è più valida.",
            )

            return

        except MedicalAPIAuthorizationError as exc:

            QMessageBox.warning(
                self,
                "Accesso negato",
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
                f"Impossibile registrare la calibrazione:\n{exc}",
            )

    # ============================================================
    # DETTAGLI
    # ============================================================

    def show_details(self) -> None:
        """
        Mostra i dettagli della calibrazione selezionata.
        """

        selected_rows = (
            self.table.selectionModel()
            .selectedRows()
        )

        if not selected_rows:

            QMessageBox.information(
                self,
                "Calibrazione",
                "Seleziona una calibrazione.",
            )

            return

        row = selected_rows[0].row()

        calibration_item = (
            self.table.item(
                row,
                0,
            )
        )

        if calibration_item is None:

            QMessageBox.warning(
                self,
                "Calibrazione",
                "Impossibile recuperare i dati della calibrazione.",
            )

            return

        calibration = (
            calibration_item.data(
                Qt.ItemDataRole.UserRole
            )
        )

        if not isinstance(
            calibration,
            dict,
        ):

            QMessageBox.warning(
                self,
                "Calibrazione",
                "Dati della calibrazione non validi.",
            )

            return

        self._show_calibration_details(
            calibration
        )

    # ============================================================
    # DIALOG DETTAGLI
    # ============================================================

    def _show_calibration_details(
        self,
        calibration: dict[str, Any],
    ) -> None:
        """
        Mostra una finestra con i dettagli completi.
        """

        dialog = QDialog(
            self
        )

        dialog.setWindowTitle(
            "Dettagli calibrazione"
        )

        dialog.setMinimumWidth(
            500
        )

        layout = QVBoxLayout(
            dialog
        )

        layout.setContentsMargins(
            20,
            20,
            20,
            20,
        )

        layout.setSpacing(
            12
        )

        title = QLabel(
            "Dettagli della calibrazione"
        )

        title.setObjectName(
            "sectionTitle"
        )

        layout.addWidget(
            title
        )

        form_layout = QFormLayout()

        form_layout.addRow(
            "ID:",
            QLabel(
                str(
                    calibration.get(
                        "id",
                        "N/D",
                    )
                )
            ),
        )

        form_layout.addRow(
            "Data:",
            QLabel(
                self._format_date(
                    calibration.get(
                        "data"
                    )
                )
            ),
        )

        form_layout.addRow(
            "Esito:",
            QLabel(
                self._format_result(
                    calibration.get(
                        "esito"
                    )
                )
            ),
        )

        form_layout.addRow(
            "Ente certificatore:",
            QLabel(
                str(
                    calibration.get(
                        "ente_certificatore"
                    )
                    or "N/D"
                )
            ),
        )

        form_layout.addRow(
            "Prossima scadenza:",
            QLabel(
                self._format_date(
                    calibration.get(
                        "prossima_scadenza"
                    )
                )
            ),
        )

        form_layout.addRow(
            "Stato scadenza:",
            QLabel(
                self._get_deadline_status(
                    calibration.get(
                        "prossima_scadenza"
                    )
                )
            ),
        )

        layout.addLayout(
            form_layout
        )

        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Close
        )

        button_box.rejected.connect(
            dialog.reject
        )

        button_box.accepted.connect(
            dialog.accept
        )

        layout.addWidget(
            button_box
        )

        dialog.exec()

    # ============================================================
    # REFRESH
    # ============================================================

    def refresh_page(self) -> None:
        """
        Aggiorna completamente la pagina.
        """

        try:

            self.load_devices()

            device_id = (
                self.device_combo.currentData()
            )

            if device_id is None:

                self.calibrations = []

                self.table.setRowCount(
                    0
                )

                self.status_label.setText(
                    "Seleziona un dispositivo."
                )

                return

            self.load_calibrations(
                device_id
            )

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
                "Calibrazioni",
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
        Aggiorna la pagina quando viene visualizzata.
        """

        super().showEvent(
            event
        )

        if not self.devices:

            try:
                self.refresh_page()

            except Exception:
                pass