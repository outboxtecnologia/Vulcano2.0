import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import main

try:
    tables = main.api_tables("questor")
    print(tables['tables'][:5])
except Exception as e:
    print("Error:", e)
