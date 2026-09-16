# 📖 Data Dictionary // Risk Bunny Platform

This document outlines the data model, tables, field descriptions, and data cleaning transformations applied across the UPI fraud and merchant chargeback analytical dataset.

---

## 🏗️ Data Architecture (Star Schema)

```text
       ┌──────────────────┐               ┌──────────────────┐
       │  dim_customers   │               │  dim_merchants   │
       │ (28,921 records) │               │ (4,344 records)  │
       └────────┬─────────┘               └────────┬─────────┘
                │ user_id                          │ merchant_id
                │                                  │
                ▼                                  ▼
      ┌─────────────────────────────────────────────────────┐
      │                  fact_transactions                  │
      │                  (20,001 records)                   │
      └──────────────────────────┬──────────────────────────┘
                                 │ txn_id
                                 ▼
                    ┌─────────────────────────┐
                    │    fact_chargebacks     │
                    │     (2,801 records)     │
                    └─────────────────────────┘
```

---

## 1. `dim_customers` (Customer & KYC Dimension)
Contains customer identity, demographic data, and KYC risk tiers.

| Field Name | Type | Description | Sample / Constraints |
| :--- | :--- | :--- | :--- |
| `user_id` | `VARCHAR` | Unique customer identifier (Primary Key). | `USR16112`, `USR85256` |
| `full_name` | `VARCHAR` | Customer's full registered name. | `Synthetic Customer` |
| `state` | `VARCHAR` | Residential state. | `Maharashtra`, `Karnataka` |
| `city_clean` | `VARCHAR` | Standardized city name. | `Mumbai`, `Bangalore` |
| `occupation` | `VARCHAR` | Declared occupation. | `Salaried`, `Freelancer`, `Retired` |
| `monthly_income_clean` | `FLOAT` | Verified/cleaned monthly income in INR. | `35119.0`, `80907.0` |
| `date_of_birth_clean` | `DATETIME`| Standardized birth date. | `1967-04-06 00:14:00` |
| `signup_timestamp_clean`| `DATETIME`| Platform account creation timestamp. | `2025-12-02 02:18:16` |
| `pan_clean` | `VARCHAR` | Cleaned 10-character PAN number. | `ABCDE1234F` (placeholder) |
| `pan_valid` | `BOOLEAN` | Validation flag for PAN format regex. | `True`, `False` |
| `aadhaar_clean` | `VARCHAR` | Cleaned 12-digit Aadhaar number string. | `XXXX-XXXX-1234` (masked placeholder) |
| `aadhaar_valid` | `BOOLEAN` | Validation flag for Aadhaar formatting. | `True`, `False` |
| `kyc_status_clean` | `VARCHAR` | Standardized KYC verification outcome. | `VERIFIED`, `REJECTED`, `PENDING` |
| `risk_segment_clean` | `VARCHAR` | Assigned customer risk classification. | `LOW`, `MEDIUM`, `HIGH`, `UNKNOWN` |

---

## 2. `dim_merchants` (Merchant Master Dimension)
Contains onboarded vendor profiles, Merchant Category Codes (MCC), and business details.

| Field Name | Type | Description | Sample / Constraints |
| :--- | :--- | :--- | :--- |
| `merchant_id` | `VARCHAR` | Unique merchant identifier (Primary Key). | `MCH2849`, `MCH4859` |
| `merchant_name` | `VARCHAR` | Registered trade/business name. | `Deshmukh Ltd`, `VASA-RAJU` |
| `state` | `VARCHAR` | Business registration state. | `Punjab`, `Telangana` |
| `city_clean` | `VARCHAR` | Standardized merchant city. | `Ludhiana`, `Hyderabad` |
| `mcc_clean` | `INTEGER` | Standard 4-digit Merchant Category Code. | `5411` (Grocery), `5812` (Dining) |
| `merchant_category_clean`| `VARCHAR` | Human-readable category mapped from MCC. | `Apparel`, `Hotel / Lodging`, `Restaurant` |
| `business_type_clean` | `VARCHAR` | Entity structure. | `Private Limited`, `Sole Proprietor` |
| `onboarding_date_clean` | `DATETIME`| Onboarding timestamp. | `2025-09-23 00:00:00` |
| `merchant_status_clean` | `VARCHAR` | Current vendor account standing. | `ACTIVE`, `INACTIVE`, `SUSPENDED` |
| `declared_avg_ticket_size_clean`| `FLOAT` | Expected average transaction amount (INR). | `1271.48`, `2432.18` |
| `avg_ticket_was_negative`| `BOOLEAN`| Data hygiene flag (fixed negative sign anomaly). | `True`, `False` |
| `settlement_account_on_file` | `BOOLEAN`| Flag indicating verified bank account link. | `True`, `False` |

---

## 3. `fact_transactions` (Core Transaction Fact Table)
The central ledger of all processed UPI payments.

| Field Name | Type | Description | Sample / Constraints |
| :--- | :--- | :--- | :--- |
| `txn_id` | `VARCHAR` | Unique transaction ID (Primary Key). | `TXN00011869` |
| `user_id` | `VARCHAR` | Customer ID (Foreign Key -> `dim_customers`). | `USR45826` |
| `merchant_id` | `VARCHAR` | Merchant ID (Foreign Key -> `dim_merchants`). | `MCH7045` |
| `amount` | `FLOAT` | Transaction value in INR (absolute cleaned). | `15722.34`, `6362.90` |
| `amount_was_negative` | `BOOLEAN` | Hygiene flag (fixed corrupted negative values).| `True`, `False` |
| `txn_timestamp` | `DATETIME`| Exact payment timestamp. | `2026-01-15 00:11:30` |
| `utr_clean` | `VARCHAR` | Cleaned 12-digit Unique Transaction Reference. | `UTR6498104698` |
| `utr_missing_or_invalid`| `BOOLEAN` | Flag indicating synthetic/unresolved UTRs. | `True`, `False` |
| `mcc_clean` | `INTEGER` | MCC associated with the transaction. | `5411`, `4131` |
| `status_clean` | `VARCHAR` | Standardized transaction outcome. | `SUCCESS`, `FAILED`, `PENDING` |
| `has_kyc_match` | `BOOLEAN` | Integrity flag: User ID matched in customer master.| `True`, `False` |
| `has_merchant_match` | `BOOLEAN` | Integrity flag: Merchant ID matched in merchant master.| `True`, `False` |
| `merchant_category_final`| `VARCHAR` | Consolidated merchant category across joins. | `Grocery`, `Transportation`, `Dining` |
| `risk_segment_clean` | `VARCHAR` | Denormalized customer risk tier for OLAP speed. | `HIGH`, `MEDIUM`, `LOW`, `UNKNOWN` |

---

## 4. `fact_chargebacks` (Disputes & Chargeback Fact Table)
Records customer grievance reports, fraud claims, and recovery statuses.

| Field Name | Type | Description | Sample / Constraints |
| :--- | :--- | :--- | :--- |
| `complaint_id` | `VARCHAR` | Unique dispute ID (Primary Key). | `CBK0002082` |
| `txn_id` | `VARCHAR` | Disputed Transaction ID (Foreign Key -> `fact_transactions`). | `TXN00004325` |
| `user_id` | `VARCHAR` | Complainant Customer ID. | `USR97580` |
| `merchant_id` | `VARCHAR` | Disputed Merchant ID. | `MCH1127` |
| `complaint_text` | `VARCHAR` | Raw customer dispute narrative. | `"Customer says amount was debited twice."` |
| `disputed_amount_clean`| `FLOAT` | Disputed claim value in INR. | `20243.78`, `414.69` |
| `disputed_amount_imputed`| `BOOLEAN`| Flag indicating value imputed from transaction. | `True`, `False` |
| `transaction_timestamp_clean`| `DATETIME`| Original transaction timestamp. | `2026-01-28 00:00:00` |
| `reported_timestamp_clean` | `DATETIME`| Timestamp when customer filed grievance. | `2026-02-01 00:00:00` |
| `bank_response_timestamp_clean`| `DATETIME`| Acquiring bank response timestamp. | `2026-02-10 03:19:10` |
| `report_delay_days` | `FLOAT` | Filing latency (`reported_timestamp - txn_timestamp`). | `4.0`, `7.0` |
| `reason_code_clean` | `VARCHAR` | Classified dispute root cause. | `Service Not Delivered`, `Account Takeover` |
| `severity_clean` | `VARCHAR` | Triage priority rating. | `CRITICAL`, `HIGH`, `LOW` |
| `resolution_status_clean`| `VARCHAR` | Dispute workflow state. | `OPEN`, `IN_PROGRESS`, `CLOSED`, `REJECTED` |
| `channel_clean` | `VARCHAR` | Intake grievance channel. | `IVR`, `Call Center`, `Mobile App` |
| `txn_fk_valid` | `BOOLEAN` | Integrity check: Linked transaction exists in dataset.| `True`, `False` |

---

## 🧹 Key Data Cleaning & Hygiene Rules

1. **Unmatched Entity Preservation**: Real-world fraud often involves burner/unregistered IDs. Records with `has_kyc_match = False` or `has_merchant_match = False` are retained with `"Unmatched"` / `"UNKNOWN"` designations rather than dropped.
2. **Negative Amount Corrections**: Erroneously negative transactional amounts were converted via absolute value, with boolean audit flags (`amount_was_negative = True`).
3. **MCC & Category Fallback Hierarchy**: Merchant category is resolved from `dim_merchants.merchant_category_clean` ➔ `fact_transactions.mcc_clean` ➔ fallback lookup table to ensure zero null categories.
