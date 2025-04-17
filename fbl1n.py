import streamlit as st
import pandas as pd
import requests
from requests.auth import HTTPBasicAuth
import altair as alt
import re
from datetime import datetime, date
import io

ODATA_URL = st.secrets["odatas"]["ODATA_URL"]
ODATA_URL2 = st.secrets["odatas"]["ODATA_URL2"]

SAP_USER = st.secrets["sap_logon"]["SAP_USER"]
SAP_PASS = st.secrets["sap_logon"]["SAP_PASS"]

def formatar_data_sap(date_str):
    match = re.search(r'/Date\((\d+)\)/', date_str)
    if match:
        timestamp = int(match.group(1)) // 1000
        return datetime.utcfromtimestamp(timestamp).strftime("%d/%m/%Y")
    return date_str

st.set_page_config(page_title="Ops Finan Forn", layout="wide")
st.title("💰 Operações Financeiras de Fornecedores - v 1.0")

if "data_ini" not in st.session_state:
    st.session_state["data_ini"] = date.today().replace(day=1)
if "data_fim" not in st.session_state:
    st.session_state["data_fim"] = date.today().replace()

with st.sidebar:
    st.header("🔍 Filtros Datas de Lançamentos ")
    data_ini = st.date_input("Data Inicial", value=st.session_state["data_ini"])
    st.caption(f"Selecionado: {data_ini.strftime('%d/%m/%Y')}")
    data_fim = st.date_input("Data FInal" , value=st.session_state["data_fim"])
    st.caption(f"Selecionado: {data_fim.strftime('%d/%m/%Y')}")
    tipo_filtro = st.selectbox("Filtrar por:", ["Número do Fornecedor", "Nome do Fornecedor"])
    valor_filtro = st.text_input("Digite o valor:", "")

    if st.button("Salvar Filtros"):
        st.session_state["data_ini"] = data_ini
        st.session_state["data_fim"] = data_fim
        st.session_state["tipo_filtro"] = tipo_filtro
        st.session_state["valor_filtro"] = valor_filtro
        st.success("Filtros salvos!")

st.subheader("📊 Resultado da Consulta")

if st.button("Consultar SAP"):
    with st.spinner("🔄 Consultando SAP ..."):
        try:
            headers = {
                "Accept": "application/json",
                "data_ini": data_ini.strftime("%Y%m%d"),
                "data_fim": data_fim.strftime("%Y%m%d"),
                "x-csrf-token": "fetch"
            }

            if tipo_filtro == "Número do Fornecedor":
                headers["lifnr"] = str(valor_filtro).strip()
            elif tipo_filtro == "Nome do Fornecedor":
                headers["name1"] = str(valor_filtro).strip()

            response =  requests.get(
                ODATA_URL,
                auth=HTTPBasicAuth(SAP_USER, SAP_PASS),
                headers=headers,
                verify=False
            )
            df = pd.DataFrame(response.json().get("d", {}).get("results", [])) if response.status_code == 200 else pd.DataFrame()
            
            if not df.empty:
                df.columns = [col.upper() for col in df.columns]
                df = df.drop(columns=[col for col in df.columns if "__METADATA" in col or col.startswith("__")], errors="ignore")
                if "DATADOC" in df.columns:
                    df["DATADOC"] = df["DATADOC"].apply(formatar_data_sap)

            response2 = requests.get(
                ODATA_URL2,
                auth=HTTPBasicAuth(SAP_USER, SAP_PASS),
                headers=headers,
                verify=False
            )
            df2 = pd.DataFrame(response2.json().get("d", {}).get("results",[])) if response2.status_code == 200 else pd.DataFrame()

            if not df2.empty:
                df2.columns = [col.upper() for col in df2.columns]
                df2 = df2.drop(columns=[col for col in df2.columns if "__METADATA" in col or col.startswith("__")], errors="ignore")
                if "DATADOC" in df2.columns:
                    df2["DATADOC"] = df2["DATADOC"].apply(formatar_data_sap)
            
            if not df.empty and not df2.empty:
                df_merged = pd.concat([df, df2], ignore_index=True)
                df_merged = df_merged.drop_duplicates()
                df_export = df_merged.copy()
            elif not df.empty:
                df_export = df.copy()
            elif not df2.empty:
                df_export = df2.copy()
            else:
                st.error("Nenhum dado encontrado nos dois serviços.")
                st.stop()

            colunas_reordenadas = [
                "NOMEFORNECEDOR",
                "NUMFORNECEDOR",
                "NUMDOC",
                "TPDOC",
                "MONTIMI",
                "DOCCOMPANS",
                "TEXTO"
            ]

            colunas_desordenadas = [col for col in colunas_reordenadas if col in df_export.columns]
            df_export = df_export[colunas_desordenadas + [col for col in df_export.columns if col not in colunas_desordenadas]]

            st.success(f" {len(df_export)} registros encontrados")
            st.dataframe(df_export)

            if not df_export.empty:
               with st.expander("📥 Exportar"):
                   output = io.BytesIO()
                   with pd.ExcelWriter(output, engine="openpyxl") as writer:
                       df_export.to_excel(writer, index=False, sheet_name="OpFinan")
                   output.seek(0)

                   st.download_button(
                       label="📤 Baixar Excel (.xlsx)",
                       data=output.getvalue(),
                       file_name="consulta_financeira.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                   )

        except Exception as e:
            st.error("Erro ao conectar ou processar os dados.")
            st.exception(e)




