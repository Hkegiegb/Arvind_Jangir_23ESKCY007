import mongomock
from datetime import timedelta

from routes import notifications
from routes.notifications import check_and_notify_if_needed, outbox_list


def make_date(days_from_today):
    from datetime import datetime

    return datetime.combine(
        (datetime.today() + timedelta(days=days_from_today)).date(),
        datetime.min.time(),
    )


def setup_mock(threshold=10):
    client = mongomock.MongoClient()
    db = client["testdb"]
    notifications.batches = db["batches"]
    notifications.outbox = db["outbox"]
    notifications.REORDER_THRESHOLD = threshold
    return notifications.batches, notifications.outbox


def test_reorder_alert_when_below_threshold():
    mock_batches, mock_outbox = setup_mock(threshold=10)
    mock_batches.insert_one(
        {
            "medicine_name": "MedX",
            "batch_number": "B1",
            "quantity": 8,
            "expiry_date": make_date(30),
        }
    )

    alert = check_and_notify_if_needed("MedX")
    assert alert is not None
    assert mock_outbox.count_documents({}) == 1


def test_no_alert_when_above_threshold():
    mock_batches, mock_outbox = setup_mock(threshold=10)
    mock_batches.insert_one(
        {
            "medicine_name": "MedY",
            "batch_number": "B1",
            "quantity": 50,
            "expiry_date": make_date(30),
        }
    )

    assert check_and_notify_if_needed("MedY") is None
    assert mock_outbox.count_documents({}) == 0


def test_quarantined_stock_not_counted():
    mock_batches, mock_outbox = setup_mock(threshold=10)
    mock_batches.insert_one(
        {
            "medicine_name": "MedZ",
            "batch_number": "B1",
            "quantity": 50,
            "expiry_date": make_date(30),
            "quarantined": True,
        }
    )

    assert check_and_notify_if_needed("MedZ") is not None


def test_outbox_returns_json():
    _, mock_outbox = setup_mock()
    mock_outbox.insert_one(
        {
            "medicine_name": "MedA",
            "current_quantity": 5,
            "threshold": 10,
            "message": "Re-order needed",
            "timestamp": make_date(0),
        }
    )

    with notifications.notifications_bp.test_request_context(
        "/outbox", headers={"Accept": "application/json"}
    ):
        resp = outbox_list()
        data = resp.get_json()

    assert len(data) == 1
    assert data[0]["medicine_name"] == "MedA"
