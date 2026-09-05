-- Star schema for item-level sales analysis.
CREATE TABLE IF NOT EXISTS dim_customer (
    customer_key BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    customer_id TEXT NOT NULL UNIQUE,
    customer_unique_id TEXT NOT NULL,
    customer_zip_code_prefix INTEGER,
    customer_city TEXT NOT NULL,
    customer_state CHAR(2) NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_product (
    product_key BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    product_id TEXT NOT NULL UNIQUE,
    product_category_name TEXT,
    product_category_name_english TEXT,
    product_name_length INTEGER,
    product_description_length INTEGER,
    product_photos_qty INTEGER,
    product_weight_g NUMERIC(12, 2),
    product_length_cm NUMERIC(10, 2),
    product_height_cm NUMERIC(10, 2),
    product_width_cm NUMERIC(10, 2)
);

CREATE TABLE IF NOT EXISTS dim_seller (
    seller_key BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    seller_id TEXT NOT NULL UNIQUE,
    seller_zip_code_prefix INTEGER,
    seller_city TEXT NOT NULL,
    seller_state CHAR(2) NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_location (
    location_key BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    zip_code_prefix INTEGER NOT NULL UNIQUE,
    latitude NUMERIC(10, 7) NOT NULL,
    longitude NUMERIC(10, 7) NOT NULL,
    city TEXT,
    state CHAR(2)
);

CREATE TABLE IF NOT EXISTS dim_date (
    date_key INTEGER PRIMARY KEY,
    date_value DATE NOT NULL UNIQUE,
    year INTEGER NOT NULL,
    month INTEGER NOT NULL,
    month_name TEXT NOT NULL,
    quarter INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS fact_order_item (
    order_id TEXT NOT NULL,
    order_item_id INTEGER NOT NULL,
    customer_key BIGINT NOT NULL REFERENCES dim_customer(customer_key),
    product_key BIGINT NOT NULL REFERENCES dim_product(product_key),
    seller_key BIGINT REFERENCES dim_seller(seller_key),
    date_key INTEGER NOT NULL REFERENCES dim_date(date_key),
    customer_location_key BIGINT REFERENCES dim_location(location_key),
    seller_location_key BIGINT REFERENCES dim_location(location_key),
    price NUMERIC(12, 2) NOT NULL CHECK (price >= 0),
    freight_value NUMERIC(12, 2) NOT NULL CHECK (freight_value >= 0),
    PRIMARY KEY (order_id, order_item_id)
);

CREATE INDEX IF NOT EXISTS idx_fact_order_item_date ON fact_order_item(date_key);
CREATE INDEX IF NOT EXISTS idx_fact_order_item_product ON fact_order_item(product_key);
CREATE INDEX IF NOT EXISTS idx_fact_order_item_customer ON fact_order_item(customer_key);

-- Populate dimensions from the operational model. ON CONFLICT makes reruns safe.
INSERT INTO dim_customer (
    customer_id, customer_unique_id, customer_zip_code_prefix, customer_city, customer_state
)
SELECT customer_id, customer_unique_id, customer_zip_code_prefix, customer_city, customer_state
FROM customers
ON CONFLICT (customer_id) DO UPDATE SET
    customer_unique_id = EXCLUDED.customer_unique_id,
    customer_zip_code_prefix = EXCLUDED.customer_zip_code_prefix,
    customer_city = EXCLUDED.customer_city,
    customer_state = EXCLUDED.customer_state;

INSERT INTO dim_product (
    product_id, product_category_name, product_category_name_english, product_name_length,
    product_description_length, product_photos_qty, product_weight_g, product_length_cm,
    product_height_cm, product_width_cm
)
SELECT product_id, product_category_name, product_category_name_english, product_name_length,
       product_description_length, product_photos_qty, product_weight_g, product_length_cm,
       product_height_cm, product_width_cm
FROM products
ON CONFLICT (product_id) DO UPDATE SET
    product_category_name = EXCLUDED.product_category_name,
    product_category_name_english = EXCLUDED.product_category_name_english,
    product_name_length = EXCLUDED.product_name_length,
    product_description_length = EXCLUDED.product_description_length,
    product_photos_qty = EXCLUDED.product_photos_qty,
    product_weight_g = EXCLUDED.product_weight_g,
    product_length_cm = EXCLUDED.product_length_cm,
    product_height_cm = EXCLUDED.product_height_cm,
    product_width_cm = EXCLUDED.product_width_cm;

INSERT INTO dim_seller (seller_id, seller_zip_code_prefix, seller_city, seller_state)
SELECT seller_id, seller_zip_code_prefix, seller_city, seller_state
FROM sellers
ON CONFLICT (seller_id) DO UPDATE SET
    seller_zip_code_prefix = EXCLUDED.seller_zip_code_prefix,
    seller_city = EXCLUDED.seller_city,
    seller_state = EXCLUDED.seller_state;

INSERT INTO dim_location (zip_code_prefix, latitude, longitude, city, state)
SELECT zip_code_prefix, latitude, longitude, city, state
FROM locations
ON CONFLICT (zip_code_prefix) DO UPDATE SET
    latitude = EXCLUDED.latitude,
    longitude = EXCLUDED.longitude,
    city = EXCLUDED.city,
    state = EXCLUDED.state;

INSERT INTO dim_date (date_key, date_value, year, month, month_name, quarter)
SELECT DISTINCT
    TO_CHAR(order_purchase_timestamp::date, 'YYYYMMDD')::INTEGER,
    order_purchase_timestamp::date,
    EXTRACT(YEAR FROM order_purchase_timestamp)::INTEGER,
    EXTRACT(MONTH FROM order_purchase_timestamp)::INTEGER,
    TO_CHAR(order_purchase_timestamp, 'FMMonth'),
    EXTRACT(QUARTER FROM order_purchase_timestamp)::INTEGER
FROM orders
ON CONFLICT (date_key) DO UPDATE SET
    date_value = EXCLUDED.date_value,
    year = EXCLUDED.year,
    month = EXCLUDED.month,
    month_name = EXCLUDED.month_name,
    quarter = EXCLUDED.quarter;

INSERT INTO fact_order_item (
    order_id, order_item_id, customer_key, product_key, seller_key, date_key,
    customer_location_key, seller_location_key, price, freight_value
)
SELECT
    oi.order_id,
    oi.order_item_id,
    dc.customer_key,
    dp.product_key,
    ds.seller_key,
    dd.date_key,
    dcl.location_key,
    dsl.location_key,
    oi.price,
    oi.freight_value
FROM order_items AS oi
JOIN orders AS o ON o.order_id = oi.order_id
JOIN dim_customer AS dc ON dc.customer_id = o.customer_id
JOIN dim_product AS dp ON dp.product_id = oi.product_id
JOIN dim_date AS dd ON dd.date_value = o.order_purchase_timestamp::date
LEFT JOIN dim_seller AS ds ON ds.seller_id = oi.seller_id
LEFT JOIN dim_location AS dcl ON dcl.zip_code_prefix = (
    SELECT customer_zip_code_prefix FROM customers WHERE customer_id = o.customer_id
)
LEFT JOIN dim_location AS dsl ON dsl.zip_code_prefix = (
    SELECT seller_zip_code_prefix FROM sellers WHERE seller_id = oi.seller_id
)
ON CONFLICT (order_id, order_item_id) DO UPDATE SET
    customer_key = EXCLUDED.customer_key,
    product_key = EXCLUDED.product_key,
    seller_key = EXCLUDED.seller_key,
    date_key = EXCLUDED.date_key,
    customer_location_key = EXCLUDED.customer_location_key,
    seller_location_key = EXCLUDED.seller_location_key,
    price = EXCLUDED.price,
    freight_value = EXCLUDED.freight_value;