# Data Quality

As regras abaixo serao aplicadas antes da publicacao em `data/processed` e antes da carga no PostgreSQL.

| Dataset | Regra |
| --- | --- |
| customers | `customer_id` unico e nao nulo. |
| orders | `order_id` unico; `customer_id` existente; data de compra valida. |
| order_items | chave composta unica; `price >= 0`; `freight_value >= 0`. |
| products | `product_id` unico e nao nulo. |
| payments | chave composta unica; `payment_value >= 0`. |
| reviews | Chave composta (`review_id`, `order_id`) unica; `review_score` entre 1 e 5. |
| sellers | `seller_id` unico e nao nulo; deve existir para cada item que informa vendedor. |
| geolocation | CEP unico apos a curadoria; latitude e longitude validas. |
| category_translation | `product_category_name` unico e nao nulo. |

O processamento produz `data_quality_report.json` com linhas recebidas, validas e invalidas, duplicidades, nulos, falhas de chave referencial e status (`PASS`, `WARNING` ou `FAIL`). Linhas invalidas sao mantidas em `data/processed/quarantine/`, nunca descartadas silenciosamente.
