"""
Launcher principal para los dashboards de embargos bancarios
Interfaz gráfica con Tkinter para seleccionar archivos CSV
"""
import subprocess
import sys
import os
import webbrowser
import time
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import shutil
import pandas as pd

def get_base_path():
    """Obtiene la ruta base del ejecutable o script"""
    if getattr(sys, 'frozen', False):
        if sys.platform == 'win32':
            return os.path.dirname(sys.executable)
        else:
            return os.path.dirname(os.path.abspath(sys.executable))
    else:
        return os.path.dirname(os.path.abspath(__file__))

def get_data_path():
    """Obtiene la ruta donde se pueden escribir archivos CSV sin permisos de administrador"""
    if getattr(sys, 'frozen', False):
        if sys.platform == 'win32':
            appdata = os.getenv('APPDATA')
            if appdata:
                data_path = os.path.join(appdata, "DashboardEmbargos", "datos")
                os.makedirs(data_path, exist_ok=True)
                return data_path
        return get_base_path()
    else:
        return os.path.dirname(os.path.abspath(__file__))

def get_script_path(script_name):
    """Obtiene la ruta del script, buscando en _MEIPASS si es ejecutable"""
    if getattr(sys, 'frozen', False):
        meipass = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
        script_path = os.path.join(meipass, script_name)
        if os.path.exists(script_path):
            return os.path.abspath(script_path)
        alt_path = os.path.join(os.path.dirname(sys.executable), script_name)
        if os.path.exists(alt_path):
            return os.path.abspath(alt_path)
        return os.path.abspath(script_path)
    else:
        return os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), script_name))

def validate_csv_file(csv_path, csv_name, show_warning=True):
    """Valida que un archivo CSV tenga las columnas esperadas (solo advertencia, no bloquea)"""
    if not csv_path or not os.path.exists(csv_path):
        return False, "El archivo no existe"
    
    # Definir columnas esperadas para cada CSV
    expected_columns = {
        "embargos_consolidado_mensual.csv": ["mes"],
        "predicciones_oficios_por_mes.csv": ["mes", "real_oficios", "pred_oficios"],
        "predicciones_demandados_por_mes.csv": ["mes", "real_demandados", "pred_demandados"],
        "resultados_clasificaciones.csv": ["modelo", "clase"]
    }
    
    if csv_name not in expected_columns:
        return True, None  # Si no hay validación definida, permitir
    
    try:
        # Intentar diferentes codificaciones como lo hacen los dashboards
        encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1', 'utf-8-sig']
        df = None
        
        for encoding in encodings:
            try:
                df = pd.read_csv(csv_path, nrows=5, low_memory=False, encoding=encoding)
                break
            except (UnicodeDecodeError, Exception):
                continue
        
        if df is None:
            try:
                df = pd.read_csv(csv_path, nrows=5, low_memory=False, encoding_errors='ignore')
            except Exception:
                return True, None  # Si no se puede leer, permitir y dejar que el dashboard maneje el error
        
        if df is None or df.empty:
            return True, None
        
        # Limpiar nombres de columnas (como lo hacen los dashboards)
        df.columns = df.columns.str.strip()
        
        # Normalizar nombres (case-insensitive, sin espacios extra)
        df.columns = [col.lower().strip() for col in df.columns]
        required_cols = [col.lower().strip() for col in expected_columns[csv_name]]
        
        missing_cols = [col for col in required_cols if col not in df.columns]
        
        # Si faltan columnas importantes, mostrar advertencia pero permitir continuar
        if missing_cols and show_warning:
            found_cols = [col for col in df.columns[:10]]  # Mostrar primeras 10 columnas
            warning_msg = (
                f"⚠️ ADVERTENCIA: El archivo CSV podría no tener el formato esperado.\n\n"
                f"Columnas esperadas: {', '.join(expected_columns[csv_name])}\n"
                f"Columnas encontradas: {', '.join(found_cols[:5])}\n\n"
                f"¿Deseas continuar de todas formas?\n"
                f"(El dashboard mostrará un error si el archivo no es compatible)"
            )
            return "warning", warning_msg
        
        return True, None
    except Exception as e:
        # Si hay error al leer, permitir continuar (el dashboard manejará el error)
        return True, None

def find_available_port(start_port=8501):
    """Encuentra un puerto disponible empezando desde start_port"""
    import socket
    port = start_port
    while port < start_port + 10:  # Intentar hasta 10 puertos
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('localhost', port))
        sock.close()
        if result != 0:  # Puerto disponible
            return port
        port += 1
    return start_port  # Si no encuentra, usar el inicial

def run_streamlit(script_path, base_path, dashboard_name, csv_files=None, port=8501):
    """Ejecuta Streamlit con el script especificado en segundo plano"""
    # Si se proporcionaron archivos CSV, copiarlos a la carpeta de datos del usuario
    # (que tiene permisos de escritura, a diferencia de Program Files)
    if csv_files:
        # Usar la carpeta de datos del usuario en lugar de base_path para evitar problemas de permisos
        data_path = get_data_path()
        
        for csv_name, csv_path in csv_files.items():
            if csv_path and os.path.exists(csv_path):
                dest_path = os.path.join(data_path, csv_name)
                
                # Verificar si el archivo ya está en la ubicación destino
                try:
                    # Usar samefile para comparar si son el mismo archivo (más robusto)
                    if os.path.exists(dest_path) and os.path.samefile(csv_path, dest_path):
                        continue
                except (OSError, ValueError):
                    # Si samefile falla (archivos diferentes o uno no existe), continuar con la copia
                    pass
                
                try:
                    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                    shutil.copy2(csv_path, dest_path)
                except shutil.SameFileError:
                    continue
                except PermissionError as e:
                    try:
                        fallback_path = os.path.join(base_path, csv_name)
                        if "Program Files" not in base_path:
                            shutil.copy2(csv_path, fallback_path)
                        else:
                            messagebox.showerror(
                                "Error de permisos",
                                f"No se pudo copiar {csv_name}.\n\n"
                                f"El archivo se guardará en:\n{data_path}\n\n"
                                f"Por favor, copia manualmente el archivo a esa ubicación."
                            )
                            return None
                    except Exception as e2:
                        messagebox.showerror("Error", f"Error al copiar {csv_name}: {e2}")
                        return None
                except Exception as e:
                    messagebox.showerror("Error", f"Error al copiar {csv_name}: {e}")
                    return None
    
    # Verificar que streamlit esté disponible
    try:
        import streamlit
    except ImportError:
        messagebox.showerror("Error", "Streamlit no está instalado")
        return None
    
    # Asegurar que la ruta sea absoluta
    script_path = os.path.abspath(script_path)
    
    # Verificar que el script exista
    if not os.path.exists(script_path):
        messagebox.showerror("Error", f"No se encontró el archivo {script_path}")
        return None
    
    # Si es ejecutable congelado, copiar el script y utils_csv.py a la carpeta de datos del usuario
    # para que Streamlit pueda accederlos (evitar Program Files que requiere permisos de administrador)
    if getattr(sys, 'frozen', False):
        script_name = os.path.basename(script_path)
        # Usar la carpeta de datos del usuario en lugar de base_path para evitar problemas de permisos
        data_path = get_data_path()
        dest_script_path = os.path.join(data_path, script_name)
        if script_path != dest_script_path:
            try:
                os.makedirs(os.path.dirname(dest_script_path), exist_ok=True)
                shutil.copy2(script_path, dest_script_path)
                script_path = dest_script_path
                
                utils_csv_source = get_script_path("utils_csv.py")
                if utils_csv_source and os.path.exists(utils_csv_source):
                    utils_csv_dest = os.path.join(data_path, "utils_csv.py")
                    if utils_csv_source != utils_csv_dest:
                        try:
                            shutil.copy2(utils_csv_source, utils_csv_dest)
                        except Exception as e:
                            pass
            except Exception as e:
                pass
    
    # Encontrar puerto disponible
    available_port = find_available_port(port)
    
    try:
        if getattr(sys, 'frozen', False):
            streamlit_cmd = None
            python_exe = None
            
            streamlit_path = shutil.which("streamlit")
            if streamlit_path:
                streamlit_cmd = [streamlit_path, "run", script_path]
            else:
                possible_paths = [
                    os.path.join(os.path.dirname(sys.executable), "python.exe"),
                    os.path.join(os.path.dirname(sys.executable), "pythonw.exe"),
                    shutil.which("python"),
                    shutil.which("pythonw"),
                ]
                
                if sys.platform == 'win32':
                    try:
                        import winreg
                        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Python\PythonCore")
                        for i in range(winreg.QueryInfoKey(key)[0]):
                            subkey_name = winreg.EnumKey(key, i)
                            try:
                                subkey = winreg.OpenKey(key, subkey_name + r"\InstallPath")
                                install_path = winreg.QueryValue(subkey, None)
                                python_exe = os.path.join(install_path, "python.exe")
                                if os.path.exists(python_exe):
                                    break
                            except:
                                continue
                        winreg.CloseKey(key)
                    except:
                        pass
                
                for path in possible_paths:
                    if path and os.path.exists(path):
                        python_exe = path
                        break
                
                if python_exe and os.path.exists(python_exe):
                    streamlit_cmd = [python_exe, "-m", "streamlit", "run", script_path]
            
            if streamlit_cmd:
                # Configurar variables de entorno para desactivar apertura automática del navegador
                env = os.environ.copy()
                env['STREAMLIT_BROWSER_GATHER_USAGE_STATS'] = 'false'
                env['STREAMLIT_SERVER_HEADLESS'] = 'false'
                
                # Agregar opciones adicionales
                streamlit_cmd.extend([
                    "--server.headless=false",
                    f"--server.port={available_port}",
                    "--server.address=localhost",
                    "--server.enableXsrfProtection=false",
                    "--server.enableCORS=false",
                    "--browser.gatherUsageStats=false"
                ])
                # Redirigir stdout/stderr a un archivo de log para evitar bloqueos del buffer
                # El archivo se mantiene abierto mientras el proceso esté activo
                # Usar la carpeta de datos del usuario para evitar problemas de permisos
                data_path = get_data_path()
                log_file = os.path.join(data_path, f"streamlit_{dashboard_name.lower()}.log")
                # Asegurar que la carpeta existe
                os.makedirs(os.path.dirname(log_file), exist_ok=True)
                log_handle = open(log_file, 'w', encoding='utf-8', buffering=1)  # Line buffering
                process = subprocess.Popen(
                    streamlit_cmd,
                    cwd=base_path,
                    stdout=log_handle,
                    stderr=subprocess.STDOUT,  # Redirigir stderr a stdout
                    env=env,
                    creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
                )
                process._log_handle = log_handle
                process._log_file = log_file
            else:
                messagebox.showerror(
                    "Error",
                    "No se pudo iniciar el dashboard.\n\n"
                    "El sistema no pudo encontrar los componentes necesarios.\n"
                    "Contacta al administrador del sistema para resolver este problema."
                )
                return None
        else:
            env = os.environ.copy()
            env['STREAMLIT_BROWSER_GATHER_USAGE_STATS'] = 'false'
            env['STREAMLIT_SERVER_HEADLESS'] = 'false'
            
            cmd = [
                sys.executable, "-m", "streamlit", "run", script_path,
                "--server.headless=false",
                f"--server.port={available_port}",
                "--server.address=localhost",
                "--server.enableXsrfProtection=false"
            ]
            data_path = get_data_path()
            log_file = os.path.join(data_path, f"streamlit_{dashboard_name.lower()}.log")
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
            log_handle = open(log_file, 'w', encoding='utf-8', buffering=1)
            process = subprocess.Popen(
                cmd,
                cwd=base_path,
                stdout=log_handle,
                stderr=subprocess.STDOUT,
                env=env,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            )
            process._log_handle = log_handle
            process._log_file = log_file
        
        time.sleep(3)
        
        # Verificar que el proceso esté aún ejecutándose
        if process.poll() is not None:
            # El proceso ya terminó, probablemente hubo un error
            log_file_path = getattr(process, '_log_file', 'streamlit_error.log')
            error_msg = f"El proceso de Streamlit terminó inesperadamente.\n\nRevisa el log: {log_file_path}"
            if hasattr(process, '_log_handle'):
                try:
                    process._log_handle.close()
                except:
                    pass
            messagebox.showerror("Error", error_msg)
            return None
        
        return process
        
    except Exception as e:
        messagebox.showerror("Error", f"Error inesperado: {e}")
        return None

class DashboardLauncher:
    def __init__(self, root):
        self.root = root
        self.root.title("Dashboard de Análisis de Embargos Bancarios")
        self.root.geometry("700x700")  # Aumentado para incluir la sección de estado y botones de control
        self.root.resizable(False, False)
        
        # Centrar ventana
        self.center_window()
        
        # Archivos CSV originales de la BD seleccionados
        self.csv_originales = []  # Lista de archivos CSV originales de la BD
        
        # Variables para las rutas mostradas
        self.csv_original_label = None
        
        # Procesos activos de Streamlit
        self.active_processes = {
            "Embargos": None,
            "Predicciones": None
        }
        
        # Puertos asignados
        self.port_mapping = {
            "Embargos": 8501,
            "Predicciones": 8502
        }
        
        self.create_widgets()
        
        # Intentar cargar archivos existentes
        self.load_existing_files()
        
        # Actualizar estado de archivos periódicamente (cada 2 segundos)
        self.actualizar_estado_periodico()
    
    def stop_all_dashboards(self):
        """Detiene todos los dashboards en ejecución"""
        stopped = []
        for name, process in self.active_processes.items():
            if process is not None:
                try:
                    process.terminate()
                    process.wait(timeout=3)
                    stopped.append(name)
                except:
                    try:
                        process.kill()
                        stopped.append(name)
                    except:
                        pass
                finally:
                    # Cerrar el handle del log si existe
                    if hasattr(process, '_log_handle'):
                        try:
                            process._log_handle.close()
                        except:
                            pass
                    self.active_processes[name] = None
        
        if stopped:
            messagebox.showinfo("Dashboards detenidos", f"Se detuvieron los siguientes dashboards:\n" + "\n".join(f"- {name}" for name in stopped))
        else:
            messagebox.showinfo("Info", "No hay dashboards en ejecución")
    
    def on_closing(self):
        """Maneja el cierre de la ventana"""
        if any(p is not None for p in self.active_processes.values()):
            response = messagebox.askyesno(
                "Cerrar aplicación",
                "Hay dashboards en ejecución.\n¿Deseas detenerlos y cerrar la aplicación?"
            )
            if response:
                self.stop_all_dashboards()
                self.root.quit()
        else:
            self.root.quit()
    
    def center_window(self):
        """Centra la ventana en la pantalla"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def create_widgets(self):
        """Crea los widgets de la interfaz"""
        # Título
        title_frame = tk.Frame(self.root, bg="#2c3e50", height=80)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)
        
        title_label = tk.Label(
            title_frame,
            text="Dashboard de Análisis de Embargos Bancarios",
            font=("Arial", 16, "bold"),
            bg="#2c3e50",
            fg="white"
        )
        title_label.pack(pady=25)
        
        # Frame principal
        main_frame = tk.Frame(self.root, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Sección de archivos CSV originales de la BD
        csv_frame = tk.LabelFrame(
            main_frame,
            text="📁 Archivo(s) CSV de la Base de Datos (con años en el nombre, por semestres)",
            font=("Arial", 11, "bold"),
            padx=10,
            pady=10
        )
        csv_frame.pack(fill=tk.X, pady=10)
        
        # Frame para el selector de CSV original
        csv_selector_frame = tk.Frame(csv_frame)
        csv_selector_frame.pack(fill=tk.X, pady=5)
        
        label = tk.Label(csv_selector_frame, text="CSV de la BD:", width=25, anchor="w")
        label.pack(side=tk.LEFT, padx=5)
        
        btn_select_csv = tk.Button(
            csv_selector_frame,
            text="Seleccionar CSV(s)",
            command=self.select_csv_original,
            cursor="hand2"
        )
        btn_select_csv.pack(side=tk.LEFT, padx=5)
        
        # Label para mostrar los archivos seleccionados
        self.csv_original_label = tk.Label(
            csv_selector_frame,
            text="No seleccionado",
            fg="gray",
            anchor="w",
            relief=tk.SUNKEN,
            padx=5,
            pady=2,
            wraplength=400
        )
        self.csv_original_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # Información
        info_label = tk.Label(
            csv_frame,
            text="💡 Selecciona el/los archivo(s) CSV extraído(s) de la BD.\n    El modelo procesará los datos y generará los archivos necesarios automáticamente.",
            font=("Arial", 9),
            fg="#7f8c8d",
            justify=tk.LEFT
        )
        info_label.pack(fill=tk.X, pady=5)
        
        # Sección de estado de archivos generados
        status_frame = tk.LabelFrame(
            main_frame,
            text="📊 Estado de Archivos Generados",
            font=("Arial", 10, "bold"),
            padx=10,
            pady=10
        )
        status_frame.pack(fill=tk.X, pady=10)
        
        # Frame para los checkboxes
        checkboxes_frame = tk.Frame(status_frame)
        checkboxes_frame.pack(fill=tk.X, pady=5)
        
        # Archivos necesarios para cada dashboard
        self.file_status = {
            "embargos_consolidado_mensual.csv": {
                "label": "embargos_consolidado_mensual.csv",
                "dashboard": "Dashboard de Embargos",
                "var": tk.BooleanVar(),
                "checkbox": None
            },
            "predicciones_oficios_por_mes.csv": {
                "label": "predicciones_oficios_por_mes.csv",
                "dashboard": "Dashboard de Predicciones",
                "var": tk.BooleanVar(),
                "checkbox": None
            },
            "predicciones_demandados_por_mes.csv": {
                "label": "predicciones_demandados_por_mes.csv",
                "dashboard": "Dashboard de Predicciones",
                "var": tk.BooleanVar(),
                "checkbox": None
            },
            "resultados_clasificaciones.csv": {
                "label": "resultados_clasificaciones.csv",
                "dashboard": "Dashboard de Predicciones",
                "var": tk.BooleanVar(),
                "checkbox": None
            }
        }
        
        # Crear checkboxes (2 columnas)
        col1_frame = tk.Frame(checkboxes_frame)
        col1_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        col2_frame = tk.Frame(checkboxes_frame)
        col2_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        files_list = list(self.file_status.items())
        for idx, (filename, info) in enumerate(files_list):
            frame = col1_frame if idx < 2 else col2_frame
            
            # Checkbox con estilo personalizado
            checkbox = tk.Checkbutton(
                frame,
                text=info["label"],
                variable=info["var"],
                state=tk.DISABLED,  # Solo lectura, no se puede marcar manualmente
                font=("Arial", 9),
                anchor="w",
                disabledforeground="#2c3e50"
            )
            checkbox.pack(fill=tk.X, pady=2)
            info["checkbox"] = checkbox
        
        # Frame para botones de estado
        btn_status_frame = tk.Frame(status_frame)
        btn_status_frame.pack(pady=5)
        
        # Botón para actualizar estado
        btn_refresh = tk.Button(
            btn_status_frame,
            text="🔄 Actualizar Estado",
            font=("Arial", 8),
            bg="#95a5a6",
            fg="white",
            padx=10,
            pady=3,
            command=self.actualizar_estado_archivos,
            cursor="hand2"
        )
        btn_refresh.pack(side=tk.LEFT, padx=5)
        
        # Botón para recalcular/regenerar archivos
        btn_recalcular = tk.Button(
            btn_status_frame,
            text="🔄 Recalcular Archivos",
            font=("Arial", 9, "bold"),
            bg="#e67e22",
            fg="white",
            padx=15,
            pady=5,
            command=self.recalcular_archivos,
            cursor="hand2"
        )
        btn_recalcular.pack(side=tk.LEFT, padx=5)
        
        # Actualizar estado inicial
        self.actualizar_estado_archivos()
        
        # Botones de acción
        button_frame = tk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=20)
        
        self.btn_embargos = tk.Button(
            button_frame,
            text="🚀 Iniciar Dashboard de Embargos",
            font=("Arial", 11, "bold"),
            bg="#3498db",
            fg="white",
            padx=20,
            pady=10,
            command=self.start_embargos_dashboard,
            cursor="hand2"
        )
        self.btn_embargos.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        self.btn_predicciones = tk.Button(
            button_frame,
            text="🔮 Iniciar Dashboard de Predicciones",
            font=("Arial", 11, "bold"),
            bg="#9b59b6",
            fg="white",
            padx=20,
            pady=10,
            command=self.start_predicciones_dashboard,
            cursor="hand2"
        )
        self.btn_predicciones.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # Botones de control
        control_frame = tk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=10)
        
        btn_detener = tk.Button(
            control_frame,
            text="🛑 Detener Todos los Dashboards",
            font=("Arial", 10),
            bg="#f39c12",
            fg="white",
            padx=20,
            pady=5,
            command=self.stop_all_dashboards,
            cursor="hand2"
        )
        btn_detener.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        btn_salir = tk.Button(
            control_frame,
            text="Salir",
            font=("Arial", 10),
            bg="#e74c3c",
            fg="white",
            padx=20,
            pady=5,
            command=self.on_closing,
            cursor="hand2"
        )
        btn_salir.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # Configurar cierre de ventana
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def select_csv_original(self):
        """Abre el diálogo para seleccionar uno o más archivos CSV originales de la BD"""
        filenames = filedialog.askopenfilenames(
            title="Seleccionar archivo(s) CSV de la Base de Datos",
            filetypes=[("Archivos CSV", "*.csv"), ("Todos los archivos", "*.*")]
        )
        
        if filenames:
            self.csv_originales = list(filenames)
            # Mostrar los nombres de los archivos seleccionados
            if len(self.csv_originales) == 1:
                display_text = os.path.basename(self.csv_originales[0])
            else:
                display_text = f"{len(self.csv_originales)} archivos seleccionados"
                if len(display_text) > 50:
                    display_text = f"{len(self.csv_originales)} archivos..."
            
            self.csv_original_label.config(text=display_text, fg="green")
    
    def mostrar_ayuda_csv(self):
        """Muestra una ventana con instrucciones sobre cómo obtener/generar los CSV"""
        ayuda_window = tk.Toplevel(self.root)
        ayuda_window.title("Instrucciones: Cómo obtener los CSV de la Base de Datos")
        ayuda_window.geometry("700x600")
        ayuda_window.transient(self.root)
        ayuda_window.grab_set()
        
        # Centrar ventana
        ayuda_window.update_idletasks()
        x = (ayuda_window.winfo_screenwidth() // 2) - (700 // 2)
        y = (ayuda_window.winfo_screenheight() // 2) - (600 // 2)
        ayuda_window.geometry(f"700x600+{x}+{y}")
        
        # Frame principal con scroll
        main_frame = tk.Frame(ayuda_window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Canvas y scrollbar para contenido largo
        canvas = tk.Canvas(main_frame, bg="white")
        scrollbar = tk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="white")
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Título
        titulo = tk.Label(
            scrollable_frame,
            text="📋 Cómo Obtener los CSV de la Base de Datos",
            font=("Arial", 16, "bold"),
            bg="white",
            fg="#2c3e50"
        )
        titulo.pack(pady=15)
        
        # Contenido
        contenido = """
¿Qué archivos CSV necesito?

Solo necesitas el/los archivo(s) CSV extraído(s) directamente de la Base de Datos.
Estos archivos tienen años en el nombre y están organizados por semestres.

Ejemplos de nombres de archivos:
  • consulta detalle embargos-2023-01.csv
  • consulta detalle embargos-2023-02.csv
  • consulta detalle embargos-2024-01.csv
  • consulta detalle embargos-2024-02.csv

═══════════════════════════════════════════════════════════════

¿Cómo obtener los CSV de la Base de Datos?

OPCIÓN 1: Extraer desde la Base de Datos (Recomendado)

1. Conectarte a la Base de Datos donde están los datos de embargos
2. Ejecutar una consulta SQL para exportar los datos
3. Exportar los resultados como CSV con el formato:
   - Nombre: "consulta detalle embargos-YYYY-MM.csv"
   - Donde YYYY es el año y MM es el mes (01-12) o semestre (01, 02)

Ejemplo de consulta SQL (ajusta según tu esquema):
  SELECT 
    id, ciudad, entidad_remitente, correo, direccion, 
    funcionario, fecha_banco, fecha_oficio, referencia, 
    cuenta, identificacion, tipo_identificacion_tipo, 
    montoaembargar, nombres, expediente, mes, 
    entidad_bancaria, estado_embargo, tipo_documento,
    tipo_embargo, estado_demandado, es_cliente, tipo_carta
  FROM tabla_embargos
  WHERE mes LIKE '2023-%'  -- Ajustar según el período
  ORDER BY mes;

4. Guardar cada período como un archivo CSV separado
5. Los archivos deben tener exactamente las columnas mencionadas arriba

═══════════════════════════════════════════════════════════════

OPCIÓN 2: Si ya tienes archivos CSV existentes

Si ya tienes archivos CSV con datos de embargos pero con nombres diferentes:

1. Verifica que tengan las columnas necesarias (ver lista arriba)
2. Puedes renombrarlos para que sigan el patrón:
   "consulta detalle embargos-YYYY-MM.csv"
3. O simplemente selecciónalos tal como están (el programa los procesará)

═══════════════════════════════════════════════════════════════

¿Qué hace el programa con estos CSV?

1. Procesa y consolida todos los archivos CSV que selecciones
2. Limpia y normaliza los datos
3. Entrena modelos de Machine Learning (XGBoost)
4. Genera automáticamente los siguientes archivos:
   • embargos_consolidado_mensual.csv
   • predicciones_oficios_por_mes.csv
   • predicciones_demandados_por_mes.csv
   • resultados_clasificaciones.csv

5. Los dashboards usan estos archivos generados automáticamente

═══════════════════════════════════════════════════════════════

Requisitos de los archivos CSV:

✓ Formato: CSV (valores separados por comas)
✓ Codificación: UTF-8, Latin-1, o CP1252 (se detecta automáticamente)
✓ Columnas: Deben tener las 23 columnas estándar (ver lista arriba)
✓ Delimitador: Coma (,)
✓ Primera fila: Debe contener los nombres de las columnas

═══════════════════════════════════════════════════════════════

¿Dónde se guardan los archivos generados?

Los archivos generados se guardan automáticamente en:
  Windows: C:\\Users\\[TuUsuario]\\AppData\\Roaming\\DashboardEmbargos\\datos\\
  
No necesitas hacer nada manual, el programa los gestiona automáticamente.

═══════════════════════════════════════════════════════════════

¿Necesitas ayuda adicional?

Si tienes problemas para obtener los CSV o el formato no coincide,
contacta al administrador de la Base de Datos o al equipo técnico.
        """
        
        texto_ayuda = tk.Text(
            scrollable_frame,
            wrap=tk.WORD,
            font=("Arial", 10),
            bg="white",
            fg="#2c3e50",
            padx=15,
            pady=15,
            relief=tk.FLAT,
            borderwidth=0
        )
        texto_ayuda.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        texto_ayuda.insert("1.0", contenido)
        texto_ayuda.config(state=tk.DISABLED)
        
        # Botón cerrar
        btn_cerrar = tk.Button(
            scrollable_frame,
            text="Cerrar",
            font=("Arial", 10, "bold"),
            bg="#e74c3c",
            fg="white",
            padx=30,
            pady=8,
            command=ayuda_window.destroy,
            cursor="hand2"
        )
        btn_cerrar.pack(pady=10)
        
        # Configurar scroll
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Habilitar scroll con rueda del mouse
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        # Enfocar la ventana
        ayuda_window.focus_set()
    
    def load_existing_files(self):
        """Carga archivos CSV existentes (ya no se usa, pero se mantiene por compatibilidad)"""
        pass  # Ya no cargamos archivos existentes, solo el CSV original
    
    def actualizar_estado_archivos(self):
        """Verifica qué archivos están generados y actualiza los checkboxes"""
        from utils_csv import find_csv_file
        
        for filename, info in self.file_status.items():
            file_path = find_csv_file(filename)
            exists = file_path is not None and os.path.exists(file_path)
            info["var"].set(exists)
            
            # Cambiar color del texto según el estado
            if exists:
                info["checkbox"].config(disabledforeground="#27ae60")  # Verde
            else:
                info["checkbox"].config(disabledforeground="#e74c3c")  # Rojo
    
    def actualizar_estado_periodico(self):
        """Actualiza el estado de los archivos periódicamente"""
        self.actualizar_estado_archivos()
        # Programar próxima actualización en 2 segundos
        self.root.after(2000, self.actualizar_estado_periodico)
    
    def recalcular_archivos(self):
        """Recalcula/regenera todos los archivos CSV usando los CSV originales seleccionados"""
        if not self.csv_originales:
            messagebox.showwarning(
                "CSV requerido",
                "Por favor selecciona primero el/los archivo(s) CSV de la Base de Datos.\n\n"
                "Los archivos deben tener años en el nombre (por ejemplo: 'consulta detalle embargos-2023-01.csv')"
            )
            return
        
        # Confirmar con el usuario
        respuesta = messagebox.askyesno(
            "Recalcular archivos",
            "¿Estás seguro de que deseas recalcular todos los archivos?\n\n"
            "Esto sobrescribirá los archivos existentes:\n"
            "  • embargos_consolidado_mensual.csv\n"
            "  • predicciones_oficios_por_mes.csv\n"
            "  • predicciones_demandados_por_mes.csv\n"
            "  • resultados_clasificaciones.csv\n\n"
            "El proceso puede tardar varios minutos."
        )
        
        if not respuesta:
            return
        
        # Ejecutar el procesamiento (sobrescribirá los archivos existentes)
        if self.ejecutar_procesamiento():
            messagebox.showinfo(
                "Recálculo completado",
                "✅ Los archivos han sido recalculados exitosamente.\n\n"
                "Puedes iniciar los dashboards con los nuevos datos."
            )
            # Actualizar el estado de los archivos
            self.actualizar_estado_archivos()
        else:
            messagebox.showerror(
                "Error en el recálculo",
                "❌ Hubo un error al recalcular los archivos.\n\n"
                "Revisa la ventana de progreso para ver los detalles del error."
            )
    
    def ejecutar_procesamiento(self):
        """Ejecuta el script de procesamiento del modelo"""
        if not self.csv_originales:
            messagebox.showwarning(
                "Archivo requerido",
                "Por favor selecciona al menos un archivo CSV de la Base de Datos.\n\n"
                "Los archivos deben tener años en el nombre (por ejemplo: 'consulta detalle embargos-2023-01.csv')"
            )
            return False
        
        # Obtener ruta del script de procesamiento (solo para referencia, no se usa en ejecutable)
        base_path = get_base_path()
        script_path = get_script_path("procesar_modelo.py")
        
        # Verificar que el script existe (solo para mostrar error si no está)
        if not os.path.exists(script_path):
            # En ejecutable, el script está en _MEIPASS, así que no verificar existencia aquí
            if not getattr(sys, 'frozen', False):
                messagebox.showerror(
                    "Error",
                    f"No se encontró el script de procesamiento: procesar_modelo.py\n\n"
                    f"Buscar en:\n{base_path}\n{os.path.dirname(os.path.abspath(__file__))}"
                )
                return False
        
        # Mostrar ventana de progreso modal
        progress_window = tk.Toplevel(self.root)
        progress_window.title("Procesando datos...")
        progress_window.geometry("600x300")
        progress_window.transient(self.root)
        progress_window.grab_set()
        
        # Centrar ventana de progreso
        progress_window.update_idletasks()
        x = (progress_window.winfo_screenwidth() // 2) - (600 // 2)
        y = (progress_window.winfo_screenheight() // 2) - (300 // 2)
        progress_window.geometry(f"600x300+{x}+{y}")
        
        progress_label = tk.Label(
            progress_window,
            text="🔄 Procesando archivos CSV y entrenando modelos...\n\nEsto puede tardar varios minutos.",
            font=("Arial", 11),
            justify=tk.CENTER
        )
        progress_label.pack(pady=20)
        
        progress_text = tk.Text(progress_window, height=12, wrap=tk.WORD, state=tk.DISABLED, font=("Courier", 9))
        progress_text.pack(padx=20, pady=10, fill=tk.BOTH, expand=True)
        
        scrollbar = tk.Scrollbar(progress_text)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        progress_text.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=progress_text.yview)
        
        # Botón para mantener la ventana abierta si hay errores
        btn_frame = tk.Frame(progress_window)
        btn_frame.pack(pady=5)
        
        def cerrar_ventana():
            progress_window.destroy()
        
        btn_cerrar = tk.Button(
            btn_frame,
            text="Cerrar",
            command=cerrar_ventana,
            font=("Arial", 9),
            bg="#3498db",
            fg="white",
            padx=20,
            pady=5
        )
        btn_cerrar.pack(side=tk.LEFT, padx=5)
        
        resultado = {'exito': False, 'error': None, 'completado': False}
        
        def ejecutar():
            try:
                import io
                import queue
                import threading
                
                # Cola para capturar la salida
                output_queue = queue.Queue()
                
                # Clase para redirigir stdout
                class OutputRedirect:
                    def __init__(self, queue, text_widget):
                        self.queue = queue
                        self.text_widget = text_widget
                    def write(self, text):
                        if text and text.strip():
                            self.queue.put(text)
                    def flush(self):
                        pass
                
                # Redirigir stdout
                old_stdout = sys.stdout
                sys.stdout = OutputRedirect(output_queue, progress_text)
                
                # Función para leer de la cola y mostrar en la UI
                def leer_salida():
                    while True:
                        try:
                            line = output_queue.get(timeout=0.1)
                            if line:
                                progress_text.config(state=tk.NORMAL)
                                progress_text.insert(tk.END, line)
                                progress_text.see(tk.END)
                                progress_text.config(state=tk.DISABLED)
                                progress_window.update()
                        except queue.Empty:
                            if resultado.get('completado', False):
                                break
                            continue
                        except:
                            break
                
                # Iniciar hilo para leer salida
                output_thread = threading.Thread(target=leer_salida, daemon=True)
                output_thread.start()
                
                try:
                    # Importar las funciones directamente
                    # Estrategia: intentar importar normalmente primero, si falla, cargar desde archivo
                    procesar_csv_original = None
                    entrenar_modelos_y_generar_predicciones = None
                    
                    # Intentar 1: Importar normalmente (funciona en script y a veces en ejecutable)
                    try:
                        import procesar_modelo
                        procesar_csv_original = procesar_modelo.procesar_csv_original
                        entrenar_modelos_y_generar_predicciones = procesar_modelo.entrenar_modelos_y_generar_predicciones
                        print("[INFO] Modulo procesar_modelo importado correctamente")
                    except ImportError:
                        # Intentar 2: Cargar desde archivo (necesario en ejecutable)
                        import importlib.util
                        
                        # Buscar el archivo en diferentes ubicaciones
                        script_locations = []
                        if getattr(sys, 'frozen', False):
                            meipass = getattr(sys, '_MEIPASS', None)
                            if meipass:
                                script_locations.append(os.path.join(meipass, "procesar_modelo.py"))
                            script_locations.append(os.path.join(os.path.dirname(sys.executable), "procesar_modelo.py"))
                        script_locations.append(script_path)
                        script_locations.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "procesar_modelo.py"))
                        
                        module_loaded = False
                        for script_loc in script_locations:
                            if os.path.exists(script_loc):
                                try:
                                    spec = importlib.util.spec_from_file_location("procesar_modelo", script_loc)
                                    if spec and spec.loader:
                                        module = importlib.util.module_from_spec(spec)
                                        spec.loader.exec_module(module)
                                        procesar_csv_original = module.procesar_csv_original
                                        entrenar_modelos_y_generar_predicciones = module.entrenar_modelos_y_generar_predicciones
                                        print(f"[INFO] Modulo cargado desde: {script_loc}")
                                        module_loaded = True
                                        break
                                except Exception as e:
                                    print(f"[ADVERTENCIA] Error al cargar desde {script_loc}: {e}")
                                    continue
                        
                        if not module_loaded:
                            raise ImportError(f"No se pudo cargar procesar_modelo desde ninguna ubicacion:\n" + "\n".join(script_locations))
                    
                    if procesar_csv_original is None or entrenar_modelos_y_generar_predicciones is None:
                        raise ImportError("No se pudieron importar las funciones necesarias de procesar_modelo")
                    
                    # Ejecutar el procesamiento
                    output_dir = get_data_path()
                    print("="*60)
                    print("PROCESANDO ARCHIVOS CSV DE LA BASE DE DATOS")
                    print("="*60)
                    print(f"Archivos a procesar: {len(self.csv_originales)}")
                    for f in self.csv_originales:
                        print(f"  - {os.path.basename(f)}")
                        if not os.path.exists(f):
                            raise FileNotFoundError(f"El archivo no existe: {f}")
                    print(f"\nDirectorio de salida: {output_dir}")
                    print(f"Verificando permisos de escritura...")
                    # Verificar que se puede escribir en el directorio
                    try:
                        test_file = os.path.join(output_dir, "test_write.tmp")
                        with open(test_file, 'w') as f:
                            f.write("test")
                        os.remove(test_file)
                        print(f"[OK] Permisos de escritura OK")
                    except Exception as e:
                        print(f"[ADVERTENCIA] Problema de permisos en {output_dir}: {e}")
                    print("="*60)
                    
                    # Paso 1: Procesar y consolidar
                    print("\n[INFO] Paso 1: Procesando y consolidando archivos CSV...")
                    print(f"[INFO] Llamando a procesar_csv_original con {len(self.csv_originales)} archivo(s)...")
                    consolidado_path = procesar_csv_original(self.csv_originales, output_dir)
                    
                    # Verificar que el archivo se generó
                    print(f"[INFO] Verificando que el archivo consolidado existe en: {consolidado_path}")
                    if not os.path.exists(consolidado_path):
                        # Buscar en otras ubicaciones posibles
                        posibles_rutas = [
                            consolidado_path,
                            os.path.join(output_dir, "embargos_consolidado_mensual.csv"),
                            os.path.join(os.path.dirname(output_dir), "embargos_consolidado_mensual.csv"),
                        ]
                        encontrado = False
                        for ruta in posibles_rutas:
                            if os.path.exists(ruta):
                                consolidado_path = ruta
                                encontrado = True
                                print(f"[INFO] Archivo encontrado en ubicación alternativa: {ruta}")
                                break
                        
                        if not encontrado:
                            raise FileNotFoundError(
                                f"El archivo consolidado no se generó.\n"
                                f"Ruta esperada: {consolidado_path}\n"
                                f"Rutas verificadas:\n" + "\n".join([f"  - {r}" for r in posibles_rutas])
                            )
                    print(f"[OK] Archivo consolidado generado: {consolidado_path}")
                    print(f"[INFO] Tamaño del archivo: {os.path.getsize(consolidado_path):,} bytes")
                    
                    # Paso 2: Entrenar modelos y generar predicciones
                    print("\n[INFO] Paso 2: Entrenando modelos y generando predicciones...")
                    entrenar_modelos_y_generar_predicciones(consolidado_path, output_dir)
                    
                    # Verificar que todos los archivos se generaron
                    archivos_esperados = [
                        "embargos_consolidado_mensual.csv",
                        "predicciones_oficios_validacion.csv",
                        "predicciones_oficios_futuro.csv",
                        "predicciones_demandados_validacion.csv",
                        "predicciones_demandados_futuro.csv",
                        "resultados_clasificaciones.csv"
                    ]
                    
                    print(f"\n[INFO] Verificando archivos generados...")
                    archivos_generados = []
                    archivos_faltantes = []
                    for archivo in archivos_esperados:
                        ruta_archivo = os.path.join(output_dir, archivo)
                        if os.path.exists(ruta_archivo):
                            tamaño = os.path.getsize(ruta_archivo)
                            print(f"  [OK] {archivo} ({tamaño:,} bytes)")
                            archivos_generados.append(archivo)
                        else:
                            print(f"  [ERROR] {archivo} NO encontrado en: {ruta_archivo}")
                            archivos_faltantes.append(archivo)
                    
                    # El archivo consolidado es CRÍTICO - debe existir siempre
                    if "embargos_consolidado_mensual.csv" in archivos_faltantes:
                        raise FileNotFoundError(
                            f"ERROR CRITICO: El archivo 'embargos_consolidado_mensual.csv' no se generó.\n"
                            f"Directorio esperado: {output_dir}\n"
                            f"Verifica que el procesamiento se completó correctamente."
                        )
                    
                    if archivos_faltantes:
                        print(f"\n[ADVERTENCIA] Algunos archivos no se generaron: {', '.join(archivos_faltantes)}")
                        print(f"[INFO] Esto puede ser normal si no hay suficientes datos para entrenar modelos")
                        print(f"[INFO] El archivo consolidado SÍ se generó, puedes usar el dashboard de embargos")
                    
                    print(f"\n[OK] Procesamiento completado. Archivos en: {output_dir}")
                    print(f"[INFO] Archivos generados exitosamente: {len(archivos_generados)}/{len(archivos_esperados)}")
                    
                    resultado['exito'] = True
                    resultado['completado'] = True
                    sys.stdout = old_stdout
                    progress_label.config(text="✅ Procesamiento completado exitosamente!\n\nPuedes cerrar esta ventana.")
                    # No cerrar automáticamente, dejar que el usuario cierre con el botón
                    
                    # Actualizar estado de archivos en el launcher después de un breve delay
                    self.root.after(500, self.actualizar_estado_archivos)
                    
                except Exception as e:
                    sys.stdout = old_stdout
                    resultado['completado'] = True
                    error_msg = str(e)
                    import traceback
                    error_trace = traceback.format_exc()
                    resultado['error'] = error_msg
                    
                    # Mostrar error en el texto también
                    progress_text.config(state=tk.NORMAL)
                    progress_text.insert(tk.END, f"\n\n{'='*60}\n")
                    progress_text.insert(tk.END, f"[ERROR CRITICO] Error durante el procesamiento\n")
                    progress_text.insert(tk.END, f"{'='*60}\n")
                    progress_text.insert(tk.END, f"Tipo de error: {type(e).__name__}\n")
                    progress_text.insert(tk.END, f"Mensaje: {error_msg}\n\n")
                    progress_text.insert(tk.END, f"Traceback completo:\n{error_trace}\n")
                    progress_text.see(tk.END)
                    progress_text.config(state=tk.DISABLED)
                    progress_window.update()
                    
                    progress_label.config(text="❌ El procesamiento falló.\n\nRevisa los detalles abajo y luego cierra esta ventana.")
                    # No cerrar automáticamente si hay error, dejar que el usuario lea y cierre manualmente
                    messagebox.showerror(
                        "Error en el procesamiento",
                        f"Hubo un error al procesar los archivos CSV.\n\n"
                        f"Error: {error_msg}\n\n"
                        f"Revisa la ventana de progreso para más detalles."
                    )
            except Exception as e:
                resultado['error'] = str(e)
                resultado['completado'] = True
                if 'progress_window' in locals():
                    progress_window.destroy()
                import traceback
                error_full = traceback.format_exc()
                messagebox.showerror("Error", f"Error al ejecutar el procesamiento:\n{error_full[:500]}")
        
        # Ejecutar en un hilo separado para no bloquear la UI
        thread = threading.Thread(target=ejecutar)
        thread.daemon = True
        thread.start()
        
        # Esperar a que termine (la ventana modal se cerrará automáticamente)
        self.root.wait_window(progress_window)
        
        return resultado.get('exito', False)
    
    def start_embargos_dashboard(self):
        """Inicia el dashboard de embargos"""
        # Verificar si ya está ejecutándose
        if self.active_processes["Embargos"] is not None:
            port = self.port_mapping["Embargos"]
            url = f"http://localhost:{port}"
            response = messagebox.askyesno(
                "Dashboard ya en ejecución",
                f"El Dashboard de Embargos ya está ejecutándose en:\n{url}\n\n¿Deseas abrirlo en el navegador?"
            )
            if response:
                webbrowser.open(url)
            return
        
        # Verificar si hay archivos generados, si no, ejecutar procesamiento
        data_path = get_data_path()
        base_path = get_base_path()
        
        # Buscar el archivo consolidado en múltiples ubicaciones
        consolidado_path = None
        posibles_rutas = [
            os.path.join(data_path, "embargos_consolidado_mensual.csv"),
            os.path.join(base_path, "embargos_consolidado_mensual.csv"),
            os.path.join(base_path, "datos", "embargos_consolidado_mensual.csv"),
        ]
        
        for ruta in posibles_rutas:
            if os.path.exists(ruta):
                consolidado_path = ruta
                break
        
        if not consolidado_path:
            if not self.csv_originales:
                messagebox.showwarning(
                    "Archivo requerido",
                    "Por favor selecciona el/los archivo(s) CSV de la Base de Datos primero.\n\n"
                    "Los archivos deben tener años en el nombre (por ejemplo: 'consulta detalle embargos-2023-01.csv')\n\n"
                    "Haz clic en '¿Cómo generar/obtener los CSV?' para más información."
                )
                return
            
            # Ejecutar procesamiento (bloquea hasta que termine)
            if not self.ejecutar_procesamiento():
                messagebox.showerror(
                    "Error",
                    "No se pudo procesar los archivos CSV.\n\n"
                    "Por favor verifica que los archivos CSV sean válidos e intenta nuevamente.\n\n"
                    "Revisa la ventana de progreso para ver los detalles del error."
                )
                return
            
            # Verificar nuevamente que el archivo se generó (buscar en todas las ubicaciones)
            consolidado_path = None
            for ruta in posibles_rutas:
                if os.path.exists(ruta):
                    consolidado_path = ruta
                    break
            
            if not consolidado_path:
                # Mostrar todas las ubicaciones donde se buscó
                rutas_buscadas = "\n".join([f"  - {r}" for r in posibles_rutas])
                messagebox.showerror(
                    "Error",
                    f"El procesamiento se completó pero no se encontró el archivo generado.\n\n"
                    f"Ubicaciones buscadas:\n{rutas_buscadas}\n\n"
                    f"Por favor verifica:\n"
                    f"1. Que el procesamiento se completó sin errores\n"
                    f"2. Que tienes permisos de escritura en: {data_path}\n"
                    f"3. Revisa la ventana de progreso para ver si hubo errores"
                )
                return
        
        # Iniciar dashboard (ya sea que existía el archivo o se generó)
        self._iniciar_dashboard_embargos()
    
    def _iniciar_dashboard_embargos(self):
        """Inicia el dashboard de embargos (método auxiliar)"""
        base_path = get_base_path()
        script_path = get_script_path("dashboard_embargos.py")
        data_path = get_data_path()
        
        # Buscar el archivo consolidado en múltiples ubicaciones
        consolidado_path = None
        posibles_rutas = [
            os.path.join(data_path, "embargos_consolidado_mensual.csv"),
            os.path.join(base_path, "embargos_consolidado_mensual.csv"),
            os.path.join(base_path, "datos", "embargos_consolidado_mensual.csv"),
        ]
        
        for ruta in posibles_rutas:
            if os.path.exists(ruta):
                consolidado_path = ruta
                break
        
        if not consolidado_path:
            rutas_buscadas = "\n".join([f"  - {r}" for r in posibles_rutas])
            messagebox.showerror(
                "Error",
                f"No se encontró el archivo 'embargos_consolidado_mensual.csv'.\n\n"
                f"Ubicaciones buscadas:\n{rutas_buscadas}\n\n"
                f"Por favor ejecuta el procesamiento primero seleccionando el CSV original de la BD."
            )
            return
        
        # Preparar archivos CSV
        csv_files = {
            "embargos_consolidado_mensual.csv": consolidado_path
        }
        
        # Ejecutar en segundo plano
        port = self.port_mapping["Embargos"]
        process = run_streamlit(script_path, base_path, "Embargos", csv_files, port)
        
        if process:
            self.active_processes["Embargos"] = process
            messagebox.showinfo(
                "Dashboard iniciado",
                f"✅ Dashboard de Embargos iniciado en http://localhost:{port}\n\n"
                "El menú permanecerá abierto para que puedas iniciar otros dashboards."
            )
        else:
            messagebox.showerror("Error", "No se pudo iniciar el dashboard")
    
    def start_predicciones_dashboard(self):
        """Inicia el dashboard de predicciones"""
        # Verificar si ya está ejecutándose
        if self.active_processes["Predicciones"] is not None:
            port = self.port_mapping["Predicciones"]
            url = f"http://localhost:{port}"
            response = messagebox.askyesno(
                "Dashboard ya en ejecución",
                f"El Dashboard de Predicciones ya está ejecutándose en:\n{url}\n\n¿Deseas abrirlo en el navegador?"
            )
            if response:
                webbrowser.open(url)
            return
        
        # Verificar si hay archivos generados, si no, ejecutar procesamiento
        data_path = get_data_path()
        predicciones_oficios = os.path.join(data_path, "predicciones_oficios_por_mes.csv")
        predicciones_demandados = os.path.join(data_path, "predicciones_demandados_por_mes.csv")
        resultados_clasificaciones = os.path.join(data_path, "resultados_clasificaciones.csv")
        
        missing_files = []
        if not os.path.exists(predicciones_oficios):
            missing_files.append("predicciones_oficios_por_mes.csv")
        if not os.path.exists(predicciones_demandados):
            missing_files.append("predicciones_demandados_por_mes.csv")
        if not os.path.exists(resultados_clasificaciones):
            missing_files.append("resultados_clasificaciones.csv")
        
        if missing_files:
            if not self.csv_originales:
                messagebox.showwarning(
                    "Archivo requerido",
                    "Por favor selecciona el/los archivo(s) CSV de la Base de Datos primero.\n\n"
                    "El modelo generará automáticamente los archivos necesarios."
                )
                return
            
            # Ejecutar procesamiento (bloquea hasta que termine)
            if not self.ejecutar_procesamiento():
                return
        
        # Iniciar dashboard (ya sea que existían los archivos o se generaron)
        self._iniciar_dashboard_predicciones()
    
    def _iniciar_dashboard_predicciones(self):
        """Inicia el dashboard de predicciones (método auxiliar)"""
        base_path = get_base_path()
        script_path = get_script_path("dashboard_predicciones.py")
        data_path = get_data_path()
        
        # Buscar los archivos generados
        csv_files = {}
        archivos_requeridos = [
            "predicciones_oficios_por_mes.csv",
            "predicciones_demandados_por_mes.csv",
            "resultados_clasificaciones.csv"
        ]
        
        missing_files = []
        for csv_name in archivos_requeridos:
            data_csv = os.path.join(data_path, csv_name)
            base_csv = os.path.join(base_path, csv_name)
            
            if os.path.exists(data_csv):
                csv_files[csv_name] = data_csv
            elif os.path.exists(base_csv):
                csv_files[csv_name] = base_csv
            else:
                missing_files.append(csv_name)
        
        if missing_files:
            messagebox.showerror(
                "Error",
                f"No se encontraron los siguientes archivos:\n" + "\n".join(f"- {f}" for f in missing_files) +
                "\n\nPor favor ejecuta el procesamiento primero."
            )
            return
        
        # Ejecutar en segundo plano
        port = self.port_mapping["Predicciones"]
        process = run_streamlit(script_path, base_path, "Predicciones", csv_files, port)
        
        if process:
            self.active_processes["Predicciones"] = process
            messagebox.showinfo(
                "Dashboard iniciado",
                f"✅ Dashboard de Predicciones iniciado en http://localhost:{port}\n\n"
                "El menú permanecerá abierto para que puedas iniciar otros dashboards."
            )
        else:
            messagebox.showerror("Error", "No se pudo iniciar el dashboard")

def main():
    """Función principal - crea y ejecuta la GUI"""
    root = tk.Tk()
    app = DashboardLauncher(root)
    root.mainloop()

if __name__ == "__main__":
    # Siempre ejecutar el launcher normal
    # Streamlit debe ejecutarse a través de subprocess para evitar errores de señales
    main()
