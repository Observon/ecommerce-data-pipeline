# Arquitetura

## Fluxo atual: pipeline local

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

## Responsabilidades por camada

- **RAW:** arquivos recebidos, somente leitura para o pipeline e preservados para auditoria.
- **Ingestion:** localiza os nomes de arquivo aceitos, valida colunas obrigatorias e carrega os CSVs.
- **Transformation:** normaliza texto, datas e tipos; calcula atributos derivados; cura geolocalizacao por CEP.
- **Quality:** separa linhas validas e invalidas, calcula metricas e gera o relatorio de qualidade.
- **PROCESSED:** Parquets validados e arquivos de quarentena para reprocessamento e analise de falhas.
- **Storage:** publica RAW e PROCESSED no S3 quando `--upload-s3` e informado.
- **Database:** schema operacional preparado; carga ainda pendente.

## Fronteiras e riscos conhecidos

O pipeline local nao altera a camada RAW. As fontes opcionais nao impedem a execucao quando ausentes, mas o enriquecimento de produtos e a dimensao de localizacao dependem delas. Pagamentos, itens e reviews possuem granularidades diferentes; consultas analiticas devem agregar cada fato antes de cruza-los para evitar duplicacao de valores.

A carga PostgreSQL devera receber apenas datasets validados e respeitar a ordem das chaves estrangeiras. O upload S3 exige configuracao externa de credenciais e bucket; nenhuma credencial deve ser versionada.
