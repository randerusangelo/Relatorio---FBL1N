import streamlit as st
import pandas as pd
import requests
from requests.auth import HTTPBasicAuth
import altair as alt
import re
from datetime import datetime, date
import io
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
from PIL import Image

ODATA_URL = st.secrets["odatas"]["ODATA_URL"]
ODATA_URL2 = st.secrets["odatas"]["ODATA_URL2"]

SAP_USER = st.secrets["sap_logon"]["SAP_USER"]
SAP_PASS = st.secrets["sap_logon"]["SAP_PASS"]

def formatar_data_sap(date_str):
    match = re.search(r'/Date\((\d+)\)/', date_str)
    if match:
        timestamp = int(match.group(1)) // 1000
        return datetime.utcfromtimestamp(timestamp) #.strftime("%d/%m/%Y") -> testar
    return date_str

st.set_page_config(page_title="Ops Finan Forn", layout="wide")


col1, col2 = st.columns([1, 16])
with col1:
    logo = Image.open("LOGO_USA_ORIGINAL_SEM_FUNDO.png")
    st.image(logo, width=70)  

with col2:
    st.title("Operações Financeiras de Fornecedores - v 1.0.2 - FBL1N")

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
    opcoes_tpdoc_sidebar = ["ZP", "ZC", "RE", "TODOS"]
    filtro_tpdoc = st.selectbox("Escolha o tipo de documento:", opcoes_tpdoc_sidebar, index=0)
    st.caption(f"Selecionado: {filtro_tpdoc}")

    if st.button("Salvar Filtros"):
        st.session_state["data_ini"] = data_ini
        st.session_state["data_fim"] = data_fim
        st.session_state["tipo_filtro"] = tipo_filtro
        st.session_state["valor_filtro"] = valor_filtro
        st.session_state["filtro_tpdoc"] = filtro_tpdoc
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

            filtro_tpdoc_final = st.session_state.get("filtro_tpdoc", "ZP")
            if filtro_tpdoc_final != "TODOS":
                headers["tpdoc"] = filtro_tpdoc_final

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
                st.error("Nenhum dado foi encontrado.")
                st.stop()
            
            colunas_reordenadas = [
                "NOMEFORNECEDOR",
                "NUMFORNECEDOR",
                "NUMDOC",
                "TPDOC",
                "DATADOC",
                "MONTMI",
                "DOCCOMPANS",
                "TEXTO"
            ]

            colunas_desordenadas = [col for col in colunas_reordenadas if col in df_export.columns]
            df_export = df_export[colunas_desordenadas + [col for col in df_export.columns if col not in colunas_desordenadas]]

            if "MONTMI" in df_export.columns:
                df_export["MONTMI"] = pd.to_numeric(df_export["MONTMI"], errors="coerce")
                df_export["MONTMI"] = df_export["MONTMI"].apply(
                    lambda x: f"{x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") if pd.notnull(x) else ""
     )
            df_export = df_export.rename(columns={
                "NOMEFORNECEDOR": "NOME",
                "NUMFORNECEDOR": "Nº. Fornec.",
                "NUMDOC": "Nº. DOC",
                "MONTMI": "Mont.Mi. (R$)",
                "DOCCOMPANS": "DOCCOMPENS"
            })

            if "Mont.Mi. (R$)" in df_export.columns:
                largura = df_export["Mont.Mi. (R$)"].map(len).max()
                df_export["Mont.Mi. (R$)"] = df_export["Mont.Mi. (R$)"].apply(lambda x: x.rjust(largura))

            locale_text = {
                "sortAscending": "Ordenar ascendente",
                "sortDescending": "Ordenar descendente",
                "hideColumn": "Ocultar coluna",
                "filterOoo": "Filtrar...",
                "equals": "Igual a",
                "notEqual": "Diferente de",
                "contains": "Contém",
                "startsWith": "Começa com",
                "endsWith": "Termina com",
                "noRowsToShow": "Nenhuma linha para mostrar"
            }

            if "TPDOC" in df_export.columns:
             df_export["TPDOC"] = df_export["TPDOC"].fillna("").astype(str)

            opcoes_tpdoc = df_export["TPDOC"].dropna().unique().tolist()
            gb = GridOptionsBuilder.from_dataframe(df_export)
            gb.configure_default_column(filter=False) 
            #testando ord datas
            gb.configure_column("TPDOC", header_name="TPDOC", filter="agSetColumnFilter", filterParams={"values": df_export["TPDOC"].dropna().unique().tolist()},maxWidth=80)
            gb.configure_column("DATADOC", header_name="DataDoc", type=["dateColumnFilter", "customDateTimeFormat"], custom_format_string="dd/MM/yy", pivot=True, maxWidth=150, sortable=True, sort="desc", sortIndex=0)
            gb.configure_column("Mont.Mi. (R$)", type=["numericColumn", "rightAligned"],maxWidth=200)
            gb.configure_grid_options(
                rowSelection='single',  
                rowClassRules={
                    "row-selected": "params.node.isSelected()"
                },
                suppressCellSelection=True,
                enableCellTextSelection=True,
            )

            grid_options = gb.build()
            st.success(f"🧮 {len(df_export)} registros encontrados!")
            AgGrid(df_export,
                gridOptions=grid_options,
                enable_enterprise_modules=False,
                update_mode=GridUpdateMode.NO_UPDATE,
                fit_columns_on_grid_load=True,
                height=500,
                allow_unsafe_jscode=True,
                )

            if not df_export.empty:
               with st.expander("📥 Exportar"):
                   output = io.BytesIO()
                   with pd.ExcelWriter(output, engine="openpyxl") as writer:
                       df_export.to_excel(writer, index=False, sheet_name="OpFinan")
                   output.seek(0)

                   st.download_button(
                       label="📤 Baixar Planilha Excel (.xlsx)",
                       data=output.getvalue(),
                       file_name="extrato_fbl1n.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                   )

        except Exception as e:
            st.error("Erro ao conectar ou processar os dados.")
            st.exception(e)




