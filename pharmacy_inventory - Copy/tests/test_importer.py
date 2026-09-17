import mongomock
from datetime import datetime

from routes import importer
from routes.importer import parse_quantity, parse_maybe_date, do_import


def setup_mock():
    client = mongomock.MongoClient()
    db = client["testdb"]
    importer.batches = db["batches"]
    return importer.batches


def test_parse_quantity_and_dates():
    assert parse_quantity("10 units") == 10
    assert parse_quantity(None) is None
    assert parse_maybe_date("2026-12-31") == datetime(2026, 12, 31, 0, 0, 0)
    assert parse_maybe_date("31/12/2026") == datetime(2026, 12, 31, 0, 0, 0)
    assert parse_maybe_date("bad") is None


def test_import_messy_csv_report():
    mock_batches = setup_mock()
    csv_data = """medicine_name,batch_number,quantity,expiry_date
Paracetamol,B001,10 units,2026-12-31
Paracetamol,B001,5,31/12/2026
, B002 ,3,2026-06-01
Ibuprofen,B003,not-a-number,2026-06-01
Aspirin,B004,7,01/06/2026
"""

    with importer.importer_bp.test_request_context(
        "/import",
        method="POST",
        data={"csv_data": csv_data},
        headers={"Accept": "application/json"},
    ):
        resp = do_import()
        report = resp.get_json()

    assert report["imported"] == 2
    assert report["deduped"] == 0
    assert report["rejected"] == 2
    assert mock_batches.count_documents({}) == 2
    paracetamol = mock_batches.find_one({"batch_number": "B001"})
    assert paracetamol["quantity"] == 15
