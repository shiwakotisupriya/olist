# SQL validation results

Evidence: MySQL Workbench result screenshots supplied by the project owner on 30 October 2026. The assistant reviewed the displayed results; it did not execute these queries locally.

| Check | Observed result | Assessment |
|---|---|---|
| Fact rows / distinct orders | 99,441 / 99,441 | One row per order preserved |
| Delivered / eligible / late / excluded | 96,478 / 96,470 / 6,534 / 8 | Matches Python profile |
| Delivered merchandise difference | BRL 0.00 | Raw items and fact reconcile |
| Delivered freight difference | BRL 0.00 | Raw items and fact reconcile |
| Payment difference, all orders | BRL 0.00 | Raw payments and fact reconcile |
| Conflicting winning review ties | Zero rows returned, earlier screenshot | No conflict found |
| Invalid review scores | Zero rows returned, earlier screenshot | No invalid score found |
| Multi-seller orders, all statuses | 1,278 | Group order counts are not additive |
| Multi-category orders, all statuses | 786 | Group order counts are not additive |

## Record coverage
| Status | Orders | Missing items | Missing payments | Missing selected reviews |
|---|---:|---:|---:|---:|
| delivered | 96,478 | 0 | 1 | 646 |
| unavailable | 609 | 603 | 0 | 14 |
| shipped | 1,107 | 1 | 0 | 75 |
| canceled | 625 | 164 | 0 | 20 |
| invoiced | 314 | 2 | 0 | 5 |
| processing | 301 | 0 | 0 | 6 |
| approved | 2 | 0 | 0 | 0 |
| created | 5 | 5 | 0 | 2 |

## Reporting decisions
- Proceed with descriptive business queries; these checks validate the tested joins and totals, not every possible source-data issue.
- Keep all delivered orders in commercial metrics: none lack items.
- Keep the delivered order missing payment in merchandise reporting. Payment absence does not imply zero merchandise value; investigate separately.
- Do not impute missing reviews. Delivered review coverage is 95,832 / 96,478, approximately 99.33%. Review comparisons must also show coverage separately for late and on-time orders.
- Exclude eight delivered orders lacking required delivery dates from the late-rate denominator only.
- Baseline calendar-date late-delivery rate is 6,534 / 96,470 = approximately 6.77%.
- Retain missing-item records in status reporting; commercial KPIs currently use delivered orders only.
- Seller/category delay counts describe whole-order outcomes and cannot establish responsibility or be summed across overlapping groups.

Next: execute sql/04_business_analysis.sql and inspect the twelve result sets. No seller, category or regional concentration findings have yet been established.
