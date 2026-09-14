-- Business queries over the analytical model.

-- 1. Revenue, order volume and average ticket by month.
WITH order_sales AS (
    SELECT
        f.order_id,
        f.date_key,
        SUM(f.price + f.freight_value) AS order_revenue
    FROM fact_order_item AS f
    GROUP BY f.order_id, f.date_key
)
SELECT
    d.date_value AS purchase_date,
    COUNT(*) AS orders,
    ROUND(SUM(order_sales.order_revenue), 2) AS revenue,
    ROUND(AVG(order_sales.order_revenue), 2) AS average_ticket
FROM order_sales
JOIN dim_date AS d ON d.date_key = order_sales.date_key
JOIN orders AS o ON o.order_id = order_sales.order_id
WHERE o.order_status = 'delivered'
GROUP BY d.date_value
ORDER BY d.date_value;

-- 2. Payment totals aggregated before joining to item-level revenue.
WITH order_sales AS (
    SELECT order_id, SUM(price + freight_value) AS item_revenue
    FROM fact_order_item
    GROUP BY order_id
), payment_totals AS (
    SELECT order_id, SUM(payment_value) AS paid_value
    FROM payments
    GROUP BY order_id
)
SELECT
    COUNT(*) AS orders,
    ROUND(SUM(order_sales.item_revenue), 2) AS item_revenue,
    ROUND(SUM(COALESCE(payment_totals.paid_value, 0)), 2) AS paid_value
FROM order_sales
LEFT JOIN payment_totals ON payment_totals.order_id = order_sales.order_id;

-- 3. Revenue by product category.
SELECT
    COALESCE(dp.product_category_name_english, dp.product_category_name, 'unknown') AS category,
    COUNT(*) AS items,
    ROUND(SUM(f.price + f.freight_value), 2) AS revenue
FROM fact_order_item AS f
JOIN dim_product AS dp ON dp.product_key = f.product_key
GROUP BY 1
ORDER BY revenue DESC;

-- 4. Order status distribution and cancellation rate.
SELECT
    order_status,
    COUNT(*) AS orders,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS percentage
FROM orders
GROUP BY order_status
ORDER BY orders DESC;

-- 5. Average delivery time for delivered orders.
SELECT
    ROUND(AVG(EXTRACT(EPOCH FROM (order_delivered_customer_date - order_purchase_timestamp)) / 86400), 2) AS average_delivery_days,
    COUNT(*) AS delivered_orders
FROM orders
WHERE order_status = 'delivered'
  AND order_delivered_customer_date IS NOT NULL;

-- 6. Average review score by customer state.
SELECT
    dc.customer_state,
    COUNT(DISTINCT r.order_id) AS reviewed_orders,
    ROUND(AVG(r.review_score), 2) AS average_review_score
FROM reviews AS r
JOIN orders AS o ON o.order_id = r.order_id
JOIN dim_customer AS dc ON dc.customer_id = o.customer_id
GROUP BY dc.customer_state
ORDER BY reviewed_orders DESC;