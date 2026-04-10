import re

with open(r"C:\Users\dirfe\.gemini\antigravity\scratch\questor_explorer\backend\main.py", "r", encoding="utf-8") as f:
    code = f.read()

replacement = """            except Exception as ml_err:
                import traceback
                err_str = str(ml_err) + " | " + traceback.format_exc()
                logging.error(f"Erro na inferência qualitativa do Gemini: {ml_err}")
                for a in anomalias:
                    a["causa_raiz"] = f"Erro na IA: {str(ml_err)[:150]}"
                    a["recomendacao"] = "A Vertex API falhou ao responder ou parsing falhou." """

code = code.replace("""            except Exception as ml_err:
                logging.error(f"Erro na inferência qualitativa do Gemini: {ml_err}")""", replacement)

with open(r"C:\Users\dirfe\.gemini\antigravity\scratch\questor_explorer\backend\main.py", "w", encoding="utf-8") as f:
    f.write(code)

print("Patch applied for displaying errors in UI.")
