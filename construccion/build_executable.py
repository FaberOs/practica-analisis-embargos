"""
Script para construir el ejecutable usando PyInstaller
Ejecuta este script desde la raíz del proyecto para generar el .exe
"""
import PyInstaller.__main__
import os
import sys

# Obtener la ruta del directorio de construcción y la raíz del proyecto
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)

# Rutas de los archivos fuente
src_dir = os.path.join(project_root, "src")
dashboards_dir = os.path.join(src_dir, "dashboards")
orquestacion_dir = os.path.join(src_dir, "orquestacion")
pipeline_ml_dir = os.path.join(src_dir, "pipeline_ml")

# Archivos fuente
launcher_path = os.path.join(orquestacion_dir, "launcher.py")
utils_csv_path = os.path.join(orquestacion_dir, "utils_csv.py")
dashboard_embargos_path = os.path.join(dashboards_dir, "dashboard_embargos.py")
dashboard_predicciones_path = os.path.join(dashboards_dir, "dashboard_predicciones.py")
dashboard_styles_path = os.path.join(dashboards_dir, "dashboard_styles.py")
procesar_modelo_path = os.path.join(pipeline_ml_dir, "procesar_modelo.py")
icon_path = os.path.join(project_root, "ob.ico")

# Verificar que existen los archivos necesarios
required_files = {
    "launcher.py": launcher_path,
    "utils_csv.py": utils_csv_path,
    "dashboard_embargos.py": dashboard_embargos_path,
    "dashboard_predicciones.py": dashboard_predicciones_path,
    "dashboard_styles.py": dashboard_styles_path,
    "procesar_modelo.py": procesar_modelo_path,
}

print("[INFO] Verificando archivos fuente...")
for name, path in required_files.items():
    if os.path.exists(path):
        print(f"  [OK] {name}: {path}")
    else:
        print(f"  [ERROR] No encontrado: {name}")
        print(f"         Esperado en: {path}")
        sys.exit(1)

# NOTA: Los archivos CSV NO se incluyen en el ejecutable
# Los usuarios pueden agregarlos después usando la interfaz gráfica del launcher
# El ejecutable solo necesita el CSV original de la BD, el modelo lo procesará automáticamente

# Construir los argumentos para PyInstaller
args = [
    launcher_path,  # Script principal (ruta completa)
    "--name=DashboardEmbargos",  # Nombre del ejecutable
    "--onefile",  # Un solo archivo ejecutable
    "--noconsole",  # Sin consola - la aplicación usa GUI (Tkinter)
    f"--distpath={os.path.join(project_root, 'dist')}",  # Directorio de salida
    f"--workpath={os.path.join(current_dir, 'build_temp')}",  # Directorio temporal
    f"--specpath={current_dir}",  # Directorio del .spec
    # Incluir scripts necesarios (todos en la raíz del ejecutable empaquetado)
    f"--add-data={launcher_path};.",
    f"--add-data={dashboard_embargos_path};.",
    f"--add-data={dashboard_predicciones_path};.",
    f"--add-data={dashboard_styles_path};.",
    f"--add-data={procesar_modelo_path};.",
    f"--add-data={utils_csv_path};.",
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
    "--hidden-import=openpyxl",
    "--hidden-import=openpyxl.workbook",
    "--hidden-import=openpyxl.worksheet",
    "--hidden-import=openpyxl.cell",
    # Incluir todos los módulos de librerías grandes
    "--collect-all=streamlit",
    "--collect-all=plotly",
    "--collect-all=sklearn",
    "--collect-all=xgboost",
    "--collect-all=openpyxl",
]

if os.path.exists(icon_path):
    args.append(f"--icon={icon_path}")
    args.append(f"--add-data={icon_path};.")
    print(f"  [OK] ob.ico: {icon_path}")
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
dist_path = os.path.join(project_root, "dist", "DashboardEmbargos.exe")
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

