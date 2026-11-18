"""Write portfolio narratives from executed results; preserve original evidence files."""
from pathlib import Path
import json
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]

def write(name,content):
    p=ROOT/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(content.strip()+'\n',encoding='utf8')

def main():
    data=ROOT/'data/processed'
    checks=json.loads((ROOT/'docs/analysis_checks.json').read_text())
    audit=json.loads((ROOT/'docs/model_audit.json').read_text())
    metrics=pd.read_csv(data/'model_metrics.csv')
    capacity=pd.read_csv(data/'capacity_tradeoff.csv')
    monthly=pd.read_csv(data/'monthly.csv')
    old=monthly[monthly.month.between('2017-01','2017-08')]
    new=monthly[monthly.month.between('2018-01','2018-08')]
    value_growth=new.merchandise_brl.sum()/old.merchandise_brl.sum()-1
    order_growth=new.orders.sum()/old.orders.sum()-1
    reviewed=pd.read_csv(data/'review_comparison.csv').set_index('delivery_outcome')
    test=metrics[metrics.split.eq('test')]
    chosen=test[test.model.eq(audit['selected_model'])].iloc[0]
    budget=capacity[capacity.model.eq(audit['selected_model'])&capacity.budget_fraction.eq(.10)].iloc[0]
    write('docs/analysis.md',f'''
# E-commerce Delivery Performance and Customer Experience Analytics
Prepared 19 November 2026 · Historical Brazilian Olist commercial data, 2016–2018 · BRL

## Executive Summary
Rio de Janeiro combines substantial delivery problems with an elevated late rate: 1,495 late orders from 12,350 eligible orders (12.11%), compared with 6.77% overall. São Paulo has the largest late count (1,820) but a lower rate (4.49%); prioritise workload and poor relative performance separately. Together these states contain 50.73% of all late orders. [1]

Among reviewed eligible orders, 62.40% of late orders received a score of 1–2 versus 9.27% of on-time orders. This association supports investigating delivery performance, but it does not establish how much a delivery intervention would improve reviews. [2]

An approval-time model improves prioritisation modestly: investigating 1,255 test orders finds 124 late deliveries, about 10.12 investigations per late order. It captures only 20.70% of test late deliveries and its fixed threshold suffers workload drift. Treat it as a historical experiment requiring further validation. [3]

## Commercial volume grew, but the extraction boundaries matter
Delivered orders generated BRL 13,221,498.11 in merchandise, plus BRL 2,198,275.64 in freight. Merchandise AOV is BRL 137.04 across 96,478 delivered orders. Merchandise value is not accounting revenue or profit. [4]

For January–August, delivered-order count increased from {int(old.orders.sum()):,} in 2017 to {int(new.orders.sum()):,} in 2018 ({order_growth:.2%}). Merchandise value increased from BRL {old.merchandise_brl.sum():,.2f} to BRL {new.merchandise_brl.sum():,.2f} ({value_growth:.2%}). These equal calendar windows reduce seasonal mismatch, but the dataset cannot establish that growth represents the whole marketplace. August 2018 ends on the 29th for delivered purchases, so the latest period is incomplete. Sparse 2016 records and zero delivered purchases in September–October 2018 are extraction/coverage limitations, not evidence of a business collapse. [4]

![Monthly delivered merchandise value](figures/monthly_value.png)

November 2017 was the highest observed delivered-order month (7,289 orders; BRL 987,765.37 merchandise). This is an observed peak; the data alone does not identify its cause. Mean delivered-order purchase-to-delivery duration is 12.56 days. [4]

## Where operations should investigate
| Customer state | Eligible orders | Late orders | Late rate | Implication |
|---|---:|---:|---:|---|
| SP | 40,494 | 1,820 | 4.49% | High investigation volume despite below-overall rate |
| RJ | 12,350 | 1,495 | 12.11% | High volume and elevated rate |
| MG | 11,354 | 519 | 4.57% | Volume exists; rate below overall |
| BA | 3,256 | 396 | 12.16% | Additional high-rate regional investigation |
| AL | 397 | 85 | 21.41% | High rate with much lower volume |

![Late-order volume by customer state](figures/region_volume.png)

RJ has approximately 659 more late orders than the arithmetic benchmark obtained by applying the overall rate to its eligible volume. That is a descriptive comparison, not a preventable-delay forecast: route length, seller mix, promise windows and purchase month differ. [1]

Among categories with at least 100 eligible orders, audio has the highest late rate (41/348, 11.78%). In contrast, bed_bath_table has 689 late orders from 9,272 eligible orders (7.43%), and health_beauty has 649 from 8,647 (7.51%). The higher-volume categories can justify more investigation than a small category ranked first by rate. Category groups overlap at the order level; do not add their late counts. [5]

The highest-rate qualifying seller has 74 late orders from 389 eligible orders (19.02%). There are 210 sellers meeting the 100-order threshold overall. Seller comparisons must recalculate eligibility after filters, and order-level delays cannot identify which seller caused a problem on multi-seller orders. [5]

## Delivery and customer reviews are strongly associated
| Outcome | Reviewed / eligible orders | Review coverage | Mean score / 5 | Low-review rate |
|---|---:|---:|---:|---:|
| On time | 89,443 / 89,936 | 99.45% | 4.29 | 9.27% |
| Late | 6,381 / 6,534 | 97.66% | 2.27 | 62.40% |

![Low-review rates by delivery outcome](figures/review_gap.png)

The low-review gap is 53.14 percentage points using unrounded values (53.13 points from displayed rounded rates), approximately 6.73 times the on-time rate. Review response coverage differs. In addition, {checks['review_created_before_delivery']:,} delivered orders have selected review creation dates before actual delivery; these outcomes must not all be described as post-delivery feedback. Latest-review selection can reflect later updates. These are associations among observed reviewed orders, not causal effects. [2]

## Approval-time prioritisation: useful ranking, limited precision
Training uses earlier approvals and only labels available before validation starts; validation labels must be available before July testing. No actual delivery, review or carrier outcomes enter the explicit feature list. Product/location/price snapshot availability at approval is an assumption, because the source has no attribute histories. [3]

| Model | Test average precision | Precision at frozen threshold | Recall at frozen threshold |
|---|---:|---:|---:|
{chr(10).join('| '+r.model+' | '+f'{r.average_precision:.4f}'+' | '+f'{r.precision:.2%}'+' | '+f'{r.recall:.2%}'+' |' for r in test.itertuples())}

The baseline always predicts the training prevalence. At a 0.5 cutoff it flags no orders; its test AP is the test late prevalence, 4.77%. Logistic regression was selected on validation AP (0.1922 versus 0.1860 for gradient boosting), before reviewing test performance. [3]

![Precision–recall curves on later test orders](figures/model_pr.png)

For the chosen model at a predeclared 10% test budget: investigate {int(budget.investigated):,} orders, find {int(budget.late_found):,} late orders, precision {budget.precision:.2%}, recall {budget.recall:.2%}. Random selection at the same budget would identify approximately 60 late orders in expectation, requiring 20.94 investigations per late order. Investigations are not prevented delays. [3]

The validation-selected threshold flags {int(chosen.investigated):,} test orders ({chosen.investigation_fraction:.2%}), versus approximately 10% in validation. Precision is {chosen.precision:.2%}; 357 of 599 late orders are identified. A fixed top-k queue controls staffing load better in this simulation, but the score is not established as a calibrated probability. The dataset contains delivered outcomes only for this model, so results exclude unresolved and cancelled orders and may suffer cohort observation bias. [3]

## Three recommendations
1. **Investigate RJ first, with BA as a secondary regional case.** Compare promise windows and seller/customer routes within purchase months; distinguish late carrier handoff from transit delays before selecting a remedy. Use late rate and late count together, with staffing capacity agreed by actual stakeholders.
2. **Pilot proactive communication for delayed or high-risk orders.** The review gap supports testing this intervention, not assuming it works. Compare eligible pilot/control orders on low-review rate, contacts per order and actual late rate, preserving review-response coverage and avoiding promises of measured savings.
3. **Trial a capacity-limited approval-time investigation queue.** Start with a documented budget rather than the unstable fixed threshold. Monitor precision, recall, investigations per late order, geographic burden and workload; require a later validation period before deployment or claims of operational benefit.

Stakeholders, staffing budgets and proposed processes are case-study assumptions; no interviews or live operational intervention were conducted.

## Sources and reproducibility
1. [Region results](../data/processed/regions.csv), generated from order-grain data; SQL Query 10 reconciled with saved owner export.
2. [Review comparison](../data/processed/review_comparison.csv), latest selected valid review per eligible delivered order. [Build code](../python/build_analysis.py) records the tie rule and timing check.
3. [Executed notebook](../notebooks/late_delivery_prediction.ipynb), [metrics](../data/processed/model_metrics.csv), [capacity simulation](../data/processed/capacity_tradeoff.csv), [model audit](model_audit.json).
4. [Monthly results](../data/processed/monthly.csv), [analysis checks and input hashes](analysis_checks.json); source is the owner's original CSVs from [Olist on Kaggle](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce).
5. [Category results](../data/processed/categories.csv), [seller results](../data/processed/sellers.csv). Shared counts, monetary values and rates in SQL exports 2/5/6/9/10 reconcile to independently rebuilt pandas results within their displayed precision. The original monthly growth column skipped missing months; the revised query and Python calendar spine fix this, so that original growth column is not reused.

Processed raw/order-level data are intentionally excluded from Git. Run the scripts to regenerate these links locally. Findings are historical Brazilian evidence, not current Australian market conclusions. Detailed metric definitions are in the project README and Power BI measure descriptions.
''')
    write('docs/business_case.md','''
# Business Analyst case study
Historical Brazilian Olist data, 2016–2018 · Portfolio scenario · Prepared 19 November 2026

## Problem, scope and stakeholders
Operations needs to distinguish where late deliveries are concentrated, understand their association with reviews, and prioritise investigation within available staffing. The analysis covers 99,441 historical orders, with commercial KPIs scoped to delivered orders. It does not represent current Australian delivery performance, a live operations queue, profit, or proven intervention benefits.

**Case-study assumptions:** intended stakeholders are an operations manager (delivery investigation), seller support (seller discussions), customer support (communication), and an analyst (metric reconciliation). No stakeholder interviews were conducted. Roles, needs, staffing budgets and the process below are proposed rather than observed.

## Five requirements and acceptance criteria
| ID | Dashboard requirement | Acceptance criteria |
|---|---|---|
| R1 | Operations can see commercial scale and monthly trends | Unfiltered delivered orders = 96,478; merchandise BRL 13,221,498.11; freight BRL 2,198,275.64; AOV BRL 137.04. Values reconcile to SQL; freight remains separate. Date axis includes calendar months; sparse/partial coverage is labelled. |
| R2 | Operations can filter delivery comparisons by month and category | Date/category selections affect all page metrics. Unfiltered eligibility = 96,470; late = 6,534; late rate = 6.77%. Eight delivered orders with missing dates are excluded from this denominator. Empty selections return blanks rather than an invented zero rate. |
| R3 | Seller support can compare sellers without misleading tiny samples | Seller view shows eligible count, late count and rate; rate is blank below 100 eligible orders after filters. The qualifying seller with 389 eligible / 74 late displays 19.02%. Multi-seller order outcomes are labelled as whole-order associations; totals use distinct orders. |
| R4 | Customer support can compare reviews across delivery outcomes | Latest-review rule is documented. Unfiltered on-time mean = 4.29 and late mean = 2.27; low-review rates = 9.27% / 62.40%. Coverage is available, missing reviews remain missing, and association/causality and review-timing limits are visible. |
| R5 | Operations can prioritise problems using both scale and rate | Region view shows SP: 1,820 late / 40,494 eligible, RJ: 1,495 / 12,350. Category view shows counts and rates, including Unknown. Scenario queue reports investigation count, precision, recall and investigations per late order; it is explicitly historical and does not imply current unresolved orders. |

Automated pandas/SQL-export reconciliation supports metric acceptance. Power BI JSON passes public schema checks; Desktop refresh and interactive acceptance checks remain pending and must be recorded before calling the dashboard accepted.

## Proposed current and improved processes
Both maps are **case-study assumptions**.

```mermaid
flowchart LR
 A[Order approved] --> B[Seller prepares order]
 B --> C[Carrier transports order]
 C --> D[Customer receives or raises a concern]
 D --> E[Support investigates reactively]
 E --> F[Issue recorded across separate views]
```

```mermaid
flowchart LR
 A[Order approved] --> B[Estimate risk using approval-time features]
 B --> C[Select cases within agreed staff capacity]
 C --> D[Operations checks seller handoff and route context]
 D --> E[Support communicates verified information]
 E --> F[Record action and observed delivery outcome]
 F --> G[Review workload, delay rates and feedback coverage]
 G --> H[Adjust process using controlled pilot evidence]
```

The improved process adds early triage and a feedback loop; it does not assume that a prediction prevents a delay. Actions require access to operational events absent from this historical dataset.

## Recommendations and decision gates
1. **Investigate RJ routes and promise windows, then BA.** RJ has 1,495 late orders and a 12.11% rate versus 6.77% overall; BA has 396 and 12.16%. Compare matched purchase months and route/seller mix before attributing the problem. SP remains a volume priority despite its 4.49% rate.
2. **Pilot customer communication.** Low-review rates are 62.40% for reviewed late orders versus 9.27% on time. Use a controlled comparison of low reviews, contact workload and review coverage; the association does not prove communication will improve scores.
3. **Pilot capacity-limited risk triage.** The selected model's top 10% test queue finds 124 late deliveries from 1,255 investigations, approximately twice random expectation but only 20.70% recall. Define staff capacity with stakeholders and validate a later cohort before live deployment. Monitor false positives and regional burden.

No cost-benefit ROI is calculated: staffing costs, intervention effectiveness and delay-related financial losses are unknown. Evidence and methods: [analysis](analysis.md), [model audit](model_audit.json), [SQL validation](sql_validation_results.md).
''')
    write('docs/relationship_diagram.md','''
# Data relationships and grain
```mermaid
erDiagram
 CUSTOMERS ||--o{ ORDERS : customer_id
 ORDERS ||--o{ ORDER_ITEMS : order_id
 ORDERS ||--o{ PAYMENTS : order_id
 ORDERS ||--o{ REVIEWS : order_id
 PRODUCTS ||--o{ ORDER_ITEMS : product_id
 SELLERS ||--o{ ORDER_ITEMS : seller_id
 CATEGORY_TRANSLATION o|--o{ PRODUCTS : category_name
```
Raw grain: orders = order; customers = order-specific customer_id; items = order + item sequence; payments = order + payment sequence; reviews = review rows, not necessarily unique order or review ID; products = product; sellers = seller. Translation is optional for a product's category.

Payments, items and reviews are independently aggregated/selected before the SQL order-fact join. Repeat purchases use customer_unique_id. ZIP-prefix geolocation has many coordinate rows and is not joined directly; the baseline model uses states and avoids geolocation inflation.

Power BI: Calendar (1) → Orders (*); Orders (1) → Items (*); Categories (1) → Items (*); Sellers (1) → Items (*). All relationships filter one way. Measures apply distinct visible Items[order_id] to Orders through TREATAS, so category/seller selections affect order outcomes without bidirectional relationship ambiguity. Merchandise sums selected item prices; overlapping category order counts are not additive. Physical item-level attribution remains separate from whole-order delay attribution.
''')
    write('powerbi/README.md','''
# Three-page Power BI project

Open **Olist.pbip** in a current Power BI Desktop version supporting PBIP/PBIR, then select **Refresh**. This editable source project contains all three pages, 32 visuals, five import tables, four single-direction relationships and explicit DAX measures. It uses processed CSV files generated by `python/build_analysis.py` and `python/build_powerbi.py`; no MySQL credentials are embedded.

## Status and opening
Report JSON passed Microsoft's public schema validation (see validation.json). Desktop rendering, refresh, DAX evaluation and interaction tests are **not verified**: the Windows Computer Use runtime failed with `invalid sandbox permission path: file:///A:`. Do not describe this as an accepted PBIX dashboard or supply synthetic screenshots.

1. Run `python python/build_analysis.py`, then `python python/build_powerbi.py` from the project root.
2. Open `powerbi/Olist.pbip` and refresh. Files currently point to `A:/olist-delivery-analytics/data/processed/`. On another machine, rerun the generator to write its local absolute paths.
3. If a file privacy prompt appears, choose the appropriate local-file privacy classification yourself; no cloud publication is needed.
4. Verify the checks below, then save as PBIX if wanted. Store screenshots in `docs/screenshots/` and record acceptance in `docs/completion_status.md` only after observation.

## Pages
- **Business overview:** delivered orders, merchandise, AOV and freight; monthly order and value lines; purchase-month/category slicers.
- **Delivery performance:** eligible and late counts, late rate, duration; customer-state late volume, monthly late rate, qualified seller table.
- **Customer experience:** reviewed orders, low-review rate, mean score and coverage; review distribution, outcomes comparison and volume/rate category priorities.

## Desktop acceptance checklist
- Unfiltered cards: 96,478 delivered orders; BRL 13,221,498.11 merchandise; BRL 2,198,275.64 freight; BRL 137.04 AOV.
- Delivery cards: 96,470 eligible; 6,534 late; 6.77% late; 12.56 mean elapsed delivery days.
- Select RJ: 12,350 eligible / 1,495 late / 12.11%. Clear it; totals restore.
- Select category audio: 348 eligible / 41 late / 11.78%. Merchandise includes audio item prices only, not all merchandise in orders containing audio.
- Select a month and category together; compare counts and value with equivalent SQL predicates. Seller rates below 100 eligible orders must be blank.
- Check zero-order months, empty selections, reviews missing/Not eligible outcome, slicer syncing across pages and unfiltered totals after clearing.
- Review charts for clipping, titles, accessible labels and note visibility; no seller/category sum should replace distinct overall order counts.

Metric descriptions are embedded in the model and [measures.dax](measures.dax). The `Not eligible` outcome can include delivered orders missing delivery dates; it must not be treated as on-time. Review comparisons describe associations and can include reviews created before delivery.

Reference: [Microsoft PBIP documentation](https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-overview) and [PBIR report format](https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-report). Downloaded Microsoft schema files under schemas/ are retained solely for offline validation and keep their original schema URLs.
''')
    write('docs/walkthrough.md','''
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
''')
    write('docs/completion_status.md','''
# Completion and verification status
Updated 19 November 2026.

| Deliverable | Status | Evidence / remaining work |
|---|---|---|
| Source profiling and metric contract | Completed | Owner profile; independently rebuilt analysis; docs/analysis_checks.json |
| MySQL reporting layer and 12 queries | Completed with executed owner evidence | Original scripts executed by owner; Results 2/5/6/9/10 reconciled to pandas. Calendar-spine revision of Query 2 is authored but not re-executed in MySQL. |
| Findings, charts and recommendations | Completed | docs/analysis.md and generated figures |
| Business Analyst case study | Completed as Markdown and two-page PDF | Five requirements and acceptance criteria; assumed processes; three recommendations. Both PDF pages rendered and visually inspected. |
| Approval-time model | Executed | Baseline, logistic regression and gradient boosting; validation-selected model; chronological label-availability purge; saved metrics and notebook |
| Notebook presentation | Rendered and inspected | Executed outputs, split table, metrics and precision-recall chart inspected in isolated headless Edge |
| Three-page Power BI source | Authored and schema-validated | 32 visuals; Desktop refresh, DAX/interaction QA and real screenshots remain pending due Computer Use runtime failure |
| README and reproducible package | Completed locally | Scripts, pinned core dependencies, documentation, source hashes |
| Five-minute walkthrough | Script completed | docs/walkthrough.md; recording not made |
| GitHub publication | Not performed | Local repository exists; no remote publication requested or claimed |

The repository is ready for review, reproduction and final Power BI Desktop acceptance. Do not label the whole six-week plan fully completed until the outstanding Desktop checks and any intended recording/publication are done. Historical model queue is not a live intervention queue.
''')
    write('README.md',f'''
# E-commerce Delivery Performance and Customer Experience Analytics

**Where are delivery problems concentrated, how are they associated with customer satisfaction, and which orders should operations prioritise?**

A portfolio project using **historical Brazilian Olist commercial data from 2016–2018**: 99,441 orders linked to items, customers, sellers, payments, products and reviews. All monetary values are **BRL**, not AUD. Findings do not represent current Australian market conditions.

## Findings
- **6.77% late delivery:** 6,534 late orders from 96,470 eligible delivered orders.
- **RJ combines volume and an elevated rate:** 1,495 late orders, 12.11%, versus 6.77% overall. SP has 1,820 late orders but a lower 4.49% rate. Together they account for 50.73% of late orders.
- **Reviews differ sharply:** reviewed late orders have a 62.40% low-review rate versus 9.27% on time; mean scores are 2.27 versus 4.29. This is association, not a causal estimate.
- **Volume matters alongside rate:** audio has an 11.78% late rate (41/348), whereas bed_bath_table has 689 late orders from 9,272 eligible orders (7.43%). Seller/category order counts overlap.
- **Prioritisation has a workload cost:** the validation-selected logistic model finds 124 of 599 late orders by investigating 1,255 test orders, approximately 10.12 investigations per late order found. Recall is 20.70%; most flagged orders arrive on time.

![Low-review rates for late and on-time deliveries](docs/figures/review_gap.png)

## Commercial baseline
| Delivered-order metric | Result |
|---|---:|
| Orders | 96,478 |
| Merchandise value | BRL 13,221,498.11 |
| Freight, separate | BRL 2,198,275.64 |
| Average order value | BRL 137.04 |
| Mean elapsed delivery duration | 12.56 days |

January–August delivered orders increased from 21,998 in 2017 to 52,783 in 2018 ({order_growth:.2%}); merchandise increased {value_growth:.2%}. August 2018 is incomplete and dataset coverage may change; no whole-market growth claim is made. Sparse 2016 records and extraction-boundary zero months require caution.

## Open the deliverables
- [Full analysis and recommendations](docs/analysis.md)
- [Business Analyst case study](docs/business_case.md) and [two-page PDF](docs/business_case.pdf): five requirements, acceptance criteria, assumed processes and recommendations
- [Executed prediction notebook](notebooks/late_delivery_prediction.ipynb)
- [Power BI project](powerbi/Olist.pbip) and [opening / acceptance instructions](powerbi/README.md)
- [Data relationship diagram](docs/relationship_diagram.md), [quality log](docs/data_quality_log.md), [SQL validation evidence](docs/sql_validation_results.md)
- [Five-minute walkthrough and application summary](docs/walkthrough.md)
- [Exact completion status and remaining checks](docs/completion_status.md)

**Status:** analysis and models have run successfully; five saved MySQL exports reconcile to Python. The three-page Power BI source passes public JSON schemas, but **Desktop refresh, DAX/interaction testing and screenshots are not verified** because the Computer Use runtime could not start. No live deployment, recording, measured business improvement or GitHub publication is claimed.

## Reproduce locally
Use Python 3.11+ and MySQL 8+ for SQL. Core analysis was executed with pandas 3.0.3 and scikit-learn 1.7.1.

1. Download the [Olist dataset from Kaggle](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce). Preserve original filenames in `data/raw/`; the nine CSVs are excluded from Git.
2. From this project folder run:

```powershell
python -m pip install -r requirements.txt
python python/profile_data.py
python python/build_analysis.py
python python/train_models.py
python python/create_notebook.py
python python/build_powerbi.py
python python/package_project.py
python python/build_business_case_pdf.py
python python/verify_project.py
```

The notebook executes its model comparison again so its saved outputs are reproducible. No script needs credentials except the optional MySQL importer, which prompts privately. Generated order-level data stay local. Summary CSVs and charts are reproducible; the notebook retains bounded outputs for review.

For MySQL, run `python python/import_mysql.py` against a **new** database, then select it in Workbench and execute `sql/02_reporting_views.sql`, `sql/03_validation.sql`, and `sql/04_business_analysis.sql`. The importer refuses an existing database. The owner already ran the original SQL; the monthly query now includes a calendar spine and requires rerunning to verify that revision in MySQL.

For Power BI, open `powerbi/Olist.pbip` and refresh. CSV paths are generated for this checkout; rerun `build_powerbi.py` after moving the project. Use its README to verify filters, eligible counts, suppressed small sellers and reconciled totals before saving a PBIX or taking screenshots.

## Metric dictionary
| Metric | Definition and scope |
|---|---|
| Merchandise value | Sum item prices for delivered orders; selected item/category/seller scope; freight separate |
| AOV | Merchandise value / distinct delivered orders containing those selected items |
| Late-delivery rate | Delivered orders with actual calendar date after estimated date / delivered orders with both dates |
| Delivery duration | Elapsed purchase-to-delivery seconds / 86,400; nonnegative delivered durations only |
| Low-review rate | Selected valid reviews scored 1–2 / selected valid reviewed orders; delivered scope in the report |
| Review selection | Latest creation date, latest answer timestamp, greatest review ID; score descending only as deterministic fallback, with no conflicting winning score ties found |
| Repeat customer | customer_unique_id; customer_id is order-specific |
| Seller comparison | Minimum 100 eligible orders after filters; show denominator and whole-order attribution limitation |

Dates remain source-local, with no unsupported timezone conversion. Items, payments and reviews are aggregated/selected before order-grain joins. Payment totals are separate from merchandise value. Eight delivered orders lack actual delivery dates; they remain in commercial counts and leave the late-rate denominator. No delivered orders lack items; one lacks payment and 646 lack reviews. Missing reviews are not imputed. Unmapped categories remain visible. Raw geolocation is not joined because ZIP prefixes repeat.

## Prediction design and limitations
Predict at **approval**, using the explicit whitelist in `python/train_models.py`: price/freight, item and seller counts, product size/weight, customer and representative seller state/category, approval time and promised window. Snapshot attributes being available and unchanged then are documented assumptions. Actual delivery dates are used only for labels and chronology checks; reviews, carrier dates and future aggregates are excluded from model features.

Train before January 2018 (41,183 orders), validate January–June 2018 (38,622), test July–August 2018 (12,545). Training/validation labels unavailable at the next period boundary are purged. Selection uses validation average precision, not test performance. Test AP: logistic regression 0.0917, gradient boosting 0.0799, constant baseline 0.0477. PR-AUC here means sklearn average precision.

A frozen validation threshold flags 31.95% of test orders despite approximately 10% in validation. Capacity scenarios (5%, 10%, 20%) are separate, predetermined historical simulations. The baseline budget result is random-ranking expectation, not an observed model ranking. Only delivered, observable labels are evaluated; cancellations, unresolved orders, unequal follow-up and time drift limit generalisation. No causal or financial benefits are claimed.

## Repository map
```text
data/raw/             Original Kaggle CSVs (ignored)
data/processed/       Regenerated facts, dimensions, summaries and simulations (ignored)
sql/                  MySQL reporting, validation, 12 queries; owner's five CSV exports
python/               Profiling, import, analysis, modelling and packaging
notebooks/            Executed model comparison
powerbi/              PBIP/PBIR, model, DAX, schemas and acceptance instructions
docs/                 Analysis, figures, BA case study, evidence and walkthrough
```

Recommendations: investigate RJ routes/promises (then BA), pilot proactive communication, and trial capacity-limited triage with monitoring. Stakeholder needs, processes and staff capacity are **case-study assumptions**, not interview findings.

Source attribution: [Olist Brazilian E-commerce Public Dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce). Raw data are not redistributed; consult the source terms before redistribution. No repository-wide licence is asserted over third-party data or Microsoft schema files.
''')
    print('Wrote README, analysis, BA case study, relationship diagram, walkthrough, Power BI instructions and status.')

if __name__=='__main__':main()
