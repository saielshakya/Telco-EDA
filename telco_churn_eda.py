import os
import sqlite3
import urllib.request
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

CSV = "Telco-Customer-Churn.csv"
URL = ("https://raw.githubusercontent.com/IBM/telco-customer-churn-on-icp4d/"
       "master/data/Telco-Customer-Churn.csv")
OUT = "eda_output"
os.makedirs(OUT, exist_ok=True)
plt.style.use("seaborn-v0_8-whitegrid")
RED, BLUE, GREY = "#e53e3e", "#2b6cb0", "#a0aec0"


# ------------------------------------------------------------ 1. LOAD
def load_db():
    if not os.path.exists(CSV):
        print("Downloading dataset...")
        urllib.request.urlretrieve(URL, CSV)
    df = pd.read_csv(CSV)
    # TotalCharges has blanks for brand-new customers (tenure = 0)
    df["TotalCharges"] = pd.to_numeric(df["TotalCharges"], errors="coerce").fillna(0)
    df["churned"] = (df["Churn"] == "Yes").astype(int)
    con = sqlite3.connect(":memory:")
    df.to_sql("customers", con, index=False)
    return con, df


def q(con, sql):
    return pd.read_sql_query(sql, con)


# ------------------------------------------------------------ 2. SQL
SQL_OVERVIEW = """
SELECT COUNT(*)                                        AS customers,
       SUM(churned)                                    AS churned,
       ROUND(100.0 * AVG(churned), 1)                  AS churn_pct,
       ROUND(AVG(tenure), 1)                           AS avg_tenure_months,
       ROUND(SUM(MonthlyCharges), 0)                   AS total_mrr,
       ROUND(SUM(CASE WHEN churned=1 THEN MonthlyCharges END), 0) AS mrr_lost_to_churn
FROM customers;
"""


def seg_sql(col):
    """Churn breakdown for any categorical column."""
    return f"""
    SELECT {col}                                       AS segment,
           COUNT(*)                                    AS customers,
           ROUND(100.0 * AVG(churned), 1)              AS churn_pct,
           ROUND(AVG(MonthlyCharges), 2)               AS avg_monthly,
           ROUND(SUM(CASE WHEN churned=1 THEN MonthlyCharges END), 0) AS mrr_lost
    FROM customers GROUP BY {col} ORDER BY churn_pct DESC;
    """


SQL_TENURE_BUCKET = """
SELECT CASE WHEN tenure <= 6  THEN '1) 0-6 mo'
            WHEN tenure <= 12 THEN '2) 7-12 mo'
            WHEN tenure <= 24 THEN '3) 13-24 mo'
            WHEN tenure <= 48 THEN '4) 25-48 mo'
            ELSE                   '5) 49+ mo' END     AS tenure_bucket,
       COUNT(*)                                        AS customers,
       ROUND(100.0 * AVG(churned), 1)                  AS churn_pct
FROM customers GROUP BY 1 ORDER BY 1;
"""

SQL_CHURN_BY_TENURE_MONTH = """
SELECT tenure, COUNT(*) AS customers, ROUND(100.0 * AVG(churned), 1) AS churn_pct
FROM customers WHERE tenure > 0 GROUP BY tenure ORDER BY tenure;
"""

# Number of add-on services (security, backup, protection, support) per customer
SQL_ADDONS = """
WITH x AS (
  SELECT *, (OnlineSecurity='Yes') + (OnlineBackup='Yes') +
            (DeviceProtection='Yes') + (TechSupport='Yes') AS addons
  FROM customers WHERE InternetService <> 'No'
)
SELECT addons, COUNT(*) AS customers, ROUND(100.0 * AVG(churned), 1) AS churn_pct
FROM x GROUP BY addons ORDER BY addons;
"""

# Combined risk segment: contract x internet service
SQL_RISK_MATRIX = """
SELECT Contract, InternetService, COUNT(*) AS customers,
       ROUND(100.0 * AVG(churned), 1) AS churn_pct,
       ROUND(SUM(CASE WHEN churned=1 THEN MonthlyCharges END), 0) AS mrr_lost
FROM customers GROUP BY Contract, InternetService
ORDER BY mrr_lost DESC;
"""

# Simple LTV: ARPU x expected lifetime (1 / monthly churn), lifetime capped at
# 60 months because low-churn contracts are right-censored in this data.
SQL_LTV = """
SELECT Contract,
       ROUND(AVG(MonthlyCharges), 2)                        AS arpu,
       ROUND(1.0 * SUM(churned) / SUM(tenure), 4)           AS monthly_churn_rate,
       ROUND(MIN(1.0 * SUM(tenure) / SUM(churned), 60), 1)  AS lifetime_months,
       ROUND(AVG(MonthlyCharges) * MIN(1.0 * SUM(tenure) / SUM(churned), 60), 0) AS est_ltv
FROM customers GROUP BY Contract ORDER BY est_ltv DESC;
"""


# ------------------------------------------------------------ 3. CHARTS
def bar_churn(df, title, fname, color=RED, rotate=0):
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.bar(df.iloc[:, 0].astype(str), df["churn_pct"], color=color)
    ax.axhline(OVERALL, color="black", ls="--", lw=1, label=f"Overall {OVERALL}%")
    for i, v in enumerate(df["churn_pct"]):
        ax.text(i, v + 0.5, f"{v}%", ha="center", fontsize=9)
    ax.set_title(title); ax.set_ylabel("Churn %"); ax.legend()
    plt.xticks(rotation=rotate)
    plt.tight_layout(); plt.savefig(f"{OUT}/{fname}", dpi=150); plt.close()


def main():
    global OVERALL
    con, df = load_db()

    overview = q(con, SQL_OVERVIEW)
    OVERALL = float(overview.churn_pct[0])
    print("\n=== OVERVIEW ===\n", overview.to_string(index=False))

    results = {}
    for col in ["Contract", "InternetService", "PaymentMethod", "SeniorCitizen",
                "PaperlessBilling", "Partner", "TechSupport"]:
        results[col] = q(con, seg_sql(col))
        print(f"\n=== CHURN BY {col.upper()} ===\n", results[col].to_string(index=False))

    tenure_b = q(con, SQL_TENURE_BUCKET)
    tenure_m = q(con, SQL_CHURN_BY_TENURE_MONTH)
    addons = q(con, SQL_ADDONS)
    risk = q(con, SQL_RISK_MATRIX)
    ltv = q(con, SQL_LTV)
    for name, d in [("TENURE BUCKET", tenure_b), ("ADD-ON SERVICES (internet users)", addons),
                    ("TOP RISK SEGMENTS BY MRR LOST", risk.head(6)), ("LTV BY CONTRACT", ltv)]:
        print(f"\n=== {name} ===\n", d.to_string(index=False))

    # ---- charts
    bar_churn(results["Contract"], "Churn by contract type", "01_contract.png")
    bar_churn(results["InternetService"], "Churn by internet service", "02_internet.png", BLUE)
    bar_churn(results["PaymentMethod"], "Churn by payment method", "03_payment.png", rotate=20)
    bar_churn(tenure_b, "Churn by tenure bucket", "04_tenure_bucket.png", BLUE)
    bar_churn(addons.rename(columns={"addons": "add-ons"}),
              "Churn by # of add-on services (internet users)", "05_addons.png")

    fig, ax = plt.subplots(figsize=(9, 4))
    ax.plot(tenure_m["tenure"], tenure_m["churn_pct"], color=GREY, marker="o", ms=3)
    ax.plot(tenure_m["tenure"], tenure_m["churn_pct"].rolling(6, center=True).mean(),
            color=RED, lw=2.5, label="6-month rolling avg")
    ax.set_title("Churn rate by tenure month"); ax.set_xlabel("Tenure (months)")
    ax.set_ylabel("Churn %"); ax.legend()
    plt.tight_layout(); plt.savefig(f"{OUT}/06_tenure_curve.png", dpi=150); plt.close()

    fig, ax = plt.subplots(figsize=(8, 4))
    for label, color in [(0, BLUE), (1, RED)]:
        ax.hist(df.loc[df.churned == label, "MonthlyCharges"], bins=30, alpha=.6, color=color,
                label="Churned" if label else "Retained", density=True)
    ax.set_title("Monthly charges: churned vs retained"); ax.set_xlabel("$ / month"); ax.legend()
    plt.tight_layout(); plt.savefig(f"{OUT}/07_charges_dist.png", dpi=150); plt.close()

    # correlation of numeric/binary features with churn
    feat = pd.get_dummies(df.drop(columns=["customerID", "Churn"]), drop_first=True).astype(float)
    corr = feat.corr()["churned"].drop("churned").sort_values()
    top = pd.concat([corr.head(8), corr.tail(8)])
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.barh(top.index, top.values, color=[BLUE if v < 0 else RED for v in top.values])
    ax.set_title("Features most correlated with churn"); ax.set_xlabel("Correlation")
    plt.tight_layout(); plt.savefig(f"{OUT}/08_correlations.png", dpi=150); plt.close()

    print(f"\nCharts saved to ./{OUT}/")


if __name__ == "__main__":
    main()
