# E-commerce Delivery Performance and Customer Experience Analytics

## Business question
Where are delivery problems concentrated, how are they associated with customer satisfaction, and which orders should operations prioritise?

## Context
This portfolio uses historical, anonymised Brazilian Olist commercial data from 2016–2018. Values are Brazilian reais (BRL). Findings must not be presented as current Australian market evidence.

## Status
Dataset supplied by the project owner in `data/raw/`. File contents and results have not yet been verified because the execution environment cannot start. No numerical findings are claimed.

## Deliverables
1. MySQL analysis with reconciled reporting tables and 10–12 business queries.
2. Three-page Power BI report: business overview, delivery performance, customer experience.
3. Business Analyst case study with five testable requirements and assumed process maps.
4. Approval-time late-delivery prediction with chronological evaluation.

## Initial metric contract (subject to data validation)
- Merchandise value: sum item prices for delivered orders; report freight separately in BRL.
- Average order value: merchandise value divided by distinct delivered orders, including those without item records in the denominator while flagging missing items as a quality issue.
- Late-delivery rate: delivered orders whose actual delivery calendar date exceeds the estimated delivery calendar date, divided by delivered orders with both dates. Dates remain in source-local time; no unsupported timezone conversion.
- Delivery duration: elapsed seconds from purchase to customer delivery divided by 86,400. Flag negative durations and exclude them from duration summaries.
- Low-review rate: eligible reviewed orders scored 1 or 2 divided by eligible reviewed orders scored 1–5. Choose the latest review creation timestamp per order, then latest answer timestamp, then review ID for ties. Log any remaining conflicting ties.
- Repeat customers: use customer_unique_id, never customer_id, to link purchases across orders.
- Seller comparisons: initially require 100 delivery-eligible orders and show the denominator; validate this threshold against coverage.

## Grain and attribution
Aggregate items, payments and selected reviews independently before joining to one row per order. Assert uniqueness after each join. Payments are a reconciliation measure, not merchandise value.

Maintain separate order-seller and order-category bridges. Attribute item value directly to its seller/category. Count each order once within a group for delivery rates, but do not add grouped order counts across sellers/categories: an order can belong to multiple groups. Order-level delivery outcomes describe the whole shipment/order and cannot establish which seller caused a delay. Region means customer state unless explicitly labelled seller state.

## Prediction contract
Score at order approval. Use only features demonstrably available at approval; exclude actual delivery, carrier handoff, reviews, later status, and future aggregates. Item/payment information requires an explicit availability assumption. Exclude missing approvals and unavailable delivery labels, and document selection bias from restricting labels to delivered orders. Split chronologically by approval time into training, validation and untouched later test periods. Fit preprocessing on training data only. Tune thresholds on validation only. Compare a constant-prevalence baseline, logistic regression and a tree model with precision, recall, average precision (PR-AUC convention), and investigations per true late delivery. Simulated staff capacity is a case-study assumption, not an observed business requirement.

## Validation gates
Record row counts, keys, duplicates, nulls, orphan references, date anomalies, status coverage and review conflicts. Reconcile merchandise and freight to raw items for the same status scope; reconcile payment totals separately. Verify monthly and filtered Power BI results against SQL. Publish recommendations only after evidence is validated.

## Source
https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce

## Working folders
data/raw/ — original CSV files, unchanged
data/processed/ — reproducible derived tables
sql/ — schema, transformations, analysis, reconciliation
python/ — profiling and modelling code
powerbi/ — model instructions, measures and report
docs/ — quality log, requirements, case study and presentation

Stakeholder needs and current/improved processes are case-study assumptions until validated through interviews. Relationships between delivery and reviews are associations, not causal estimates.
