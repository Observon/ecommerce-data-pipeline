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

Python, Pandas, PyArrow/Parquet, PostgreSQL, SQL, pytest, Docker Compose, AWS S3 (etapa posterior).

## Como executar o MVP

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m src.pipeline
```

O comando usa o recorte versionado em `data/raw/sample`. Para uma carga real, informe o diretorio que contem os seis CSVs:

```powershell
python -m src.pipeline --raw-directory data\raw
```

### Dataset Olist

Baixe os CSVs oficiais para a camada RAW, preservando seus nomes e conteudo originais:

```powershell
python -m src.ingestion.download
python -m src.pipeline --raw-directory data\raw\olist
```

O download requer acesso ao Kaggle. Os arquivos recebidos nao sao versionados pelo Git.

Para iniciar o PostgreSQL local quando a etapa de carga estiver pronta:

```powershell
docker compose up -d
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

## Proximas etapas

1. Carga idempotente no PostgreSQL e camada analitica.
2. Integracao S3 para RAW e PROCESSED.
3. Queries de negocio, notebook e testes automatizados.
