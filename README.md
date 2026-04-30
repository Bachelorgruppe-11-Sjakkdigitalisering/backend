# Backend og Maskinsyn for Digitalisering av Sjakkparti

- [Backend og Maskinsyn for Digitalisering av Sjakkparti](#backend-og-maskinsyn-for-digitalisering-av-sjakkparti)
  - [Oversikt](#oversikt)
  - [Nøkkelfunksjoner](#nøkkelfunksjoner)
  - [Teknologistack](#teknologistack)
  - [Kom i gang](#kom-i-gang)
    - [Forutsetninger](#forutsetninger)
    - [Installasjon](#installasjon)
    - [Kjøring av systemet](#kjøring-av-systemet)
  - [Testing](#testing)
  - [Prosjektstruktur](#prosjektstruktur)
  - [Trådhåndtering og Ytelse](#trådhåndtering-og-ytelse)
  - [Akademisk kontekst](#akademisk-kontekst)

## Oversikt

Dette repositoryet inneholder backend- og maskinsyn-koden for et bachelorprosjekt om digitalisering av fysiske sjakkpartier. Systemet består av to hovedkomponenter:

1. **REST API (FastAPI):** Håndterer database, spillerprofiler, historiske partier og state-håndtering for live-partier.
2. **Admin-klient (CustomTkinter):** Et grafisk kontrollpanel som bruker webkameraer, YOLO-modeller og OpenCV for å analysere fysiske sjakkbrett i sanntid. Klienten detekterer trekk, leser av sjakklokker, og sender oppdateringer direkte til API-et.

## Nøkkelfunksjoner

- **Maskinsyn:** Automatisk kalibrering og perspektivkorrigering av sjakkbrettet via OpenCV. Bruk av YOLO-modeller for gjenkjenning av brikker og avlesning av digitale sjakklokker.
- **Robust Trekkdeteksjon:** Kombinerer bevegelsesdeteksjon (for å ignorere hender i bildet) med sammenligning av brikkenes posisjon. Validerer trekk opp mot offisielle sjakkregler (inkludert rokade og en passant) via `python-chess`.
- **Grafisk Admin-panel:** Et desktop-grensesnitt bygget med CustomTkinter for å opprette partier, koble spillere til kameraer, justere "Region of Interest" (ROI) for sjakklokker, og overvåke live-feeder.
- **RESTful API & Database:** Raskt og asynkront API bygget med FastAPI og SQLModel (SQLite). Håndterer strømming av spillets tilstand (FEN/PGN) til web-frontenden.
- **Arkivering av spilte partier:** Lagrer ferdigspilte partier rett i en lokal SQLite-database for senere analyse og spillerstatistikk som vises i web-frontenden.

## Teknologistack

- **Språk:** Python 3.x
- **Maskinlæring & CV:** Ultralytics (YOLOv8), OpenCV (`opencv-python`), Numpy
- **Web & API:** FastAPI, Uvicorn, Requests
- **Database:** SQLModel, SQLAlchemy, SQLite
- **GUI:** CustomTkinter, Pillow (PIL)
- **Sjakklogikk:** `chess` (python-chess)
- **Testing:** Pytest

## Kom i gang

### Forutsetninger

- Python 3.10 eller nyere anbefales.
- Et tilkoblet webkamera.
- Pre-trente YOLO-modeller (`brett.pt`, `klokke.pt`, `fargebrikker.onnx`) plassert i rotkatalogen.

### Installasjon

1. Klon repositoryet:

```bash
git clone https://github.com/Bachelorgruppe-11-Sjakkdigitalisering/backend.git
cd backend
```

2. Opprett og aktiver et virtuelt miljø (anbefalt):

```bash
python -m venv venv
source venv/bin/activate       # Mac/Linux
source venv\Scripts\activate   # Windows
```

3. Installer avhengighetene:

```bash
pip install -r requirements.txt
```

### Kjøring av systemet

Systemet krever at du kjører API-et og Admin-panelet i to separate terminalvinduer.

1. Start FastAPI-serveren:

Dette starter databasen og lytter etter oppdateringer.

```bash
python -m uvicorn api.main:app --reload --port 8000
```

2. Start Admin-panelet:

```bash
python -m gui.main
```

## Testing

Prosjektet er testet med Pytest og en in-memory SQLite-database for å sikre at databasen ikke endres under testing.

Kjør alle tester med:

```bash
python -m pytest
```

For å se testdekning:

```bash
pytest --cov
```

## Prosjektstruktur

- `/api` - Inneholder FastAPI-applikasjonen, databasemodeller (`models.py`) og database-oppsett (`database.py`).

- `/machine_learning` - Logikk for maskinsyn. Inneholder `vision_thread.py` (bakgrunnsprosessering for YOLO/OpenCV) og `motion_detector.py`.

- `/gui` - UI-komponenter og sider for CustomTkinter Admin-panelet.

- `/clock` & `/chessboard` & `/moves` - Domenelogikk for å oversette piksler og bounding-boxes til faktiske sjakktrekk og klokketider.

- `/network` - ChessAPIClient for asynkron kommunikasjon mellom maskinsyn-tråden og FastAPI.

- `tests/` - Enhetstester for API og domenelogikk.

## Trådhåndtering og Ytelse

For å forhindre at det grafiske brukergrensesnittet (GUI) ikke fryser under tung bildebehandling, kjøres YOLO-modellene og OpenCV i en egen `VisionThread`. Kommunikasjon mellom GUI, maskinsyn og API-klient skjer asynkront via trådsikre køer (`queue.Queue`) og bakgrunnstråder.

## Akademisk kontekst

Dette prosjektet ble utviklet av Herman Lundby-Holen og Dennis Johansen som en del av bacheloroppgaven ved NTNU i Ålesund, 2026, med Aalesund Schacklag som oppdragsgiver.
