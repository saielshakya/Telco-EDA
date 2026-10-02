# Telco Customer Churn: EDA with SQL + Python

Exploratory analysis of **7,043 telecom customers** to understand who churns, why, and how much recurring revenue is at stake. The dataset is loaded into SQLite, metrics are computed in SQL, and results are visualized with pandas and matplotlib.

## Key Findings

| # | Finding | Evidence |
|---|---------|----------|
| 1 | **Contract type is the strongest churn driver** | Month-to-month churns at **42.7%**, one-year at 11.3%, two-year at 2.8% |
| 2 | **Fiber optic customers are the biggest revenue risk** | 41.9% churn vs. 19.0% for DSL; month-to-month fiber alone loses about **$100K** of monthly recurring revenue |
| 3 | **The first months are the danger zone** | Churn is 52.9% in months 0-6, falling to 9.5% after 4 years |
| 4 | **Add-on services track with retention** | Churn drops from 56.7% (0 add-ons) to 5.3% (4 add-ons) among internet customers |
| 5 | **Payment method is a strong signal** | Electronic check users churn at 45.3%, vs. 15-19% for other methods |
| 6 | **Seniors and customers without partners churn more** | 41.7% for senior citizens (vs. 23.6%); 33.0% without a partner (vs. 19.7%) |

Overall churn is **26.5%**, representing about **$139K of $456K** total monthly recurring revenue (MRR).

> These are correlations, not causal claims. For example, customers who buy add-ons may simply be more engaged to begin with.

## Business Recommendations

1. **Push contract upgrades.** Incentivize month-to-month customers to move to one- or two-year terms, especially fiber customers.
2. **Invest in onboarding.** Target the first 6 months with check-ins, offers, or support outreach.
3. **Bundle add-ons.** Test free trials of security, backup, and tech support to see whether they improve retention.
4. **Encourage automatic payments.** Offer small incentives to move electronic-check users to autopay.
5. **Investigate fiber.** High price and high churn suggest a value, reliability, or competition problem worth a deeper look.

## Repository Structure

```
.
├── telco_churn_eda.py          # Full analysis (SQL + Python)
├── Telco-Customer-Churn.csv    # Dataset
├── eda_output/                 # Generated charts (8 PNGs)
└── README.md
```



## Data Source

[IBM Telco Customer Churn dataset](https://github.com/IBM/telco-customer-churn-on-icp4d), a sample dataset provided by IBM.

## Author

**[Saiel Shakya]** | Data Analyst | [LinkedIn](https://www.linkedin.com/in/saiel-shakya-842a10228/) | [Email](saielshakya@gmail.com)
