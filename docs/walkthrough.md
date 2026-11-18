# Five-minute portfolio walkthrough

**0:00–0:40 — Question and context.** “I used historical Brazilian Olist data from 2016–2018 to investigate delivery concentration, customer-review associations and approval-time investigation priorities. Currency is BRL; this is not evidence about current Australian customers.”

**0:40–1:20 — Trustworthy analysis.** Explain the separate item/payment aggregation and latest-review selection before joining. Show 99,441 fact rows and distinct orders, the zero-value reconciliation differences, and why customer_unique_id matters for repeat customers.

**1:20–2:10 — Business overview.** Show delivered orders, merchandise, freight and AOV. Compare January–August 2017/2018, explaining incomplete endpoint coverage instead of presenting extraction-boundary zero months as collapse.

**2:10–3:00 — Delivery priorities.** RJ has 12.11% late deliveries against 6.77% overall; SP has the highest late count but a 4.49% rate. Explain why rate and volume drive different actions. Audio has a high qualifying rate; bed/bath/table has more late orders. Seller delay is association, not blame.

**3:00–3:40 — Customer experience.** Compare 62.40% low reviews on late orders with 9.27% on time. State review coverage and timing limitations; propose a communication pilot rather than claiming causation.

**3:40–4:30 — Prediction and workload.** Explain approval-time features, chronological split and label-availability purging. Logistic regression wins validation AP. Its top 10% test queue finds 124 late deliveries in 1,255 investigations; 20.70% recall. Discuss low precision and fixed-threshold workload drift.

**4:30–5:00 — Recommendation and honesty.** Investigate RJ routes, pilot communication and evaluate capacity-limited triage. State which artifacts were executed and which Desktop acceptance checks remain pending. Do not imply stakeholder interviews, live deployment, measured savings or a completed dashboard acceptance test.

## Application summary
“Built a reproducible e-commerce delivery analytics portfolio using MySQL, pandas, Power BI project source and scikit-learn on 99,441 historical Brazilian orders. Reconciled order-grain commercial metrics, identified regional delay concentration, analysed delivery/review associations, and evaluated approval-time prioritisation with chronological testing and investigation workload metrics.”

Use ‘Power BI dashboard’ in an application only after refreshing and verifying the supplied project in Desktop. Link the GitHub repository after publishing; no repository URL is invented here.
