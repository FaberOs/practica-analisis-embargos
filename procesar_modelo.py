"""
Script para procesar el CSV original de la BD y generar todos los archivos necesarios
para los dashboards (consolidado, predicciones y clasificaciones)
"""
import argparse
import csv
import os
import sys
from dataclasses import dataclass
from typing import Optional

import pandas as pd
import numpy as np
from xgboost import XGBRegressor, XGBClassifier
from sklearn.metrics import mean_squared_error, mean_absolute_error, classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
import json

Z_VALUE = 1.96
MIN_CLASS_SAMPLES = 5


@dataclass
class SamplingConfig:
    """Configura cómo se realiza el muestreo mensual del consolidado."""
    frac: float = 1.0
    n_per_month: Optional[int] = None
    random_state: int = 42


@dataclass
class ForecastConfig:
    """Parámetros para la generación de pronósticos."""
    horizon: int = 12


def _confidence_label(horizonte: int) -> str:
    if horizonte <= 3:
        return "Alta"
    if horizonte <= 6:
        return "Media"
    return "Baja"


def _compute_interval(residual_scale: float, horizonte: int) -> float:
    base = residual_scale if residual_scale > 0 else 1.0
    return Z_VALUE * base * np.sqrt(max(1, horizonte))


def _ensure_month_continuity(df: pd.DataFrame) -> pd.DataFrame:
    """Garantiza que la serie mensual no tenga huecos."""
    if df.empty:
        return df
    df = df.sort_values(['año', 'mes_num']).copy()
    fecha = pd.to_datetime({'year': df['año'], 'month': df['mes_num'], 'day': 1})
    df['fecha'] = fecha
    full_range = pd.date_range(fecha.min(), fecha.max(), freq='MS')
    df = df.set_index('fecha').reindex(full_range)
    df['año'] = df.index.year
    df['mes_num'] = df.index.month
    for col in ['id', 'identificacion', 'montoaembargar']:
        if col in df.columns:
            df[col] = df[col].fillna(0)
    df = df.reset_index().rename(columns={'index': 'fecha'})
    df['mes_label'] = df['año'].astype(str) + "-" + df['mes_num'].astype(str).str.zfill(2)
    return df

# Configurar codificación UTF-8 para Windows
if sys.platform == 'win32':
    try:
        # Intentar configurar la salida estándar para usar UTF-8
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8')
        if hasattr(sys.stderr, 'reconfigure'):
            sys.stderr.reconfigure(encoding='utf-8')
    except:
        # Si falla, continuar sin cambios (los mensajes ya no usan emojis)
        pass

def procesar_csv_original(csv_files, output_dir=None, sampling_cfg: Optional[SamplingConfig] = None):
    """
    Procesa los archivos CSV originales de la BD y genera el consolidado
    
    Args:
        csv_files: Lista de rutas a los archivos CSV originales
        output_dir: Directorio donde guardar los archivos generados (None = directorio actual)
        sampling_cfg: Configuración de muestreo mensual
    
    Returns:
        str: Ruta al archivo consolidado generado
    """
    sampling_cfg = sampling_cfg or SamplingConfig()
    if output_dir is None:
        output_dir = os.getcwd()
    else:
        os.makedirs(output_dir, exist_ok=True)
    
    # Orden estándar de columnas
    expected_columns = [
        "id", "ciudad", "entidad_remitente", "correo", "direccion", "funcionario", "fecha_banco",
        "fecha_oficio", "referencia", "cuenta", "identificacion", "tipo_identificacion_tipo", "montoaembargar",
        "nombres", "expediente", "mes", "entidad_bancaria", "estado_embargo", "tipo_documento",
        "tipo_embargo", "estado_demandado", "es_cliente", "tipo_carta"
    ]
    num_expected = len(expected_columns)
    
    dataframes = []
    log_corregidas, log_omitidas = [], []
    
    for input_file in csv_files:
        print(f"Leyendo archivo: {os.path.basename(input_file)}")
        rows = []
        # Intentar diferentes codificaciones
        encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
        df_temp = None
        
        for encoding in encodings:
            try:
                with open(input_file, encoding=encoding) as infile:
                    reader = csv.reader(infile)
                    headers = next(reader)
                    for idx, row in enumerate(reader, start=2):
                        # Reparar filas con menos columnas
                        if len(row) < num_expected:
                            row = row + [''] * (num_expected - len(row))
                            log_corregidas.append((os.path.basename(input_file), idx, 'faltantes', len(row)))
                        # Reparar filas con más columnas
                        if len(row) > num_expected:
                            extra = len(row) - num_expected
                            direccion = ','.join(row[4:4+1+extra])
                            fixed = row[:4] + [direccion] + row[4+1+extra:]
                            if len(fixed) == num_expected:
                                row = fixed
                                log_corregidas.append((os.path.basename(input_file), idx, 'excedente', len(row)))
                            else:
                                log_omitidas.append((os.path.basename(input_file), idx, len(row), row))
                                continue
                        if len(row) == num_expected:
                            rows.append(row)
                        else:
                            log_omitidas.append((os.path.basename(input_file), idx, len(row), row))
                df_temp = pd.DataFrame(rows, columns=expected_columns)
                break
            except UnicodeDecodeError:
                continue
            except Exception as e:
                print(f"Error al leer {input_file} con encoding {encoding}: {e}")
                continue
        
        if df_temp is not None and not df_temp.empty:
            dataframes.append(df_temp)
        else:
            print(f"[ADVERTENCIA] No se pudo leer {input_file}")
    
    if not dataframes:
        raise ValueError("No se pudieron leer los archivos CSV")
    
    # Unión de todo
    df = pd.concat(dataframes, ignore_index=True)
    
    # Limpieza y normalización
    df['montoaembargar'] = pd.to_numeric(df['montoaembargar'], errors='coerce').fillna(0)
    
    def clean_es_cliente(val):
        v = str(val).strip().upper()
        return 1 if v in {'1', 'SI_ES_CLIENTE', 'CLIENTE', 'SI', 'SÍ', 'TRUE', 'Y', 'YES'} else 0
    
    df['es_cliente'] = df['es_cliente'].apply(clean_es_cliente).astype(int)
    
    # Categóricas: upper, strip y sin nulos
    cat_cols = ['entidad_bancaria', 'ciudad', 'entidad_remitente', 'tipo_documento', 
                'tipo_embargo', 'estado_embargo', 'estado_demandado', 'tipo_carta', 'mes']
    for col in cat_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().str.upper().replace({'NAN': '', 'NONE': '', 'NULL': ''})
    
    # Agrupa clases raras
    for col in ['tipo_embargo', 'estado_embargo']:
        if col in df.columns:
            vc = df[col].value_counts()
            raros = vc[vc < 10].index
            df.loc[df[col].isin(raros), col] = 'OTRO'
    
    # Limpia fechas
    for col in ['fecha_banco', 'fecha_oficio']:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')
    
    apply_sampling = (sampling_cfg.n_per_month is not None) or (sampling_cfg.frac < 0.9999)
    if apply_sampling:
        print(f"[INFO] Aplicando muestreo mensual (frac={sampling_cfg.frac}, n={sampling_cfg.n_per_month})")

        def _sampler(group: pd.DataFrame) -> pd.DataFrame:
            if sampling_cfg.n_per_month is not None:
                n_rows = min(sampling_cfg.n_per_month, len(group))
                return group.sample(n=n_rows, random_state=sampling_cfg.random_state)
            frac = min(max(sampling_cfg.frac, 0.0), 1.0)
            if frac == 0:
                return group.head(0)
            return group.sample(frac=frac, random_state=sampling_cfg.random_state)

        df_muestreado = df.groupby('mes', group_keys=False).apply(_sampler).reset_index(drop=True)
    else:
        df_muestreado = df.reset_index(drop=True).copy()
    
    # Guarda resultado consolidado
    output_file = os.path.join(output_dir, "embargos_consolidado_mensual.csv")
    df_muestreado.to_csv(output_file, index=False)
    print(f"\n[OK] Archivo consolidado generado: {output_file}")
    print(f"   Filas originales: {len(df):,}, tras muestreo: {len(df_muestreado):,}")
    print(f"   Filas corregidas: {len(log_corregidas)}")
    print(f"   Filas omitidas: {len(log_omitidas)}")
    
    return output_file

def entrenar_modelos_y_generar_predicciones(consolidado_path, output_dir=None, horizonte=12):
    """
    Entrena los modelos y genera los archivos de predicciones y clasificaciones
    
    Args:
        consolidado_path: Ruta al archivo consolidado
        output_dir: Directorio donde guardar los archivos generados
    """
    if output_dir is None:
        output_dir = os.path.dirname(consolidado_path) if os.path.dirname(consolidado_path) else os.getcwd()
    else:
        os.makedirs(output_dir, exist_ok=True)
    
    print("\n" + "="*60)
    print("ENTRENANDO MODELOS Y GENERANDO PREDICCIONES")
    print("="*60)
    
    # Cargar datos consolidados
    df = pd.read_csv(consolidado_path)
    
    def agrupar_otros(df, col, min_freq=10):
        freq = df[col].value_counts()
        otros = freq[freq < min_freq].index
        df[col] = df[col].apply(lambda x: 'OTRO' if x in otros else x)
        return df
    
    # Limpieza adicional
    for col in ['ciudad', 'entidad_remitente', 'tipo_embargo', 'estado_embargo']:
        df[col] = df[col].fillna('OTRO').astype(str).str.strip().str.upper()
        df = agrupar_otros(df, col, min_freq=10)
    
    df['montoaembargar'] = pd.to_numeric(df['montoaembargar'], errors='coerce')
    
    def clean_cliente(val):
        v = str(val).strip().upper()
        return 1 if v in {'1', 'SI', 'SI_ES_CLIENTE', 'CLIENTE', 'TRUE', 'SÍ', 'YES'} else 0
    
    df['es_cliente_bin'] = df['es_cliente'].apply(clean_cliente).astype(int)
    
    df['fecha_banco'] = pd.to_datetime(df['fecha_banco'], errors='coerce')
    df['año'] = pd.to_numeric(df['fecha_banco'].dt.year, errors='coerce')
    df['mes_num'] = pd.to_numeric(df['fecha_banco'].dt.month, errors='coerce')
    df = df.dropna(subset=['año', 'mes_num']).copy()
    df['año'] = df['año'].astype(int)
    df['mes_num'] = df['mes_num'].astype(int)
    
    # Encoding
    le_ciudad = LabelEncoder()
    le_entidad = LabelEncoder()
    le_tipo_embargo = LabelEncoder()
    le_estado_embargo = LabelEncoder()
    
    df['ciudad_enc'] = le_ciudad.fit_transform(df['ciudad'])
    df['entidad_remitente_enc'] = le_entidad.fit_transform(df['entidad_remitente'])
    df['tipo_embargo_enc'] = le_tipo_embargo.fit_transform(df['tipo_embargo'])
    df['estado_embargo_enc'] = le_estado_embargo.fit_transform(df['estado_embargo'])
    
    df['mes_sin'] = np.sin(2 * np.pi * df['mes_num'] / 12.0)
    df['mes_cos'] = np.cos(2 * np.pi * df['mes_num'] / 12.0)
    df['mes_index'] = df['año'] * 12 + df['mes_num']
    
    # Agregación por mes
    oficios_por_mes = df.groupby(['año', 'mes_num']).agg({
        'id': 'count',
        'identificacion': pd.Series.nunique,
        'montoaembargar': 'sum'
    }).reset_index().sort_values(['año', 'mes_num'])
    oficios_por_mes = _ensure_month_continuity(oficios_por_mes)
    
    oficios_por_mes['oficios_lag1'] = oficios_por_mes['id'].shift(1)
    oficios_por_mes['oficios_lag2'] = oficios_por_mes['id'].shift(2)
    oficios_por_mes['oficios_lag3'] = oficios_por_mes['id'].shift(3)
    oficios_por_mes['oficios_ma3'] = oficios_por_mes['id'].rolling(window=3).mean().shift(1)
    oficios_por_mes['demandados_lag1'] = oficios_por_mes['identificacion'].shift(1)
    oficios_por_mes['demandados_lag2'] = oficios_por_mes['identificacion'].shift(2)
    oficios_por_mes['demandados_lag3'] = oficios_por_mes['identificacion'].shift(3)
    oficios_por_mes['demandados_ma3'] = oficios_por_mes['identificacion'].rolling(window=3).mean().shift(1)
    oficios_por_mes['mes_sin'] = np.sin(2 * np.pi * oficios_por_mes['mes_num'] / 12.0)
    oficios_por_mes['mes_cos'] = np.cos(2 * np.pi * oficios_por_mes['mes_num'] / 12.0)
    
    # Validación temporal
    ultimo_año = oficios_por_mes['año'].max()
    train = oficios_por_mes[oficios_por_mes['año'] < ultimo_año]
    test = oficios_por_mes[oficios_por_mes['año'] == ultimo_año]
    
    if len(train) == 0 or len(test) == 0:
        print("[ADVERTENCIA] No hay suficientes datos para entrenar los modelos (se necesita al menos 2 años)")
        return
    
    forecast_cfg = ForecastConfig(horizon=horizonte)

    # REGRESIÓN: Oficios por mes
    print("\n[INFO] Entrenando modelo de regresión: Oficios por mes...")
    features_reg = ['año', 'mes_num', 'mes_sin', 'mes_cos', 'oficios_lag1', 'oficios_lag2', 'oficios_lag3', 'oficios_ma3']
    X_train = train[features_reg]
    y_train = train['id']
    X_test = test[features_reg]
    y_test = test['id']
    
    mask_train = ~(X_train.isnull().any(axis=1) | y_train.isnull())
    mask_test = ~(X_test.isnull().any(axis=1) | y_test.isnull())
    X_train_clean, y_train_clean = X_train[mask_train], y_train[mask_train]
    X_test_clean, y_test_clean = X_test[mask_test], y_test[mask_test]
    
    if len(X_train_clean) > 0 and len(X_test_clean) > 0:
        regressor = XGBRegressor(
            n_estimators=200, learning_rate=0.1, max_depth=7,
            objective='count:poisson', random_state=42,
            base_score=np.mean(y_train_clean)
        )
        regressor.fit(X_train_clean, y_train_clean)
        y_pred = regressor.predict(X_test_clean)
        
        rmse = np.sqrt(mean_squared_error(y_test_clean, y_pred))
        mae = mean_absolute_error(y_test_clean, y_pred)
        residuals = y_test_clean.values - y_pred
        residual_std = np.std(residuals) if len(residuals) > 1 else 0.0
        interval_scale = residual_std if residual_std > 0 else mae
        print(f"   RMSE: {rmse:.2f}, MAE: {mae:.2f}")
        
        # Guardar predicciones de validación histórica de oficios
        df_pred_oficios = test.iloc[mask_test.values][['año', 'mes_num']].copy()
        df_pred_oficios['real_oficios'] = y_test_clean.values
        df_pred_oficios['pred_oficios'] = y_pred
        if 'mes_label' in df_pred_oficios.columns:
            df_pred_oficios['mes'] = df_pred_oficios['mes_label']
        else:
            df_pred_oficios['mes'] = df_pred_oficios['año'].astype(str) + "-" + df_pred_oficios['mes_num'].astype(str).str.zfill(2)
        output_file = os.path.join(output_dir, "predicciones_oficios_validacion.csv")
        df_pred_oficios[['mes', 'real_oficios', 'pred_oficios']].to_csv(output_file, index=False)
        print(f"   [OK] Generado: {output_file}")
        
        # ============================================================================
        # PREDICCIÓN FUTURA: Entrenar con TODOS los datos y predecir 12 meses adelante
        # ============================================================================
        print("\n[INFO] Generando predicciones futuras de oficios (12 meses)...")
        
        # Entrenar modelo con todos los datos disponibles
        X_full = oficios_por_mes[features_reg]
        y_full = oficios_por_mes['id']
        mask_full = ~(X_full.isnull().any(axis=1) | y_full.isnull())
        X_full_clean, y_full_clean = X_full[mask_full], y_full[mask_full]
        
        if len(X_full_clean) > 0:
            # Entrenar modelo con todos los datos
            regressor_futuro = XGBRegressor(
                n_estimators=200, learning_rate=0.1, max_depth=7,
                objective='count:poisson', random_state=42,
                base_score=np.mean(y_full_clean)
            )
            regressor_futuro.fit(X_full_clean, y_full_clean)
            print(f"   Modelo entrenado con {len(X_full_clean)} registros históricos")

            residual_scale = interval_scale if interval_scale > 0 else max(1.0, np.std(y_full_clean))
            
            # Obtener últimos valores para lags
            ultimo_registro = oficios_por_mes.iloc[-1]
            ultimo_año = int(ultimo_registro['año'])
            ultimo_mes = int(ultimo_registro['mes_num'])
            
            # Obtener últimos 3 valores reales de oficios para lags
            ultimos_oficios = oficios_por_mes['id'].tail(3).values
            oficios_lag1 = ultimos_oficios[-1] if len(ultimos_oficios) >= 1 else oficios_por_mes['id'].mean()
            oficios_lag2 = ultimos_oficios[-2] if len(ultimos_oficios) >= 2 else oficios_por_mes['id'].mean()
            oficios_lag3 = ultimos_oficios[-3] if len(ultimos_oficios) >= 3 else oficios_por_mes['id'].mean()
            oficios_ma3 = np.mean(ultimos_oficios) if len(ultimos_oficios) == 3 else oficios_por_mes['id'].mean()
            
            # Predicción recursiva para 12 meses
            predicciones_futuras = []
            
            for horizonte in range(1, forecast_cfg.horizon + 1):
                # Calcular fecha del mes a predecir
                mes_futuro = ultimo_mes + horizonte
                año_futuro = ultimo_año
                while mes_futuro > 12:
                    mes_futuro -= 12
                    año_futuro += 1
                
                # Calcular componentes trigonométricas
                mes_sin = np.sin(2 * np.pi * mes_futuro / 12)
                mes_cos = np.cos(2 * np.pi * mes_futuro / 12)
                
                # Crear features para predicción
                X_futuro = pd.DataFrame({
                    'año': [año_futuro],
                    'mes_num': [mes_futuro],
                    'mes_sin': [mes_sin],
                    'mes_cos': [mes_cos],
                    'oficios_lag1': [oficios_lag1],
                    'oficios_lag2': [oficios_lag2],
                    'oficios_lag3': [oficios_lag3],
                    'oficios_ma3': [oficios_ma3]
                })
                
                # Predecir
                pred_oficios = regressor_futuro.predict(X_futuro)[0]
                pred_oficios = max(0, pred_oficios)  # No permitir valores negativos
                
                intervalo = _compute_interval(residual_scale, horizonte)
                
                limite_inferior = max(0, pred_oficios - intervalo)
                limite_superior = pred_oficios + intervalo
                
                nivel_confianza = _confidence_label(horizonte)
                
                # Guardar predicción
                mes_str = f"{año_futuro}-{str(mes_futuro).zfill(2)}"
                predicciones_futuras.append({
                    'mes': mes_str,
                    'pred_oficios': round(pred_oficios, 2),
                    'limite_inferior': round(limite_inferior, 2),
                    'limite_superior': round(limite_superior, 2),
                    'nivel_confianza': nivel_confianza,
                    'horizonte_meses': horizonte
                })
                
                # Actualizar lags para siguiente iteración (predicción recursiva)
                oficios_lag3 = oficios_lag2
                oficios_lag2 = oficios_lag1
                oficios_lag1 = pred_oficios
                oficios_ma3 = np.mean([oficios_lag1, oficios_lag2, oficios_lag3])
            
            # Guardar predicciones futuras
            df_futuro_oficios = pd.DataFrame(predicciones_futuras)
            output_file_futuro = os.path.join(output_dir, "predicciones_oficios_futuro.csv")
            df_futuro_oficios.to_csv(output_file_futuro, index=False)
            print(f"   [OK] Generado: {output_file_futuro}")
            print(f"   Predicción para próximo mes ({predicciones_futuras[0]['mes']}): {predicciones_futuras[0]['pred_oficios']:.0f} oficios")
            print(f"   Proyección anual (12 meses): {sum(p['pred_oficios'] for p in predicciones_futuras):.0f} oficios")
        else:
            print(f"   [ADVERTENCIA] No hay suficientes datos para generar predicciones futuras")
            # Crear archivo vacío
            output_file_futuro = os.path.join(output_dir, "predicciones_oficios_futuro.csv")
            df_futuro_oficios = pd.DataFrame(columns=['mes', 'pred_oficios', 'limite_inferior', 'limite_superior', 'nivel_confianza', 'horizonte_meses'])
            df_futuro_oficios.to_csv(output_file_futuro, index=False)
            print(f"   [INFO] Archivo vacío creado: {output_file_futuro}")
    else:
        print(f"   [ADVERTENCIA] No hay suficientes datos limpios para entrenar el modelo de oficios")
        print(f"      Datos de entrenamiento limpios: {len(X_train_clean)}, Datos de test limpios: {len(X_test_clean)}")
        # Generar archivos vacíos
        output_file = os.path.join(output_dir, "predicciones_oficios_validacion.csv")
        df_pred_oficios = pd.DataFrame(columns=['mes', 'real_oficios', 'pred_oficios'])
        df_pred_oficios.to_csv(output_file, index=False)
        print(f"   [INFO] Archivo vacío creado: {output_file}")
        
        output_file_futuro = os.path.join(output_dir, "predicciones_oficios_futuro.csv")
        df_futuro_oficios = pd.DataFrame(columns=['mes', 'pred_oficios', 'limite_inferior', 'limite_superior', 'nivel_confianza', 'horizonte_meses'])
        df_futuro_oficios.to_csv(output_file_futuro, index=False)
        print(f"   [INFO] Archivo vacío creado: {output_file_futuro}")
    
    # REGRESIÓN: Demandados por mes
    print("\n[INFO] Entrenando modelo de regresión: Demandados únicos por mes...")
    features_dem = ['año', 'mes_num', 'mes_sin', 'mes_cos', 'demandados_lag1', 'demandados_lag2', 'demandados_lag3', 'demandados_ma3']
    X_train_d = train[features_dem]
    y_train_d = train['identificacion']
    X_test_d = test[features_dem]
    y_test_d = test['identificacion']
    
    mask_train_d = ~(X_train_d.isnull().any(axis=1) | y_train_d.isnull())
    mask_test_d = ~(X_test_d.isnull().any(axis=1) | y_test_d.isnull())
    X_train_d_clean, y_train_d_clean = X_train_d[mask_train_d], y_train_d[mask_train_d]
    X_test_d_clean, y_test_d_clean = X_test_d[mask_test_d], y_test_d[mask_test_d]
    
    if len(X_train_d_clean) > 0 and len(X_test_d_clean) > 0:
        regressor_dem = XGBRegressor(
            n_estimators=200, learning_rate=0.1, max_depth=7,
            objective='count:poisson', random_state=42,
            base_score=np.mean(y_train_d_clean)
        )
        regressor_dem.fit(X_train_d_clean, y_train_d_clean)
        y_pred_d = regressor_dem.predict(X_test_d_clean)
        
        rmse = np.sqrt(mean_squared_error(y_test_d_clean, y_pred_d))
        mae = mean_absolute_error(y_test_d_clean, y_pred_d)
        residuals_d = y_test_d_clean.values - y_pred_d
        residual_std_d = np.std(residuals_d) if len(residuals_d) > 1 else 0.0
        interval_scale_d = residual_std_d if residual_std_d > 0 else mae
        print(f"   RMSE: {rmse:.2f}, MAE: {mae:.2f}")
        
        # Guardar predicciones de validación histórica de demandados
        df_pred_demandados = test.iloc[mask_test_d.values][['año', 'mes_num']].copy()
        df_pred_demandados['real_demandados'] = y_test_d_clean.values
        df_pred_demandados['pred_demandados'] = y_pred_d
        if 'mes_label' in df_pred_demandados.columns:
            df_pred_demandados['mes'] = df_pred_demandados['mes_label']
        else:
            df_pred_demandados['mes'] = df_pred_demandados['año'].astype(str) + "-" + df_pred_demandados['mes_num'].astype(str).str.zfill(2)
        output_file = os.path.join(output_dir, "predicciones_demandados_validacion.csv")
        df_pred_demandados[['mes', 'real_demandados', 'pred_demandados']].to_csv(output_file, index=False)
        print(f"   [OK] Generado: {output_file}")
        
        # ============================================================================
        # PREDICCIÓN FUTURA: Entrenar con TODOS los datos y predecir 12 meses adelante
        # ============================================================================
        print("\n[INFO] Generando predicciones futuras de demandados (12 meses)...")
        
        # Entrenar modelo con todos los datos disponibles
        X_full_d = oficios_por_mes[features_dem]
        y_full_d = oficios_por_mes['identificacion']
        mask_full_d = ~(X_full_d.isnull().any(axis=1) | y_full_d.isnull())
        X_full_d_clean, y_full_d_clean = X_full_d[mask_full_d], y_full_d[mask_full_d]
        
        if len(X_full_d_clean) > 0:
            # Entrenar modelo con todos los datos
            regressor_dem_futuro = XGBRegressor(
                n_estimators=200, learning_rate=0.1, max_depth=7,
                objective='count:poisson', random_state=42,
                base_score=np.mean(y_full_d_clean)
            )
            regressor_dem_futuro.fit(X_full_d_clean, y_full_d_clean)
            print(f"   Modelo entrenado con {len(X_full_d_clean)} registros históricos")

            residual_scale_d = interval_scale_d if interval_scale_d > 0 else max(1.0, np.std(y_full_d_clean))
            
            # Obtener últimos valores para lags
            ultimo_registro = oficios_por_mes.iloc[-1]
            ultimo_año = int(ultimo_registro['año'])
            ultimo_mes = int(ultimo_registro['mes_num'])
            
            # Obtener últimos 3 valores reales de demandados para lags
            ultimos_demandados = oficios_por_mes['identificacion'].tail(3).values
            demandados_lag1 = ultimos_demandados[-1] if len(ultimos_demandados) >= 1 else oficios_por_mes['identificacion'].mean()
            demandados_lag2 = ultimos_demandados[-2] if len(ultimos_demandados) >= 2 else oficios_por_mes['identificacion'].mean()
            demandados_lag3 = ultimos_demandados[-3] if len(ultimos_demandados) >= 3 else oficios_por_mes['identificacion'].mean()
            demandados_ma3 = np.mean([demandados_lag1, demandados_lag2, demandados_lag3])
            
            # Predicción recursiva para 12 meses
            predicciones_futuras_dem = []
            
            for horizonte in range(1, forecast_cfg.horizon + 1):
                # Calcular fecha del mes a predecir
                mes_futuro = ultimo_mes + horizonte
                año_futuro = ultimo_año
                while mes_futuro > 12:
                    mes_futuro -= 12
                    año_futuro += 1
                
                # Calcular componentes trigonométricas
                mes_sin = np.sin(2 * np.pi * mes_futuro / 12)
                mes_cos = np.cos(2 * np.pi * mes_futuro / 12)
                
                # Crear features para predicción
                X_futuro_d = pd.DataFrame({
                    'año': [año_futuro],
                    'mes_num': [mes_futuro],
                    'mes_sin': [mes_sin],
                    'mes_cos': [mes_cos],
                    'demandados_lag1': [demandados_lag1],
                    'demandados_lag2': [demandados_lag2],
                    'demandados_lag3': [demandados_lag3],
                    'demandados_ma3': [demandados_ma3]
                })
                
                # Predecir
                pred_demandados = regressor_dem_futuro.predict(X_futuro_d)[0]
                pred_demandados = max(0, pred_demandados)  # No permitir valores negativos
                
                intervalo = _compute_interval(residual_scale_d, horizonte)
                
                limite_inferior = max(0, pred_demandados - intervalo)
                limite_superior = pred_demandados + intervalo
                
                nivel_confianza = _confidence_label(horizonte)
                
                # Guardar predicción
                mes_str = f"{año_futuro}-{str(mes_futuro).zfill(2)}"
                predicciones_futuras_dem.append({
                    'mes': mes_str,
                    'pred_demandados': round(pred_demandados, 2),
                    'limite_inferior': round(limite_inferior, 2),
                    'limite_superior': round(limite_superior, 2),
                    'nivel_confianza': nivel_confianza,
                    'horizonte_meses': horizonte
                })
                
                # Actualizar lags para siguiente iteración (predicción recursiva)
                demandados_lag3 = demandados_lag2
                demandados_lag3 = demandados_lag2
                demandados_lag2 = demandados_lag1
                demandados_lag1 = pred_demandados
                demandados_ma3 = np.mean([demandados_lag1, demandados_lag2, demandados_lag3])
            
            # Guardar predicciones futuras
            df_futuro_demandados = pd.DataFrame(predicciones_futuras_dem)
            output_file_futuro = os.path.join(output_dir, "predicciones_demandados_futuro.csv")
            df_futuro_demandados.to_csv(output_file_futuro, index=False)
            print(f"   [OK] Generado: {output_file_futuro}")
            print(f"   Predicción para próximo mes ({predicciones_futuras_dem[0]['mes']}): {predicciones_futuras_dem[0]['pred_demandados']:.0f} demandados")
            print(f"   Proyección anual (12 meses): {sum(p['pred_demandados'] for p in predicciones_futuras_dem):.0f} demandados")
        else:
            print(f"   [ADVERTENCIA] No hay suficientes datos para generar predicciones futuras")
            # Crear archivo vacío
            output_file_futuro = os.path.join(output_dir, "predicciones_demandados_futuro.csv")
            df_futuro_demandados = pd.DataFrame(columns=['mes', 'pred_demandados', 'limite_inferior', 'limite_superior', 'nivel_confianza', 'horizonte_meses'])
            df_futuro_demandados.to_csv(output_file_futuro, index=False)
            print(f"   [INFO] Archivo vacío creado: {output_file_futuro}")
    else:
        print(f"   [ADVERTENCIA] No hay suficientes datos limpios para entrenar el modelo de demandados")
        print(f"      Datos de entrenamiento limpios: {len(X_train_d_clean)}, Datos de test limpios: {len(X_test_d_clean)}")
        # Generar archivos vacíos
        output_file = os.path.join(output_dir, "predicciones_demandados_validacion.csv")
        df_pred_demandados = pd.DataFrame(columns=['mes', 'real_demandados', 'pred_demandados'])
        df_pred_demandados.to_csv(output_file, index=False)
        print(f"   [INFO] Archivo vacío creado: {output_file}")
        
        output_file_futuro = os.path.join(output_dir, "predicciones_demandados_futuro.csv")
        df_futuro_demandados = pd.DataFrame(columns=['mes', 'pred_demandados', 'limite_inferior', 'limite_superior', 'nivel_confianza', 'horizonte_meses'])
        df_futuro_demandados.to_csv(output_file_futuro, index=False)
        print(f"   [INFO] Archivo vacío creado: {output_file_futuro}")
    
    # CLASIFICACIONES
    print("\n[INFO] Entrenando modelos de clasificación...")
    features_clf = [
        'entidad_remitente_enc', 'mes_num', 'montoaembargar',
        'estado_embargo_enc', 'es_cliente_bin'
    ]
    
    def report_to_df(report, modelo, target_names, y_test, y_pred, label_names):
        """Convierte un reporte de clasificación a DataFrame e incluye matriz de confusión"""
        df_metrics = pd.DataFrame(report).transpose().reset_index()
        df_metrics = df_metrics.rename(columns={'index': 'clase'})
        df_metrics['modelo'] = modelo
        df_metrics = df_metrics[df_metrics['clase'].isin(target_names)]
        if 'precision' in df_metrics.columns:
            df_metrics = df_metrics.rename(columns={
                'precision': 'precision',
                'recall': 'recall',
                'f1-score': 'f1',
                'support': 'soporte'
            })
            df_metrics = df_metrics[['modelo', 'clase', 'precision', 'recall', 'f1', 'soporte']]
        
        # Calcular matriz de confusión
        try:
            cm = confusion_matrix(y_test, y_pred, labels=range(len(label_names)))
            # Guardar como JSON (una sola fila por modelo)
            df_metrics['matriz_confusion'] = json.dumps(cm.tolist())
            df_metrics['clases_matriz'] = json.dumps(label_names)
        except Exception as e:
            print(f"      [ADVERTENCIA] No se pudo calcular matriz de confusión: {e}")
            df_metrics['matriz_confusion'] = None
            df_metrics['clases_matriz'] = None
        
        return df_metrics
    
    def prepare_multiclass_dataset(feature_cols, target_col, encoder, min_samples=MIN_CLASS_SAMPLES):
        """Filtra clases poco representadas y re-encodea etiquetas para evitar errores."""
        target_series = df[target_col].copy()
        counts = target_series.value_counts()
        valid_codes = counts[counts >= min_samples].index.tolist()
        if len(valid_codes) < 2:
            return None
        mask = target_series.isin(valid_codes)
        X_local = df.loc[mask, feature_cols].copy()
        y_codes = target_series[mask].copy()
        labels_text = encoder.inverse_transform(y_codes.to_numpy())
        subset_encoder = LabelEncoder()
        y_encoded = subset_encoder.fit_transform(labels_text)
        label_names = subset_encoder.classes_.tolist()
        return X_local, y_encoded, label_names
    
    dfs_clasificaciones = []
    
    # 1. Tipo Embargo
    tipo_dataset = prepare_multiclass_dataset(features_clf, 'tipo_embargo_enc', le_tipo_embargo)
    if tipo_dataset is None:
        print(f"   [ADVERTENCIA] Tipo Embargo: no hay suficientes clases con al menos {MIN_CLASS_SAMPLES} registros.")
    else:
        try:
            X_tipo, y_tipo, tipo_labels = tipo_dataset
            X_train, X_test, y_train, y_test = train_test_split(
                X_tipo, y_tipo, stratify=y_tipo, test_size=0.2, random_state=42
            )
            clf = XGBClassifier(
                n_estimators=100, max_depth=7, learning_rate=0.1,
                subsample=0.9, colsample_bytree=0.8,
                eval_metric='mlogloss', use_label_encoder=False,
                tree_method="hist"
            )
            clf.fit(X_train, y_train)
            y_pred = clf.predict(X_test)
            report = classification_report(
                y_test, y_pred, output_dict=True,
                target_names=tipo_labels, zero_division=0
            )
            dfs_clasificaciones.append(
                report_to_df(report, "Tipo Embargo", tipo_labels, y_test, y_pred, tipo_labels)
            )
            print("   [OK] Modelo: Tipo Embargo")
        except Exception as e:
            print(f"   [ADVERTENCIA] Error en Tipo Embargo: {e}")
    
    # 2. Estado Embargo
    features_clf2 = [
        'entidad_remitente_enc', 'mes_num', 'montoaembargar',
        'tipo_embargo_enc', 'es_cliente_bin'
    ]
    estado_dataset = prepare_multiclass_dataset(features_clf2, 'estado_embargo_enc', le_estado_embargo)
    if estado_dataset is None:
        print(f"   [ADVERTENCIA] Estado Embargo: no hay suficientes clases con al menos {MIN_CLASS_SAMPLES} registros.")
    else:
        try:
            X_estado, y_estado, estado_labels = estado_dataset
            X_train2, X_test2, y_train2, y_test2 = train_test_split(
                X_estado, y_estado, stratify=y_estado, test_size=0.2, random_state=42
            )
            clf2 = XGBClassifier(
                n_estimators=100, max_depth=7, learning_rate=0.1,
                subsample=0.9, colsample_bytree=0.8,
                eval_metric='mlogloss', use_label_encoder=False,
                tree_method="hist"
            )
            clf2.fit(X_train2, y_train2)
            y_pred2 = clf2.predict(X_test2)
            report2 = classification_report(
                y_test2, y_pred2, output_dict=True,
                target_names=estado_labels, zero_division=0
            )
            dfs_clasificaciones.append(
                report_to_df(report2, "Estado Embargo", estado_labels, y_test2, y_pred2, estado_labels)
            )
            print("   [OK] Modelo: Estado Embargo")
        except Exception as e:
            print(f"   [ADVERTENCIA] Error en Estado Embargo: {e}")
    
    # 3. Cliente/No Cliente
    try:
        features_clf3 = [
            'entidad_remitente_enc', 'mes_num', 'montoaembargar',
            'tipo_embargo_enc', 'estado_embargo_enc'
        ]
        y3 = df['es_cliente_bin']
        X_train3, X_test3, y_train3, y_test3 = train_test_split(
            df[features_clf3], y3, stratify=y3, test_size=0.2, random_state=42)
        scale_pos_weight = (y_train3 == 0).sum() / (y_train3 == 1).sum() if (y_train3 == 1).sum() > 0 else 1
        clf3 = XGBClassifier(n_estimators=100, max_depth=7, learning_rate=0.1,
                            subsample=0.9, colsample_bytree=0.8,
                            eval_metric='auc', use_label_encoder=False,
                            tree_method="hist", scale_pos_weight=scale_pos_weight)
        clf3.fit(X_train3, y_train3)
        y_pred3 = clf3.predict(X_test3)
        labels_report3 = np.unique(np.concatenate([y_test3, y_pred3]))
        target_names3 = ["NO_CLIENTE", "CLIENTE"]
        all_classes3 = ["NO_CLIENTE", "CLIENTE"]
        report3 = classification_report(y_test3, y_pred3, output_dict=True,
                                       target_names=target_names3, zero_division=0)
        dfs_clasificaciones.append(report_to_df(report3, "Cliente", target_names3, y_test3, y_pred3, all_classes3))
        print("   [OK] Modelo: Cliente/No Cliente")
    except Exception as e:
        print(f"   [ADVERTENCIA] Error en Cliente: {e}")
    
    # Guardar resultados de clasificaciones
    if dfs_clasificaciones:
        df_metrics_all = pd.concat(dfs_clasificaciones, ignore_index=True)
        output_file = os.path.join(output_dir, "resultados_clasificaciones.csv")
        df_metrics_all.to_csv(output_file, index=False)
        print(f"\n[OK] Generado: {output_file}")
    
    print("\n" + "="*60)
    print("[OK] PROCESAMIENTO COMPLETADO")
    print("="*60)


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Procesa los CSV de embargos y genera archivos para los dashboards"
    )
    parser.add_argument("csv_files", nargs="+", help="Rutas a los archivos CSV originales")
    parser.add_argument("--output-dir", dest="output_dir", default=None,
                        help="Directorio donde guardar los resultados (default: carpeta de datos del usuario if disponible)")
    parser.add_argument("--frac-muestra", dest="frac_muestra", type=float, default=1.0,
                        help="Fracción mensual a muestrear (1.0 = usa todos los registros)")
    parser.add_argument("--n-muestra", dest="n_muestra", type=int, default=None,
                        help="Número máximo de filas por mes (se usa antes que frac si se especifica)")
    parser.add_argument("--horizonte", dest="horizonte", type=int, default=12,
                        help="Meses futuros a pronosticar")
    parser.add_argument("--random-state", dest="random_state", type=int, default=42,
                        help="Semilla para operaciones aleatorias (muestreo)")
    return parser.parse_args()

def main():
    """Función principal"""
    args = parse_arguments()
    csv_files = args.csv_files

    # Verificar que los archivos existan
    for csv_file in csv_files:
        if not os.path.exists(csv_file):
            print(f"[ERROR] No se encontro el archivo: {csv_file}")
            sys.exit(1)

    # Obtener directorio de salida
    output_dir = args.output_dir
    if output_dir is None:
        try:
            from utils_csv import get_data_path
            output_dir = get_data_path()
        except Exception:
            output_dir = os.getcwd()
    os.makedirs(output_dir, exist_ok=True)

    sampling_cfg = SamplingConfig(
        frac=args.frac_muestra if args.frac_muestra is not None else 1.0,
        n_per_month=args.n_muestra,
        random_state=args.random_state
    )
    
    print("="*60)
    print("PROCESANDO ARCHIVOS CSV DE LA BASE DE DATOS")
    print("="*60)
    print(f"Archivos a procesar: {len(csv_files)}")
    for f in csv_files:
        print(f"  - {os.path.basename(f)}")
    print(f"\nDirectorio de salida: {output_dir}")
    print("="*60)
    
    try:
        # Paso 1: Procesar y consolidar
        consolidado_path = procesar_csv_original(csv_files, output_dir, sampling_cfg)
        
        # Paso 2: Entrenar modelos y generar predicciones
        entrenar_modelos_y_generar_predicciones(consolidado_path, output_dir, horizonte=args.horizonte)
        
        print(f"\n[OK] Todos los archivos han sido generados en: {output_dir}")
        
    except Exception as e:
        print(f"\n[ERROR] Error durante el procesamiento: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

