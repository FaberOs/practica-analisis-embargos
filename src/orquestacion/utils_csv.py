"""
Utilidades para encontrar archivos CSV en diferentes ubicaciones
Permite agregar CSV después de la instalación
"""
import os
import sys

CSV_DEBUG = os.getenv("CSV_DEBUG_FILES", "").strip().lower() in {"1", "true", "yes", "on"}

def get_base_path():
    """Obtiene la ruta base donde buscar archivos"""
    if getattr(sys, 'frozen', False):
        # Si está ejecutándose como ejecutable
        # Buscar en la carpeta donde está el ejecutable (no en _MEIPASS)
        if sys.platform == 'win32':
            return os.path.dirname(sys.executable)
        else:
            return os.path.dirname(os.path.abspath(sys.executable))
    else:
        # Si está ejecutándose como script, retornar la raíz del proyecto
        script_dir = os.path.dirname(os.path.abspath(__file__))
        src_dir = os.path.dirname(script_dir)  # carpeta src
        project_root = os.path.dirname(src_dir)  # raíz del proyecto
        return project_root

def get_data_path():
    """Obtiene la ruta donde se pueden escribir archivos CSV sin permisos de administrador"""
    if getattr(sys, 'frozen', False):
        # Si es ejecutable, usar AppData del usuario para evitar problemas de permisos
        if sys.platform == 'win32':
            appdata = os.getenv('APPDATA')
            if appdata:
                data_path = os.path.join(appdata, "DashboardEmbargos", "datos")
                # Crear la carpeta si no existe
                os.makedirs(data_path, exist_ok=True)
                return data_path
        # Fallback a la carpeta del ejecutable si no hay AppData
        return get_base_path()
    else:
        # Si es script, usar la carpeta datos del proyecto
        project_root = get_base_path()
        datos_dir = os.path.join(project_root, "datos")
        os.makedirs(datos_dir, exist_ok=True)
        return datos_dir

def find_csv_file(filename):
    """
    Busca un archivo CSV en múltiples ubicaciones:
    1. Carpeta de datos del usuario (AppData) - PRIORIDAD ALTA (sin permisos de admin)
    2. Carpeta del ejecutable (donde está instalado)
    3. Subcarpeta 'datos' o 'data' en la carpeta del ejecutable
    4. Carpeta actual (para desarrollo)
    
    Returns:
        str: Ruta completa al archivo CSV encontrado, o None si no se encuentra
    """
    base_path = get_base_path()
    data_path = get_data_path()
    
    # IMPORTANTE: En Windows, siempre buscar primero en AppData cuando existe
    # porque los archivos se generan ahí cuando se ejecuta desde el ejecutable
    # Incluso si Streamlit se ejecuta como proceso separado y no detecta sys.frozen
    appdata_path = None
    if sys.platform == 'win32':
        appdata = os.getenv('APPDATA')
        if appdata:
            appdata_path = os.path.join(appdata, "DashboardEmbargos", "datos")
    
    # Obtener la carpeta donde está este script (utils_csv.py)
    # IMPORTANTE: Cuando se ejecuta desde el ejecutable, __file__ apunta a _MEIPASS
    # Por eso usamos get_base_path() cuando es ejecutable, y __file__ solo cuando es script
    if getattr(sys, 'frozen', False):
        # Si es ejecutable, usar base_path (donde está el ejecutable)
        script_dir = base_path
    else:
        # Si es script, usar la carpeta donde está el archivo
        script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Lista de ubicaciones donde buscar (en orden de prioridad)
    search_paths = []
    
    # PRIORIDAD 1: AppData (siempre primero en Windows, donde se generan los archivos)
    if appdata_path and appdata_path not in search_paths:
        search_paths.append(appdata_path)
    
    # PRIORIDAD 2: data_path (puede ser AppData o carpeta del proyecto)
    if data_path and data_path not in search_paths:
        search_paths.append(data_path)
    
    # PRIORIDAD 3: base_path (carpeta del ejecutable o del proyecto)
    if base_path and base_path not in search_paths:
        search_paths.append(base_path)
    
    # PRIORIDAD 4: Subcarpetas en base_path
    if base_path:
        for subdir in ["datos", "data"]:
            subpath = os.path.join(base_path, subdir)
            if subpath not in search_paths:
                search_paths.append(subpath)
    
    # PRIORIDAD 5: script_dir (solo relevante cuando es script, no ejecutable)
    if script_dir and script_dir not in search_paths:
        search_paths.append(script_dir)
        for subdir in ["datos", "data"]:
            subpath = os.path.join(script_dir, subdir)
            if subpath not in search_paths:
                search_paths.append(subpath)
    
    # PRIORIDAD 6: Carpeta actual
    cwd = os.getcwd()
    if cwd and cwd not in search_paths:
        search_paths.append(cwd)
    
    # Eliminar duplicados manteniendo el orden
    seen = set()
    unique_paths = []
    for path in search_paths:
        if path and path not in seen:
            seen.add(path)
            unique_paths.append(path)
    search_paths = unique_paths
    
    # Buscar el archivo en cada ubicación
    for search_path in search_paths:
        if search_path:  # Asegurar que la ruta no sea None
            file_path = os.path.join(search_path, filename)
            if os.path.exists(file_path) and os.path.isfile(file_path):
                return file_path
    
    # No se encontró - para depuración, podemos imprimir las rutas buscadas
    # (solo en modo desarrollo, no en producción)
    if CSV_DEBUG:
        print(f"[DEBUG] Archivo '{filename}' no encontrado en las siguientes ubicaciones:")
        for path in search_paths:
            if path:
                print(f"  - {path}")
    
    return None

def get_csv_path(filename, required=True):
    """
    Obtiene la ruta de un archivo CSV, con manejo de errores
    
    Args:
        filename: Nombre del archivo CSV
        required: Si es True, muestra error si no se encuentra
    
    Returns:
        str: Ruta al archivo CSV, o None si no se encuentra y required=False
    """
    file_path = find_csv_file(filename)
    
    if file_path is None and required:
        base_path = get_base_path()
        data_path = get_data_path()
        error_msg = f"""
❌ ERROR: No se encontró el archivo '{filename}'

📁 Ubicaciones buscadas (en orden de prioridad):
   1. {data_path} (RECOMENDADO - sin permisos de administrador)
   2. {base_path}
   3. {os.path.join(base_path, 'datos')}
   4. {os.path.join(base_path, 'data')}
   5. {os.getcwd()}

💡 SOLUCIÓN:
   1. Coloca el archivo '{filename}' en la carpeta de datos del usuario:
      {data_path}
   2. O colócalo en la carpeta de instalación: {base_path}
   3. O crea una carpeta 'datos' en la carpeta de instalación y coloca el archivo ahí

📝 Archivos CSV necesarios:
    - embargos_consolidado_mensual.csv
    - predicciones_oficios_validacion.csv
    - predicciones_oficios_futuro.csv
    - predicciones_demandados_validacion.csv
    - predicciones_demandados_futuro.csv
    - resultados_clasificaciones.csv
"""
        raise FileNotFoundError(error_msg)
    
    return file_path


def get_icon_path(icon_filename="ob.ico"):
    """Devuelve la ruta completa del icono si existe."""
    candidates = []
    if getattr(sys, 'frozen', False):
        meipass = getattr(sys, '_MEIPASS', None)
        if meipass:
            candidates.append(os.path.join(meipass, icon_filename))
    base_path = get_base_path()
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = get_data_path()
    cwd = os.getcwd()
    for tentative in [
        os.path.join(base_path, icon_filename) if base_path else None,
        os.path.join(script_dir, icon_filename) if script_dir else None,
        os.path.join(data_path, icon_filename) if data_path else None,
        os.path.join(cwd, icon_filename) if cwd else None,
    ]:
        if tentative and tentative not in candidates:
            candidates.append(tentative)
    for path in candidates:
        if path and os.path.exists(path):
            return os.path.abspath(path)
    return None

