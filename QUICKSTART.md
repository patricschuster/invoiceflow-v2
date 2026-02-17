# InvoiceFlow - Quick Start Guide

## Schritt 1: System starten

```bash
# Im Projektverzeichnis
cd c:\Docker\invoiceflow

# Docker Container bauen und starten
docker-compose up --build
```

Warten Sie, bis alle Container gestartet sind. Sie sollten sehen:
- ✅ PostgreSQL: "database system is ready to accept connections"
- ✅ Backend: "Application startup complete"
- ✅ Frontend: "Local: http://localhost:3000/"

## Schritt 2: Testdaten importieren

Öffnen Sie ein **neues Terminal** und führen Sie aus:

```bash
# Seed-Script im Backend-Container ausführen
docker-compose exec backend python seed_data.py
```

Das Script erstellt **8 Beispiel-Rechnungen** mit verschiedenen Status:
- ⏳ 4 offene Rechnungen (pending)
- ✅ 3 freigegebene Rechnungen (approved)
- ❌ 1 abgelehnte Rechnung (rejected)

## Schritt 3: Anwendung öffnen

Öffnen Sie Ihren Browser:
- **Frontend**: http://localhost:3000
- **API-Dokumentation**: http://localhost:8000/docs

## Was Sie jetzt testen können

### Dashboard
- Navigieren Sie zu http://localhost:3000
- Sehen Sie die Statistiken-Karten (Gesamt, Offen, Freigegeben, Abgelehnt)
- Nutzen Sie die Tabs zum Filtern (Alle, Offen, Freigegeben, Abgelehnt)
- Verwenden Sie die Suchfunktion

### Rechnung freigeben
1. Klicken Sie auf eine offene Rechnung
2. Füllen Sie die Felder aus:
   - Kostenstelle (z.B. "KST-IT")
   - Projekt (z.B. "PROJ-2024")
   - Tags (z.B. "urgent", "hardware")
   - Kommentar
3. Klicken Sie auf "Freigeben"

### Rechnung ablehnen
1. Öffnen Sie eine offene Rechnung
2. Klicken Sie auf "Ablehnen"
3. Geben Sie einen Ablehnungsgrund ein
4. Bestätigen Sie

### API testen
- Öffnen Sie http://localhost:8000/docs
- Testen Sie die Endpoints direkt in der Swagger-UI

## System stoppen

```bash
# Container stoppen
docker-compose down

# Container stoppen UND Datenbank löschen
docker-compose down -v
```

## Neu starten mit frischen Daten

```bash
# Alles löschen
docker-compose down -v

# Neu starten
docker-compose up --build

# Testdaten erneut importieren (in neuem Terminal)
docker-compose exec backend python seed_data.py
```

## Troubleshooting

### Port 5432 bereits belegt
Wenn PostgreSQL-Port bereits verwendet wird:
```bash
# In docker-compose.yml ändern:
ports:
  - "5433:5432"  # Statt 5432:5432
```

### Frontend lädt nicht
1. Browser-Cache leeren
2. Container-Logs prüfen: `docker-compose logs frontend`
3. Neustart: `docker-compose restart frontend`

### Backend-Fehler
```bash
# Logs anzeigen
docker-compose logs backend

# Migration manuell ausführen
docker-compose exec backend alembic upgrade head
```

## Nächste Schritte

Nachdem Sie das System getestet haben, können Sie:
1. Eigene Rechnungen über die API hinzufügen
2. Die Frontend-Komponenten anpassen
3. Weitere Features implementieren (siehe README.md - Roadmap)
