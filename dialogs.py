"""
dialogs.py — Finestre di dialogo modali per l'inserimento dei dati
"""

from PySide6.QtWidgets import (
    QDialog, QFormLayout, QVBoxLayout, QLineEdit, QComboBox, QDoubleSpinBox, QDialogButtonBox,
    QDateEdit, QTextEdit, QMessageBox, QLabel, QGroupBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QPushButton,
)
from PySide6.QtCore import QDate


class NuovoDispositivoDialog(QDialog):
    """Form per la creazione di un nuovo dispositivo medico."""

    def __init__(self, client, parent=None):
        super().__init__(parent)
        self.client = client
        self.setWindowTitle("Nuovo dispositivo")
        self.setMinimumWidth(400)

        layout = QFormLayout(self)

        self.input_nome = QLineEdit()
        self.input_categoria = QLineEdit()
        self.input_seriale = QLineEdit()
        self.input_udi = QLineEdit()
        self.input_udi.setPlaceholderText("es. (01)00844588003288(11)230501(21)SN00234")
        self.input_produttore = QLineEdit()
        self.input_modello = QLineEdit()
        self.input_costo = QDoubleSpinBox()
        self.input_costo.setMaximum(10_000_000)
        self.input_costo.setPrefix("€ ")
        self.input_reparto = QComboBox()
        self.input_fornitore = QComboBox()

        layout.addRow("Nome*", self.input_nome)
        layout.addRow("Categoria*", self.input_categoria)
        layout.addRow("N. Seriale*", self.input_seriale)
        layout.addRow("UDI", self.input_udi)
        layout.addRow("Produttore*", self.input_produttore)
        layout.addRow("Modello", self.input_modello)
        layout.addRow("Costo", self.input_costo)
        layout.addRow("Reparto", self.input_reparto)
        layout.addRow("Fornitore", self.input_fornitore)

        self._carica_combo()

        bottoni = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bottoni.accepted.connect(self._valida_e_accetta)
        bottoni.rejected.connect(self.reject)
        layout.addRow(bottoni)

    def _carica_combo(self):
        self.input_reparto.addItem("— nessuno —", None)
        self.input_fornitore.addItem("— nessuno —", None)
        try:
            for r in self.client.lista_reparti():
                self.input_reparto.addItem(r["nome"], r["id"])
            for f in self.client.lista_fornitori():
                self.input_fornitore.addItem(f["ragione_sociale"], f["id"])
        except Exception:
            pass  # la finestra principale segnalerà l'errore di connessione al refresh

    def _valida_e_accetta(self):
        if not (self.input_nome.text().strip() and self.input_categoria.text().strip()
                and self.input_seriale.text().strip() and self.input_produttore.text().strip()):
            QMessageBox.warning(self, "Campi mancanti", "Nome, categoria, numero seriale e produttore sono obbligatori.")
            return
        self.accept()

    def dati(self) -> dict:
        return {
            "nome": self.input_nome.text().strip(),
            "categoria": self.input_categoria.text().strip(),
            "numero_seriale": self.input_seriale.text().strip(),
            "udi": self.input_udi.text().strip() or None,
            "produttore": self.input_produttore.text().strip(),
            "modello": self.input_modello.text().strip() or None,
            "costo": self.input_costo.value() or None,
            "reparto_id": self.input_reparto.currentData(),
            "fornitore_id": self.input_fornitore.currentData(),
        }


class ModificaDispositivoDialog(QDialog):
    """Form per modificare un dispositivo esistente, pre-compilato con i dati attuali."""

    def __init__(self, client, dispositivo: dict, parent=None):
        super().__init__(parent)
        self.client = client
        self.setWindowTitle(f"Modifica dispositivo — {dispositivo['nome']}")
        self.setMinimumWidth(400)

        layout = QFormLayout(self)

        self.input_nome = QLineEdit(dispositivo.get("nome", ""))
        self.input_categoria = QLineEdit(dispositivo.get("categoria", ""))
        self.input_seriale = QLineEdit(dispositivo.get("numero_seriale", ""))
        self.input_udi = QLineEdit(dispositivo.get("udi") or "")
        self.input_produttore = QLineEdit(dispositivo.get("produttore", ""))
        self.input_modello = QLineEdit(dispositivo.get("modello") or "")
        self.input_costo = QDoubleSpinBox()
        self.input_costo.setMaximum(10_000_000)
        self.input_costo.setPrefix("€ ")
        self.input_costo.setValue(dispositivo.get("costo") or 0)
        self.input_stato = QComboBox()
        self.input_stato.addItems(["in_uso", "manutenzione", "guasto", "dismesso"])
        self.input_stato.setCurrentText(dispositivo.get("stato", "in_uso"))
        self.input_reparto = QComboBox()
        self.input_fornitore = QComboBox()

        layout.addRow("Nome*", self.input_nome)
        layout.addRow("Categoria*", self.input_categoria)
        layout.addRow("N. Seriale*", self.input_seriale)
        layout.addRow("UDI", self.input_udi)
        layout.addRow("Produttore*", self.input_produttore)
        layout.addRow("Modello", self.input_modello)
        layout.addRow("Costo", self.input_costo)
        layout.addRow("Stato", self.input_stato)
        layout.addRow("Reparto", self.input_reparto)
        layout.addRow("Fornitore", self.input_fornitore)

        self._carica_combo(dispositivo.get("reparto_id"), dispositivo.get("fornitore_id"))

        bottoni = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bottoni.accepted.connect(self._valida_e_accetta)
        bottoni.rejected.connect(self.reject)
        layout.addRow(bottoni)

    def _carica_combo(self, reparto_id, fornitore_id):
        self.input_reparto.addItem("— nessuno —", None)
        self.input_fornitore.addItem("— nessuno —", None)
        try:
            for r in self.client.lista_reparti():
                self.input_reparto.addItem(r["nome"], r["id"])
            for f in self.client.lista_fornitori():
                self.input_fornitore.addItem(f["ragione_sociale"], f["id"])
        except Exception:
            pass
        idx = self.input_reparto.findData(reparto_id)
        if idx >= 0:
            self.input_reparto.setCurrentIndex(idx)
        idx = self.input_fornitore.findData(fornitore_id)
        if idx >= 0:
            self.input_fornitore.setCurrentIndex(idx)

    def _valida_e_accetta(self):
        if not (self.input_nome.text().strip() and self.input_categoria.text().strip()
                and self.input_seriale.text().strip() and self.input_produttore.text().strip()):
            QMessageBox.warning(self, "Campi mancanti", "Nome, categoria, numero seriale e produttore sono obbligatori.")
            return
        self.accept()

    def dati(self) -> dict:
        return {
            "nome": self.input_nome.text().strip(),
            "categoria": self.input_categoria.text().strip(),
            "numero_seriale": self.input_seriale.text().strip(),
            "udi": self.input_udi.text().strip() or None,
            "produttore": self.input_produttore.text().strip(),
            "modello": self.input_modello.text().strip() or None,
            "costo": self.input_costo.value() or None,
            "stato": self.input_stato.currentText(),
            "reparto_id": self.input_reparto.currentData(),
            "fornitore_id": self.input_fornitore.currentData(),
        }


class DettaglioDispositivoDialog(QDialog):
    """Mostra i dati del dispositivo e lo storico completo di manutenzioni e calibrazioni."""

    def __init__(self, client, dispositivo: dict, parent=None):
        super().__init__(parent)
        self.client = client
        self.setWindowTitle(f"Dettaglio — {dispositivo['nome']}")
        self.setMinimumSize(600, 520)

        layout = QVBoxLayout(self)

        info = QLabel(
            f"<b>{dispositivo['nome']}</b><br>"
            f"Categoria: {dispositivo['categoria']} · Produttore: {dispositivo['produttore']}"
            f"{' ' + dispositivo['modello'] if dispositivo.get('modello') else ''}<br>"
            f"N. Seriale: {dispositivo['numero_seriale']} · UDI: {dispositivo.get('udi') or '-'}<br>"
            f"Stato attuale: {dispositivo['stato']}"
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        box_man = QGroupBox("Storico manutenzioni")
        layout_man = QVBoxLayout()
        self.tabella_man = QTableWidget()
        self.tabella_man.setColumnCount(4)
        self.tabella_man.setHorizontalHeaderLabels(["Data", "Tipo", "Tecnico", "Prossima scadenza"])
        self.tabella_man.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabella_man.setEditTriggers(QTableWidget.NoEditTriggers)
        layout_man.addWidget(self.tabella_man)
        box_man.setLayout(layout_man)
        layout.addWidget(box_man)

        box_cal = QGroupBox("Storico calibrazioni")
        layout_cal = QVBoxLayout()
        self.tabella_cal = QTableWidget()
        self.tabella_cal.setColumnCount(4)
        self.tabella_cal.setHorizontalHeaderLabels(["Data", "Esito", "Ente certificatore", "Prossima scadenza"])
        self.tabella_cal.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabella_cal.setEditTriggers(QTableWidget.NoEditTriggers)
        layout_cal.addWidget(self.tabella_cal)
        box_cal.setLayout(layout_cal)
        layout.addWidget(box_cal)

        self._carica_storico(dispositivo["id"])

        btn_chiudi = QPushButton("Chiudi")
        btn_chiudi.clicked.connect(self.accept)
        layout.addWidget(btn_chiudi)

    def _carica_storico(self, dispositivo_id: int):
        try:
            manutenzioni = self.client.lista_manutenzioni(dispositivo_id)
            calibrazioni = self.client.lista_calibrazioni(dispositivo_id)
        except Exception:
            return  # la finestra principale segnala già gli errori di connessione altrove

        self.tabella_man.setRowCount(len(manutenzioni))
        for row, m in enumerate(manutenzioni):
            valori = [m["data"], m["tipo"], m.get("tecnico") or "-", m.get("prossima_scadenza") or "-"]
            for col, val in enumerate(valori):
                self.tabella_man.setItem(row, col, QTableWidgetItem(val))

        self.tabella_cal.setRowCount(len(calibrazioni))
        for row, c in enumerate(calibrazioni):
            valori = [c["data"], c["esito"], c.get("ente_certificatore") or "-", c.get("prossima_scadenza") or "-"]
            for col, val in enumerate(valori):
                self.tabella_cal.setItem(row, col, QTableWidgetItem(val))


class NuovaManutenzioneDialog(QDialog):
    """Form per registrare una manutenzione su un dispositivo esistente."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Nuova manutenzione")
        self.setMinimumWidth(380)

        layout = QFormLayout(self)

        self.input_data = QDateEdit(QDate.currentDate())
        self.input_data.setCalendarPopup(True)
        self.input_tipo = QComboBox()
        self.input_tipo.addItems(["preventiva", "correttiva"])
        self.input_tecnico = QLineEdit()
        self.input_descrizione = QTextEdit()
        self.input_descrizione.setFixedHeight(60)
        self.input_prossima = QDateEdit(QDate.currentDate().addMonths(6))
        self.input_prossima.setCalendarPopup(True)

        layout.addRow("Data*", self.input_data)
        layout.addRow("Tipo*", self.input_tipo)
        layout.addRow("Tecnico", self.input_tecnico)
        layout.addRow("Descrizione", self.input_descrizione)
        layout.addRow("Prossima scadenza", self.input_prossima)

        bottoni = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bottoni.accepted.connect(self.accept)
        bottoni.rejected.connect(self.reject)
        layout.addRow(bottoni)

    def dati(self) -> dict:
        return {
            "data": self.input_data.date().toString("yyyy-MM-dd"),
            "tipo": self.input_tipo.currentText(),
            "tecnico": self.input_tecnico.text().strip() or None,
            "descrizione": self.input_descrizione.toPlainText().strip() or None,
            "prossima_scadenza": self.input_prossima.date().toString("yyyy-MM-dd"),
        }


class NuovaCalibrazioneDialog(QDialog):
    """Form per registrare una calibrazione su un dispositivo esistente."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Nuova calibrazione")
        self.setMinimumWidth(380)

        layout = QFormLayout(self)

        self.input_data = QDateEdit(QDate.currentDate())
        self.input_data.setCalendarPopup(True)
        self.input_esito = QComboBox()
        self.input_esito.addItems(["conforme", "non_conforme"])
        self.input_ente = QLineEdit()
        self.input_ente.setPlaceholderText("es. TÜV Italia, Metrica Srl...")
        self.input_prossima = QDateEdit(QDate.currentDate().addYears(1))
        self.input_prossima.setCalendarPopup(True)

        layout.addRow("Data*", self.input_data)
        layout.addRow("Esito*", self.input_esito)
        layout.addRow("Ente certificatore", self.input_ente)
        layout.addRow("Prossima scadenza", self.input_prossima)

        bottoni = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bottoni.accepted.connect(self.accept)
        bottoni.rejected.connect(self.reject)
        layout.addRow(bottoni)

    def dati(self) -> dict:
        return {
            "data": self.input_data.date().toString("yyyy-MM-dd"),
            "esito": self.input_esito.currentText(),
            "ente_certificatore": self.input_ente.text().strip() or None,
            "prossima_scadenza": self.input_prossima.date().toString("yyyy-MM-dd"),
        }


class NuovoRepartoDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Nuovo reparto")
        layout = QFormLayout(self)

        self.input_nome = QLineEdit()
        self.input_piano = QLineEdit()
        layout.addRow("Nome*", self.input_nome)
        layout.addRow("Piano", self.input_piano)

        bottoni = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bottoni.accepted.connect(self._valida_e_accetta)
        bottoni.rejected.connect(self.reject)
        layout.addRow(bottoni)

    def _valida_e_accetta(self):
        if not self.input_nome.text().strip():
            QMessageBox.warning(self, "Campo mancante", "Il nome del reparto è obbligatorio.")
            return
        self.accept()

    def dati(self) -> dict:
        return {"nome": self.input_nome.text().strip(), "piano": self.input_piano.text().strip() or None}