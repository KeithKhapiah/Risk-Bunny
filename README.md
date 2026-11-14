# Risk Bunny

Risk Bunny is a Streamlit dashboard for exploring UPI payment activity, merchant risk, and chargebacks. pandas loads and validates the analytical tables. DuckDB powers the natural-language query panel, and Plotly renders the results.

## Quick start

    git clone https://github.com/KeithKhapiah/Risk-Bunny.git
    cd Risk-Bunny
    python -m pip install -r requirements.txt
    python -m streamlit run dashboard/app.py

The dashboard starts with a deterministic synthetic demo when a complete local dataset is unavailable. It includes 120 fictional customers, 24 fictional merchants, 1,200 transactions, and 107 chargebacks across 90 days. The demo uses generated identifiers and needs no download, credentials, or external API.

## Explore the data

- **Executive Overview** shows payment volume, success rates, and the share of distinct transactions with a linked chargeback.
- **Fraud & Risk** surfaces high-risk segments, invalid UTRs, missing dimension matches, and chargeback patterns for review.
- **Merchant Analytics** compares transaction volume and chargeback exposure across merchants and categories.
- **Chargeback Analytics** shows disputed amounts, reporting delays, reasons, and resolution status.
- **Ask Risk Bunny** runs selected DuckDB queries offline. Try “Show daily transaction volume” or “Top merchants by chargebacks.” A Gemini API key in a local .env file enables optional model-generated queries with an offline fallback.

Dashboard filters apply to the four analytics sections. The query panel uses the full loaded dataset. Risk indicators are for review. The source tables describe customer-to-merchant payments and chargebacks.

## Data and validation

See the [data dictionary](DATA_DICTIONARY.md) for the original dataset schema. To use local data, put the following tables in data/processed/ or DATA/cleaned_data/ as CSV or Parquet:

| Table | Key |
| --- | --- |
| dim_customers | user_id |
| dim_merchants | merchant_id |
| fact_transactions | txn_id |
| fact_chargebacks | complaint_id |

Keep those files local. The dashboard preserves unmatched transactions and shows quality counts in the sidebar. The CLI reports missing and duplicate primary keys, unmatched references, and invalid transaction timestamps. It exits with a nonzero status when a check finds an issue.

    python risk_data.py --demo
    python risk_data.py
    python -m unittest discover -s tests -v

The tests check synthetic table integrity, offline queries, the read-only query boundary, and rendering for all four dashboard sections.

## License

No license has been specified.
