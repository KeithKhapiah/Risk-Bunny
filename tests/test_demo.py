import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

from agent.agent import get_duckdb_connection, query_agent, run_analytics_query
from risk_data import demo_tables, find_data_files, load_tables, quality_report


class DemoTests(unittest.TestCase):
    def test_demo_and_quality_checks(self):
        tables = demo_tables()
        self.assertEqual(len(tables["fact_transactions"]), 1200)
        self.assertEqual(len(tables["fact_chargebacks"]), 107)
        self.assertFalse(any(quality_report(tables).values()))
        transactions = tables["fact_transactions"]
        transactions.loc[1, "txn_id"] = transactions.loc[0, "txn_id"]
        transactions.loc[0, "user_id"] = "unknown"
        report = quality_report(tables)
        self.assertEqual(report["fact_transactions.duplicate_keys"], 1)
        self.assertEqual(report["transactions.unmatched_customers"], 1)

    def test_complete_local_csv_and_parquet_dataset(self):
        with TemporaryDirectory() as tmp, patch("risk_data.ROOT", Path(tmp)):
            data = Path(tmp) / "data" / "processed"
            data.mkdir(parents=True)
            tables = demo_tables()
            tables["dim_customers"].to_csv(data / "dim_customers.csv", index=False)
            self.assertEqual(find_data_files(), {})
            for name, table in tables.items():
                if name != "dim_customers":
                    table.to_parquet(data / f"{name}.parquet", index=False)
            loaded = load_tables(find_data_files())
            self.assertFalse(any(quality_report(loaded).values()))

    def test_offline_queries_and_read_only_boundary(self):
        with patch.dict("os.environ", {"GEMINI_API_KEY": ""}), patch(
            "agent.agent.find_data_files", return_value={}
        ):
            for question in (
                "Show daily transaction volume", "Show chargebacks by severity",
                "top merchants", "missing UTR by status", "top customers by disputed amount",
                "Which merchant categories have the highest chargebacks?",
                "chargeback reasons", "KYC verification", "reporting delay",
            ):
                with self.subTest(question=question):
                    result = query_agent(question)
                    self.assertIsNone(result.get("error"))
                    self.assertFalse(result["df"].empty)

            connection = get_duckdb_connection()
            for sql in ("DROP TABLE fact_transactions", "SELECT 1; SELECT 2"):
                with self.assertRaises(ValueError):
                    run_analytics_query(connection, sql)
            with self.assertRaisesRegex(Exception, "disabled"):
                run_analytics_query(connection, "SELECT * FROM read_csv_auto('outside.csv')")
            self.assertEqual(len(run_analytics_query(connection, "SELECT * FROM fact_transactions")), 500)

    def test_dashboard_sections(self):
        with patch("risk_data.find_data_files", return_value={}):
            entrypoint = Path(__file__).resolve().parents[1] / "dashboard" / "app.py"
            app = AppTest.from_file(str(entrypoint), default_timeout=30)
            app.session_state["boot_complete"] = True
            app.run()
            self.assertFalse(app.exception, app.exception)
            for section in ("Fraud & Risk", "Merchant Analytics", "Chargeback Analytics", "Executive Overview"):
                with self.subTest(section=section):
                    app.radio[0].set_value(section).run()
                    self.assertFalse(app.exception, app.exception)
            app.button(key="quick_failed").click().run()
            self.assertFalse(app.exception, app.exception)


if __name__ == "__main__":
    unittest.main()
