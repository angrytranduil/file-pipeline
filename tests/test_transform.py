from src.transform import calculate_metrics


def test_calculate_metrics_for_orders():
    orders = [
        {
            "order_id": 1,
            "customer_id": 101,
            "order_date": "2026-09-01",
            "amount": 250.50,
            "status": "paid",
        },
        {
            "order_id": 2,
            "customer_id": 102,
            "order_date": "2026-09-01",
            "amount": 99.90,
            "status": "paid",
        },
        {
            "order_id": 3,
            "customer_id": 103,
            "order_date": "2026-09-02",
            "amount": 180.00,
            "status": "cancelled",
        },
        {
            "order_id": 4,
            "customer_id": 104,
            "order_date": "2026-09-02",
            "amount": 320.10,
            "status": "paid",
        },
        {
            "order_id": 5,
            "customer_id": 105,
            "order_date": "2026-09-03",
            "amount": 15.00,
            "status": "failed",
        },
    ]

    metrics = calculate_metrics(orders)

    assert metrics == {
        "orders_count": 5,
        "paid_orders_count": 3,
        "cancelled_orders_count": 1,
        "failed_orders_count": 1,
        "total_amount": 865.5,
        "paid_amount": 670.5,
        "average_paid_amount": 223.5,
    }


def test_calculate_metrics_for_empty_orders():
    orders = []

    metrics = calculate_metrics(orders)

    assert metrics == {
        "orders_count": 0,
        "paid_orders_count": 0,
        "cancelled_orders_count": 0,
        "failed_orders_count": 0,
        "total_amount": 0,
        "paid_amount": 0,
        "average_paid_amount": None,
    }


def test_calculate_metrics_without_paid_orders():
    orders = [
        {
            "order_id": 3,
            "customer_id": 103,
            "order_date": "2026-09-02",
            "amount": 180.00,
            "status": "cancelled",
        },
        {
            "order_id": 5,
            "customer_id": 105,
            "order_date": "2026-09-03",
            "amount": 15.00,
            "status": "failed",
        },
    ]

    metrics = calculate_metrics(orders)

    assert metrics["paid_orders_count"] == 0
    assert metrics["paid_amount"] == 0
    assert metrics["average_paid_amount"] is None
