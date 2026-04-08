"""Script para diagnosticar o que trava o startup do main.py"""
import sys
import time

steps = [
    ("fastapi", "from fastapi import FastAPI"),
    ("firebirdsql", "import firebirdsql"),
    ("pdfplumber", "import pdfplumber"),
    ("numpy", "import numpy as np"),
    ("pandas", "import pandas as pd"),
    ("dotenv", "from dotenv import load_dotenv"),
    ("vertexai", "import vertexai"),
    ("os/re/io", "import os, re, io, tempfile, asyncio, math"),
]

for name, stmt in steps:
    t = time.time()
    try:
        exec(stmt)
        elapsed = time.time() - t
        print(f"  [{elapsed:.2f}s] OK: {name}")
    except Exception as e:
        elapsed = time.time() - t
        print(f"  [{elapsed:.2f}s] ERRO: {name}: {e}")

print("\nAgora testando o main completo...")
t = time.time()
import subprocess, threading

def kill_after(proc, secs):
    time.sleep(secs)
    if proc.poll() is None:
        proc.kill()
        print(f"\n  TIMEOUT: main.py travou depois de {secs}s")

proc = subprocess.Popen(
    [sys.executable, "-c", "import sys; sys.path.insert(0,'.'); from main import app; print('main OK')"],
    stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
)
t_kill = threading.Thread(target=kill_after, args=(proc, 30))
t_kill.daemon = True
t_kill.start()

out, _ = proc.communicate()
print(f"  [{time.time()-t:.1f}s] main saida: {out[:500]}")
