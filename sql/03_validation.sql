-- MySQL 8+. Each check has an explicit expected result.
-- 1: 99441 rows and 99441 distinct orders, matching the supplied profile.
SELECT COUNT(*) AS rows_in_fact, COUNT(DISTINCT order_id) AS distinct_orders FROM v_order_fact;

-- 2: 96478 delivered, 96470 eligible, 6534 late, 8 missing dates.
SELECT SUM(is_delivered) AS delivered, SUM(delivery_eligible) AS eligible,
       SUM(is_late) AS late, SUM(is_delivered - delivery_eligible) AS excluded
FROM v_order_fact;

-- 3: Both differences must be zero (same delivered status scope).
SELECT a.item_value - b.fact_value AS merchandise_difference,
       a.item_freight - b.fact_freight AS freight_difference
FROM (
 SELECT SUM(i.price) AS item_value, SUM(i.freight_value) AS item_freight
 FROM olist_order_items_dataset i JOIN olist_orders_dataset o USING(order_id)
 WHERE o.order_status = 'delivered'
) a CROSS JOIN (
 SELECT SUM(merchandise_value) AS fact_value, SUM(freight_value) AS fact_freight
 FROM v_order_fact WHERE is_delivered = 1
) b;

-- 4: Coverage is measured, not assumed. Investigate all missing records.
SELECT order_status, COUNT(*) AS orders,
 SUM(item_count IS NULL) AS missing_items,
 SUM(payment_row_count IS NULL) AS missing_payments,
 SUM(review_score IS NULL) AS missing_reviews
FROM v_order_fact GROUP BY order_status;

-- 5: Expected no rows. Any conflict blocks final review metrics until resolved.
WITH ranked AS (
 SELECT r.*, DENSE_RANK() OVER (PARTITION BY order_id ORDER BY
 review_creation_date DESC, review_answer_timestamp DESC, review_id DESC) AS tie_rank
 FROM olist_order_reviews_dataset r
)
SELECT order_id, COUNT(DISTINCT review_score) AS conflicting_scores
FROM ranked WHERE tie_rank = 1 GROUP BY order_id
HAVING COUNT(DISTINCT review_score) > 1;

-- 6: Review score validity: expected no rows.
SELECT review_score, COUNT(*) AS rows_affected
FROM olist_order_reviews_dataset
WHERE review_score IS NULL OR review_score NOT BETWEEN 1 AND 5 GROUP BY review_score;

-- 7: Payment reconciliation: expected zero, independent of item values.
SELECT (SELECT SUM(payment_value) FROM olist_order_payments_dataset)
     - (SELECT SUM(payment_value) FROM v_order_fact) AS payment_difference;

-- 8: Attribution coverage: quantify non-additive seller/category order counts.
SELECT SUM(seller_count > 1) AS multi_seller_orders FROM v_order_fact;
SELECT COUNT(*) AS multi_category_orders FROM (
 SELECT order_id FROM v_order_category GROUP BY order_id HAVING COUNT(*) > 1
) x;
