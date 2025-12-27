"""
Script de prueba rápida para verificar que las matrices de confusión
se carguen correctamente desde el CSV
"""
import os
import sys
import pandas as pd
import json
import numpy as np

# Configurar rutas
test_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(test_dir)
datos_dir = os.path.join(project_root, "datos")

print("="*60)
print("TEST: Verificación de Matrices de Confusión en CSV")
print("="*60)

# Cargar CSV
csv_path = os.path.join(datos_dir, 'resultados_clasificaciones.csv')
print(f"\n1. Cargando archivo: {csv_path}")

try:
    df = pd.read_csv(csv_path)
    print(f"   ✓ Archivo cargado correctamente")
    print(f"   Filas: {len(df)}, Columnas: {len(df.columns)}")
except Exception as e:
    print(f"   ✗ Error al cargar: {e}")
    exit(1)

# Verificar columnas
print(f"\n2. Verificando columnas...")
print(f"   Columnas encontradas: {df.columns.tolist()}")

required_cols = ['matriz_confusion', 'clases_matriz']
missing = [col for col in required_cols if col not in df.columns]

if missing:
    print(f"   ✗ FALTAN columnas: {missing}")
    exit(1)
else:
    print(f"   ✓ Todas las columnas requeridas están presentes")

# Verificar contenido de matrices
print(f"\n3. Verificando contenido de matrices...")
modelos = df['modelo'].unique()
print(f"   Modelos encontrados: {modelos.tolist()}")

for i, modelo in enumerate(modelos, 1):
    print(f"\n   Modelo {i}/{len(modelos)}: {modelo}")
    df_modelo = df[df['modelo'] == modelo]
    primera_fila = df_modelo.iloc[0]
    
    # Verificar que no sea NaN
    if pd.isna(primera_fila['matriz_confusion']):
        print(f"      ✗ matriz_confusion es NaN")
        continue
    if pd.isna(primera_fila['clases_matriz']):
        print(f"      ✗ clases_matriz es NaN")
        continue
    
    # Intentar deserializar
    try:
        cm = np.array(json.loads(primera_fila['matriz_confusion']))
        clases = json.loads(primera_fila['clases_matriz'])
        print(f"      ✓ Matriz deserializada correctamente")
        print(f"      Dimensiones: {cm.shape}")
        print(f"      Clases: {clases}")
        print(f"      Suma total: {cm.sum()}")
    except json.JSONDecodeError as e:
        print(f"      ✗ Error JSON: {e}")
        print(f"      Contenido: {primera_fila['matriz_confusion'][:100]}...")
    except Exception as e:
        print(f"      ✗ Error al procesar: {e}")

print("\n" + "="*60)
print("TEST COMPLETADO")
print("="*60)
