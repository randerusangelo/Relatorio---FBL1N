@echo off
echo Abrindo no navegador ...
echo Apenas feche esta janela se desejar encerrar o sistema.
cd /d "%~dp0"

REM Executa o app Streamlit
streamlit run fbl1n.py

pause