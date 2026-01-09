"""
Script para generar gráficas de validación (Backtesting) para la tesis
Genera imágenes estáticas comparando datos reales vs predicciones
Incluye análisis granular de registros para documentación
"""
import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
import numpy as np
import json

# Configurar rutas
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
datos_dir = os.path.join(project_root, "datos")
docs_dir = os.path.join(project_root, "docs")

# Crear carpeta para evidencias si no existe
evidencias_dir = os.path.join(docs_dir, "evidencias_validacion")
os.makedirs(evidencias_dir, exist_ok=True)

print("=" * 80)
print("GENERACIÓN DE GRÁFICAS DE VALIDACIÓN (BACKTESTING) - ANÁLISIS GRANULAR")
print("=" * 80)

# Configurar estilo de matplotlib
plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams['figure.figsize'] = (12, 6)
plt.rcParams['font.size'] = 11
plt.rcParams['axes.titlesize'] = 14
plt.rcParams['axes.labelsize'] = 12

# Diccionario para almacenar todas las estadísticas
stats = {
    'dataset': {},
    'filtrado': {},
    'entrenamiento': {},
    'validacion': {},
    'metricas': {},
    'clasificacion': {}
}

# =============================================================================
# 1. ANÁLISIS GRANULAR DEL DATASET ORIGINAL
# =============================================================================
print("\n" + "=" * 80)
print("[1] ANÁLISIS GRANULAR DEL DATASET ORIGINAL")
print("=" * 80)

historico_path = os.path.join(datos_dir, "embargos_consolidado_mensual.csv")
print(f"\n    Archivo: {os.path.basename(historico_path)}")

# Cargar dataset completo
raw_full = pd.read_csv(historico_path, low_memory=False)
stats['dataset']['total_filas_original'] = len(raw_full)
stats['dataset']['total_columnas'] = len(raw_full.columns)
stats['dataset']['columnas'] = raw_full.columns.tolist()

print(f"    Total de filas en archivo: {len(raw_full):,}")
print(f"    Total de columnas: {len(raw_full.columns)}")

# Análisis de valores nulos por columna crítica
print(f"\n    Valores nulos en columnas críticas:")
columnas_criticas = ['mes', 'identificacion', 'tipo_embargo', 'estado_embargo', 'es_cliente']
stats['dataset']['nulos_por_columna'] = {}
for col in columnas_criticas:
    if col in raw_full.columns:
        nulos = raw_full[col].isna().sum()
        stats['dataset']['nulos_por_columna'][col] = int(nulos)
        print(f"      - {col}: {nulos:,} nulos ({nulos/len(raw_full)*100:.2f}%)")

# Filtrar registros con mes válido
raw_full['mes_valido'] = raw_full['mes'].str.match(r'^\d{4}-\d{2}$', na=False)
registros_validos = raw_full[raw_full['mes_valido']].copy()
registros_invalidos = raw_full[~raw_full['mes_valido']]

stats['filtrado']['registros_mes_valido'] = len(registros_validos)
stats['filtrado']['registros_mes_invalido'] = len(registros_invalidos)
stats['filtrado']['valores_mes_invalido'] = registros_invalidos['mes'].unique().tolist() if len(registros_invalidos) > 0 else []

print(f"\n    Filtrado por formato de mes (YYYY-MM):")
print(f"      - Registros con mes válido: {len(registros_validos):,}")
print(f"      - Registros con mes inválido: {len(registros_invalidos):,}")
if len(registros_invalidos) > 0:
    print(f"      - Valores inválidos encontrados: {stats['filtrado']['valores_mes_invalido']}")

# Distribución por mes
print(f"\n    Distribución de registros por mes:")
month_counts = registros_validos['mes'].value_counts().sort_index()
stats['dataset']['registros_por_mes'] = {k: int(v) for k, v in month_counts.items()}
for mes, count in month_counts.items():
    print(f"      {mes}: {count:>10,} registros")

stats['dataset']['total_meses'] = len(month_counts)
stats['dataset']['rango_fechas'] = {
    'inicio': month_counts.index.min(),
    'fin': month_counts.index.max()
}
print(f"\n    Total de meses únicos: {len(month_counts)}")
print(f"    Rango temporal: {month_counts.index.min()} a {month_counts.index.max()}")

# Identificaciones únicas
demandados_unicos = registros_validos['identificacion'].nunique()
stats['dataset']['demandados_unicos_total'] = int(demandados_unicos)
print(f"    Demandados únicos (identificaciones): {demandados_unicos:,}")

# =============================================================================
# 2. CARGAR DATOS DE VALIDACIÓN Y GENERAR SERIE HISTÓRICA
# =============================================================================
print("\n" + "=" * 80)
print("[2] CARGA DE DATOS DE VALIDACIÓN")
print("=" * 80)

# Cargar predicciones de oficios
oficios_val_path = os.path.join(datos_dir, "predicciones_oficios_validacion.csv")
oficios_val = pd.read_csv(oficios_val_path)
oficios_val['mes'] = pd.to_datetime(oficios_val['mes'])
stats['validacion']['oficios_registros'] = len(oficios_val)
print(f"\n    Archivo: predicciones_oficios_validacion.csv")
print(f"    Registros de validación (oficios): {len(oficios_val)}")

# Cargar predicciones de demandados
demandados_val_path = os.path.join(datos_dir, "predicciones_demandados_validacion.csv")
demandados_val = pd.read_csv(demandados_val_path)
demandados_val['mes'] = pd.to_datetime(demandados_val['mes'])
stats['validacion']['demandados_registros'] = len(demandados_val)
print(f"\n    Archivo: predicciones_demandados_validacion.csv")
print(f"    Registros de validación (demandados): {len(demandados_val)}")

# Mostrar datos de validación
print(f"\n    Período de validación: {oficios_val['mes'].min().strftime('%Y-%m')} a {oficios_val['mes'].max().strftime('%Y-%m')}")
stats['validacion']['periodo'] = {
    'inicio': oficios_val['mes'].min().strftime('%Y-%m'),
    'fin': oficios_val['mes'].max().strftime('%Y-%m')
}

# Generar datos históricos agregados
print(f"\n    Generando serie histórica agregada por mes...")
raw_data = pd.read_csv(historico_path, low_memory=False, usecols=['mes', 'identificacion'])
raw_data = raw_data[raw_data['mes'].str.match(r'^\d{4}-\d{2}$', na=False)]
raw_data['mes'] = pd.to_datetime(raw_data['mes'], format='%Y-%m')

historico = raw_data.groupby('mes').agg(
    oficios=('mes', 'count'),
    demandados_unicos=('identificacion', 'nunique')
).reset_index()
historico = historico.sort_values('mes')

# Calcular conjunto de entrenamiento vs validación
train_months = historico[~historico['mes'].isin(oficios_val['mes'])]
stats['entrenamiento']['meses'] = len(train_months)
stats['entrenamiento']['registros_oficios'] = int(train_months['oficios'].sum())
stats['validacion']['meses'] = len(oficios_val)

print(f"    Serie histórica: {len(historico)} meses")
print(f"    - Entrenamiento: {len(train_months)} meses ({train_months['oficios'].sum():,} registros)")
print(f"    - Validación: {len(oficios_val)} meses")

# =============================================================================
# 3. CÁLCULO DE MÉTRICAS DE ERROR
# =============================================================================
print("\n" + "=" * 80)
print("[3] CÁLCULO DE MÉTRICAS DE ERROR")
print("=" * 80)

def calcular_metricas(real, pred):
    """Calcula RMSE, MAE, MAPE y R²"""
    rmse = np.sqrt(np.mean((real - pred) ** 2))
    mae = np.mean(np.abs(real - pred))
    mape = np.mean(np.abs((real - pred) / real)) * 100
    # R² (coeficiente de determinación)
    ss_res = np.sum((real - pred) ** 2)
    ss_tot = np.sum((real - np.mean(real)) ** 2)
    r2 = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
    return rmse, mae, mape, r2

# Métricas para Oficios
rmse_of, mae_of, mape_of, r2_of = calcular_metricas(
    oficios_val['real_oficios'].values, 
    oficios_val['pred_oficios'].values
)
stats['metricas']['oficios'] = {
    'RMSE': float(rmse_of),
    'MAE': float(mae_of),
    'MAPE': float(mape_of),
    'R2': float(r2_of)
}
print(f"\n    MODELO DE REGRESIÓN: OFICIOS MENSUALES")
print(f"      RMSE (Root Mean Square Error):     {rmse_of:>15,.2f}")
print(f"      MAE  (Mean Absolute Error):        {mae_of:>15,.2f}")
print(f"      MAPE (Mean Absolute % Error):      {mape_of:>14.2f}%")
print(f"      R²   (Coef. de Determinación):     {r2_of:>15.4f}")

# Métricas para Demandados
rmse_dem, mae_dem, mape_dem, r2_dem = calcular_metricas(
    demandados_val['real_demandados'].values, 
    demandados_val['pred_demandados'].values
)
stats['metricas']['demandados'] = {
    'RMSE': float(rmse_dem),
    'MAE': float(mae_dem),
    'MAPE': float(mape_dem),
    'R2': float(r2_dem)
}
print(f"\n    MODELO DE REGRESIÓN: DEMANDADOS ÚNICOS MENSUALES")
print(f"      RMSE (Root Mean Square Error):     {rmse_dem:>15,.2f}")
print(f"      MAE  (Mean Absolute Error):        {mae_dem:>15,.2f}")
print(f"      MAPE (Mean Absolute % Error):      {mape_dem:>14.2f}%")
print(f"      R²   (Coef. de Determinación):     {r2_dem:>15.4f}")

# =============================================================================
# 4. ANÁLISIS DE MODELOS DE CLASIFICACIÓN
# =============================================================================
print("\n" + "=" * 80)
print("[4] ANÁLISIS DE MODELOS DE CLASIFICACIÓN")
print("=" * 80)

clasificaciones_path = os.path.join(datos_dir, "resultados_clasificaciones.csv")
clf_df = pd.read_csv(clasificaciones_path)
print(f"\n    Archivo: resultados_clasificaciones.csv")
print(f"    Total de filas: {len(clf_df)}")

modelos_unicos = clf_df['modelo'].unique()
print(f"    Modelos de clasificación: {len(modelos_unicos)}")

for modelo in modelos_unicos:
    modelo_data = clf_df[clf_df['modelo'] == modelo]
    print(f"\n    MODELO: {modelo}")
    
    # Obtener matriz de confusión (solo del primer registro que tiene la matriz completa)
    matriz_str = modelo_data.iloc[0]['matriz_confusion']
    clases_str = modelo_data.iloc[0]['clases_matriz']
    
    try:
        import ast
        matriz = np.array(ast.literal_eval(matriz_str))
        clases = ast.literal_eval(clases_str)
        total_predicciones = matriz.sum()
        accuracy = np.trace(matriz) / total_predicciones * 100
        
        stats['clasificacion'][modelo] = {
            'clases': clases,
            'num_clases': len(clases),
            'total_predicciones': int(total_predicciones),
            'accuracy': float(accuracy),
            'matriz_shape': matriz.shape
        }
        
        print(f"      Clases: {clases}")
        print(f"      Número de clases: {len(clases)}")
        print(f"      Total de predicciones: {total_predicciones:,}")
        print(f"      Accuracy global: {accuracy:.2f}%")
        print(f"      Dimensión matriz: {matriz.shape}")
        
        # Métricas por clase
        print(f"      Métricas por clase:")
        for _, row in modelo_data.iterrows():
            print(f"        - {row['clase']}: Precision={row['precision']:.4f}, Recall={row['recall']:.4f}, F1={row['f1']:.4f}")
    except Exception as e:
        print(f"      Error procesando matriz: {e}")

# =============================================================================
# 5. Gráfica 1: Backtesting de Oficios
# =============================================================================
print("\n" + "=" * 80)
print("[5] GENERACIÓN DE GRÁFICAS")
print("=" * 80)
print("\n    Generando gráfica de backtesting - Oficios...")

fig, ax = plt.subplots(figsize=(14, 7))

# Datos históricos (entrenamiento)
train_oficios = historico[~historico['mes'].isin(oficios_val['mes'])]
ax.plot(train_oficios['mes'], train_oficios['oficios'], 
        color='#2196F3', linewidth=2, label='Datos de entrenamiento', alpha=0.7)

# Datos reales del conjunto de prueba
ax.plot(oficios_val['mes'], oficios_val['real_oficios'], 
        color='#4CAF50', linewidth=2.5, marker='o', markersize=8,
        label='Datos reales (test)', zorder=5)

# Predicciones
ax.plot(oficios_val['mes'], oficios_val['pred_oficios'], 
        color='#F44336', linewidth=2.5, marker='s', markersize=8,
        linestyle='--', label='Predicción XGBoost', zorder=5)

# Sombrear área de validación
ax.axvspan(oficios_val['mes'].min(), oficios_val['mes'].max(), 
           alpha=0.1, color='orange', label='Período de validación')

# Configuración del gráfico
ax.set_title('Backtesting: Predicción de Oficios Mensuales\nModelo XGBoost - Validación con conjunto de prueba', 
             fontsize=14, fontweight='bold', pad=20)
ax.set_xlabel('Período', fontsize=12)
ax.set_ylabel('Cantidad de Oficios', fontsize=12)
ax.legend(loc='upper left', fontsize=10)
ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
plt.xticks(rotation=45)

# Añadir caja de métricas
metrics_text = f'Métricas de Validación:\nRMSE: {rmse_of:,.0f}\nMAE: {mae_of:,.0f}\nMAPE: {mape_of:.1f}%'
props = dict(boxstyle='round', facecolor='wheat', alpha=0.8)
ax.text(0.98, 0.97, metrics_text, transform=ax.transAxes, fontsize=10,
        verticalalignment='top', horizontalalignment='right', bbox=props)

ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: format(int(x), ',')))
plt.tight_layout()

# Guardar
oficios_path = os.path.join(evidencias_dir, "backtesting_oficios.png")
plt.savefig(oficios_path, dpi=150, bbox_inches='tight', facecolor='white')
plt.close()
print(f"    ✅ Guardado: {oficios_path}")

# =============================================================================
# 6. Gráfica 2: Backtesting de Demandados
# =============================================================================
print("\n    Generando gráfica de backtesting - Demandados...")

fig, ax = plt.subplots(figsize=(14, 7))

# Datos históricos (entrenamiento)
train_demandados = historico[~historico['mes'].isin(demandados_val['mes'])]
ax.plot(train_demandados['mes'], train_demandados['demandados_unicos'], 
        color='#2196F3', linewidth=2, label='Datos de entrenamiento', alpha=0.7)

# Datos reales del conjunto de prueba
ax.plot(demandados_val['mes'], demandados_val['real_demandados'], 
        color='#4CAF50', linewidth=2.5, marker='o', markersize=8,
        label='Datos reales (test)', zorder=5)

# Predicciones
ax.plot(demandados_val['mes'], demandados_val['pred_demandados'], 
        color='#F44336', linewidth=2.5, marker='s', markersize=8,
        linestyle='--', label='Predicción XGBoost', zorder=5)

# Sombrear área de validación
ax.axvspan(demandados_val['mes'].min(), demandados_val['mes'].max(), 
           alpha=0.1, color='orange', label='Período de validación')

# Configuración del gráfico
ax.set_title('Backtesting: Predicción de Demandados Únicos Mensuales\nModelo XGBoost - Validación con conjunto de prueba', 
             fontsize=14, fontweight='bold', pad=20)
ax.set_xlabel('Período', fontsize=12)
ax.set_ylabel('Cantidad de Demandados Únicos', fontsize=12)
ax.legend(loc='upper left', fontsize=10)
ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
plt.xticks(rotation=45)

# Añadir caja de métricas
metrics_text = f'Métricas de Validación:\nRMSE: {rmse_dem:,.0f}\nMAE: {mae_dem:,.0f}\nMAPE: {mape_dem:.1f}%'
props = dict(boxstyle='round', facecolor='wheat', alpha=0.8)
ax.text(0.98, 0.97, metrics_text, transform=ax.transAxes, fontsize=10,
        verticalalignment='top', horizontalalignment='right', bbox=props)

ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: format(int(x), ',')))
plt.tight_layout()

# Guardar
demandados_path = os.path.join(evidencias_dir, "backtesting_demandados.png")
plt.savefig(demandados_path, dpi=150, bbox_inches='tight', facecolor='white')
plt.close()
print(f"    ✅ Guardado: {demandados_path}")

# =============================================================================
# 7. Gráfica 3: Comparativa lado a lado (Real vs Predicción)
# =============================================================================
print("\n    Generando gráfica comparativa lado a lado...")

fig, axes = plt.subplots(1, 2, figsize=(16, 6))

# Subplot 1: Oficios
ax1 = axes[0]
x = range(len(oficios_val))
width = 0.35
bars1 = ax1.bar([i - width/2 for i in x], oficios_val['real_oficios'], width, 
                label='Real', color='#4CAF50', alpha=0.8)
bars2 = ax1.bar([i + width/2 for i in x], oficios_val['pred_oficios'], width, 
                label='Predicción', color='#F44336', alpha=0.8)

ax1.set_xlabel('Mes de validación')
ax1.set_ylabel('Cantidad de Oficios')
ax1.set_title('Oficios: Real vs Predicción\n(Conjunto de Prueba)', fontweight='bold')
ax1.set_xticks(x)
ax1.set_xticklabels([d.strftime('%Y-%m') for d in oficios_val['mes']], rotation=45, ha='right')
ax1.legend()
ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: format(int(x), ',')))

# Subplot 2: Demandados
ax2 = axes[1]
bars3 = ax2.bar([i - width/2 for i in x], demandados_val['real_demandados'], width, 
                label='Real', color='#4CAF50', alpha=0.8)
bars4 = ax2.bar([i + width/2 for i in x], demandados_val['pred_demandados'], width, 
                label='Predicción', color='#F44336', alpha=0.8)

ax2.set_xlabel('Mes de validación')
ax2.set_ylabel('Cantidad de Demandados')
ax2.set_title('Demandados: Real vs Predicción\n(Conjunto de Prueba)', fontweight='bold')
ax2.set_xticks(x)
ax2.set_xticklabels([d.strftime('%Y-%m') for d in demandados_val['mes']], rotation=45, ha='right')
ax2.legend()
ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: format(int(x), ',')))

plt.tight_layout()

# Guardar
comparativa_path = os.path.join(evidencias_dir, "comparativa_real_vs_prediccion.png")
plt.savefig(comparativa_path, dpi=150, bbox_inches='tight', facecolor='white')
plt.close()
print(f"    ✅ Guardado: {comparativa_path}")

# =============================================================================
# 8. Gráfica 4: Scatter plot de correlación
# =============================================================================
print("\n    Generando gráfica de correlación (scatter plot)...")

fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# Scatter Oficios
ax1 = axes[0]
ax1.scatter(oficios_val['real_oficios'], oficios_val['pred_oficios'], 
            c='#2196F3', s=100, alpha=0.7, edgecolors='white', linewidth=2)

# Línea de ajuste perfecto (y = x)
min_val = min(oficios_val['real_oficios'].min(), oficios_val['pred_oficios'].min())
max_val = max(oficios_val['real_oficios'].max(), oficios_val['pred_oficios'].max())
ax1.plot([min_val, max_val], [min_val, max_val], 'r--', linewidth=2, label='Ajuste perfecto (y=x)')

ax1.set_xlabel('Valores Reales')
ax1.set_ylabel('Valores Predichos')
ax1.set_title('Correlación: Oficios\nReal vs Predicción', fontweight='bold')
ax1.legend()

# Calcular ambas métricas: R² (determinación) y r (correlación de Pearson)
correlation_of = np.corrcoef(oficios_val['real_oficios'], oficios_val['pred_oficios'])[0, 1]
# Mostrar R² de determinación (el real) y correlación de Pearson
metrics_text_of = f'R² = {r2_of:.4f}\nr (Pearson) = {correlation_of:.4f}'
ax1.text(0.05, 0.95, metrics_text_of, transform=ax1.transAxes, fontsize=11,
         verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

# Scatter Demandados
ax2 = axes[1]
ax2.scatter(demandados_val['real_demandados'], demandados_val['pred_demandados'], 
            c='#FF9800', s=100, alpha=0.7, edgecolors='white', linewidth=2)

# Línea de ajuste perfecto
min_val2 = min(demandados_val['real_demandados'].min(), demandados_val['pred_demandados'].min())
max_val2 = max(demandados_val['real_demandados'].max(), demandados_val['pred_demandados'].max())
ax2.plot([min_val2, max_val2], [min_val2, max_val2], 'r--', linewidth=2, label='Ajuste perfecto (y=x)')

ax2.set_xlabel('Valores Reales')
ax2.set_ylabel('Valores Predichos')
ax2.set_title('Correlación: Demandados\nReal vs Predicción', fontweight='bold')
ax2.legend()

# Calcular ambas métricas: R² (determinación) y r (correlación de Pearson)
correlation_dem = np.corrcoef(demandados_val['real_demandados'], demandados_val['pred_demandados'])[0, 1]
# Mostrar R² de determinación (el real) y correlación de Pearson
metrics_text_dem = f'R² = {r2_dem:.4f}\nr (Pearson) = {correlation_dem:.4f}'
ax2.text(0.05, 0.95, metrics_text_dem, transform=ax2.transAxes, fontsize=11,
         verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

plt.tight_layout()

# Guardar
scatter_path = os.path.join(evidencias_dir, "correlacion_real_vs_prediccion.png")
plt.savefig(scatter_path, dpi=150, bbox_inches='tight', facecolor='white')
plt.close()
print(f"    ✅ Guardado: {scatter_path}")

# =============================================================================
# 9. GUARDAR ESTADÍSTICAS EN JSON
# =============================================================================
print("\n" + "=" * 80)
print("[6] EXPORTAR ESTADÍSTICAS")
print("=" * 80)

# Actualizar stats con las gráficas generadas
stats['graficas_generadas'] = [
    os.path.basename(oficios_path),
    os.path.basename(demandados_path),
    os.path.basename(comparativa_path),
    os.path.basename(scatter_path)
]
stats['fecha_generacion'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

# Guardar JSON con todas las estadísticas
json_path = os.path.join(evidencias_dir, "estadisticas_validacion.json")
with open(json_path, 'w', encoding='utf-8') as f:
    json.dump(stats, f, indent=2, ensure_ascii=False, default=str)
print(f"\n    ✅ Estadísticas exportadas: {json_path}")

# =============================================================================
# 10. RESUMEN FINAL
# =============================================================================
print("\n" + "=" * 80)
print("RESUMEN COMPLETO DE VALIDACIÓN")
print("=" * 80)
print(f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                         ANÁLISIS DEL DATASET                                 ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Archivo fuente: embargos_consolidado_mensual.csv                            ║
║  Total de registros originales:        {stats['dataset']['total_filas_original']:>15,}                      ║
║  Registros con mes válido:             {stats['filtrado']['registros_mes_valido']:>15,}                      ║
║  Registros filtrados (mes inválido):   {stats['filtrado']['registros_mes_invalido']:>15,}                      ║
║  Demandados únicos (identificaciones): {stats['dataset']['demandados_unicos_total']:>15,}                      ║
║  Rango temporal: {stats['dataset']['rango_fechas']['inicio']} a {stats['dataset']['rango_fechas']['fin']}                                       ║
║  Total de meses: {stats['dataset']['total_meses']:>2}                                                          ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                     DIVISIÓN ENTRENAMIENTO / VALIDACIÓN                      ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Meses de entrenamiento: {stats['entrenamiento']['meses']:>2}                                                   ║
║  Meses de validación:    {stats['validacion']['meses']:>2} ({stats['validacion']['periodo']['inicio']} a {stats['validacion']['periodo']['fin']})                            ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                    MÉTRICAS DEL MODELO XGBoost                               ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  PREDICCIÓN DE OFICIOS MENSUALES                                             ║
║    • RMSE (Root Mean Square Error):     {rmse_of:>15,.2f}                    ║
║    • MAE  (Mean Absolute Error):        {mae_of:>15,.2f}                    ║
║    • MAPE (Mean Absolute % Error):      {mape_of:>14.2f}%                    ║
║    • R²   (Coef. de Determinación):     {r2_of:>15.4f}                    ║
╠──────────────────────────────────────────────────────────────────────────────╣
║  PREDICCIÓN DE DEMANDADOS ÚNICOS MENSUALES                                   ║
║    • RMSE (Root Mean Square Error):     {rmse_dem:>15,.2f}                    ║
║    • MAE  (Mean Absolute Error):        {mae_dem:>15,.2f}                    ║
║    • MAPE (Mean Absolute % Error):      {mape_dem:>14.2f}%                    ║
║    • R²   (Coef. de Determinación):     {r2_dem:>15.4f}                    ║
╚══════════════════════════════════════════════════════════════════════════════╝
""")

print("\nGRÁFICAS GENERADAS:")
print(f"  1. {oficios_path}")
print(f"  2. {demandados_path}")
print(f"  3. {comparativa_path}")
print(f"  4. {scatter_path}")
print(f"\nESTADÍSTICAS JSON:")
print(f"  {json_path}")
print("\n" + "=" * 80)
print("✅ EVIDENCIAS GENERADAS EXITOSAMENTE")
print("=" * 80)
