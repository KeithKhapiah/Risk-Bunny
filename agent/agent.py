"""
AI Risk Agent module powered by DuckDB with optional Google Gemini.
Translates Natural Language business questions into SQL, executes them,
renders styled Plotly charts, and provides executive takeaways.
"""

import os
import re
import json
from functools import lru_cache

import duckdb

from risk_data import find_data_files, load_tables
try:
    import plotly.express as px
    import plotly.graph_objects as go
    HAS_PLOTLY = True
except ImportError:
    px = None
    go = None
    HAS_PLOTLY = False
from pathlib import Path
from dotenv import load_dotenv

def load_app_env():
    here = Path(__file__).resolve().parent
    repo_root = here.parent
    candidates = [
        repo_root / ".env",
        here / ".env",
        here / "DATA" / ".env",
        repo_root / "DATA" / ".env",
        Path(".env").resolve(),
        Path("DATA/.env").resolve(),
    ]
    for c in candidates:
        if c.exists():
            load_dotenv(dotenv_path=c)
            return
    load_dotenv()

load_app_env()

@lru_cache(maxsize=4)
def load_database(file_versions):
    files = {name: path for name, path, _mtime in file_versions}
    connection = duckdb.connect(":memory:", config={
        "allow_unsigned_extensions": "false", "threads": "2",
    })
    for name, frame in load_tables(files).items():
        connection.register("incoming_table", frame)
        connection.execute(f"CREATE TABLE {name} AS SELECT * FROM incoming_table")
        connection.unregister("incoming_table")
    connection.execute("SET enable_external_access = false")
    return connection


def get_duckdb_connection():
    return load_database(tuple(
        (name, path, path.stat().st_mtime_ns) for name, path in find_data_files().items()
    ))


def run_analytics_query(connection, sql):
    statements = connection.extract_statements(sql)
    if len(statements) != 1 or statements[0].type != duckdb.StatementType.SELECT:
        raise ValueError("Only one read-only SELECT query is allowed.")
    # A cursor has independent result state when multiple Streamlit sessions query concurrently.
    return connection.cursor().execute(
        f"SELECT * FROM ({statements[0].query.strip().removesuffix(';')}) AS result LIMIT 500"
    ).df()


SYSTEM_PROMPT = """You are an elite FinTech Data Analyst Agent for a National Payments Authority.
Your task is to answer business questions about UPI transactions, merchant risk, and fraud chargebacks.

You have access to 4 tables in a SQL database:

1. `fact_transactions`:
   - txn_id (VARCHAR), user_id (VARCHAR), merchant_id (VARCHAR), amount (FLOAT)
   - txn_timestamp (TIMESTAMP), status_clean (VARCHAR: 'SUCCESS', 'FAILED', 'PENDING')
   - merchant_category_final (VARCHAR: 'Grocery', 'Hotel / Lodging', 'Telecom', 'Transportation', etc.)
   - has_kyc_match (BOOLEAN), has_merchant_match (BOOLEAN), utr_missing_or_invalid (BOOLEAN)

2. `fact_chargebacks`:
   - complaint_id (VARCHAR), txn_id (VARCHAR), user_id (VARCHAR), merchant_id (VARCHAR)
   - disputed_amount_clean (FLOAT), report_delay_days (FLOAT)
   - resolution_status_clean (VARCHAR: 'OPEN', 'IN_PROGRESS', 'CLOSED', 'REJECTED')
   - severity_clean (VARCHAR: 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW')
   - reason_code_clean (VARCHAR: 'Duplicate Debit', 'Service Not Delivered', 'Account Takeover', etc.)
   - channel_clean (VARCHAR: 'IVR', 'App', 'Call Center', 'Chatbot', etc.)
   - txn_amount (FLOAT), txn_status (VARCHAR)

3. `dim_merchants`:
   - merchant_id (VARCHAR), merchant_name (VARCHAR), business_type_clean (VARCHAR)
   - city_clean (VARCHAR), state (VARCHAR), merchant_status_clean (VARCHAR: 'ACTIVE', 'INACTIVE', 'SUSPENDED')
   - declared_avg_ticket_size_clean (FLOAT), settlement_account_on_file (BOOLEAN)

4. `dim_customers`:
   - user_id (VARCHAR), full_name (VARCHAR), city_clean (VARCHAR), state (VARCHAR)
   - monthly_income_clean (FLOAT), kyc_status_clean (VARCHAR: 'VERIFIED', 'PENDING', 'REJECTED')
   - risk_segment_clean (VARCHAR: 'LOW', 'MEDIUM', 'HIGH')

Guidelines:
- For UPI database questions (transactions, merchants, chargebacks, fraud):
  Return only a single valid JSON object with:
  "sql_query": "SELECT ... FROM ...",
  "chart_type": "bar" | "line" | "scatter" | "table",
  "x_axis": "column_name_for_x",
  "y_axis": "column_name_for_y",
  "chart_title": "Professional Graph Title",
  "executive_summary": "2-3 sentence executive business takeaway summarizing the insights."
- For general coding, mathematics, or questions unrelated to the payment database (e.g. "code to find prime number", python help):
  Return:
  "sql_query": "",
  "chart_type": "none",
  "x_axis": "",
  "y_axis": "",
  "chart_title": "Risk Bunny Assistant",
  "executive_summary": "Direct, helpful answer including formatted code blocks if requested."
- Use DuckDB SQL. Always use COALESCE and LIMIT where appropriate.
"""

def fallback_semantic_query(question: str):
    """
    Intelligent offline rule-based semantic parser.
    Covers the 15+ standard Datathon questions from track1_dataset_notes.txt,
    as well as general queries and coding requests.
    """
    q = question.lower().strip()

    # 1. Code to find prime numbers
    if any(k in q for k in ["prime", "prime number", "prime nymber", "primes"]):
        return {
            "sql_query": "",
            "chart_type": "none",
            "x_axis": "",
            "y_axis": "",
            "chart_title": "Python: Find Prime Numbers",
            "executive_summary": """Here is Python code to check for and find prime numbers:

```python
def is_prime(n: int) -> bool:
    \"\"\"Return True if n is prime, else False.\"\"\"
    if n <= 1:
        return False
    if n <= 3:
        return True
    if n % 2 == 0 or n % 3 == 0:
        return False
    i = 5
    while i * i <= n:
        if n % i == 0 or n % (i + 2) == 0:
            return False
        i += 6
    return True

def find_primes_up_to(limit: int) -> list[int]:
    \"\"\"Find all prime numbers up to `limit` using the Sieve of Eratosthenes.\"\"\"
    if limit < 2:
        return []
    sieve = [True] * (limit + 1)
    sieve[0] = sieve[1] = False
    for p in range(2, int(limit ** 0.5) + 1):
        if sieve[p]:
            for i in range(p * p, limit + 1, p):
                sieve[i] = False
    return [num for num, prime in enumerate(sieve) if prime]

# Example:
print("Is 29 prime?", is_prime(29))
print("Primes up to 50:", find_primes_up_to(50))
```

*Tip: You can also ask me questions about your **UPI transactions, fraud rings, merchant exposure, or chargebacks**!*"""
        }

    # 2. General coding / script requests
    elif any(k in q for k in ["code", "python", "script", "algorithm", "function"]) and not any(k in q for k in ["sql", "query", "transaction", "merchant", "fraud", "chargeback"]):
        return {
            "sql_query": "",
            "chart_type": "none",
            "x_axis": "",
            "y_axis": "",
            "chart_title": "Python Assistant",
            "executive_summary": "I'm happy to help with coding questions! As **Risk Bunny**, my primary specialization is analyzing **UPI payment transactions, merchant risk clusters, and fraud chargebacks**. Let me know what specific script or financial analysis you'd like to perform."
        }

    # 3. Greetings & capabilities
    elif any(k in q for k in ["hello", "hi", "hey", "who are you", "what can you do", "help"]) and not any(k in q for k in ["transaction", "merchant", "fraud", "chargeback"]):
        return {
            "sql_query": "",
            "chart_type": "none",
            "x_axis": "",
            "y_axis": "",
            "chart_title": "Risk Bunny AI Copilot",
            "executive_summary": "👋 Hi! I am **Risk Bunny**, your UPI fraud intelligence copilot. I can query the transactions, merchants, and chargebacks loaded into DuckDB.\n\nTry asking:\n- *Which merchant categories have the highest chargebacks?*\n- *Show daily transaction volume and failure spikes.*\n- *What is the correlation between missing UTR and transaction status?*\n- *Who are the top 10 serial disputers by disputed value?*"
        }

    elif any(k in q for k in ["category", "categories", "mcc"]) and any(k in q for k in ["chargeback", "dispute", "highest"]):
        return {
            "sql_query": """
                SELECT 
                    COALESCE(ft.merchant_category_final, 'Unknown') AS merchant_category, 
                    COUNT(fc.complaint_id) AS total_chargebacks, 
                    ROUND(SUM(fc.disputed_amount_clean), 2) AS total_disputed_amount 
                FROM fact_chargebacks fc 
                JOIN fact_transactions ft ON fc.txn_id = ft.txn_id 
                GROUP BY ft.merchant_category_final 
                ORDER BY total_chargebacks DESC 
                LIMIT 10
            """,
            "chart_type": "bar",
            "x_axis": "merchant_category",
            "y_axis": "total_chargebacks",
            "chart_title": "Top Merchant Categories by Dispute Claims",
            "executive_summary": "Grocery, Transportation, and Hotel/Lodging drive over 60% of all consumer dispute volume. High dispute concentrations in rapid micro-transactions highlight potential merchant point-of-sale friction and delayed delivery issues."
        }

    elif any(k in q for k in ["daily", "trend", "volume", "day", "time"]) and not any(k in q for k in ["user", "merchant"]):
        return {
            "sql_query": """
                SELECT 
                    CAST(txn_timestamp AS DATE) AS txn_date,
                    COUNT(txn_id) AS total_transactions,
                    ROUND(SUM(amount), 2) AS total_volume,
                    SUM(CASE WHEN status_clean = 'FAILED' THEN 1 ELSE 0 END) AS failed_count
                FROM fact_transactions
                WHERE txn_timestamp IS NOT NULL
                GROUP BY txn_date
                ORDER BY txn_date ASC
            """,
            "chart_type": "line",
            "x_axis": "txn_date",
            "y_axis": "total_volume",
            "chart_title": "Daily UPI Transaction Volume & Failures",
            "executive_summary": "Transaction velocity shows healthy weekday stability with recurring weekend volatility. Periodic failure spikes correlate with gateway downtime and unverified user activity spikes."
        }

    elif any(k in q for k in ["top merchant", "merchant count", "highest chargeback", "highest dispute"]):
        return {
            "sql_query": """
                SELECT 
                    COALESCE(dm.merchant_name, fc.merchant_id) AS merchant_name,
                    COUNT(fc.complaint_id) AS dispute_count,
                    ROUND(SUM(fc.disputed_amount_clean), 2) AS total_disputed_amount,
                    COALESCE(dm.merchant_status_clean, 'ACTIVE') AS status
                FROM fact_chargebacks fc
                LEFT JOIN dim_merchants dm ON fc.merchant_id = dm.merchant_id
                GROUP BY 1, 4
                ORDER BY dispute_count DESC
                LIMIT 10
            """,
            "chart_type": "bar",
            "x_axis": "merchant_name",
            "y_axis": "dispute_count",
            "chart_title": "Top Merchants by Chargeback Complaint Volume",
            "executive_summary": "A concentrated cluster of top 10 merchants generates disproportionate dispute volume. Risk ops should flag accounts exceeding a 3.5% chargeback-to-transaction threshold for merchant account suspension."
        }

    elif any(k in q for k in ["user", "customer"]) and any(k in q for k in ["top", "disputed", "highest", "amount"]):
        return {
            "sql_query": """
                SELECT 
                    COALESCE(dc.full_name, fc.user_id) AS customer_name,
                    COUNT(fc.complaint_id) AS dispute_count,
                    ROUND(SUM(fc.disputed_amount_clean), 2) AS total_disputed_value,
                    COALESCE(dc.risk_segment_clean, 'UNKNOWN') AS risk_segment
                FROM fact_chargebacks fc
                LEFT JOIN dim_customers dc ON fc.user_id = dc.user_id
                GROUP BY 1, 4
                ORDER BY total_disputed_value DESC
                LIMIT 10
            """,
            "chart_type": "bar",
            "x_axis": "customer_name",
            "y_axis": "total_disputed_value",
            "chart_title": "Top Users by Total Disputed Value",
            "executive_summary": "Top high-value dispute claims stem primarily from users flagged in High or Medium risk segments. Multiple repeat claims from single synthetic identities warrant immediate automated KYC re-verification."
        }

    elif any(k in q for k in ["reason", "cause", "complaint reason"]):
        return {
            "sql_query": """
                SELECT 
                    reason_code_clean AS dispute_reason,
                    COUNT(complaint_id) AS complaint_count,
                    ROUND(SUM(disputed_amount_clean), 2) AS total_amount
                FROM fact_chargebacks
                GROUP BY reason_code_clean
                ORDER BY complaint_count DESC
            """,
            "chart_type": "bar",
            "x_axis": "dispute_reason",
            "y_axis": "complaint_count",
            "chart_title": "Dispute Reason Distribution",
            "executive_summary": "Service Not Delivered and Duplicate Debit constitute over 70% of consumer chargebacks. Account Takeover claims show the highest average ticket size, indicating targeted credential theft."
        }

    elif any(k in q for k in ["severity", "p1", "critical", "high"]):
        return {
            "sql_query": """
                SELECT 
                    severity_clean AS severity_level,
                    COUNT(complaint_id) AS total_disputes,
                    ROUND(SUM(disputed_amount_clean), 2) AS total_disputed_amount
                FROM fact_chargebacks
                GROUP BY severity_clean
                ORDER BY total_disputes DESC
            """,
            "chart_type": "bar",
            "x_axis": "severity_level",
            "y_axis": "total_disputes",
            "chart_title": "Chargebacks by Severity Classification",
            "executive_summary": "Critical and High severity disputes represent urgent regulatory liability. Automated SLA escalations are active for all claims unresolved beyond 48 hours."
        }

    elif any(k in q for k in ["utr", "missing utr", "invalid utr"]):
        return {
            "sql_query": """
                SELECT 
                    status_clean AS txn_status,
                    utr_missing_or_invalid,
                    COUNT(txn_id) AS transaction_count,
                    ROUND(AVG(amount), 2) AS avg_amount
                FROM fact_transactions
                GROUP BY txn_status, utr_missing_or_invalid
                ORDER BY txn_status, utr_missing_or_invalid
            """,
            "chart_type": "bar",
            "x_axis": "txn_status",
            "y_axis": "transaction_count",
            "chart_title": "Missing/Invalid UTR Impact on Transaction Status",
            "executive_summary": "Missing or corrupted UTR numbers correlate with an 8.4x increase in failed and disputed transactions. Enforcing strict NPCI-compliant 12-digit UTR validation at the switch reduces dropped debits significantly."
        }

    elif any(k in q for k in ["kyc", "verification", "verified", "rejected"]):
        return {
            "sql_query": """
                SELECT 
                    COALESCE(kyc_status_clean, 'UNMATCHED') AS kyc_status,
                    COUNT(txn_id) AS total_txns,
                    ROUND(SUM(amount), 2) AS total_volume,
                    ROUND(AVG(amount), 2) AS avg_ticket_size
                FROM fact_transactions
                GROUP BY kyc_status
                ORDER BY total_volume DESC
            """,
            "chart_type": "bar",
            "x_axis": "kyc_status",
            "y_axis": "total_volume",
            "chart_title": "UPI Volume Distribution by KYC Status",
            "executive_summary": "Verified users account for 82% of total transaction volume. However, rejected and pending KYC accounts account for over 38% of total dispute amounts, validating strict onboarding gatekeeping."
        }

    elif any(k in q for k in ["delay", "reporting delay", "lag"]):
        return {
            "sql_query": """
                SELECT 
                    CAST(report_delay_days AS INTEGER) AS delay_days,
                    COUNT(complaint_id) AS dispute_count,
                    ROUND(AVG(disputed_amount_clean), 2) AS avg_disputed_amount
                FROM fact_chargebacks
                WHERE report_delay_days IS NOT NULL AND report_delay_days <= 30
                GROUP BY delay_days
                ORDER BY delay_days ASC
            """,
            "chart_type": "bar",
            "x_axis": "delay_days",
            "y_axis": "dispute_count",
            "chart_title": "Chargeback Reporting Delay Distribution (Days)",
            "executive_summary": "Most consumers report transaction issues within 1-4 days. Long-tail disputes reported after 10+ days have a 4x higher incidence of Account Takeover and compromised credentials."
        }

    else:
        # Check if the query has any financial/UPI context
        has_fin_context = any(k in q for k in [
            "transaction", "merchant", "chargeback", "dispute", "fraud", "utr",
            "kyc", "volume", "amount", "ticket", "failed", "success", "status",
            "user", "customer", "category", "payment", "bank", "ring", "summary"
        ])
        if has_fin_context:
            return {
                "sql_query": """
                    SELECT 
                        COALESCE(ft.merchant_category_final, 'General') AS category, 
                        COUNT(ft.txn_id) AS total_transactions, 
                        ROUND(SUM(ft.amount), 2) AS total_amount,
                        ROUND(AVG(ft.amount), 2) AS avg_ticket
                    FROM fact_transactions ft
                    GROUP BY category
                    ORDER BY total_amount DESC
                    LIMIT 8
                """,
                "chart_type": "bar",
                "x_axis": "category",
                "y_axis": "total_amount",
                "chart_title": "Overview of Transaction Volume by Category",
                "executive_summary": "Grocery, Transportation, and Hotel categories represent the primary transaction pillars. Risk exposure remains concentrated in high-velocity micro-payments."
            }
        else:
            return {
                "sql_query": "",
                "chart_type": "none",
                "x_axis": "",
                "y_axis": "",
                "chart_title": "Risk Bunny Copilot",
                "executive_summary": f"I specialize in analyzing **UPI payment transactions, merchant risk clusters, and fraud chargebacks**.\n\nCould you ask a question related to your payment data (e.g. *highest chargeback categories*, *daily volume trends*, *missing UTR anomalies*, or *top serial disputers*)?"
            }

def query_agent(question: str):
    """
    Try Gemini when configured, otherwise use the built-in offline queries.
    """
    engine = get_duckdb_connection()
    api_key = os.getenv("GEMINI_API_KEY")

    spec = None

    # 1. Try Gemini if API key is present
    if api_key and api_key.strip():
        try:
            from google import genai

            prompt = f"{SYSTEM_PROMPT}\n\nQuestion: {question}\n\nRespond ONLY with valid JSON."
            with genai.Client(api_key=api_key) as client:
                response = client.models.generate_content(
                    model=os.getenv("GEMINI_MODEL", "gemini-3.8-flash"),
                    contents=prompt,
                )
            raw_text = response.text.strip()
            if raw_text.startswith("```"):
                raw_text = re.sub(r"^```[a-zA-Z]*\n", "", raw_text)
                raw_text = re.sub(r"\n```$", "", raw_text)
            spec = json.loads(raw_text)
        except Exception:
            spec = None

    # 2. If Gemini didn't return or was offline, use smart semantic fallback
    if not isinstance(spec, dict):
        spec = fallback_semantic_query(question)

    sql = spec.get("sql_query")
    sql_query = sql.strip() if isinstance(sql, str) else ""
    chart_type = spec.get("chart_type", "none")
    x_axis = spec.get("x_axis", "")
    y_axis = spec.get("y_axis", "")
    chart_title = spec.get("chart_title", "Risk Bunny Assistant")
    executive_summary = spec.get("executive_summary", "Summary of results.")

    if sql_query:
        executive_summary = "The chart and table show the results of the query for the loaded dataset."

    # 3. If no SQL query is needed (e.g. general questions, coding help, greetings)
    if not sql_query:
        return {
            "sql_query": None,
            "chart_type": "none",
            "chart_title": chart_title,
            "executive_summary": executive_summary,
            "fig": None,
            "df": None,
        }

    # Execute SQL against the loaded tables.
    try:
        df = run_analytics_query(engine, sql_query)
    except Exception as err:
        return {
            "error": f"SQL Execution Error: {err}",
            "sql_query": sql_query,
            "df": None,
            "fig": None,
            "executive_summary": "The agent encountered a query syntax issue."
        }

    # Build styled Plotly Chart
    fig = None
    if HAS_PLOTLY and not df.empty and x_axis in df.columns and y_axis in df.columns:
        if chart_type == "line":
            fig = px.line(
                df, x=x_axis, y=y_axis, title=chart_title,
                color_discrete_sequence=["#06B6D4"]
            )
            fig.update_traces(mode="lines+markers", line=dict(width=3, color="#06B6D4"), marker=dict(size=6, color="#38BDF8"))
        elif chart_type == "scatter":
            fig = px.scatter(
                df, x=x_axis, y=y_axis, title=chart_title,
                color_discrete_sequence=["#818CF8"]
            )
        else: # Default bar
            fig = px.bar(
                df, x=x_axis, y=y_axis, title=chart_title,
                color_discrete_sequence=["#06B6D4", "#818CF8", "#10B981", "#F59E0B", "#F43F5E"]
            )
            fig.update_traces(marker_line_color='rgba(255, 255, 255, 0.12)', marker_line_width=1.0, opacity=0.92)

        fig.update_layout(
            template="plotly_dark",
            font_family="Inter, sans-serif",
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=40, r=20, t=50, b=40),
            title=dict(font=dict(size=15, color="#FFFFFF", family="Inter")),
            xaxis=dict(gridcolor="rgba(255, 255, 255, 0.07)", tickfont=dict(color="#94A3B8")),
            yaxis=dict(gridcolor="rgba(255, 255, 255, 0.07)", tickfont=dict(color="#94A3B8")),
        )

    return {
        "sql_query": sql_query,
        "chart_type": chart_type,
        "chart_title": chart_title,
        "executive_summary": executive_summary,
        "df": df,
        "fig": fig,
        "error": None
    }
