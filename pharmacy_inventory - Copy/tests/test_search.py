import mongomock
from datetime import datetime, timedelta

from routes import search


def make_date(days_from_today):
    return datetime.combine((datetime.today() + timedelta(days=days_from_today)).date(), datetime.min.time())


def test_search_sellable_stock_counts_only_in_date_batches():
    client = mongomock.MongoClient()
    mock_batches = client["testdb"]["batches"]
    # inject into module
    search.batches = mock_batches

    mock_batches.insert_many(
        [
            {"medicine_name": "Y", "batch_number": "Y1", "quantity": 5, "expiry_date": make_date(10)},
            {"medicine_name": "Y", "batch_number": "Y2", "quantity": 3, "expiry_date": make_date(-1)},  # expired
        ]
    )

    # replicate logic used in search route
    pipeline = [
        {
            "$match": {"medicine_name": "Y", "expiry_date": {"$gte": search.today_start()}},
        },
        {"$group": {"_id": "$medicine_name", "total": {"$sum": "$quantity"}}},
    ]
    agg = list(mock_batches.aggregate(pipeline))
    sellable_stock = agg[0]["total"] if agg else 0
    assert sellable_stock == 5
