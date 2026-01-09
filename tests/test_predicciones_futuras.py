"""
Script de prueba para verificar la generación de archivos de predicción futura
"""
import os
import sys

# Agregar la carpeta src/pipeline_ml al path para importar el módulo
test_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(test_dir)
pipeline_ml_dir = os.path.join(project_root, "src", "pipeline_ml")
sys.path.insert(0, pipeline_ml_dir)

# Importar la función de procesamiento
from procesar_modelo import entrenar_modelos_y_generar_predicciones

# Usar el consolidado existente desde la carpeta datos
datos_dir = os.path.join(project_root, "datos")
consolidado_path = os.path.join(datos_dir, "embargos_consolidado_mensual.csv")
output_dir = datos_dir

print("="*80)
print("PRUEBA DE GENERACIÓN DE PREDICCIONES FUTURAS")
print("="*80)
print(f"Archivo consolidado: {consolidado_path}")
print(f"Directorio de salida: {output_dir}")
print("="*80)

if not os.path.exists(consolidado_path):
    print(f"\n[ERROR] No se encontró el archivo: {consolidado_path}")
    print("Asegúrate de tener el archivo consolidado en el directorio actual")
    sys.exit(1)

try:
    entrenar_modelos_y_generar_predicciones(consolidado_path, output_dir)
    
    print("\n" + "="*80)
    print("VERIFICACIÓN DE ARCHIVOS GENERADOS")
    print("="*80)
    
    archivos_esperados = [
        "predicciones_oficios_validacion.csv",
        "predicciones_oficios_futuro.csv",
        "predicciones_demandados_validacion.csv",
        "predicciones_demandados_futuro.csv",
        "resultados_clasificaciones.csv"
    ]
    
    for archivo in archivos_esperados:
        ruta = os.path.join(output_dir, archivo)
        if os.path.exists(ruta):
            tamaño = os.path.getsize(ruta)
            print(f"✅ {archivo} - {tamaño:,} bytes")
            
            # Mostrar primeras líneas
            with open(ruta, 'r', encoding='utf-8') as f:
                primera_linea = f.readline().strip()
                print(f"   Columnas: {primera_linea}")
        else:
            print(f"❌ {archivo} - NO ENCONTRADO")
    
    print("\n" + "="*80)
    print("PRUEBA COMPLETADA")
    print("="*80)
    
except Exception as e:
    print(f"\n[ERROR] Error durante la ejecución: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
