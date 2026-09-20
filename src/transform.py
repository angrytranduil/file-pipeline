from src.schemas import Metrics, Order


def calculate_metrics(orders: list[Order]) -> Metrics:
    orders_count = len(orders)

    paid_orders_count = 0
    cancelled_orders_count = 0
    failed_orders_count = 0

    total_amount = 0.0
    paid_amount = 0.0

    for order in orders:
        amount = order["amount"]
        status = order["status"]

        total_amount += amount

        if status == "paid":
            paid_orders_count += 1
            paid_amount += amount
        elif status == "cancelled":
            cancelled_orders_count += 1
        elif status == "failed":
            failed_orders_count += 1

    if paid_orders_count == 0:
        average_paid_amount = None
    else:
        average_paid_amount = paid_amount / paid_orders_count

    return {
        "orders_count": orders_count,
        "paid_orders_count": paid_orders_count,
        "cancelled_orders_count": cancelled_orders_count,
        "failed_orders_count": failed_orders_count,
        "total_amount": round(total_amount, 2),
        "paid_amount": round(paid_amount, 2),
        "average_paid_amount": (
            None if average_paid_amount is None else round(average_paid_amount, 2)
        ),
    }


if __name__ == "__main__":
    orders: list[Order] = [
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

    print(calculate_metrics(orders))
