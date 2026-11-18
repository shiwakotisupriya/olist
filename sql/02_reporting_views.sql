-- MySQL 8+. Prerequisite: import original CSVs into tables named below,
-- with empty timestamps converted to NULL, timestamps typed DATETIME,
-- and price/freight_value/payment_value typed DECIMAL(12,2).
-- Owner executed these views after importing the CSVs into MySQL.
-- Shared exported results independently reconciled in pandas on 19 Nov 2026.

CREATE OR REPLACE VIEW v_order_items AS
SELECT order_id, COUNT(*) AS item_count,
       COUNT(DISTINCT seller_id) AS seller_count,
       SUM(price) AS merchandise_value, SUM(freight_value) AS freight_value
FROM olist_order_items_dataset GROUP BY order_id;

CREATE OR REPLACE VIEW v_order_payments AS
SELECT order_id, COUNT(*) AS payment_row_count, SUM(payment_value) AS payment_value
FROM olist_order_payments_dataset GROUP BY order_id;

CREATE OR REPLACE VIEW v_order_review AS
SELECT order_id, review_id, review_score, review_creation_date, review_answer_timestamp
FROM (
 SELECT r.*, ROW_NUMBER() OVER (
   PARTITION BY order_id ORDER BY review_creation_date DESC,
   review_answer_timestamp DESC, review_id DESC, review_score DESC
 ) AS rn
 FROM olist_order_reviews_dataset r
) ranked WHERE rn = 1;
-- review_score DESC is a deterministic fallback only. The validation file
-- must show no conflicting scores at otherwise identical winning tie keys.

CREATE OR REPLACE VIEW v_order_fact AS
SELECT o.*, c.customer_unique_id, c.customer_state,
       i.item_count, i.seller_count, i.merchandise_value, i.freight_value,
       p.payment_row_count, p.payment_value,
       r.review_score, r.review_creation_date, r.review_answer_timestamp,
       CASE WHEN o.order_status = 'delivered' THEN 1 ELSE 0 END AS is_delivered,
       CASE WHEN o.order_status = 'delivered'
             AND o.order_delivered_customer_date IS NOT NULL
             AND o.order_estimated_delivery_date IS NOT NULL
            THEN 1 ELSE 0 END AS delivery_eligible,
       CASE WHEN o.order_status = 'delivered'
             AND o.order_delivered_customer_date IS NOT NULL
             AND o.order_estimated_delivery_date IS NOT NULL
            THEN CASE WHEN DATE(o.order_delivered_customer_date) > DATE(o.order_estimated_delivery_date)
                      THEN 1 ELSE 0 END END AS is_late,
       CASE WHEN o.order_status = 'delivered'
             AND o.order_delivered_customer_date >= o.order_purchase_timestamp
            THEN TIMESTAMPDIFF(SECOND, o.order_purchase_timestamp,
                               o.order_delivered_customer_date) / 86400.0 END AS delivery_days,
       CASE WHEN r.review_score BETWEEN 1 AND 5 THEN 1 ELSE 0 END AS review_eligible,
       CASE WHEN r.review_score BETWEEN 1 AND 5
            THEN CASE WHEN r.review_score <= 2 THEN 1 ELSE 0 END END AS low_review
FROM olist_orders_dataset o
LEFT JOIN olist_customers_dataset c ON c.customer_id = o.customer_id
LEFT JOIN v_order_items i ON i.order_id = o.order_id
LEFT JOIN v_order_payments p ON p.order_id = o.order_id
LEFT JOIN v_order_review r ON r.order_id = o.order_id;

CREATE OR REPLACE VIEW v_order_seller AS
SELECT order_id, seller_id, SUM(price) AS seller_merchandise_value,
       SUM(freight_value) AS seller_freight_value
FROM olist_order_items_dataset GROUP BY order_id, seller_id;

CREATE OR REPLACE VIEW v_order_category AS
SELECT i.order_id,
       COALESCE(p.product_category_name, '__UNKNOWN__') AS category_key,
       SUM(i.price) AS category_merchandise_value
FROM olist_order_items_dataset i
LEFT JOIN olist_products_dataset p ON p.product_id = i.product_id
GROUP BY i.order_id, COALESCE(p.product_category_name, '__UNKNOWN__');
