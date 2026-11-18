# Initial data-quality assessment

Evidence: user-supplied output of python/profile_data.py. SQL reconciliation remains pending; no SQL execution is claimed.

Historical Brazilian Olist data, 2016–2018. Currency: BRL.

## Baseline
- 99,441 orders; 96,478 marked delivered.
- 96,470 delivery-eligible orders; eight delivered orders lack actual delivery dates.
- 6,534 late orders: 6.7731% of eligible orders, using calendar-date comparison.
- No malformed required dates or negative purchase-to-delivery durations among checked delivered orders.
- No duplicate keys in orders, customers, items, payments, products, sellers or translation.
- No orphan references in the tested core relationships.

## Decisions and follow-up
| Issue | Evidence | Treatment |
|---|---|---|
| Missing delivery outcomes | 2,965 orders lack actual delivery, including eight delivered orders | Retain for commercial/status reporting; exclude from delivery denominator; report exclusions |
| Missing approval | 160 orders | Exclude from approval-time modelling; report exclusions and delivered intersection |
| Multiple reviews | 547 orders have multiple review rows | Select latest creation timestamp, then latest answer timestamp, then review ID; detect unresolved score conflicts |
| Missing category | 610 products | Retain under Unknown category; never drop via inner join |
| Untranslated category | 13 product rows reference nonblank categories absent from translation | Preserve Portuguese category and flag missing translation; these are product rows, not necessarily 13 distinct categories |
| Missing physical attributes | Two products lack weight/dimensions | Retain and flag; fit model imputation on training data only |
| Missing other attributes | 610 products lack name length, description length and photo count | Retain and measure order-level impact |
| Geolocation duplication | 261,831 exact duplicate excess rows among 1,000,163 rows | Do not join raw geolocation to orders; deduplicate then aggregate to one ZIP-prefix row if distance features are needed |
| Missing review text | 87,658 titles; 58,274 messages | Text is optional; do not exclude valid numeric review scores |
| Uneven observation window | Purchase dates span September 2016–October 2018 | Inspect monthly counts and delivered coverage; flag partial/sparse periods before interpreting trends |

## Remaining validation
1. Reconcile item value and freight at raw-item and order grains for delivered orders.
2. Count orders without items/payments/reviews; tested child-to-parent relationships do not establish parent coverage.
3. Validate numeric parsing, negative prices/freight/payments, score range and item sequence gaps.
4. Check review ties with conflicting scores and reviews preceding delivery.
5. Inspect approval/purchase/promise chronology and approval-time availability assumptions.
6. Quantify multi-seller and multi-category orders before grouped reporting.
7. Compare on-time and late review outcomes using one review per order; raw score counts are not order-level rates.

Delivery delay is an order-level outcome. Seller comparisons show association, not seller fault. This profile does not yet support business recommendations or current Australian market conclusions.
