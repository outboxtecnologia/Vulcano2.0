import uvicorn
import webbrowser
from threading import Timer
import sys
import os

def open_browser():
    webbrowser.open_new("http://127.0.0.1:8000")

def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

if __name__ == "__main__":
    print("Iniciando Questor Explorer (Modo Producao standalone)...")
    Timer(2, open_browser).start()
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False, workers=1)
