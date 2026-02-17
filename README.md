# InvoiceFlow

Ein modernes, automatisiertes System zur Verarbeitung und Verwaltung von Rechnungen.

## Übersicht

InvoiceFlow ist eine vollständige Web-Anwendung für das digitale Rechnungsmanagement mit automatischer Verarbeitung, Freigabe-Workflows und Export-Funktionen für Buchhaltungssysteme und DMS.

### Features

- **Automatische Rechnungsverarbeitung**: Import und Verarbeitung von Rechnungen
- **Freigabe-Workflow**: Mehrstufiger Genehmigungsprozess
- **Dashboard**: Übersichtliche Darstellung aller Rechnungen und Statistiken
- **Kostenstellen & Projekte**: Zuordnung zu Kostenstellen und Projekten
- **Tags & Kommentare**: Flexible Kategorisierung
- **Export**: Export zu Buchhaltungssystemen und DMS
- **Audit-Log**: Vollständige Nachverfolgung aller Änderungen

## Technologie-Stack

### Backend
- **FastAPI**: Modernes Python-Web-Framework
- **PostgreSQL**: Relationale Datenbank
- **SQLAlchemy**: ORM für Datenbankzugriff
- **Alembic**: Datenbank-Migrationen

### Frontend
- **Vue 3**: Progressive JavaScript-Framework
- **Vuetify 3**: Material Design Component-Framework
- **Vite**: Build-Tool und Dev-Server
- **Axios**: HTTP-Client

### DevOps
- **Docker**: Containerisierung
- **Docker Compose**: Orchestrierung

## Projekt-Struktur

```
invoiceflow/
├── backend/                 # FastAPI Backend
│   ├── app/
│   │   ├── api/            # API-Endpoints
│   │   ├── models/         # SQLAlchemy-Modelle
│   │   ├── schemas/        # Pydantic-Schemas
│   │   ├── services/       # Business-Logik
│   │   ├── config.py       # Konfiguration
│   │   ├── database.py     # Datenbank-Setup
│   │   └── main.py         # FastAPI-App
│   ├── alembic/            # Datenbank-Migrationen
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/               # Vue 3 Frontend
│   ├── src/
│   │   ├── components/     # Vue-Komponenten
│   │   ├── views/          # Seiten-Views
│   │   ├── router/         # Router-Konfiguration
│   │   ├── services/       # API-Services
│   │   ├── App.vue         # Haupt-App-Komponente
│   │   └── main.js         # Einstiegspunkt
│   ├── Dockerfile
│   ├── package.json
│   └── vite.config.js
├── data/                   # Datenverzeichnis
│   ├── incoming/           # Eingehende Rechnungen
│   ├── processing/         # In Bearbeitung
│   ├── approved/           # Freigegebene Rechnungen
│   └── export/             # Export-Verzeichnisse
│       ├── accounting/     # Export Buchhaltung
│       └── dms/            # Export DMS
├── docs/                   # Dokumentation
├── docker-compose.yml      # Docker Compose-Konfiguration
├── .env                    # Umgebungsvariablen
└── README.md              # Diese Datei
```

## Installation & Setup

### Voraussetzungen

- Docker & Docker Compose
- Git

### Quick Start

1. **Repository klonen**
   ```bash
   git clone <repository-url>
   cd invoiceflow
   ```

2. **Umgebungsvariablen konfigurieren**

   Die `.env`-Datei ist bereits mit Standardwerten erstellt. Für Produktions-Deployments sollten Sie das Passwort ändern:
   ```bash
   DB_PASSWORD=your_secure_password_here
   ```

3. **Anwendung starten**
   ```bash
   docker-compose up --build
   ```

4. **Zugriff auf die Anwendung**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API-Dokumentation: http://localhost:8000/docs

### Datenbank-Migrationen

Die initiale Migration wird automatisch beim ersten Start ausgeführt. Für manuelle Migrationen:

```bash
# In den Backend-Container wechseln
docker-compose exec backend bash

# Migration ausführen
alembic upgrade head

# Neue Migration erstellen
alembic revision --autogenerate -m "Description"
```

## Entwicklung

### Backend-Entwicklung

```bash
# Backend-Container starten
docker-compose up backend postgres

# Logs anzeigen
docker-compose logs -f backend

# Tests ausführen
docker-compose exec backend pytest
```

### Frontend-Entwicklung

```bash
# Frontend-Container starten
docker-compose up frontend

# Logs anzeigen
docker-compose logs -f frontend
```

## API-Dokumentation

### Endpoints

#### Invoices

- `GET /api/invoices/` - Alle Rechnungen abrufen
  - Query-Parameter: `status` (pending/approved/rejected), `skip`, `limit`

- `GET /api/invoices/stats` - Rechnungs-Statistiken

- `GET /api/invoices/{id}` - Einzelne Rechnung abrufen

- `POST /api/invoices/` - Neue Rechnung erstellen

- `PATCH /api/invoices/{id}` - Rechnung aktualisieren

- `POST /api/invoices/{id}/approve` - Rechnung freigeben
  ```json
  {
    "approved_by": "username",
    "cost_center": "KST-123",
    "project": "PROJ-456",
    "tags": ["urgent", "hardware"],
    "comment": "Approved for Q1 budget"
  }
  ```

- `POST /api/invoices/{id}/reject` - Rechnung ablehnen
  ```json
  {
    "rejection_reason": "Missing documentation",
    "rejected_by": "username"
  }
  ```

- `DELETE /api/invoices/{id}` - Rechnung löschen

#### Health Check

- `GET /health` - Health-Check-Endpoint

### Datenmodell

#### Invoice

```python
{
  "id": 1,
  "filename": "invoice_001.pdf",
  "file_path": "/app/data/incoming/invoice_001.pdf",
  "invoice_type": "incoming",
  "invoice_number": "RE-2024-001",
  "invoice_date": "2024-01-15T00:00:00Z",
  "supplier_name": "Acme Corp",
  "supplier_id": "DE123456789",
  "amount_net": 1000.00,
  "amount_gross": 1190.00,
  "amount_vat": 190.00,
  "currency": "EUR",
  "due_date": "2024-02-15T00:00:00Z",
  "tags": ["office", "hardware"],
  "cost_center": "KST-IT",
  "project": "PROJ-2024",
  "comment": "New office equipment",
  "status": "pending",
  "approved_by": null,
  "approved_at": null,
  "created_at": "2024-01-15T10:00:00Z",
  "updated_at": "2024-01-15T10:00:00Z"
}
```

## Workflow

### 1. Rechnungsimport
- Rechnungen werden in `data/incoming/` abgelegt
- System erkennt neue Dateien automatisch (geplant)
- OCR-Verarbeitung extrahiert Daten (geplant)

### 2. Verarbeitung & Prüfung
- Manuelle oder automatische Prüfung der Daten
- Zuordnung zu Kostenstellen und Projekten
- Hinzufügen von Tags und Kommentaren

### 3. Freigabe
- Freigabe durch autorisierte Person
- Automatische Benachrichtigung (geplant)
- Verschieben nach `data/approved/`

### 4. Export
- Export zu Buchhaltungssystem (z.B. DATEV)
- Archivierung im DMS
- Audit-Trail für Compliance

## Konfiguration

### Backend-Konfiguration

Umgebungsvariablen in `.env`:

```env
# Datenbank
DB_PASSWORD=your_secure_password

# Weitere Optionen in backend/app/config.py
```

### Frontend-Konfiguration

Umgebungsvariablen für Vite:

```env
VITE_API_URL=http://localhost:8000
```

## Sicherheit

- CORS ist für `localhost:3000` konfiguriert
- Für Produktion: HTTPS verwenden
- Sichere Passwörter in `.env` setzen
- `.env` nicht in Git committen (bereits in `.gitignore`)
- Authentifizierung/Autorisierung implementieren (geplant)

## Nächste Schritte / Roadmap

- [ ] OCR-Integration für automatische Datenextraktion
- [ ] E-Mail-Integration für Rechnungsempfang
- [ ] Benutzer-Authentifizierung (OAuth2/JWT)
- [ ] Rollen & Berechtigungen
- [ ] DATEV-Export-Schnittstelle
- [ ] DMS-Integration (z.B. SharePoint, Nextcloud)
- [ ] E-Mail-Benachrichtigungen
- [ ] Automatische Workflow-Regeln
- [ ] Reporting & Analytics
- [ ] Mobile App

## Lizenz

Copyright © 2024

## Support

Bei Fragen oder Problemen:
- Issue-Tracker: <repository-url>/issues
- Dokumentation: `docs/`
