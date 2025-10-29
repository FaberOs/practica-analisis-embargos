# launcher.py
# -*- coding: utf-8 -*-
import os, sys, socket, subprocess, webbrowser, threading, time
from pathlib import Path
import tkinter as tk
from tkinter import messagebox

# Soporta ruta temporal de PyInstaller (sys._MEIPASS)
APP_DIR = Path(getattr(sys, "_MEIPASS", Path(__file__).parent))
DASH_EMB = str((APP_DIR / "dashboard_embargos.py").resolve())
DASH_PRED = str((APP_DIR / "dashboard_predicciones.py").resolve())

PROCS = []

def puerto_libre(desde=8501, hasta=8599):
    for p in range(desde, hasta+1):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("", p))
                return p
            except OSError:
                continue
    raise RuntimeError("No hay puertos libres entre 8501-8599")

def _abrir_url_luego(url, delay=1.0):
    def _t():
        time.sleep(delay)
        webbrowser.open(url)
    threading.Thread(target=_t, daemon=True).start()

def run_streamlit(script_path, port=None):
    if not Path(script_path).exists():
        messagebox.showerror("Error", f"No encuentro {script_path}")
        return
    port = port or puerto_libre()
    url = f"http://localhost:{port}"
    env = os.environ.copy()
    env["STREAMLIT_SERVER_PORT"] = str(port)
    env["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] = "false"
    cmd = [sys.executable, "-m", "streamlit", "run", script_path, "--server.port", str(port)]
    try:
        p = subprocess.Popen(cmd, env=env)
        PROCS.append(p)
        _abrir_url_luego(url, 1.0)
        return port
    except Exception as e:
        try:
            from streamlit.web import bootstrap as st_bootstrap
            def _run():
                st_bootstrap.run(script_path, "", [], {})
            t = threading.Thread(target=_run, daemon=True)
            t.start()
            _abrir_url_luego(url, 1.0)
            return port
        except Exception as e2:
            messagebox.showerror("Error", f"No pude lanzar Streamlit:\n{e}\n{e2}")

def abrir_embargos():
    p = run_streamlit(DASH_EMB, port=8501)
    if p: status.set(f"Embargos en http://localhost:{p}")

def abrir_predicciones():
    p = run_streamlit(DASH_PRED, port=8502)
    if p: status.set(f"Predicciones en http://localhost:{p}")

def abrir_ambos():
    abrir_embargos()
    abrir_predicciones()

def salir():
    for p in PROCS:
        try: p.terminate()
        except Exception: pass
    root.destroy()

# --- UI
root = tk.Tk()
root.title("Dashboard Oficios Bancarios — Lanzador")
root.geometry("420x240")

title = tk.Label(root, text="Lanzador de Dashboards (Streamlit)", font=("Segoe UI", 12, "bold"))
title.pack(pady=10)

btn1 = tk.Button(root, text="📘 Abrir Embargos", width=26, command=abrir_embargos)
btn2 = tk.Button(root, text="🔮 Abrir Predicciones", width=26, command=abrir_predicciones)
btn3 = tk.Button(root, text="🚀 Abrir ambos", width=26, command=abrir_ambos)

btn1.pack(pady=4); btn2.pack(pady=4); btn3.pack(pady=8)

status = tk.StringVar(value="Listo. Elige qué abrir.")
tk.Label(root, textvariable=status, fg="#555").pack(pady=6)

root.protocol("WM_DELETE_WINDOW", salir)
root.mainloop()
