# 🐰 Risk Bunny — UPI Fraud Ring & Merchant Analytics

Risk Bunny is an interactive UPI transaction monitoring, fraud-ring detection, and merchant chargeback analytics platform, powered by DuckDB (OLAP engine) and Risk Bunny — AI Agent that answers questions about the data in natural language.


## Features

- **Executive Overview** - Shows Realtime throughputs, transaction volumes, success rates and live chargeback ratio tracking.
- **Fraud and Risk intelligence** - Identify high-risk customer segments, spot unusual transaction patterns, and understand where transaction failures are happening most often.
- **Merchant Analysis** - Merchant category concentration, chargeback dispute rates, and vendor risk profiles.
- **Chargeback Analytics** - Explore why chargebacks happen by looking at dispute types, banks involved, and transaction activity across different velocity ranges.
- **Interactive Filter** - Easily filter the dashboard in real time by transaction status, merchant category, and risk level.
- **Risk Bunny AI Agent** - Ask questions about the data in plain English. Risk Bunny turns your questions into DuckDB SQL queries and presents the results with dynamic Plotly visualizations.


---

# Quick Start

### 1 - Clone the Repository

```bash
git clone https://github.com/KeithKhapiah/Risk-Bunny.git
cd Risk-Bunny
```

### 2 - Install Requirements

```bash
pip install -r requirements.txt
```

### 3 - Add the Local Dataset

The `DATA/` directory is intentionally excluded from Git because the supplied
synthetic dataset contains realistic KYC and financial fields. Place these
generated CSV files in `DATA/cleaned_data/` before running the dashboard:

- `dim_customers.csv`
- `dim_merchants.csv`
- `fact_transactions.csv`
- `fact_chargebacks.csv`

### 4 - Configure Risk-Bunny Agent

Create a Gemini API key and save it in a local `.env` file. Never commit that file.

### 5 - Launch the Application

```bash
python -m streamlit run dashboard/app.py
```

---

## Dashboard Preview

### Executive Overview

<img width="2560" height="1600" alt="Screenshot 2026-09-15 141557" src="https://github.com/user-attachments/assets/be108662-9d3b-4f0d-9130-d743ae19cd1a" />

### Fraud & Risk Intelligence

<img width="1266" height="708" alt="Screenshot 2026-09-15 182124" src="https://github.com/user-attachments/assets/b7e2e612-27cb-418a-af43-544c5e20e021" />

### Risk Bunny AI Agent

<img width="1277" height="658" alt="Screenshot 2026-09-15 182147" src="https://github.com/user-attachments/assets/6cbe358b-b758-44fb-a158-4ce044648c98" />

---
## Tech Stack

- **Streamlit** — Web framework used to build the interactive dashboard UI, navigation, and sidebar filter controls.
- **DuckDB** — Fast in-memory SQL analytics engine used to query transactions, chargebacks, and merchant data directly in memory.
- **Pandas** — Data processing and transformation library used for loading CSVs, cleaning, joining, and aggregating dataset records.
- **Plotly** — Interactive charting library used for building financial trendlines, risk matrices, heatmaps, and distribution graphs.
- **Google Gemini API (google-generativeai)** — Large Language Model used by Risk Bunny to convert plain English questions into DuckDB SQL queries and executive summaries.
- **python-dotenv** — Environment configuration tool used to securely load API keys from local .env files without hardcoding secrets.

## Live Link
```bash
https://risk-bunny.streamlit.app/
```

## License

This project is currently not licensed.
