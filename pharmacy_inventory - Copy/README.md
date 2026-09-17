# Pharmacy Inventory (FEFO)

A Flask-based pharmacy inventory app that manages medicine batches, enforces FEFO dispensing, tracks expiry risk, and raises reorder alerts.

## Project overview

The app exposes a small inventory workflow around a single `batches` collection:

- add inventory entries
- search current sellable stock
- dispense by first-expiry-first-out (FEFO)
- flag batches nearing expiry
- quarantine expired stock
- import messy CSV data
- store reorder alerts in an outbox

## Local setup

### 1) Create a virtual environment

```bash
cd "pharmacy_inventory - Copy"
python3 -m venv .venv
source .venv/bin/activate
```

### 2) Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 3) Configure environment variables

The app reads values from environment variables and optionally uses a local in-memory MongoDB mock if `MONGODB_URI` is not set.

For a real MongoDB connection, create a `.env` file:

```env
MONGODB_URI="mongodb+srv://<username>:<password>@<cluster-url>/<database>?retryWrites=true&w=majority"
MONGODB_DB="pharmacy_inventory"
EXPIRY_ALERT_DAYS="30"
DAILY_QUARANTINE_DAYS="7"
REORDER_THRESHOLD="10"
```

If no `MONGODB_URI` is present, the app uses `mongomock` automatically for local development.

### 4) Load sample data (optional)

```bash
python sample_data.py
```

### 5) Run the app

```bash
python app.py
```

Then browse:

- http://127.0.0.1:5000

## Debugging

The app starts with Flask debug mode enabled in `app.py`:

```python
if __name__ == "__main__":
    app.run(debug=True)
```

Useful debug commands:

```bash
# run app directly
python app.py

# run with Flask CLI and debugger
export FLASK_APP=app.py
export FLASK_DEBUG=1
flask run
```

Common issues:

- `ModuleNotFoundError: No module named 'flask'`  
  Run `pip install -r requirements.txt` inside the virtual environment.

- `RuntimeError: MONGODB_URI is not set`  
  This is only a problem if you want a real Atlas connection. For local development, the app now falls back to `mongomock` automatically.

- Debugger reload loops or stale import state  
  Restart the Flask server and ensure you are running the app from the project root.

## API endpoints

### Dashboard and inventory

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | `/` | Dashboard overview with batch counts and expiry summary |
| GET | `/inventory` | View all inventory batches |
| GET | `/inventory/add` | Render form to add a batch |
| POST | `/inventory/add` | Create a new batch with validation |

### Search and alerts

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | `/search?medicine_name=...` | Check sellable stock for a medicine |
| GET | `/alerts` | Show batches expiring within the configured window |

### Dispensing and maintenance

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | `/dispense` | Display dispensing form |
| POST | `/dispense` | FEFO dispense one medicine quantity |
| POST | `/clock` | Flag near-expiry stock, quarantine expired stock, and trigger reorder checks |

### Import and notifications

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | `/import` | Display CSV import form |
| POST | `/import` | Upload or paste messy CSV data and normalize it |
| GET | `/outbox` | View reorder alerts written to the outbox |

## Example requests

### Search stock

```bash
curl "http://127.0.0.1:5000/search?medicine_name=Paracetamol"
```

### Run maintenance tick

```bash
curl -X POST http://127.0.0.1:5000/clock
```

### Dispense stock

```bash
curl -X POST http://127.0.0.1:5000/dispense \
  -d "medicine_name=Paracetamol" \
  -d "quantity=10"
```

### Import CSV

```bash
curl -X POST http://127.0.0.1:5000/import \
  -d "csv_data=medicine_name,batch_number,quantity,expiry_date\nParacetamol,P-001,50,2026-12-31"
```

## Testing

```bash
pytest -q
```

The repository includes route-level tests for dispensing, search, maintenance, notifications, importer logic, and config fallback behavior.

## Notes

- FEFO logic sorts by earliest expiry date.
- Expired batches are excluded from sellable inventory.
- Reorder notifications are generated when in-date stock drops to or below the configured threshold.
- The app is intentionally simple and suitable for development or demonstration workflows.
