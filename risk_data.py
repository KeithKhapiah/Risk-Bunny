"""Load the analytics tables, or construct a reproducible synthetic demo."""

from datetime import datetime, timedelta
from pathlib import Path
from random import Random

import pandas as pd


ROOT = Path(__file__).resolve().parent
PRIMARY_KEYS = {
    "dim_customers": "user_id",
    "dim_merchants": "merchant_id",
    "fact_transactions": "txn_id",
    "fact_chargebacks": "complaint_id",
}
DATE_COLUMNS = {
    "dim_customers": ["date_of_birth_clean", "signup_timestamp_clean"],
    "dim_merchants": ["onboarding_date_clean"],
    "fact_transactions": ["txn_timestamp"],
    "fact_chargebacks": [
        "transaction_timestamp_clean", "reported_timestamp_clean",
        "bank_response_timestamp_clean",
    ],
}


def find_data_files():
    candidates = ("data/processed", "data", "DATA/cleaned_data", "cleaned_data")
    for relative in candidates:
        directory = ROOT / relative
        files = {}
        for table in PRIMARY_KEYS:
            parquet = directory / f"{table}.parquet"
            csv = directory / f"{table}.csv"
            files[table] = parquet if parquet.is_file() else csv
        if all(path.is_file() for path in files.values()):
            return files
    return {}


def demo_tables():
    random = Random(21)
    start = datetime(2026, 1, 1)
    categories = ["Grocery", "Apparel", "Telecom", "Transportation"]
    customers = [
        {
            "user_id": f"DEMO-C{i:03}", "full_name": f"Demo customer {i:03}",
            "city_clean": "Demo city", "state": "Demo region",
            "monthly_income_clean": 25000 + i * 250,
            "kyc_status_clean": "PENDING" if i % 7 == 0 else "VERIFIED",
            "risk_segment_clean": ["LOW", "MEDIUM", "HIGH", "UNKNOWN"][i % 4],
        }
        for i in range(1, 121)
    ]
    merchants = [
        {
            "merchant_id": f"DEMO-M{i:02}", "merchant_name": f"Demo merchant {i:02}",
            "merchant_category_clean": categories[i % 4],
            "merchant_status_clean": "SUSPENDED" if i % 11 == 0 else "ACTIVE",
            "business_type_clean": "Demo business",
            "city_clean": "Demo city", "state": "Demo region",
            "declared_avg_ticket_size_clean": 500 + i * 25,
            "settlement_account_on_file": i % 11 != 0,
        }
        for i in range(1, 25)
    ]
    transactions, chargebacks = [], []
    for i in range(1, 1201):
        customer = random.choice(customers)
        merchant = random.choice(merchants)
        timestamp = start + timedelta(days=(i - 1) % 90, minutes=random.randrange(1440))
        status = random.choices(["SUCCESS", "FAILED", "PENDING"], [78, 17, 5])[0]
        amount = random.randrange(2500, 250001) / 100
        keys = {"txn_id": f"DEMO-T{i:04}", "user_id": customer["user_id"],
                "merchant_id": merchant["merchant_id"],
                "merchant_category_final": merchant["merchant_category_clean"]}
        transactions.append({
            **keys, "amount": amount, "txn_timestamp": timestamp, "status_clean": status,
            "risk_segment_clean": customer["risk_segment_clean"],
            "kyc_status_clean": customer["kyc_status_clean"],
            "has_kyc_match": True, "has_merchant_match": True,
            "utr_missing_or_invalid": random.random() < (0.25 if status == "FAILED" else 0.04),
            "amount_was_negative": False,
        })
        if status == "SUCCESS" and i % 9 == 0:
            delay = random.randint(1, 20)
            chargebacks.append({
                **keys, "complaint_id": f"DEMO-D{i:04}",
                "txn_amount": amount, "txn_status": status,
                "disputed_amount_clean": round(amount * random.choice([0.5, 1]), 2),
                "report_delay_days": delay, "transaction_timestamp_clean": timestamp,
                "reported_timestamp_clean": timestamp + timedelta(days=delay),
                "resolution_status_clean": random.choice(["UNDER_REVIEW", "RESOLVED", "CLOSED"]),
                "severity_clean": random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"]),
                "reason_code_clean": random.choice(["Duplicate Debit", "Service Not Delivered", "Account Takeover"]),
                "channel_clean": random.choice(["App", "Call Center", "IVR"]),
            })
    return dict(zip(PRIMARY_KEYS, map(pd.DataFrame, (customers, merchants, transactions, chargebacks))))


def load_tables(files):
    tables = {}
    for name, path in files.items():
        reader = pd.read_parquet if path.suffix == ".parquet" else pd.read_csv
        frame = reader(path)
        for column in DATE_COLUMNS[name]:
            if column in frame:
                frame[column] = pd.to_datetime(frame[column], errors="coerce")
        tables[name] = frame
    return tables if files else demo_tables()


def quality_report(tables):
    report = {}
    for name, key in PRIMARY_KEYS.items():
        values = tables[name][key]
        report[f"{name}.null_keys"] = int(values.isna().sum())
        report[f"{name}.duplicate_keys"] = int(values.dropna().duplicated().sum())
    transactions = tables["fact_transactions"]
    chargebacks = tables["fact_chargebacks"]
    report["transactions.unmatched_customers"] = int(
        (~transactions["user_id"].isin(tables["dim_customers"]["user_id"])).sum()
    )
    report["transactions.unmatched_merchants"] = int(
        (~transactions["merchant_id"].isin(tables["dim_merchants"]["merchant_id"])).sum()
    )
    report["chargebacks.unmatched_transactions"] = int(
        (~chargebacks["txn_id"].isin(transactions["txn_id"])).sum()
    )
    report["transactions.invalid_timestamps"] = int(transactions["txn_timestamp"].isna().sum())
    return report


if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Check Risk Bunny primary keys, joins and timestamps.")
    parser.add_argument("--demo", action="store_true", help="Check the built-in synthetic tables.")
    args = parser.parse_args()
    files = {} if args.demo else find_data_files()
    tables = load_tables(files)
    issues = quality_report(tables)
    print(json.dumps({
        "mode": "local" if files else "synthetic demo",
        "rows": {name: len(frame) for name, frame in tables.items()},
        "issues": issues,
    }, indent=2))
    raise SystemExit(int(any(issues.values())))
