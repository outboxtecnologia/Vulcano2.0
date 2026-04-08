import os

EXTRA_CODE = """

# --- VULCANO MVP DAY 1 CRUD ENDPOINTS ---
from fastapi import Request

@app.post("/api/vulcano/empreendimentos")
async def post_empreendimentos(request: Request):
    try:
        data = await request.json()
        emp_id = data.get("empresa_id")
        if not emp_id:
            raise HTTPException(status_code=400, detail="empresa_id obrigatório")
            
        conn = get_conn("vulcano")
        cur = conn.cursor()
        
        # Generator for ID
        cur.execute("SELECT COALESCE(MAX(ID), 0) + 1 FROM EMPREENDIMENTO")
        new_id = cur.fetchone()[0]
        
        query = "INSERT INTO EMPREENDIMENTO (ID, NOME, METRAGEMTOTAL, CUSTOORCADO, RET, CODIGOEMPRESA, ATIVO) VALUES (?, ?, ?, ?, ?, ?, ?)"
        params = (
            new_id,
            str(data.get("nome", "")),
            float(data.get("metragem", 0) or 0),
            float(data.get("custo", 0) or 0),
            data.get("ret", "N"),
            int(emp_id),
            "S"
        )
        cur.execute(query, params)
        conn.commit()
        conn.close()
        
        return {"success": True, "id": new_id, "message": "Empreendimento cadastrado com sucesso!"}
    except Exception as e:
        if 'conn' in locals() and conn: conn.close()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/vulcano/vendas")
async def post_vendas(request: Request):
    try:
        data = await request.json()
        empresa_id = data.get("empresa_id")
        if not empresa_id:
            raise HTTPException(status_code=400, detail="empresa_id obrigatório")
            
        conn = get_conn("vulcano")
        cur = conn.cursor()
        
        # In this minimal MVP, we mock the master insert to the ERP, or simulate it:
        # We process VGV (Total)
        cur.execute("SELECT COALESCE(MAX(ID), 0) + 1 FROM VENDA")
        new_id = cur.fetchone()[0]
        
        query = "INSERT INTO VENDA (ID, IDEMPREENDIMENTO, NUMCADIMOB, DTOPER, DESCUNIDIMOB, TOTALVENDA, CODIGOEMPRESA, DISTRATO, PERMUTA) VALUES (?, ?, ?, ?, ?, ?, ?, 'N', 'N')"
        date_str = data.get("data", "")
        # Empreendimento in DB might require Integer ID not generic string, but keeping it flexible:
        id_empreendimento = int(data.get("id_empreendimento", 0) or 0)
        
        params = (
            new_id,
            id_empreendimento,
            "MVP-" + str(new_id),
            date_str,
            str(data.get("unidade", "")),
            float(data.get("total", 0) or 0),
            int(empresa_id)
        )
        cur.execute(query, params)
        conn.commit()
        conn.close()
        return {"success": True, "id": new_id, "message": "Venda cadastrada!"}
    except Exception as e:
        if 'conn' in locals() and conn: conn.close()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/distratos")
async def post_distratos(request: Request):
    try:
        data = await request.json()
        id_venda = data.get("id_venda")
        if not id_venda:
            raise HTTPException(status_code=400, detail="id_venda obrigatório")
            
        conn = get_conn("vulcano")
        cur = conn.cursor()
        
        cur.execute("SELECT COALESCE(MAX(ID), 0) + 1 FROM DISTRATO")
        new_id = cur.fetchone()[0]
        
        q_dist = "INSERT INTO DISTRATO (ID, IDVENDA, DATA, VALORDEVOLVIDO, DATAPAGAMENTO) VALUES (?, ?, ?, ?, ?)"
        pr_dist = (
            new_id,
            int(id_venda),
            data.get("data_distrato"),
            float(data.get("valor_devolvido", 0) or 0),
            data.get("data_pagamento")
        )
        cur.execute(q_dist, pr_dist)
        
        # update venda flag
        cur.execute("UPDATE VENDA SET DISTRATO = 'S', DATADISTRATO = ? WHERE ID = ?", (data.get("data_distrato"), int(id_venda)))
        
        conn.commit()
        conn.close()
        return {"success": True, "id": new_id, "message": "Distrato registrado!"}
    except Exception as e:
        if 'conn' in locals() and conn: conn.close()
        raise HTTPException(status_code=500, detail=str(e))
"""

with open("main.py", "a", encoding="utf-8") as f:
    f.write(EXTRA_CODE)

