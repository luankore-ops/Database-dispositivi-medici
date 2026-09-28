# Gestione Dispositivi Medici

A desktop application for managing a hospital's medical device inventory — tracking equipment, scheduled maintenance, calibration compliance, and upcoming deadlines. Built as a portfolio project to demonstrate both software engineering and MedTech regulatory knowledge (MDR 2017/745, ISO 13485).

![Status](https://img.shields.io/badge/status-active-brightgreen)
![Python](https://img.shields.io/badge/python-3.9%2B-blue)

<!-- Add a screenshot or GIF of the app here, e.g.: -->
<!-- ![App screenshot](docs/screenshot.png) -->

## Why this project

Hospitals are legally required (MDR 2017/745, ISO 13485) to track every medical device's identity, maintenance history, and calibration status. This app models that real-world requirement: each device carries a **UDI (Unique Device Identification)** field, and the system proactively flags devices approaching a maintenance or calibration deadline — the kind of feature a real clinical engineering department would actually rely on.

## Features

- **Full device inventory** — create, edit, delete, and filter devices by category or status
- **Maintenance & calibration tracking** — log preventive/corrective maintenance and calibration certificates per device
- **Deadline alerts** — a dedicated view surfaces everything expiring within a configurable window, sorted by urgency
- **Device detail & history** — double-click any device to see its full maintenance/calibration timeline
- **Department & supplier management**
- **Export** — inventory to Excel (`.xlsx`), deadline report to PDF, both formatted and ready to share
- **Single-file executable** — packaged with PyInstaller; the backend starts automatically, no terminal required

## Architecture

The app follows a client-server pattern, deliberately separating data logic from presentation:

```
┌─────────────────────┐        HTTP/JSON        ┌──────────────────────┐        ┌──────────────┐
│   Desktop GUI        │  ───────────────────►   │   FastAPI backend     │  ───►  │   SQLite /   │
│   (PySide6)           │  ◄───────────────────   │   (REST API)          │  ◄───  │   PostgreSQL │
└─────────────────────┘                          └──────────────────────┘        └──────────────┘
```

- The **GUI never touches the database directly** — every action goes through the REST API, so the backend could later run on a hospital network server while multiple desktop clients connect to it.
- In the packaged executable, the backend runs automatically in a background thread — from the user's perspective it's a single application, no separate server to manage.

## Tech stack

| Layer | Technology |
|---|---|
| Desktop GUI | PySide6 (Qt for Python) |
| Backend / API | FastAPI |
| ORM | SQLAlchemy 2.0 |
| Database | SQLite (dev) / PostgreSQL-ready |
| Export | openpyxl (Excel), ReportLab (PDF) |
| Packaging | PyInstaller |

## Project structure

```
dispositivi_medici_db/
├── app.py              # Desktop entry point (starts backend + GUI)
├── main_window.py       # Main window: Devices / Deadlines / Departments tabs
├── dialogs.py            # Modal forms (create/edit device, maintenance, calibration, detail view)
├── api_client.py         # HTTP client used by the GUI to talk to the backend
├── main.py                # FastAPI app and REST endpoints
├── crud.py                 # Database access functions
├── schemas.py               # Pydantic request/response schemas
├── models.py                 # SQLAlchemy ORM models
├── database.py                 # DB engine/session configuration
├── seed_data.py                  # Populates the database with sample data
├── export.py                       # Excel/PDF export logic
└── requirements.txt
```

## Getting started

```bash
pip install -r requirements.txt
python seed_data.py      # optional: populate with sample data
python app.py            # launches backend + GUI together
```

### Build a standalone executable

```bash
pyinstaller --onefile --name GestioneDispositiviMedici --noconfirm app.py
```

The resulting executable (in `dist/`) runs standalone — no Python installation needed on the target machine.

## Possible extensions

- QR code generation per device, for physical asset labeling
- Role-based access control (biomedical technician / department head / admin)
- Audit log of all changes
- Email notifications for approaching deadlines

## License

MIT
