import mongomock
from datetime import datetime, timedelta

from routes import dispensing


def make_date(days_from_today):
    return datetime.combine((datetime.today() + timedelta(days=days_from_today)).date(), datetime.min.time())


def test_get_fefo_plan_fulfills_and_orders_batches():
    # prepare an in-memory mongo collection and inject into module
    client = mongomock.MongoClient()
    mock_batches = client["testdb"]["batches"]
    dispensing.batches = mock_batches

    # insert two valid batches: one expiring sooner
    mock_batches.insert_many(
        [
            {"medicine_name": "TestMed", "batch_number": "B1", "quantity": 5, "expiry_date": make_date(5)},
            {"medicine_name": "TestMed", "batch_number": "B2", "quantity": 10, "expiry_date": make_date(30)},
        ]
    )

    plan = dispensing.get_fefo_plan("TestMed", 12)
    assert plan["available"] == 15
    assert plan["fulfilled"] is True
    # Expect take from B1 first (FEFO)
    assert plan["plan"][0]["batch_number"] == "B1"
    assert plan["plan"][0]["take"] == 5
    assert plan["plan"][1]["batch_number"] == "B2"
    assert plan["plan"][1]["take"] == 7


def test_get_fefo_plan_insufficient_stock():
    client = mongomock.MongoClient()
    mock_batches = client["testdb"]["batches"]
    dispensing.batches = mock_batches

    mock_batches.insert_one({"medicine_name": "X", "batch_number": "XB", "quantity": 2, "expiry_date": make_date(10)})

    plan = dispensing.get_fefo_plan("X", 5)
    assert plan["available"] == 2
    assert plan["fulfilled"] is False
