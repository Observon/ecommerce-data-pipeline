# Plano de Implementacao Revisado

## Estado atual

- Dataset oficial da Olist baixado em `data/raw/olist/` por `kagglehub` e ignorado pelo Git.
- Pipeline local processa `customers`, `orders`, `order_items`, `products`, `payments` e `reviews`.
- O processamento produz Parquet, quarentena e relatorio de qualidade.
- As fontes opcionais `sellers`, `geolocation` e `category_translation` sao descobertas automaticamente quando presentes, com transformacoes e regras de qualidade proprias.
- A geolocalizacao e reduzida a uma linha por CEP pela mediana de latitude e longitude; a RAW permanece sem alteracao.
- O schema operacional PostgreSQL esta versionado e o Compose fornece um banco local, mas ainda nao existe uma rotina de carga.
- A execucao contra o dataset completo recebeu 99.441 pedidos e 112.650 itens. A chave correta de `reviews` e (`review_id`, `order_id`), pois `review_id` nao e globalmente unico.

## Concluido

### Pipeline local

1. Extracao dos seis datasets obrigatorios com validacao estrutural.
2. Suporte opcional a sellers, geolocalizacao e traducao de categorias.
3. Padronizacao de texto, datas e tipos numericos.
4. Atributos derivados de pedido: `order_total` e `delivery_days`.
5. Validacao de chaves, referencias, valores numericos, datas, coordenadas e notas de avaliacao.
6. Escrita de Parquet, quarentena de linhas invalidas e `data_quality_report.json`.
7. Testes unitarios para extracao, transformacao, qualidade e publicacao.

### Data Lake S3 (implementado; provisionamento pendente)

1. Configuracao para bucket, regiao e prefixos por `.env`.
2. Upload dos CSVs originais ao prefixo RAW sem alteracao.
3. Upload de Parquets, quarentena e relatorio JSON ao prefixo PROCESSED.
4. Execucao local permanece como fallback; S3 e ativado somente por `--upload-s3`.
5. Interface coberta por testes com cliente S3 simulado, sem credenciais no repositorio.
6. Pendente: criar ou informar o bucket AWS e conceder permissao `s3:PutObject` para executar o upload real.

## Pendencias priorizadas

### 1. Carga operacional PostgreSQL

- Criar um modulo de conexao usando as variaveis de ambiente, sem credenciais no codigo.
- Carregar tabelas na ordem das dependencias, com transacao e carga repetivel.
- Definir estrategia de upsert ou staging para que uma segunda execucao nao duplique registros.
- Persistir `order_total` e `delivery_days` somente se isso fizer parte do contrato do schema; hoje esses campos existem no Parquet, mas nao no DDL.

**Criterio de aceite:** executar o pipeline duas vezes sobre a mesma entrada e obter o mesmo estado no PostgreSQL, sem violacao de FK ou duplicacao.

### 2. Modelo analitico

1. Aplicar o schema operacional e corrigir `reviews` para a chave composta.
2. Implementar carga idempotente e transacional para os Parquets validados.
3. Criar dimensoes `dim_customer`, `dim_product`, `dim_seller`, `dim_date` e `dim_location`.
4. Criar `fact_order_item` na granularidade de item de pedido.
5. Manter pagamentos em fato separado ou agregar por pedido antes de cruzar com itens, evitando duplicacao de receita por joins de granularidades diferentes.

**Criterio de aceite:** uma consulta de receita reconciliar com a soma de `price + freight_value` dos itens, sem multiplicacao causada por pagamentos ou reviews.

### 3. Publicacao S3 real

- Definir bucket, regiao e ciclo de vida para RAW/PROCESSED.
- Validar permissao minima e executar um upload controlado do dataset oficial.
- Registrar prefixo, data de execucao e resultado do upload.
- Documentar como reprocessar e como verificar os objetos publicados.

**Criterio de aceite:** os arquivos RAW permanecerem byte a byte inalterados e os artefatos PROCESSED, quarentena e relatorio aparecerem nos prefixos esperados.

### 4. Analise e entrega final

1. Criar queries de receita, ticket medio, produtos, cancelamento, entrega, avaliacao e regiao.
2. Construir notebook orientado a perguntas de negocio e insights.
3. Adicionar testes de integracao, screenshots do pipeline e revisao final do README.

## Ordem recomendada de execucao

1. Implementar a carga PostgreSQL e cobri-la com um teste de integracao no Compose.
2. Validar reconciliacao entre Parquet, tabelas operacionais e consulta de receita.
3. Provisionar e testar S3 real em um ambiente controlado.
4. Criar o notebook e ampliar as consultas de negocio.
5. Fechar testes end-to-end, evidencias e documentacao operacional.
