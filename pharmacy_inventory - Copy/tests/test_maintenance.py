import mongomock
from datetime import timedelta

from routes import maintenance, notifications
from routes.maintenance import clock
from helpers import today_start


def make_date(days_from_today):
    from datetime import datetime

    return datetime.combine(
        (datetime.today() + timedelta(days=days_from_today)).date(),
        datetime.min.time(),
    )


def setup_mock():
    client = mongomock.MongoClient()
    db = client["testdb"]
    mock_batches = db["batches"]
    maintenance.batches = mock_batches
    notifications.batches = mock_batches
    notifications.outbox = db["outbox"]
    return mock_batches


def test_clock_flags_and_quarantines():
    mock_batches = setup_mock()
    mock_batches.insert_many(
        [
            {
                "medicine_name": "MedA",
                "batch_number": "B1",
                "quantity": 5,
                "expiry_date": make_date(3),
            },
            {
                "medicine_name": "MedB",
                "batch_number": "B2",
                "quantity": 2,
                "expiry_date": make_date(-1),
            },
        ]
    )

    with maintenance.maintenance_bp.test_request_context("/clock", method="POST"):
        resp = clock()
        data = resp.get_json()

    assert data["flagged_count"] == 1
    assert data["quarantined_count"] == 1
    assert mock_batches.find_one({"batch_number": "B1"})["expiring_flagged"] is True
    assert mock_batches.find_one({"batch_number": "B2"})["quarantined"] is True


def test_clock_is_idempotent():
    mock_batches = setup_mock()
    mock_batches.insert_one(
        {
            "medicine_name": "MedA",
            "batch_number": "B1",
            "quantity": 5,
            "expiry_date": make_date(3),
            "expiring_flagged": True,
            "flagged_at": today_start(),
        }
    )

    with maintenance.maintenance_bp.test_request_context("/clock", method="POST"):
        data = clock().get_json()

    assert data["flagged_count"] == 0
