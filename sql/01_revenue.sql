-- Revenue and order volume by purchase month. Excludes cancelled and unavailable orders.
SELECT
    DATE_TRUNC('month', o.order_purchase_timestamp)::date AS purchase_month,
    COUNT(DISTINCT o.order_id) AS orders,
    ROUND(SUM(oi.price + oi.freight_value), 2) AS gross_merchandise_value
FROM orders AS o
JOIN order_items AS oi ON oi.order_id = o.order_id
WHERE o.order_status = 'delivered'
GROUP BY 1
ORDER BY 1;

