"""
main_window.py — Finestra principale dell'applicazione desktop
"""

import requests
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QTableWidget,
    QTableWidgetItem, QPushButton, QLabel, QLineEdit, QComboBox, QHeaderView,
    QMessageBox, QStatusBar, QFileDialog,
)
from PySide6.QtGui import QColor

from api_client import ApiClient
from dialogs import (
    NuovoDispositivoDialog, ModificaDispositivoDialog, DettaglioDispositivoDialog,
    NuovaManutenzioneDialog, NuovaCalibrazioneDialog, NuovoRepartoDialog,
)
import export

STATI_DISPOSITIVO = ["in_uso", "manutenzione", "guasto", "dismesso"]

COLORE_GUASTO = QColor(255, 205, 210)
COLORE_MANUTENZIONE = QColor(255, 236, 179)
COLORE_SCADUTO = QColor(239, 154, 154)
COLORE_URGENTE = QColor(255, 224, 130)


class DispositiviTab(QWidget):
    def __init__(self, client: ApiClient, status_bar: QStatusBar):
        super().__init__()
        self.client = client
        self.status_bar = status_bar
        self.dispositivi_correnti: list = []
        self._build_ui()
        self.aggiorna_tabella()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        # Barra filtri + azioni
        barra = QHBoxLayout()
        self.filtro_categoria = QLineEdit()
        self.filtro_categoria.setPlaceholderText("Filtra per categoria...")
        self.filtro_categoria.returnPressed.connect(self.aggiorna_tabella)
        self.filtro_stato = QComboBox()
        self.filtro_stato.addItem("Tutti gli stati", None)
        for s in STATI_DISPOSITIVO:
            self.filtro_stato.addItem(s, s)
        self.filtro_stato.currentIndexChanged.connect(self.aggiorna_tabella)

        btn_nuovo = QPushButton("+ Nuovo dispositivo")
        btn_nuovo.clicked.connect(self.nuovo_dispositivo)
        btn_modifica = QPushButton("Modifica selezionato")
        btn_modifica.clicked.connect(self.modifica_selezionato)
        btn_manutenzione = QPushButton("+ Registra manutenzione")
        btn_manutenzione.clicked.connect(self.nuova_manutenzione)
        btn_calibrazione = QPushButton("+ Registra calibrazione")
        btn_calibrazione.clicked.connect(self.nuova_calibrazione)
        btn_elimina = QPushButton("Elimina selezionato")
        btn_elimina.clicked.connect(self.elimina_selezionato)
        btn_esporta = QPushButton("Esporta Excel")
        btn_esporta.clicked.connect(self.esporta_excel)

        barra.addWidget(self.filtro_categoria)
        barra.addWidget(self.filtro_stato)
        barra.addStretch()
        barra.addWidget(btn_nuovo)
        barra.addWidget(btn_modifica)
        barra.addWidget(btn_manutenzione)
        barra.addWidget(btn_calibrazione)
        barra.addWidget(btn_elimina)
        barra.addWidget(btn_esporta)
        layout.addLayout(barra)

        # Tabella
        self.tabella = QTableWidget()
        self.tabella.setColumnCount(7)
        self.tabella.setHorizontalHeaderLabels(
            ["ID", "Nome", "Categoria", "Produttore", "N. Seriale", "Stato", "UDI"]
        )
        self.tabella.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabella.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabella.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabella.cellDoubleClicked.connect(self.apri_dettaglio)
        layout.addWidget(self.tabella)

    def aggiorna_tabella(self):
        try:
            categoria = self.filtro_categoria.text().strip() or None
            stato = self.filtro_stato.currentData()
            dispositivi = self.client.lista_dispositivi(categoria=categoria, stato=stato)
        except requests.RequestException as e:
            self._errore_connessione(e)
            return

        self.dispositivi_correnti = dispositivi
        self.tabella.setRowCount(len(dispositivi))
        for row, d in enumerate(dispositivi):
            valori = [
                str(d["id"]), d["nome"], d["categoria"], d["produttore"],
                d["numero_seriale"], d["stato"], d.get("udi") or "-",
            ]
            for col, val in enumerate(valori):
                item = QTableWidgetItem(val)
                if col == 5:
                    if val == "guasto":
                        item.setBackground(COLORE_GUASTO)
                    elif val == "manutenzione":
                        item.setBackground(COLORE_MANUTENZIONE)
                self.tabella.setItem(row, col, item)

        self.status_bar.showMessage(f"{len(dispositivi)} dispositivi trovati", 3000)

    def esporta_excel(self):
        if not self.dispositivi_correnti:
            QMessageBox.information(self, "Nessun dato", "Non ci sono dispositivi da esportare.")
            return

        path, _ = QFileDialog.getSaveFileName(
            self, "Salva inventario", "inventario_dispositivi.xlsx", "File Excel (*.xlsx)"
        )
        if not path:
            return

        try:
            export.esporta_dispositivi_excel(self.dispositivi_correnti, path)
        except Exception as e:
            QMessageBox.critical(self, "Errore export", f"Impossibile salvare il file.\n\nDettagli: {e}")
            return

        QMessageBox.information(self, "Fatto", f"Inventario esportato in:\n{path}")

    def _dispositivo_selezionato_id(self):
        riga = self.tabella.currentRow()
        if riga < 0:
            QMessageBox.warning(self, "Nessuna selezione", "Seleziona prima un dispositivo dalla tabella.")
            return None
        return int(self.tabella.item(riga, 0).text())

    def nuovo_dispositivo(self):
        dialog = NuovoDispositivoDialog(self.client, self)
        if dialog.exec():
            try:
                self.client.crea_dispositivo(dialog.dati())
            except requests.RequestException as e:
                self._errore_connessione(e)
                return
            self.aggiorna_tabella()

    def apri_dettaglio(self, row: int, column: int):
        dispositivo_id = int(self.tabella.item(row, 0).text())
        try:
            dispositivo = self.client.get_dispositivo(dispositivo_id)
        except requests.RequestException as e:
            self._errore_connessione(e)
            return
        dialog = DettaglioDispositivoDialog(self.client, dispositivo, self)
        dialog.exec()

    def modifica_selezionato(self):
        dispositivo_id = self._dispositivo_selezionato_id()
        if dispositivo_id is None:
            return
        try:
            dispositivo = self.client.get_dispositivo(dispositivo_id)
        except requests.RequestException as e:
            self._errore_connessione(e)
            return

        dialog = ModificaDispositivoDialog(self.client, dispositivo, self)
        if dialog.exec():
            try:
                self.client.aggiorna_dispositivo(dispositivo_id, dialog.dati())
            except requests.RequestException as e:
                self._errore_connessione(e)
                return
            self.aggiorna_tabella()

    def nuova_manutenzione(self):
        dispositivo_id = self._dispositivo_selezionato_id()
        if dispositivo_id is None:
            return
        dialog = NuovaManutenzioneDialog(self)
        if dialog.exec():
            try:
                self.client.crea_manutenzione(dispositivo_id, dialog.dati())
            except requests.RequestException as e:
                self._errore_connessione(e)
                return
            QMessageBox.information(self, "Fatto", "Manutenzione registrata.")

    def nuova_calibrazione(self):
        dispositivo_id = self._dispositivo_selezionato_id()
        if dispositivo_id is None:
            return
        dialog = NuovaCalibrazioneDialog(self)
        if dialog.exec():
            try:
                self.client.crea_calibrazione(dispositivo_id, dialog.dati())
            except requests.RequestException as e:
                self._errore_connessione(e)
                return
            QMessageBox.information(self, "Fatto", "Calibrazione registrata.")

    def elimina_selezionato(self):
        dispositivo_id = self._dispositivo_selezionato_id()
        if dispositivo_id is None:
            return
        riga = self.tabella.currentRow()
        nome = self.tabella.item(riga, 1).text()

        conferma = QMessageBox.question(
            self, "Conferma eliminazione", f"Eliminare '{nome}'? L'operazione è irreversibile."
        )
        if conferma != QMessageBox.Yes:
            return

        try:
            self.client.elimina_dispositivo(dispositivo_id)
        except requests.RequestException as e:
            self._errore_connessione(e)
            return
        self.aggiorna_tabella()

    def _errore_connessione(self, e):
        QMessageBox.critical(
            self, "Errore di connessione",
            "Impossibile contattare il backend.\n"
            "Verifica che sia in esecuzione (uvicorn main:app --reload).\n\n"
            f"Dettagli: {e}"
        )


class ScadenzeTab(QWidget):
    def __init__(self, client: ApiClient, status_bar: QStatusBar):
        super().__init__()
        self.client = client
        self.status_bar = status_bar
        self.scadenze_correnti: list = []
        self._build_ui()
        self.aggiorna()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        controlli = QHBoxLayout()
        controlli.addWidget(QLabel("Mostra scadenze entro (giorni):"))
        self.input_giorni = QComboBox()
        self.input_giorni.addItems(["7", "15", "30", "60", "90", "180", "365"])
        self.input_giorni.setCurrentText("30")
        self.input_giorni.currentIndexChanged.connect(self.aggiorna)
        btn_aggiorna = QPushButton("Aggiorna")
        btn_aggiorna.clicked.connect(self.aggiorna)
        btn_esporta = QPushButton("Esporta PDF")
        btn_esporta.clicked.connect(self.esporta_pdf)
        controlli.addWidget(self.input_giorni)
        controlli.addWidget(btn_aggiorna)
        controlli.addStretch()
        controlli.addWidget(btn_esporta)
        layout.addLayout(controlli)

        self.tabella = QTableWidget()
        self.tabella.setColumnCount(4)
        self.tabella.setHorizontalHeaderLabels(["Dispositivo", "Tipo", "Scadenza", "Giorni rimanenti"])
        self.tabella.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabella.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.tabella)

    def aggiorna(self):
        try:
            entro_giorni = int(self.input_giorni.currentText())
            scadenze = self.client.dispositivi_in_scadenza(entro_giorni=entro_giorni)
        except requests.RequestException as e:
            QMessageBox.critical(self, "Errore di connessione", f"Impossibile contattare il backend.\n\nDettagli: {e}")
            return

        self.scadenze_correnti = scadenze
        self.tabella.setRowCount(len(scadenze))
        for row, s in enumerate(scadenze):
            valori = [s["dispositivo_nome"], s["tipo_scadenza"], s["data_scadenza"], str(s["giorni_rimanenti"])]
            for col, val in enumerate(valori):
                item = QTableWidgetItem(val)
                if col == 3:
                    giorni = s["giorni_rimanenti"]
                    if giorni < 0:
                        item.setBackground(COLORE_SCADUTO)
                    elif giorni <= 7:
                        item.setBackground(COLORE_URGENTE)
                self.tabella.setItem(row, col, item)

        self.status_bar.showMessage(f"{len(scadenze)} scadenze trovate", 3000)

    def esporta_pdf(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Salva report scadenze", "report_scadenze.pdf", "File PDF (*.pdf)"
        )
        if not path:
            return

        try:
            entro_giorni = int(self.input_giorni.currentText())
            export.esporta_scadenze_pdf(self.scadenze_correnti, entro_giorni, path)
        except Exception as e:
            QMessageBox.critical(self, "Errore export", f"Impossibile salvare il file.\n\nDettagli: {e}")
            return

        QMessageBox.information(self, "Fatto", f"Report esportato in:\n{path}")


class RepartiTab(QWidget):
    def __init__(self, client: ApiClient, status_bar: QStatusBar):
        super().__init__()
        self.client = client
        self.status_bar = status_bar
        self._build_ui()
        self.aggiorna()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        barra = QHBoxLayout()
        btn_nuovo = QPushButton("+ Nuovo reparto")
        btn_nuovo.clicked.connect(self.nuovo_reparto)
        barra.addStretch()
        barra.addWidget(btn_nuovo)
        layout.addLayout(barra)

        self.tabella = QTableWidget()
        self.tabella.setColumnCount(3)
        self.tabella.setHorizontalHeaderLabels(["ID", "Nome", "Piano"])
        self.tabella.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabella.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.tabella)

    def aggiorna(self):
        try:
            reparti = self.client.lista_reparti()
        except requests.RequestException as e:
            QMessageBox.critical(self, "Errore di connessione", f"Impossibile contattare il backend.\n\nDettagli: {e}")
            return

        self.tabella.setRowCount(len(reparti))
        for row, r in enumerate(reparti):
            for col, val in enumerate([str(r["id"]), r["nome"], r.get("piano") or "-"]):
                self.tabella.setItem(row, col, QTableWidgetItem(val))

    def nuovo_reparto(self):
        dialog = NuovoRepartoDialog(self)
        if dialog.exec():
            try:
                self.client.crea_reparto(dialog.dati())
            except requests.RequestException as e:
                QMessageBox.critical(self, "Errore di connessione", f"Impossibile contattare il backend.\n\nDettagli: {e}")
                return
            self.aggiorna()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gestione Dispositivi Medici")
        self.resize(1050, 650)

        self.client = ApiClient()
        status_bar = QStatusBar()
        self.setStatusBar(status_bar)

        self.tab_dispositivi = DispositiviTab(self.client, status_bar)
        self.tab_scadenze = ScadenzeTab(self.client, status_bar)
        self.tab_reparti = RepartiTab(self.client, status_bar)

        tabs = QTabWidget()
        tabs.addTab(self.tab_dispositivi, "Dispositivi")
        tabs.addTab(self.tab_scadenze, "Scadenze")
        tabs.addTab(self.tab_reparti, "Reparti")
        tabs.currentChanged.connect(self._on_tab_changed)
        self.setCentralWidget(tabs)

    def _on_tab_changed(self, index: int):
        # Aggiorna i dati ogni volta che l'utente cambia scheda
        widget = self.centralWidget().widget(index)
        if hasattr(widget, "aggiorna_tabella"):
            widget.aggiorna_tabella()
        elif hasattr(widget, "aggiorna"):
            widget.aggiorna()