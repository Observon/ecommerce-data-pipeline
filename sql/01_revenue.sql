-- Revenue and order volume by purchase month from the item-level fact.
SELECT
    DATE_TRUNC('month', o.order_purchase_timestamp)::date AS purchase_month,
    COUNT(DISTINCT o.order_id) AS orders,
    ROUND(SUM(f.price + f.freight_value), 2) AS gross_merchandise_value
FROM orders AS o
JOIN fact_order_item AS f ON f.order_id = o.order_id
WHERE o.order_status = 'delivered'
GROUP BY 1
ORDER BY 1;

