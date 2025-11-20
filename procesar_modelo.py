"""
Script para procesar el CSV original de la BD y generar todos los archivos necesarios
para los dashboards (consolidado, predicciones y clasificaciones)
"""
import pandas as pd
import numpy as np
import csv
import os
import sys
from xgboost import XGBRegressor, XGBClassifier
from sklearn.metrics import mean_squared_error, mean_absolute_error, classification_report
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

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

def procesar_csv_original(csv_files, output_dir=None):
    """
    Procesa los archivos CSV originales de la BD y genera el consolidado
    
    Args:
        csv_files: Lista de rutas a los archivos CSV originales
        output_dir: Directorio donde guardar los archivos generados (None = directorio actual)
    
    Returns:
        str: Ruta al archivo consolidado generado
    """
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
    
    # Muestra por mes (7% de los datos)
    frac_muestra = 0.07
    df_muestreado = df.groupby('mes', group_keys=False).apply(
        lambda x: x.sample(frac=frac_muestra, random_state=42)
    ).reset_index(drop=True)
    
    # Guarda resultado consolidado
    output_file = os.path.join(output_dir, "embargos_consolidado_mensual.csv")
    df_muestreado.to_csv(output_file, index=False)
    print(f"\n[OK] Archivo consolidado generado: {output_file}")
    print(f"   Filas originales: {len(df):,}, tras muestreo: {len(df_muestreado):,}")
    print(f"   Filas corregidas: {len(log_corregidas)}")
    print(f"   Filas omitidas: {len(log_omitidas)}")
    
    return output_file

def entrenar_modelos_y_generar_predicciones(consolidado_path, output_dir=None):
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
    
    oficios_por_mes['oficios_lag1'] = oficios_por_mes['id'].shift(1)
    oficios_por_mes['oficios_lag2'] = oficios_por_mes['id'].shift(2)
    oficios_por_mes['oficios_lag3'] = oficios_por_mes['id'].shift(3)
    oficios_por_mes['oficios_ma3'] = oficios_por_mes['id'].rolling(window=3).mean().shift(1)
    oficios_por_mes['demandados_lag1'] = oficios_por_mes['identificacion'].shift(1)
    oficios_por_mes['demandados_lag2'] = oficios_por_mes['identificacion'].shift(2)
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
        print(f"   RMSE: {rmse:.2f}, MAE: {mae:.2f}")
        
        # Guardar predicciones de oficios
        df_pred_oficios = test.iloc[mask_test.values][['año', 'mes_num']].copy()
        df_pred_oficios['real_oficios'] = y_test_clean.values
        df_pred_oficios['pred_oficios'] = y_pred
        df_pred_oficios['mes'] = df_pred_oficios['año'].astype(str) + "-" + df_pred_oficios['mes_num'].astype(str).str.zfill(2)
        output_file = os.path.join(output_dir, "predicciones_oficios_por_mes.csv")
        df_pred_oficios[['mes', 'real_oficios', 'pred_oficios']].to_csv(output_file, index=False)
        print(f"   [OK] Generado: {output_file}")
    else:
        print(f"   [ADVERTENCIA] No hay suficientes datos limpios para entrenar el modelo de oficios")
        print(f"      Datos de entrenamiento limpios: {len(X_train_clean)}, Datos de test limpios: {len(X_test_clean)}")
        # Generar archivo vacío o con datos básicos
        output_file = os.path.join(output_dir, "predicciones_oficios_por_mes.csv")
        df_pred_oficios = pd.DataFrame(columns=['mes', 'real_oficios', 'pred_oficios'])
        df_pred_oficios.to_csv(output_file, index=False)
        print(f"   [INFO] Archivo vacío creado: {output_file}")
    
    # REGRESIÓN: Demandados por mes
    print("\n[INFO] Entrenando modelo de regresión: Demandados únicos por mes...")
    features_dem = ['año', 'mes_num', 'mes_sin', 'mes_cos', 'demandados_lag1', 'demandados_lag2', 'demandados_ma3']
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
        print(f"   RMSE: {rmse:.2f}, MAE: {mae:.2f}")
        
        # Guardar predicciones de demandados
        df_pred_demandados = test.iloc[mask_test_d.values][['año', 'mes_num']].copy()
        df_pred_demandados['real_demandados'] = y_test_d_clean.values
        df_pred_demandados['pred_demandados'] = y_pred_d
        df_pred_demandados['mes'] = df_pred_demandados['año'].astype(str) + "-" + df_pred_demandados['mes_num'].astype(str).str.zfill(2)
        output_file = os.path.join(output_dir, "predicciones_demandados_por_mes.csv")
        df_pred_demandados[['mes', 'real_demandados', 'pred_demandados']].to_csv(output_file, index=False)
        print(f"   [OK] Generado: {output_file}")
    else:
        print(f"   [ADVERTENCIA] No hay suficientes datos limpios para entrenar el modelo de demandados")
        print(f"      Datos de entrenamiento limpios: {len(X_train_d_clean)}, Datos de test limpios: {len(X_test_d_clean)}")
        # Generar archivo vacío o con datos básicos
        output_file = os.path.join(output_dir, "predicciones_demandados_por_mes.csv")
        df_pred_demandados = pd.DataFrame(columns=['mes', 'real_demandados', 'pred_demandados'])
        df_pred_demandados.to_csv(output_file, index=False)
        print(f"   [INFO] Archivo vacío creado: {output_file}")
    
    # CLASIFICACIONES
    print("\n[INFO] Entrenando modelos de clasificación...")
    features_clf = [
        'entidad_remitente_enc', 'mes_num', 'montoaembargar',
        'estado_embargo_enc', 'es_cliente_bin'
    ]
    
    def report_to_df(report, modelo, target_names):
        """Convierte un reporte de clasificación a DataFrame"""
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
        return df_metrics
    
    dfs_clasificaciones = []
    
    # 1. Tipo Embargo
    try:
        X = df[features_clf]
        y = df['tipo_embargo_enc']
        X_train, X_test, y_train, y_test = train_test_split(X, y, stratify=y, test_size=0.2, random_state=42)
        clf = XGBClassifier(n_estimators=100, max_depth=7, learning_rate=0.1,
                           subsample=0.9, colsample_bytree=0.8,
                           eval_metric='mlogloss', use_label_encoder=False,
                           tree_method="hist")
        clf.fit(X_train, y_train)
        y_pred = clf.predict(X_test)
        labels_report = np.unique(np.concatenate([y_test, y_pred]))
        target_names = le_tipo_embargo.inverse_transform(labels_report)
        report = classification_report(y_test, y_pred, output_dict=True,
                                      target_names=target_names, zero_division=0)
        dfs_clasificaciones.append(report_to_df(report, "Tipo Embargo", target_names))
        print("   [OK] Modelo: Tipo Embargo")
    except Exception as e:
        print(f"   [ADVERTENCIA] Error en Tipo Embargo: {e}")
    
    # 2. Estado Embargo
    try:
        features_clf2 = [
            'entidad_remitente_enc', 'mes_num', 'montoaembargar',
            'tipo_embargo_enc', 'es_cliente_bin'
        ]
        y2 = df['estado_embargo_enc']
        class_counts = y2.value_counts()
        clases_validas = class_counts[class_counts >= 2].index
        mask_validas = y2.isin(clases_validas)
        X2_valid = df[features_clf2][mask_validas]
        y2_valid = y2[mask_validas]
        
        if len(X2_valid) > 0:
            X_train2, X_test2, y_train2, y_test2 = train_test_split(
                X2_valid, y2_valid, stratify=y2_valid, test_size=0.2, random_state=42)
            clf2 = XGBClassifier(n_estimators=100, max_depth=7, learning_rate=0.1,
                                subsample=0.9, colsample_bytree=0.8,
                                eval_metric='mlogloss', use_label_encoder=False,
                                tree_method="hist")
            clf2.fit(X_train2, y_train2)
            y_pred2 = clf2.predict(X_test2)
            labels_report2 = np.unique(np.concatenate([y_test2, y_pred2]))
            target_names2 = le_estado_embargo.inverse_transform(labels_report2)
            report2 = classification_report(y_test2, y_pred2, output_dict=True,
                                           target_names=target_names2, zero_division=0)
            dfs_clasificaciones.append(report_to_df(report2, "Estado Embargo", target_names2))
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
        report3 = classification_report(y_test3, y_pred3, output_dict=True,
                                       target_names=target_names3, zero_division=0)
        dfs_clasificaciones.append(report_to_df(report3, "Cliente", target_names3))
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

def main():
    """Función principal"""
    if len(sys.argv) < 2:
        print("Uso: python procesar_modelo.py <csv1> [csv2] [csv3] ...")
        print("Ejemplo: python procesar_modelo.py 'consulta detalle embargos-2023-01.csv' 'consulta detalle embargos-2024-01.csv'")
        sys.exit(1)
    
    csv_files = sys.argv[1:]
    
    # Verificar que los archivos existan
    for csv_file in csv_files:
        if not os.path.exists(csv_file):
            print(f"[ERROR] No se encontro el archivo: {csv_file}")
            sys.exit(1)
    
    # Obtener directorio de salida (carpeta de datos del usuario o directorio actual)
    try:
        from utils_csv import get_data_path
        output_dir = get_data_path()
    except:
        output_dir = os.getcwd()
    
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
        consolidado_path = procesar_csv_original(csv_files, output_dir)
        
        # Paso 2: Entrenar modelos y generar predicciones
        entrenar_modelos_y_generar_predicciones(consolidado_path, output_dir)
        
        print(f"\n[OK] Todos los archivos han sido generados en: {output_dir}")
        
    except Exception as e:
        print(f"\n[ERROR] Error durante el procesamiento: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

