# Plano de Implementacao Revisado

## Estado atual

- Dataset oficial da Olist baixado em `data/raw/olist/` por `kagglehub` e ignorado pelo Git.
- Pipeline local processa `customers`, `orders`, `order_items`, `products`, `payments` e `reviews`.
- O processamento produz Parquet, quarentena e relatorio de qualidade.
- A execucao contra o dataset completo recebeu 99.441 pedidos e 112.650 itens. A chave correta de `reviews` e (`review_id`, `order_id`), pois `review_id` nao e globalmente unico.

## Proxima entrega: Data Lake S3

1. Criar configuracao para bucket e prefixos `raw/` e `processed/`.
2. Enviar os CSVs originais ao prefixo RAW sem alteracao.
3. Enviar Parquets, quarentena e relatorio JSON ao prefixo PROCESSED.
4. Manter execucao local como fallback, sem exigir credenciais AWS nos testes.
5. Testar a interface S3 com mocks, sem expor credenciais no repositorio.

## Entrega seguinte: ampliar modelo Olist

1. Adicionar `sellers` e `product_category_name_translation` como fontes de referencia.
2. Curar `geolocation` para uma dimensao por `zip_code_prefix`; o arquivo bruto possui multiplas coordenadas para o mesmo CEP e nao deve receber uma chave artificial na RAW.
3. Incluir regras de qualidade, transformacoes e relatorios para essas fontes.
4. Enriquecer produtos com categoria em ingles para analises e notebook.

## Data warehouse PostgreSQL

1. Aplicar o schema operacional e corrigir `reviews` para a chave composta.
2. Implementar carga idempotente e transacional para os Parquets validados.
3. Criar dimensoes `dim_customer`, `dim_product`, `dim_seller`, `dim_date` e `dim_location`.
4. Criar `fact_order_item` na granularidade de item de pedido.
5. Manter pagamentos em fato separado ou agregar por pedido antes de cruzar com itens, evitando duplicacao de receita por joins de granularidades diferentes.

## Analise e entrega final

1. Criar queries de receita, ticket medio, produtos, cancelamento, entrega, avaliacao e regiao.
2. Construir notebook orientado a perguntas de negocio e insights.
3. Adicionar testes de integracao, screenshots do pipeline e revisao final do README.
