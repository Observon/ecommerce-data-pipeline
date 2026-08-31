# Data Quality

As regras abaixo serao aplicadas antes da publicacao em `data/processed` e antes da carga no PostgreSQL.

| Dataset | Regra |
| --- | --- |
| customers | `customer_id` unico e nao nulo. |
| orders | `order_id` unico; `customer_id` existente; data de compra valida. |
| order_items | chave composta unica; `price >= 0`; `freight_value >= 0`. |
| products | `product_id` unico e nao nulo. |
| payments | chave composta unica; `payment_value >= 0`. |
| reviews | `review_score` entre 1 e 5. |

O processamento produzirá `data_quality_report.json` com linhas recebidas, validas e invalidas, duplicidades, nulos, falhas de chave referencial e status (`PASS`, `WARNING` ou `FAIL`). Linhas invalidas serao mantidas em uma area de quarentena, nunca descartadas silenciosamente.

