# Initial business findings

Source: user-supplied MySQL Workbench screenshots of business-analysis Results 1 and 7, reviewed 30 October 2026. Historical Brazilian Olist commercial data, 2016–2018; monetary values in BRL. SQL reconciliation evidence is in sql_validation_results.md.

## Commercial baseline: delivered orders
| Metric | Value |
|---|---:|
| Delivered orders | 96,478 |
| Merchandise value, excluding freight | BRL 13,221,498.11 |
| Freight | BRL 2,198,275.64 |
| Average order value, excluding freight | BRL 137.04 |

AOV uses merchandise value divided by delivered orders, not item count or payment value. This is delivered-order merchandise value, not accounting revenue or profit.

## Delivery and customer experience
| Outcome | Reviewed eligible orders | Mean review score / 5 | Low-review rate (scores 1–2) |
|---|---:|---:|---:|
| On time | 89,443 | 4.2903 | 9.27% |
| Late | 6,381 | 2.2708 | 62.40% |

Based on displayed rounded rates, late orders have a 53.13 percentage-point higher low-review rate, approximately 6.7 times the on-time rate. The mean score is approximately 2.02 points lower.

Review coverage can be derived from the already validated delivery totals: 89,443 / (96,470 - 6,534) = approximately 99.45% for on-time orders; 6,381 / 6,534 = approximately 97.66% for late orders. Direct SQL coverage output should be checked next. Missing reviews must not be assigned a score.

## Interpretation and limits
Delivery delays are strongly associated with poorer reviews in this historical dataset. This does not establish that delays caused the entire difference: other order problems and review-response selection may contribute. One selected review per order is used, following the documented latest-review rule. Reviews are not necessarily submitted after final delivery; investigate their timing before interpreting them as post-delivery feedback.

The findings support investigating delivery problems as an operational priority. They do not yet identify priority sellers, categories or regions, establish intervention effectiveness, or demonstrate current Australian market conditions.

## Next evidence
- Monthly volume and merchandise trends (Result 2), with partial/sparse periods flagged.
- Region prioritisation by observed late-order volume and rate (Result 10).
- Seller and category comparisons with at least 100 eligible orders (Results 5 and 6).
- Review coverage by outcome (Result 9).
- Delay severity versus reviews (Result 12).

Potential actions remain hypotheses until concentration results are examined: investigate high-volume delay areas, trial proactive communication, and evaluate approval-time risk prioritisation against a fixed staff capacity. Do not claim measured benefits from these proposed interventions.
