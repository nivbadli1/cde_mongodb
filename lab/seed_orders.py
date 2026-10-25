"""
seed_orders.py - builds the practice dataset for the Naya MongoDB lesson.

Creates 200 "orders" documents for a fictional Israeli e-commerce shop,
with intentionally MESSY fields (this is the point of the exercise):
  - total:       Decimal128 / double / string / missing
  - status:      mixed case ("shipped", "SHIPPED", "Shipped") / missing
  - created_at:  BSON Date / ISO string / epoch-millis integer
  - customer:    schema v1 has customer.email,
                 schema v2 moved it to customer.contact.email (+ phone)
  - items:       array of 0-4 sub-documents; qty sometimes a string
  - tags:        array / single string / missing
  - city:        "Tel Aviv" / "tel aviv" / "Tel-Aviv" ...
  - coupon:      string / null / missing
  - 2 duplicated order_id values (for data-quality checks)

Usage (MongoDB running as replica set rs0):
    pip install "pymongo==4.18.3"
    python seed_orders.py                       # inserts into shop.orders
    python seed_orders.py --json-only           # only writes orders.json
The connection string comes from $MONGO_URI (set inside dev_env), else localhost.

orders.json is canonical Extended JSON, so this also works:
    mongoimport --uri "mongodb://localhost:27017/?directConnection=true" \
        --db shop --collection orders --jsonArray --file orders.json

Tested with: Python 3.12/3.13, PyMongo 4.18+, MongoDB 8.0 (also valid for 7.0 / 9.0).
The generator is deterministic (seed=42): every student gets the same data,
so the "expected outputs" in the practice guide match.
"""
import argparse
import os
import random
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from bson import Decimal128, ObjectId
from bson.json_util import dumps, JSONOptions, JSONMode

SEED = 42
N_DOCS = 200
SCHEMA_V2_FROM = datetime(2026, 6, 1, tzinfo=timezone.utc)  # app release that moved email
START = datetime(2026, 1, 1, tzinfo=timezone.utc)

FIRST = ["Noa", "Yonatan", "Maya", "Itai", "Tamar", "Omer", "Shira", "Daniel",
         "Yael", "Amit", "Lior", "Roni", "Eden", "Guy", "Michal", "Ariel"]
LAST = ["Cohen", "Levi", "Mizrahi", "Peretz", "Biton", "Friedman", "Azoulay",
        "Katz", "Shapiro", "Ben-David", "Golan", "Avraham"]
CITIES = {
    "Tel Aviv": ["Tel Aviv", "Tel Aviv", "tel aviv", "Tel-Aviv", "TLV"],
    "Haifa": ["Haifa", "Haifa", "haifa"],
    "Jerusalem": ["Jerusalem", "Jerusalem", "jerusalem"],
    "Netanya": ["Netanya", "Netanya"],
    "Be'er Sheva": ["Be'er Sheva", "Beer Sheva"],
    "Rishon LeZion": ["Rishon LeZion", "Rishon Lezion"],
}
PRODUCTS = [  # sku, name, price (ILS)
    ("SKU-100", "Running Shoes", 349.90), ("SKU-101", "Yoga Mat", 89.90),
    ("SKU-102", "Water Bottle", 39.90), ("SKU-103", "Smart Watch", 899.00),
    ("SKU-104", "Headphones", 499.00), ("SKU-105", "Backpack", 229.00),
    ("SKU-106", "Sunglasses", 179.00), ("SKU-107", "Bike Helmet", 259.00),
]
STATUSES = ["created", "paid", "shipped", "delivered", "cancelled"]
PAYMENTS = ["credit_card", "paypal", "bit", "apple_pay"]
TAGS = ["gift", "express", "first_order", "vip", "sale"]


def build_docs():
    rnd = random.Random(SEED)
    docs = []
    for i in range(N_DOCS):
        created = START + timedelta(minutes=rnd.randint(0, 290 * 24 * 60))
        cust_no = rnd.randint(1, 60)
        first, last = rnd.choice(FIRST), rnd.choice(LAST)
        canonical_city = rnd.choice(list(CITIES))
        city = rnd.choice(CITIES[canonical_city])

        # ---- items (array of sub-documents) --------------------------------
        items = []
        for _ in range(rnd.choice([0, 1, 1, 2, 2, 3, 4]) if i % 25 else 0):
            sku, name, price = rnd.choice(PRODUCTS)
            qty = rnd.randint(1, 3)
            items.append({
                "sku": sku, "name": name,
                "qty": str(qty) if rnd.random() < 0.1 else qty,   # mixed type!
                "unit_price": price,
            })
        amount = round(sum(int(it["qty"]) * it["unit_price"] for it in items), 2)

        # ---- customer: schema drift v1 -> v2 -------------------------------
        email = f"{first}.{last}{cust_no}@example.com".lower().replace("'", "")
        customer = {"customer_id": f"C{cust_no:04d}", "name": f"{first} {last}"}
        if created < SCHEMA_V2_FROM:
            schema_v = 1
            customer["email"] = email
        else:
            schema_v = 2
            customer["contact"] = {"email": email,
                                   "phone": f"+972-5{rnd.randint(0, 9)}-{rnd.randint(1000000, 9999999)}"}

        doc = {
            # deterministic ObjectId: 4-byte timestamp = order time, rest = counter
            "_id": ObjectId(f"{int(created.timestamp()):08x}{i:016x}"),
            "order_id": f"ORD-{10000 + i}",
            "schema_v": schema_v,
            "customer": customer,
            "shipping": {"address": {"city": city, "country": "IL"}},
            "items": items,
        }

        # ---- total: Decimal128 / double / string / missing -----------------
        r = rnd.random()
        if r < 0.60:
            doc["total"] = Decimal128(Decimal(f"{amount:.2f}"))
        elif r < 0.85:
            doc["total"] = float(amount)
        elif r < 0.95:
            doc["total"] = f"{amount:.2f}"          # a string. Classic.
        # else: missing

        # ---- status: mixed case / missing ----------------------------------
        r = rnd.random()
        status = rnd.choice(STATUSES)
        if r < 0.85:
            doc["status"] = status
        elif r < 0.92:
            doc["status"] = status.upper()
        elif r < 0.97:
            doc["status"] = status.capitalize()
        # else: missing

        # ---- created_at: Date / ISO string / epoch millis ------------------
        r = rnd.random()
        if r < 0.85:
            doc["created_at"] = created
        elif r < 0.95:
            doc["created_at"] = created.strftime("%Y-%m-%dT%H:%M:%SZ")
        else:
            doc["created_at"] = int(created.timestamp() * 1000)

        # ---- payment: sometimes missing ------------------------------------
        if rnd.random() < 0.9:
            doc["payment"] = {"method": rnd.choice(PAYMENTS),
                              "installments": rnd.choice([1, 1, 1, 3, 6])}

        # ---- tags: array / string / missing --------------------------------
        r = rnd.random()
        if r < 0.6:
            doc["tags"] = rnd.sample(TAGS, rnd.randint(1, 2))
        elif r < 0.75:
            doc["tags"] = rnd.choice(TAGS)
        # else: missing

        # ---- coupon: string / null / missing -------------------------------
        r = rnd.random()
        if r < 0.2:
            doc["coupon"] = rnd.choice(["WELCOME10", "SUMMER26", "VIP15"])
        elif r < 0.5:
            doc["coupon"] = None

        docs.append(doc)

    # two duplicated business keys (a bug in the app's retry logic)
    docs[150]["order_id"] = docs[10]["order_id"]
    docs[151]["order_id"] = docs[11]["order_id"]
    return docs


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--uri", default=os.getenv("MONGO_URI", "mongodb://localhost:27017/?directConnection=true"))
    p.add_argument("--json-only", action="store_true")
    args = p.parse_args()

    docs = build_docs()
    with open("orders.json", "w", encoding="utf-8") as f:
        f.write(dumps(docs, json_options=JSONOptions(json_mode=JSONMode.CANONICAL), indent=1))
    print(f"wrote orders.json ({len(docs)} docs)")

    if args.json_only:
        return
    from pymongo import MongoClient
    client = MongoClient(args.uri)
    coll = client["shop"]["orders"]
    coll.drop()
    coll.insert_many(docs)
    print(f"inserted {coll.count_documents({})} docs into shop.orders")


if __name__ == "__main__":
    main()
