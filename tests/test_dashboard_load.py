"""
Test para simular la carga de CSV tal como lo hace el dashboard
"""
import os
import sys
import pandas as pd

# Configurar rutas
test_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(test_dir)
datos_dir = os.path.join(project_root, "datos")

print("="*60)
print("TEST: Simulando carga del dashboard")
print("="*60)

csv_path = os.path.join(datos_dir, 'resultados_clasificaciones.csv')
name = "resultados_clasificaciones.csv"

# Simular la lógica del dashboard
dtype_dict = {}
if "clasificaciones" in name.lower():
    dtype_dict = {
        'modelo': 'category', 
        'clase': 'category'
        # matriz_confusion y clases_matriz se leerán automáticamente
    }

print(f"\n1. dtype_dict configurado: {dtype_dict}")

encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1', 'utf-8-sig']

df = None
for encoding in encodings:
    try:
        print(f"\n2. Intentando cargar con encoding: {encoding}")
        df = pd.read_csv(
            csv_path, 
            low_memory=False, 
            encoding=encoding,
            dtype=dtype_dict,
            engine='c'
        )
        df.columns = df.columns.str.strip()
        print(f"   ✓ Carga exitosa con {encoding}")
        break
    except UnicodeDecodeError:
        print(f"   ✗ UnicodeDecodeError con {encoding}")
        continue
    except Exception as e:
        print(f"   ✗ Error con {encoding}: {e}")
        continue

if df is not None:
    print(f"\n3. DataFrame cargado correctamente")
    print(f"   Filas: {len(df)}")
    print(f"   Columnas: {df.columns.tolist()}")
    print(f"\n4. Verificando columnas críticas:")
    print(f"   'matriz_confusion' presente: {'matriz_confusion' in df.columns}")
    print(f"   'clases_matriz' presente: {'clases_matriz' in df.columns}")
    
    if 'matriz_confusion' in df.columns:
        print(f"\n5. Verificando contenido de matriz_confusion:")
        print(f"   Tipo de dato: {df['matriz_confusion'].dtype}")
        print(f"   Primer valor: {df['matriz_confusion'].iloc[0][:100]}...")
        print(f"   Valores nulos: {df['matriz_confusion'].isna().sum()}")
else:
    print("\n✗ ERROR: No se pudo cargar el DataFrame")

print("\n" + "="*60)
print("TEST COMPLETADO")
print("="*60)
