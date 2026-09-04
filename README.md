# E-commerce Data Pipeline

Pipeline de dados end-to-end para analise de e-commerce com Python, Pandas, PostgreSQL e AWS S3. O MVP inicia localmente e evolui para uma arquitetura com data lake RAW/PROCESSED e data warehouse analitico.

## Objetivo

Extrair, validar, transformar, armazenar, modelar e analisar dados de clientes, pedidos, itens, produtos, pagamentos e avaliacoes.

## Dataset

O modelo e o contrato de colunas seguem o **Brazilian E-Commerce Public Dataset by Olist**. Para desenvolvimento sem download externo, `data/raw/sample/` contem um recorte CSV com as seis entidades do pipeline.

## Arquitetura

Consulte [a arquitetura](docs/architecture.md). O modelo relacional esta em [data-model.md](docs/data-model.md) e as regras de qualidade em [data-quality.md](docs/data-quality.md).
O roadmap atualizado esta em [implementation-plan.md](docs/implementation-plan.md).

## Tecnologias

Python, Pandas, PyArrow/Parquet, PostgreSQL, SQL, pytest, Docker Compose e AWS S3.

## Como executar o pipeline local

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m src.pipeline
```

O comando usa o recorte versionado em `data/raw/sample`. Para uma carga real, informe o diretorio que contem os seis CSVs obrigatorios:

```powershell
python -m src.pipeline --raw-directory data\raw
```

As fontes `sellers`, `geolocation` e `product_category_name_translation` sao opcionais. Quando presentes no diretorio informado, elas tambem sao extraidas, transformadas e publicadas. A geolocalizacao e curada para uma linha por CEP usando a mediana das coordenadas.

### Dataset Olist

Baixe os CSVs oficiais para a camada RAW, preservando seus nomes e conteudo originais:

```powershell
python -m src.ingestion.download
python -m src.pipeline --raw-directory data\raw\olist
```

O download requer acesso ao Kaggle. Os arquivos recebidos nao sao versionados pelo Git.

### Publicacao no AWS S3

Defina `S3_BUCKET`, `AWS_REGION`, `S3_RAW_PREFIX` e `S3_PROCESSED_PREFIX` no arquivo `.env`. O pipeline continua local por padrao; use a opcao abaixo para publicar os artefatos:

```powershell
python -m src.pipeline --raw-directory data\raw\olist --upload-s3
```

Os CSVs originais sao enviados para `raw/olist/`. Parquets, o relatorio JSON e arquivos de quarentena sao enviados para `processed/`, preservando caminhos relativos e sem alterar a camada RAW.

Para iniciar o PostgreSQL local, atualmente usado apenas como infraestrutura preparada para a proxima etapa:

```powershell
docker compose up -d
```

O schema pode ser aplicado manualmente depois que o banco estiver disponivel:

```powershell
Get-Content sql\00_operational_schema.sql | docker compose exec -T postgres psql -U ecommerce -d ecommerce_dw
```

## Estrutura

```text
data/raw/             Dados recebidos; nunca alterados pelo pipeline
data/processed/       Saida tipada em Parquet e relatorio de qualidade
src/ingestion/        Leitura, validacao estrutural e logs
src/transformation/   Padronizacao e atributos derivados
src/quality/          Regras, quarentena e relatorios
src/database/         Carga PostgreSQL (proxima etapa)
sql/                  DDL e consultas de negocio
docs/                 Arquitetura, modelo e qualidade
tests/                Testes pytest
```

## Consultas SQL

`sql/00_operational_schema.sql` cria o modelo operacional com PKs, FKs, checks e indices. `sql/01_revenue.sql` calcula receita mensal e volume de pedidos entregues.

## Decisoes tecnicas

- RAW e imutavel para auditoria e reprocessamento.
- Processed usara Parquet para leituras analiticas eficientes.
- O modelo operacional normalizado e separado da futura camada estrela analitica.
- A falha de contrato na ingestao interrompe o pipeline de forma explicita, com log de erro.

## Pendencias e proxima sequencia

O status detalhado, os criterios de aceite e as dependencias estao em [implementation-plan.md](docs/implementation-plan.md). A sequencia recomendada e:

1. **PostgreSQL:** implementar carga idempotente e transacional dos Parquets validados.
2. **Modelo analitico:** criar dimensoes, fato de itens e estrategia para evitar duplicacao de receita ao cruzar pagamentos.
3. **S3 real:** configurar bucket, regiao, credenciais fora do repositorio e permissao minima `s3:PutObject`; o upload ja esta implementado e testado com cliente simulado.
4. **Analise:** ampliar `sql/01_revenue.sql` e criar notebook com perguntas de negocio e insights reproduziveis.
5. **Confiabilidade:** adicionar testes de integracao com PostgreSQL, teste de execucao end-to-end e observabilidade basica.
6. **Entrega:** atualizar evidencias de execucao, revisar o README e documentar operacao e recuperacao de falhas.

Itens ja implementados e que nao devem voltar para a fila: ingestao dos seis datasets obrigatorios, suporte as tres fontes opcionais, transformacoes tipadas, curadoria de geolocalizacao, Parquet, quarentena, relatorio de qualidade e publicacao S3 com cliente simulado.
