
# 💰 Operações Financeiras de Fornecedores

Esta aplicação foi desenvolvida em **Python com Streamlit** para consultar dados financeiros de fornecedores a partir de dois ambientes SAP diferentes (RISE e ECC), via serviços OData. Ela permite aplicar filtros, visualizar os resultados de forma tabular e exportar os dados para Excel.

---

## 📦 Funcionalidades

- Consulta simultânea a dois ambientes SAP via OData.
- Filtragem por intervalo de **data de lançamento**.
- Opção de filtro por:
  - **Número do Fornecedor** (LIFNR)
  - **Nome do Fornecedor** (NAME1)
- Apresentação dos dados em tabela com ordenação fixa de colunas.
- Exportação dos resultados para planilha **Excel (.xlsx)**.

---

## 📊 Colunas Apresentadas

| Nome da Coluna     | Descrição                                 |
|--------------------|-------------------------------------------|
| NOMEFORNECEDOR     | Nome do fornecedor (NAME1)                |
| NUMFORNECEDOR      | Número do fornecedor (LIFNR)              |
| NUMDOC             | Número do documento financeiro (BELNR)    |
| TPDOC              | Tipo de documento (BLART)                 |
| MONTIMI            | Valor monetário (DMBTR)                   |
| DOCCOMPANS         | Documento de compensação (AUGBL)          |
| TEXTO              | Texto descritivo do lançamento (SGTXT)    |

---

## 🔐 Arquivo de Segredos (`.streamlit/secrets.toml`)

Crie o arquivo `secrets.toml` no diretório `.streamlit/` com as credenciais e URLs:

```toml
[odatas]
ODATA_URL = "link_ambiente_1"
ODATA_URL2 = "link_ambiente_2"

[sap_logon]
SAP_USER = "seu_usuario"
SAP_PASS = "sua_senha"
```

> ✅ **Importante:** Adicione `secrets.toml` ao seu `.gitignore` para evitar que seja versionado.

---

## ▶️ Execução

Instale as dependências e execute com Streamlit:

```bash
pip install -r requirements.txt
streamlit run nome_do_arquivo.py
```

---

## 📁 Dependências Recomendadas (`requirements.txt`)

```txt
streamlit
pandas
requests
openpyxl
```

---

## 📝 Observações

- As datas filtram pelo campo **BLDAT** , relacionado a datas expressas no documento em si e não datas onde foram lançados.
- Os registros dos dois ambientes são mesclados e duplicatas eliminadas.
- Os serviços OData devem estar acessíveis e publicados (ambiente produtivo).

---

## ✨ Autor

Desenvolvido por [Rander Felipe, Analista Jr] com foco em integração com o SAP S4HANA via OData.
