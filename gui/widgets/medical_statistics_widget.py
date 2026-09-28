from __future__ import annotations

from typing import Any, Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from gui.medical_api_connector import (
    MedicalAPIAuthenticationError,
    MedicalAPIAuthorizationError,
    MedicalAPIConnectorError,
    medical_api_connector,
)


class MedicalStatisticsCard(QFrame):
    """
    Card grafica utilizzata per visualizzare una statistica.
    """

    def __init__(
        self,
        title: str,
        value: str = "0",
        description: str = "",
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)

        self.setObjectName(
            "statisticsCard"
        )

        self.setMinimumHeight(
            130
        )

        self._build_interface(
            title=title,
            value=value,
            description=description,
        )

    def _build_interface(
        self,
        title: str,
        value: str,
        description: str,
    ) -> None:
        layout = QVBoxLayout(
            self
        )

        layout.setContentsMargins(
            20,
            18,
            20,
            18,
        )

        layout.setSpacing(
            8
        )

        # ----------------------------------------------------------
        # TITOLO CARD
        # ----------------------------------------------------------

        self.title_label = QLabel(
            title
        )

        self.title_label.setObjectName(
            "statisticsTitle"
        )

        layout.addWidget(
            self.title_label
        )

        # ----------------------------------------------------------
        # VALORE
        # ----------------------------------------------------------

        self.value_label = QLabel(
            value
        )

        self.value_label.setObjectName(
            "statisticsValue"
        )

        value_font = QFont(
            "Segoe UI",
            28,
        )

        value_font.setBold(
            True
        )

        self.value_label.setFont(
            value_font
        )

        layout.addWidget(
            self.value_label
        )

        # ----------------------------------------------------------
        # DESCRIZIONE
        # ----------------------------------------------------------

        self.description_label = QLabel(
            description
        )

        self.description_label.setObjectName(
            "statisticsDescription"
        )

        layout.addWidget(
            self.description_label
        )

        layout.addStretch()

    def set_value(
        self,
        value: int | str,
    ) -> None:
        self.value_label.setText(
            str(value)
        )

    def set_description(
        self,
        description: str,
    ) -> None:
        self.description_label.setText(
            description
        )


class MedicalStatisticsWidget(QWidget):
    """
    Dashboard statistica dei dispositivi medici.

    Visualizza:
    - totale dispositivi;
    - dispositivi in uso;
    - dispositivi in manutenzione;
    - dispositivi guasti;
    - dispositivi dismessi;
    - percentuale di dispositivi attivi;
    - ultimo aggiornamento.
    """

    def __init__(
        self,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(
            parent
        )

        self.api_connector = medical_api_connector

        self.devices: list[
            dict[str, Any]
        ] = []

        self._build_interface()

    # ============================================================
    # INTERFACCIA
    # ============================================================

    def _build_interface(self) -> None:
        self.setObjectName(
            "medicalStatisticsWidget"
        )

        self.setStyleSheet(
            """
            /* ======================================================
               CONTENITORE PRINCIPALE
               ====================================================== */

            QWidget#medicalStatisticsWidget {
                background-color: #111827;
                color: #f9fafb;
            }

            /* ======================================================
               CARD
               ====================================================== */

            QFrame#statisticsCard {
                background-color: #1f2937;
                border: 1px solid #374151;
                border-radius: 10px;
            }

            /* ======================================================
               TITOLO DELLE CARD
               ====================================================== */

            QLabel#statisticsTitle {
                color: #e5e7eb;
                font-size: 13px;
                font-weight: 600;
            }

            /* ======================================================
               VALORE DELLE CARD
               ====================================================== */

            QLabel#statisticsValue {
                color: #ffffff;
                font-size: 28px;
                font-weight: 700;
            }

            /* ======================================================
               DESCRIZIONE DELLE CARD
               ====================================================== */

            QLabel#statisticsDescription {
                color: #d1d5db;
                font-size: 11px;
            }

            /* ======================================================
               TITOLO SEZIONE
               ====================================================== */

            QLabel#sectionTitle {
                color: #ffffff;
                font-size: 18px;
                font-weight: 700;
            }

            /* ======================================================
               SOTTOTITOLO SEZIONE
               ====================================================== */

            QLabel#sectionSubtitle {
                color: #d1d5db;
                font-size: 12px;
            }

            /* ======================================================
               MESSAGGIO DI STATO
               ====================================================== */

            QLabel#statusMessage {
                color: #d1d5db;
                font-size: 12px;
            }

            /* ======================================================
               PULSANTE AGGIORNA
               ====================================================== */

            QPushButton#refreshStatisticsButton {
                background-color: #2563eb;
                color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 8px 14px;
                font-size: 12px;
                font-weight: 600;
            }

            QPushButton#refreshStatisticsButton:hover {
                background-color: #1d4ed8;
            }

            QPushButton#refreshStatisticsButton:pressed {
                background-color: #1e40af;
            }

            QPushButton#refreshStatisticsButton:disabled {
                background-color: #374151;
                color: #9ca3af;
            }
            """
        )

        main_layout = QVBoxLayout(
            self
        )

        main_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        main_layout.setSpacing(
            16
        )

        # ============================================================
        # HEADER
        # ============================================================

        header_layout = QHBoxLayout()

        title_container = QVBoxLayout()

        title_container.setSpacing(
            4
        )

        # ------------------------------------------------------------
        # Titolo
        # ------------------------------------------------------------

        title = QLabel(
            "Panoramica dispositivi"
        )

        title.setObjectName(
            "sectionTitle"
        )

        title_container.addWidget(
            title
        )

        # ------------------------------------------------------------
        # Sottotitolo
        # ------------------------------------------------------------

        subtitle = QLabel(
            "Situazione attuale dell'inventario dei dispositivi medici."
        )

        subtitle.setObjectName(
            "sectionSubtitle"
        )

        title_container.addWidget(
            subtitle
        )

        header_layout.addLayout(
            title_container
        )

        header_layout.addStretch()

        # ------------------------------------------------------------
        # Pulsante aggiornamento
        # ------------------------------------------------------------

        self.refresh_button = QPushButton(
            "Aggiorna statistiche"
        )

        self.refresh_button.setObjectName(
            "refreshStatisticsButton"
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

        # ============================================================
        # CARDS
        # ============================================================

        cards_layout = QGridLayout()

        cards_layout.setSpacing(
            14
        )

        # ------------------------------------------------------------
        # Totale
        # ------------------------------------------------------------

        self.total_card = MedicalStatisticsCard(
            title="Totale dispositivi",
            value="0",
            description="Dispositivi presenti nel database.",
        )

        # ------------------------------------------------------------
        # In uso
        # ------------------------------------------------------------

        self.in_use_card = MedicalStatisticsCard(
            title="In uso",
            value="0",
            description="Dispositivi attualmente operativi.",
        )

        # ------------------------------------------------------------
        # Manutenzione
        # ------------------------------------------------------------

        self.maintenance_card = MedicalStatisticsCard(
            title="In manutenzione",
            value="0",
            description="Dispositivi attualmente in manutenzione.",
        )

        # ------------------------------------------------------------
        # Guasti
        # ------------------------------------------------------------

        self.faulty_card = MedicalStatisticsCard(
            title="Guasti",
            value="0",
            description="Dispositivi con stato guasto.",
        )

        # ------------------------------------------------------------
        # Dismessi
        # ------------------------------------------------------------

        self.retired_card = MedicalStatisticsCard(
            title="Dismessi",
            value="0",
            description="Dispositivi fuori servizio.",
        )

        # ------------------------------------------------------------
        # Dispositivi attivi
        # ------------------------------------------------------------

        self.active_percentage_card = MedicalStatisticsCard(
            title="Dispositivi attivi",
            value="0%",
            description="Percentuale rispetto al totale.",
        )

        # ------------------------------------------------------------
        # Inserimento nella griglia
        # ------------------------------------------------------------

        cards_layout.addWidget(
            self.total_card,
            0,
            0,
        )

        cards_layout.addWidget(
            self.in_use_card,
            0,
            1,
        )

        cards_layout.addWidget(
            self.maintenance_card,
            0,
            2,
        )

        cards_layout.addWidget(
            self.faulty_card,
            1,
            0,
        )

        cards_layout.addWidget(
            self.retired_card,
            1,
            1,
        )

        cards_layout.addWidget(
            self.active_percentage_card,
            1,
            2,
        )

        main_layout.addLayout(
            cards_layout
        )

        # ============================================================
        # STATO
        # ============================================================

        status_layout = QHBoxLayout()

        self.status_label = QLabel(
            "Statistiche non ancora caricate."
        )

        self.status_label.setObjectName(
            "statusMessage"
        )

        status_layout.addWidget(
            self.status_label
        )

        status_layout.addStretch()

        main_layout.addLayout(
            status_layout
        )

        main_layout.addStretch()

    # ============================================================
    # CARICAMENTO DATI
    # ============================================================

    def refresh(self) -> None:
        """
        Recupera i dispositivi dall'API e aggiorna le statistiche.
        """

        self.status_label.setText(
            "Caricamento statistiche..."
        )

        self.refresh_button.setEnabled(
            False
        )

        try:
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

            self._update_statistics()

            self.status_label.setText(
                "Statistiche aggiornate correttamente."
            )

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
                f"Errore nel caricamento: {exc}"
            )

        except Exception as exc:
            self.status_label.setText(
                f"Errore inatteso: {exc}"
            )

        finally:
            self.refresh_button.setEnabled(
                True
            )

    # ============================================================
    # CALCOLO STATISTICHE
    # ============================================================

    def _update_statistics(self) -> None:
        total = len(
            self.devices
        )

        in_use = 0
        maintenance = 0
        faulty = 0
        retired = 0

        for device in self.devices:
            status = device.get(
                "stato"
            )

            if isinstance(
                status,
                dict,
            ):
                status = status.get(
                    "value"
                )

            status = str(
                status
            )

            if status == "IN_USO":
                in_use += 1

            elif status == "MANUTENZIONE":
                maintenance += 1

            elif status == "GUASTO":
                faulty += 1

            elif status == "DISMESSO":
                retired += 1

        active_devices = (
            in_use
            + maintenance
            + faulty
        )

        if total > 0:
            active_percentage = (
                active_devices
                / total
                * 100
            )
        else:
            active_percentage = 0.0

        self.total_card.set_value(
            total
        )

        self.in_use_card.set_value(
            in_use
        )

        self.maintenance_card.set_value(
            maintenance
        )

        self.faulty_card.set_value(
            faulty
        )

        self.retired_card.set_value(
            retired
        )

        self.active_percentage_card.set_value(
            f"{active_percentage:.1f}%"
        )

    # ============================================================
    # DATI ESTERNI
    # ============================================================

    def set_devices(
        self,
        devices: list[dict[str, Any]],
    ) -> None:
        """
        Permette alla Dashboard di passare direttamente
        una lista di dispositivi già caricata.
        """

        self.devices = [
            device
            for device in devices
            if isinstance(
                device,
                dict,
            )
        ]

        self._update_statistics()