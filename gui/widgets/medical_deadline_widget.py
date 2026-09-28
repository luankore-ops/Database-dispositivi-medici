from __future__ import annotations

from datetime import date, datetime
from typing import Any, Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QFrame,
    QHeaderView,
    QHBoxLayout,
    QLabel,
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
    medical_api_connector,
)


class MedicalDeadlineWidget(QWidget):
    """
    Widget per la visualizzazione delle scadenze di
    manutenzione e calibrazione.

    Funzionalità:
    - visualizzazione delle scadenze;
    - classificazione per urgenza;
    - filtri temporali;
    - contatori;
    - ordinamento per data;
    - aggiornamento manuale;
    - colorazione uniforme delle righe.
    """

    def __init__(
        self,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)

        self.api_connector = medical_api_connector

        self.deadlines: list[dict[str, Any]] = []

        self._build_interface()

    # ==============================================================
    # INTERFACCIA
    # ==============================================================

    def _build_interface(self) -> None:
        self.setObjectName(
            "medicalDeadlineWidget"
        )

        self.setStyleSheet(
            """
            QWidget#medicalDeadlineWidget {
                background-color: #111827;
                color: #f9fafb;
            }

            QLabel#deadlineSectionTitle {
                color: #f9fafb;
                font-size: 18px;
                font-weight: 700;
            }

            QLabel#deadlineSectionSubtitle {
                color: #9ca3af;
                font-size: 12px;
            }

            QLabel#deadlineStatus {
                color: #9ca3af;
                font-size: 12px;
            }

            QFrame#counterCard {
                background-color: #1f2937;
                border: 1px solid #374151;
                border-radius: 8px;
            }

            QLabel#counterTitle {
                color: #9ca3af;
                font-size: 11px;
                font-weight: 600;
            }

            QLabel#counterValue {
                color: #f9fafb;
                font-size: 20px;
                font-weight: 700;
            }

            QComboBox#deadlineFilter {
                background-color: #1f2937;
                color: #f9fafb;
                border: 1px solid #374151;
                border-radius: 6px;
                padding: 7px 10px;
                min-width: 150px;
            }

            QComboBox#deadlineFilter:hover {
                border: 1px solid #4b5563;
            }

            QComboBox#deadlineFilter QAbstractItemView {
                background-color: #1f2937;
                color: #f9fafb;
                selection-background-color: #374151;
                selection-color: #ffffff;
            }

            QPushButton#refreshDeadlineButton {
                background-color: #2563eb;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 14px;
                font-size: 12px;
                font-weight: 600;
            }

            QPushButton#refreshDeadlineButton:hover {
                background-color: #1d4ed8;
            }

            QTableWidget#deadlineTable {
                background-color: #1f2937;
                color: #f9fafb;
                border: 1px solid #374151;
                border-radius: 8px;
                gridline-color: #374151;
                selection-background-color: #374151;
                selection-color: #ffffff;
                alternate-background-color: #1f2937;
            }

            QTableWidget#deadlineTable::item {
                padding: 8px;
                border: none;
            }

            QTableWidget#deadlineTable::item:selected {
                background-color: #374151;
                color: #ffffff;
            }

            QHeaderView::section {
                background-color: #0f172a;
                color: #d1d5db;
                border: none;
                border-bottom: 1px solid #374151;
                padding: 8px;
                font-weight: 600;
            }
            """
        )

        main_layout = QVBoxLayout(self)

        main_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        main_layout.setSpacing(
            12
        )

        # ==========================================================
        # HEADER
        # ==========================================================

        header_layout = QHBoxLayout()

        title_container = QVBoxLayout()

        title_container.setSpacing(
            3
        )

        title = QLabel(
            "Scadenze imminenti"
        )

        title.setObjectName(
            "deadlineSectionTitle"
        )

        title_container.addWidget(
            title
        )

        subtitle = QLabel(
            "Manutenzioni e calibrazioni che richiedono attenzione."
        )

        subtitle.setObjectName(
            "deadlineSectionSubtitle"
        )

        title_container.addWidget(
            subtitle
        )

        header_layout.addLayout(
            title_container
        )

        header_layout.addStretch()

        # ----------------------------------------------------------
        # FILTRO
        # ----------------------------------------------------------

        self.filter_combo = QComboBox()

        self.filter_combo.setObjectName(
            "deadlineFilter"
        )

        self.filter_combo.addItem(
            "Tutte le scadenze",
            "all",
        )

        self.filter_combo.addItem(
            "Scadute",
            "expired",
        )

        self.filter_combo.addItem(
            "Entro 7 giorni",
            "7",
        )

        self.filter_combo.addItem(
            "Entro 30 giorni",
            "30",
        )

        self.filter_combo.addItem(
            "Entro 90 giorni",
            "90",
        )

        self.filter_combo.currentIndexChanged.connect(
            self._apply_filter
        )

        header_layout.addWidget(
            self.filter_combo
        )

        # ----------------------------------------------------------
        # AGGIORNA
        # ----------------------------------------------------------

        self.refresh_button = QPushButton(
            "Aggiorna"
        )

        self.refresh_button.setObjectName(
            "refreshDeadlineButton"
        )

        self.refresh_button.clicked.connect(
            self.refresh
        )

        header_layout.addWidget(
            self.refresh_button
        )

        main_layout.addLayout(
            header_layout
        )

        # ==========================================================
        # CONTATORI
        # ==========================================================

        counters_layout = QHBoxLayout()

        self.expired_counter = self._create_counter(
            "Scadute"
        )

        self.seven_days_counter = self._create_counter(
            "Entro 7 giorni"
        )

        self.thirty_days_counter = self._create_counter(
            "Entro 30 giorni"
        )

        self.ninety_days_counter = self._create_counter(
            "Entro 90 giorni"
        )

        counters_layout.addWidget(
            self.expired_counter
        )

        counters_layout.addWidget(
            self.seven_days_counter
        )

        counters_layout.addWidget(
            self.thirty_days_counter
        )

        counters_layout.addWidget(
            self.ninety_days_counter
        )

        main_layout.addLayout(
            counters_layout
        )

        # ==========================================================
        # TABELLA
        # ==========================================================

        self.table = QTableWidget()

        self.table.setObjectName(
            "deadlineTable"
        )

        self.table.setColumnCount(
            5
        )

        self.table.setHorizontalHeaderLabels(
            [
                "Stato",
                "Tipo",
                "Dispositivo",
                "Scadenza",
                "Giorni",
            ]
        )

        # Disabilitiamo completamente le righe alternate.
        self.table.setAlternatingRowColors(
            False
        )

        # Selezione dell'intera riga.
        self.table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )

        self.table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )

        # Tabella non modificabile.
        self.table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )

        self.table.verticalHeader().setVisible(
            False
        )

        self.table.horizontalHeader().setStretchLastSection(
            False
        )

        self.table.setMinimumHeight(
            220
        )

        main_layout.addWidget(
            self.table
        )

        # ==========================================================
        # STATO
        # ==========================================================

        self.status_label = QLabel(
            "Scadenze non ancora caricate."
        )

        self.status_label.setObjectName(
            "deadlineStatus"
        )

        main_layout.addWidget(
            self.status_label
        )

    # ==============================================================
    # CONTATORI
    # ==============================================================

    def _create_counter(
        self,
        title: str,
    ) -> QFrame:
        frame = QFrame()

        frame.setObjectName(
            "counterCard"
        )

        layout = QVBoxLayout(
            frame
        )

        layout.setContentsMargins(
            12,
            10,
            12,
            10,
        )

        layout.setSpacing(
            2
        )

        title_label = QLabel(
            title
        )

        title_label.setObjectName(
            "counterTitle"
        )

        layout.addWidget(
            title_label
        )

        value_label = QLabel(
            "0"
        )

        value_label.setObjectName(
            "counterValue"
        )

        font = QFont(
            "Segoe UI",
            20,
        )

        font.setBold(
            True
        )

        value_label.setFont(
            font
        )

        layout.addWidget(
            value_label
        )

        frame.value_label = value_label

        return frame

    def _update_counters(
        self,
        normalized_deadlines: list[
            tuple[
                dict[str, Any],
                date,
                int,
            ]
        ],
    ) -> None:
        expired = 0
        seven_days = 0
        thirty_days = 0
        ninety_days = 0

        for (
            _deadline,
            _deadline_date,
            days_remaining,
        ) in normalized_deadlines:

            if days_remaining < 0:
                expired += 1

            elif days_remaining <= 7:
                seven_days += 1

            elif days_remaining <= 30:
                thirty_days += 1

            elif days_remaining <= 90:
                ninety_days += 1

        self.expired_counter.value_label.setText(
            str(expired)
        )

        self.seven_days_counter.value_label.setText(
            str(seven_days)
        )

        self.thirty_days_counter.value_label.setText(
            str(thirty_days)
        )

        self.ninety_days_counter.value_label.setText(
            str(ninety_days)
        )

    # ==============================================================
    # REFRESH
    # ==============================================================

    def refresh(self) -> None:
        self.refresh_button.setEnabled(
            False
        )

        self.status_label.setText(
            "Caricamento scadenze..."
        )

        try:
            deadlines = (
                self.api_connector.get_deadlines()
            )

            if not isinstance(
                deadlines,
                list,
            ):
                deadlines = []

            self.deadlines = [
                item
                for item in deadlines
                if isinstance(
                    item,
                    dict,
                )
            ]

            self._populate_table()

        except MedicalAPIAuthenticationError:
            self.status_label.setText(
                "Sessione non valida."
            )

        except MedicalAPIAuthorizationError:
            self.status_label.setText(
                "Non disponi dei permessi necessari."
            )

        except MedicalAPIConnectorError as exc:
            self.status_label.setText(
                f"Errore API: {exc}"
            )

        except Exception as exc:
            self.status_label.setText(
                f"Errore inatteso: {exc}"
            )

        finally:
            self.refresh_button.setEnabled(
                True
            )

    # ==============================================================
    # NORMALIZZAZIONE
    # ==============================================================

    def _normalize_deadlines(
        self,
    ) -> list[
        tuple[
            dict[str, Any],
            date,
            int,
        ]
    ]:
        today = date.today()

        normalized = []

        for deadline in self.deadlines:

            deadline_date = self._extract_date(
                deadline
            )

            if deadline_date is None:
                continue

            days_remaining = (
                deadline_date - today
            ).days

            normalized.append(
                (
                    deadline,
                    deadline_date,
                    days_remaining,
                )
            )

        normalized.sort(
            key=lambda item: item[2]
        )

        return normalized

    # ==============================================================
    # POPOLAMENTO TABELLA
    # ==============================================================

    def _populate_table(self) -> None:
        normalized_deadlines = (
            self._normalize_deadlines()
        )

        self._update_counters(
            normalized_deadlines
        )

        self._render_table(
            normalized_deadlines
        )

    def _render_table(
        self,
        normalized_deadlines: list[
            tuple[
                dict[str, Any],
                date,
                int,
            ]
        ],
    ) -> None:

        selected_filter = (
            self.filter_combo.currentData()
        )

        filtered_deadlines = []

        for item in normalized_deadlines:

            days_remaining = item[2]

            if selected_filter == "expired":

                if days_remaining < 0:
                    filtered_deadlines.append(
                        item
                    )

            elif selected_filter == "7":

                if 0 <= days_remaining <= 7:
                    filtered_deadlines.append(
                        item
                    )

            elif selected_filter == "30":

                if 0 <= days_remaining <= 30:
                    filtered_deadlines.append(
                        item
                    )

            elif selected_filter == "90":

                if 0 <= days_remaining <= 90:
                    filtered_deadlines.append(
                        item
                    )

            else:
                filtered_deadlines.append(
                    item
                )

        # Dashboard: massimo 15 elementi.
        filtered_deadlines = (
            filtered_deadlines[:15]
        )

        self.table.setRowCount(
            0
        )

        self.table.setRowCount(
            len(filtered_deadlines)
        )

        for row, (
            deadline,
            deadline_date,
            days_remaining,
        ) in enumerate(
            filtered_deadlines
        ):

            self._add_table_row(
                row=row,
                deadline=deadline,
                deadline_date=deadline_date,
                days_remaining=days_remaining,
            )

        self._resize_columns()

        self._update_status(
            len(filtered_deadlines),
            selected_filter,
            len(normalized_deadlines),
        )

    # ==============================================================
    # RIGA
    # ==============================================================

    def _add_table_row(
        self,
        row: int,
        deadline: dict[str, Any],
        deadline_date: date,
        days_remaining: int,
    ) -> None:

        status_text = self._status_text(
            days_remaining
        )

        deadline_type = self._extract_type(
            deadline
        )

        device_name = self._extract_device_name(
            deadline
        )

        date_text = deadline_date.strftime(
            "%d/%m/%Y"
        )

        days_text = self._days_text(
            days_remaining
        )

        values = [
            status_text,
            deadline_type,
            device_name,
            date_text,
            days_text,
        ]

        background, foreground = (
            self._get_row_colors(
                days_remaining
            )
        )

        for column, value in enumerate(
            values
        ):

            item = QTableWidgetItem(
                value
            )

            item.setBackground(
                QColor(background)
            )

            item.setForeground(
                QColor(foreground)
            )

            if column in (
                0,
                1,
                3,
                4,
            ):
                item.setTextAlignment(
                    Qt.AlignmentFlag.AlignCenter
                    | Qt.AlignmentFlag.AlignVCenter
                )

            else:
                item.setTextAlignment(
                    Qt.AlignmentFlag.AlignVCenter
                )

            self.table.setItem(
                row,
                column,
                item
            )

    # ==============================================================
    # COLORI RIGA
    # ==============================================================

    @staticmethod
    def _get_row_colors(
        days_remaining: int,
    ) -> tuple[str, str]:

        if days_remaining < 0:
            # Scaduta
            return (
                "#4a2424",
                "#fecaca",
            )

        if days_remaining <= 7:
            # Urgente
            return (
                "#4a3520",
                "#fed7aa",
            )

        if days_remaining <= 30:
            # Attenzione
            return (
                "#4a431f",
                "#fef08a",
            )

        # Entro 90 giorni / oltre
        return (
            "#24384d",
            "#bfdbfe",
        )

    # ==============================================================
    # FILTRO
    # ==============================================================

    def _apply_filter(
        self,
    ) -> None:

        normalized_deadlines = (
            self._normalize_deadlines()
        )

        self._render_table(
            normalized_deadlines
        )

    # ==============================================================
    # STATUS
    # ==============================================================

    def _update_status(
        self,
        visible_count: int,
        selected_filter: Any,
        total_count: int,
    ) -> None:

        if total_count == 0:
            self.status_label.setText(
                "Nessuna scadenza disponibile."
            )
            return

        if selected_filter == "expired":
            label = "scadute"

        elif selected_filter == "7":
            label = "entro 7 giorni"

        elif selected_filter == "30":
            label = "entro 30 giorni"

        elif selected_filter == "90":
            label = "entro 90 giorni"

        else:
            label = "totali"

        self.status_label.setText(
            f"{visible_count} scadenze visualizzate "
            f"({label}). Totale registrato: {total_count}."
        )

    # ==============================================================
    # ESTRAZIONE DATA
    # ==============================================================

    @staticmethod
    def _extract_date(
        deadline: dict[str, Any],
    ) -> Optional[date]:

        possible_fields = [
            "data_scadenza",
            "scadenza",
            "prossima_scadenza",
            "deadline",
            "date",
        ]

        value = None

        for field in possible_fields:

            if field in deadline:
                value = deadline.get(
                    field
                )

                if value:
                    break

        if value is None:
            return None

        if isinstance(
            value,
            datetime,
        ):
            return value.date()

        if isinstance(
            value,
            date,
        ):
            return value

        if isinstance(
            value,
            str,
        ):

            value = value.strip()

            try:
                return datetime.fromisoformat(
                    value.replace(
                        "Z",
                        "+00:00",
                    )
                ).date()

            except ValueError:
                pass

            try:
                return date.fromisoformat(
                    value
                )

            except ValueError:
                pass

            try:
                return datetime.strptime(
                    value,
                    "%d/%m/%Y",
                ).date()

            except ValueError:
                pass

        return None

    # ==============================================================
    # TIPO
    # ==============================================================

    @staticmethod
    def _extract_type(
        deadline: dict[str, Any],
    ) -> str:

        for field in (
            "tipo",
            "type",
            "tipo_scadenza",
        ):

            value = deadline.get(
                field
            )

            if not value:
                continue

            if isinstance(
                value,
                dict,
            ):
                value = value.get(
                    "value",
                    value.get(
                        "name",
                        "",
                    ),
                )

            text = str(
                value
            ).upper()

            if "MANUT" in text:
                return "Manutenzione"

            if "CALIB" in text:
                return "Calibrazione"

            return str(
                value
            )

        return "Scadenza"

    # ==============================================================
    # DISPOSITIVO
    # ==============================================================

    @staticmethod
    def _extract_device_name(
        deadline: dict[str, Any],
    ) -> str:

        for field in (
            "dispositivo_nome",
            "device_name",
            "nome_dispositivo",
            "dispositivo",
            "device",
            "nome",
        ):

            value = deadline.get(
                field
            )

            if not value:
                continue

            if isinstance(
                value,
                dict,
            ):

                for nested_field in (
                    "nome",
                    "name",
                    "nome_dispositivo",
                ):

                    nested_value = value.get(
                        nested_field
                    )

                    if nested_value:
                        return str(
                            nested_value
                        )

            else:
                return str(
                    value
                )

        device_id = deadline.get(
            "dispositivo_id"
        )

        if device_id is not None:
            return (
                f"Dispositivo #{device_id}"
            )

        return "Dispositivo non specificato"

    # ==============================================================
    # STATO
    # ==============================================================

    @staticmethod
    def _status_text(
        days_remaining: int,
    ) -> str:

        if days_remaining < 0:
            return "SCADUTA"

        if days_remaining == 0:
            return "OGGI"

        if days_remaining <= 7:
            return "ENTRO 7 GG"

        if days_remaining <= 30:
            return "ENTRO 30 GG"

        return "ENTRO 90 GG"

    # ==============================================================
    # GIORNI
    # ==============================================================

    @staticmethod
    def _days_text(
        days_remaining: int,
    ) -> str:

        if days_remaining < 0:

            days = abs(
                days_remaining
            )

            if days == 1:
                return "1 giorno fa"

            return f"{days} giorni fa"

        if days_remaining == 0:
            return "Oggi"

        if days_remaining == 1:
            return "1 giorno"

        return f"{days_remaining} giorni"

    # ==============================================================
    # COLONNE
    # ==============================================================

    def _resize_columns(self) -> None:

        header = (
            self.table.horizontalHeader()
        )

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
            QHeaderView.ResizeMode.Stretch,
        )

        header.setSectionResizeMode(
            3,
            QHeaderView.ResizeMode.ResizeToContents,
        )

        header.setSectionResizeMode(
            4,
            QHeaderView.ResizeMode.ResizeToContents,
        )