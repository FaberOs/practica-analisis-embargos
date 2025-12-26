# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas = [('C:\\Users\\FaberOs\\Documents\\Projects\\Python\\practica-analisis-embargos\\src\\orquestacion\\launcher.py', '.'), ('C:\\Users\\FaberOs\\Documents\\Projects\\Python\\practica-analisis-embargos\\src\\dashboards\\dashboard_embargos.py', '.'), ('C:\\Users\\FaberOs\\Documents\\Projects\\Python\\practica-analisis-embargos\\src\\dashboards\\dashboard_predicciones.py', '.'), ('C:\\Users\\FaberOs\\Documents\\Projects\\Python\\practica-analisis-embargos\\src\\dashboards\\dashboard_styles.py', '.'), ('C:\\Users\\FaberOs\\Documents\\Projects\\Python\\practica-analisis-embargos\\src\\pipeline_ml\\procesar_modelo.py', '.'), ('C:\\Users\\FaberOs\\Documents\\Projects\\Python\\practica-analisis-embargos\\src\\orquestacion\\utils_csv.py', '.'), ('C:\\Users\\FaberOs\\Documents\\Projects\\Python\\practica-analisis-embargos\\ob.ico', '.')]
binaries = [('C:\\Users\\FaberOs\\AppData\\Local\\Programs\\Python\\Python312\\Lib\\site-packages\\xgboost\\lib\\xgboost.dll', 'xgboost/lib')]
hiddenimports = ['streamlit', 'pandas', 'numpy', 'plotly', 'plotly.express', 'sklearn', 'xgboost', 'sklearn.preprocessing', 'sklearn.model_selection', 'sklearn.metrics', 'xgboost.sklearn', 'openpyxl', 'openpyxl.workbook', 'openpyxl.worksheet', 'openpyxl.cell']
tmp_ret = collect_all('streamlit')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('plotly')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('sklearn')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('xgboost')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('openpyxl')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]


a = Analysis(
    ['C:\\Users\\FaberOs\\Documents\\Projects\\Python\\practica-analisis-embargos\\src\\orquestacion\\launcher.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='DashboardEmbargos',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['C:\\Users\\FaberOs\\Documents\\Projects\\Python\\practica-analisis-embargos\\ob.ico'],
)
