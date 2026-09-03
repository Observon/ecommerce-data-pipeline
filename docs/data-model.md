# Modelo de Dados

O projeto usa como referencia o esquema do Brazilian E-Commerce Public Dataset by Olist. O recorte em `data/raw/sample` mantem o mesmo contrato funcional para permitir desenvolvimento local.

```text
customers 1 --- N orders 1 --- N order_items N --- 1 products
                    |
                    + --- N payments
                    |
                    + --- N reviews
```

| Tabela | Chave primaria | Papel |
| --- | --- | --- |
| customers | `customer_id` | Localizacao e identificador do comprador no pedido. |
| orders | `order_id` | Evento central do ciclo de compra e entrega. |
| order_items | (`order_id`, `order_item_id`) | Itens vendidos, preco e frete. |
| products | `product_id` | Atributos e categoria do produto. |
| payments | (`order_id`, `payment_sequential`) | Meio, parcelas e valor de pagamento. |
| reviews | (`review_id`, `order_id`) | Avaliacao de experiencia associada ao pedido. O `review_id` pode ocorrer em pedidos distintos no dataset da Olist. |

## Camada analitica planejada

`fact_sales` tera granularidade de item de pedido. As dimensoes iniciais serao `dim_customer`, `dim_product`, `dim_date` e `dim_payment`. Essa separacao preserva o modelo operacional normalizado e fornece uma estrutura simples para analise.
