# Arquitetura

## MVP local

```text
CSV (data/raw)
      |
      v
Python / Pandas (src.ingestion)
      |
      +--> validacao estrutural e logs
      |
      v
Transformacao e qualidade
      |
      v
Parquet (data/processed) --> PostgreSQL --> SQL / notebook
```

## Arquitetura alvo com S3

```text
Fonte CSV/API --> Python --> S3/raw/olist (imutavel) --> Pandas + qualidade
                                                    |
                                                    v
                                               S3/processed (Parquet, quarentena e relatorio)
                                                    |
                                                    v
                                               PostgreSQL warehouse
                                                    |
                                                    v
                                            consultas SQL e Jupyter
```

A camada RAW preserva os arquivos recebidos sem alteracao. Isso permite auditoria e reprocessamento quando regras de transformacao mudarem. A camada PROCESSED tera dados tipados, padronizados e em Parquet, formato colunar apropriado para leituras analiticas.
