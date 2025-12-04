"""
Script para construir el ejecutable usando PyInstaller
Ejecuta este script para generar el .exe
"""
import PyInstaller.__main__
import os
import sys

# Obtener la ruta del directorio actual
current_dir = os.path.dirname(os.path.abspath(__file__))

# NOTA: Los archivos CSV NO se incluyen en el ejecutable
# Los usuarios pueden agregarlos después usando la interfaz gráfica del launcher
# El ejecutable solo necesita el CSV original de la BD, el modelo lo procesará automáticamente

# Construir los argumentos para PyInstaller
args = [
    "launcher.py",  # Script principal
    "--name=DashboardEmbargos",  # Nombre del ejecutable
    "--onefile",  # Un solo archivo ejecutable
    "--noconsole",  # Sin consola - la aplicación usa GUI (Tkinter)
    # Incluir scripts necesarios
    "--add-data=launcher.py;.",  # Incluir el launcher
    "--add-data=dashboard_embargos.py;.",  # Incluir dashboard 1
    "--add-data=dashboard_predicciones.py;.",  # Incluir dashboard 2
    "--add-data=dashboard_styles.py;.",  # Estilos compartidos
    "--add-data=procesar_modelo.py;.",  # Incluir script de procesamiento del modelo
    "--add-data=utils_csv.py;.",  # Incluir utilidades CSV
    # Imports ocultos necesarios
    "--hidden-import=streamlit",
    "--hidden-import=pandas",
    "--hidden-import=numpy",
    "--hidden-import=plotly",
    "--hidden-import=plotly.express",
    "--hidden-import=sklearn",
    "--hidden-import=xgboost",
    "--hidden-import=sklearn.preprocessing",
    "--hidden-import=sklearn.model_selection",
    "--hidden-import=sklearn.metrics",
    "--hidden-import=xgboost.sklearn",
    "--hidden-import=openpyxl",  # Para exportar a Excel
    "--hidden-import=openpyxl.workbook",  # Módulos adicionales de openpyxl
    "--hidden-import=openpyxl.worksheet",  # Módulos adicionales de openpyxl
    "--hidden-import=openpyxl.cell",  # Módulos adicionales de openpyxl
    # Incluir todos los módulos de librerías grandes
    "--collect-all=streamlit",  # Incluir todos los módulos de streamlit
    "--collect-all=plotly",  # Incluir todos los módulos de plotly
    "--collect-all=sklearn",  # Incluir todos los módulos de sklearn
    "--collect-all=xgboost",  # Incluir todos los módulos y DLLs de xgboost
    "--collect-all=openpyxl",  
    "--collect-all=openpyxl",  # Incluir todos los módulos de openpyxl
]

icon_file = os.path.join(current_dir, "ob.ico")
if os.path.exists(icon_file):
    args.append(f"--icon={icon_file}")
    args.append(f"--add-data={icon_file};.")
else:
    args.append("--icon=NONE")
    print("[ADVERTENCIA] No se encontro ob.ico. El ejecutable usara el icono por defecto.")

# Agregar DLLs de XGBoost manualmente si es necesario
try:
    import xgboost
    import os
    xgb_path = os.path.dirname(xgboost.__file__)
    dll_path = os.path.join(xgb_path, "lib", "xgboost.dll")
    if os.path.exists(dll_path):
        # Agregar la DLL de XGBoost al ejecutable
        # Formato: --add-binary "ruta_origen;ruta_destino"
        args.append(f'--add-binary={dll_path};xgboost/lib')
        print(f"[INFO] Se agregara la DLL de XGBoost: {dll_path}")
    else:
        print(f"[ADVERTENCIA] No se encontro la DLL de XGBoost en: {dll_path}")
        # Buscar en otras ubicaciones posibles
        alt_paths = [
            os.path.join(xgb_path, "xgboost.dll"),
            os.path.join(xgb_path, "bin", "xgboost.dll"),
        ]
        for alt_path in alt_paths:
            if os.path.exists(alt_path):
                args.append(f'--add-binary={alt_path};xgboost')
                print(f"[INFO] Se agregara la DLL de XGBoost desde ubicacion alternativa: {alt_path}")
                break
except Exception as e:
    print(f"[ADVERTENCIA] No se pudo agregar la DLL de XGBoost automaticamente: {e}")
    print("[INFO] El ejecutable puede fallar al usar XGBoost. Considera agregar la DLL manualmente.")

# Verificar y eliminar ejecutable anterior si existe
dist_path = os.path.join(current_dir, "dist", "DashboardEmbargos.exe")
if os.path.exists(dist_path):
    print("[INFO] Se encontro un ejecutable anterior en dist/DashboardEmbargos.exe")
    print("[INFO] Intentando eliminarlo...")
    try:
        # Intentar eliminar el archivo
        os.remove(dist_path)
        print("[OK] Ejecutable anterior eliminado")
    except PermissionError:
        print("[ERROR] No se puede eliminar el ejecutable anterior porque esta en uso.")
        print("[INFO] Por favor:")
        print("  1. Cierra el ejecutable DashboardEmbargos.exe si esta corriendo")
        print("  2. O cierra cualquier programa que lo este usando")
        print("  3. Luego vuelve a ejecutar este script")
        sys.exit(1)
    except Exception as e:
        print(f"[ADVERTENCIA] No se pudo eliminar el ejecutable anterior: {e}")
        print("[INFO] Continuando de todas formas...")

# Ejecutar PyInstaller
print("[INFO] Iniciando construccion del ejecutable...")
print("[INFO] Esto puede tardar varios minutos...")
print("[INFO] Por favor, espera...")
print("")

try:
    PyInstaller.__main__.run(args)
    
    print("")
    print("[OK] Ejecutable creado exitosamente!")
    print("[INFO] Busca el archivo 'DashboardEmbargos.exe' en la carpeta 'dist'")
    print("")
    print("[INFO] IMPORTANTE:")
    print("  - El ejecutable solo necesita el CSV original de la BD")
    print("  - El modelo procesara los datos automaticamente")
    print("  - Los archivos generados se guardaran en la carpeta de datos del usuario")
    
except Exception as e:
    print("")
    print("[ERROR] Error al crear el ejecutable:")
    print(f"  {e}")
    print("")
    if "Acceso denegado" in str(e) or "Permission denied" in str(e) or "WinError 5" in str(e):
        print("[INFO] SOLUCION para 'Acceso denegado':")
        print("  1. Cierra el ejecutable DashboardEmbargos.exe si esta corriendo")
        print("  2. Cierra cualquier dashboard de Streamlit que este abierto")
        print("  3. Cierra el Administrador de Tareas si muestra procesos relacionados")
        print("  4. Vuelve a ejecutar: python build_executable.py")
    else:
        print("[INFO] Asegurate de tener instalado PyInstaller:")
        print("  pip install pyinstaller")
    sys.exit(1)

